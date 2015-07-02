""" Celery tasks for sms_gateway """

import datetime
import logging
import re

from django.core import validators
from django.core.exceptions import ValidationError
from django.db.models import Count

from celery.decorators import task

from common.contest import check_contest_is_running
from consumer.models import Consumer
from consumer.service import create_consumer_from_email
from coupon.models import Coupon, SubscriberAction
from coupon.service.coupon_code_service import create_coupon_code
from coupon.tasks import RecordAction
from geolocation.models import USZip
from market.models import Site
from sms_gateway.service import (create_response_relationship,
    send_consumer_welcome, send_sms, subscribe_sender)
from subscriber.models import (Carrier, MobilePhone, SMSSubscription,
    Subscriber)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def advertise_handler(sms_message_received, subscriber, consumer):
    """ Respond to an sms_message that identifies an advertiser. """
    LOG.debug('matched ad')
    if not subscriber:
        subscriber = subscribe_sender(sms_message_received, '00000')
    subscriber.sms_subscription.add(2)
    if subscriber.subscriber_zip_postal == '00000':
        sent = send_sms(template='sms/request_zip.html', 
            smsto=sms_message_received.smsfrom)
    else:
        sent = send_sms(template='sms/opt_in_success.html', 
            smsto=sms_message_received.smsfrom, 
            context={'site': subscriber.site, 'consumer': consumer})
    return sent
    
def help_handler(sms_message_received, subscriber):
    """ Respond to an sms message that is a request for help. """
    LOG.debug('matched help')
    if not subscriber:
        # Can't send a response unless we have a subscriber and phone.
        subscribe_sender(sms_message_received, '00000')
    sent = send_sms(template='sms/help.html', 
        smsto=sms_message_received.smsfrom)
    return sent

def con_is_sub_subhandler(sms_message_received, subscriber, consumer, 
        consumer_by_email):
    """ 
    Respond to an sms_message that is an email address of a registered
    consumer who is a subscriber.
    """
    if subscriber == consumer_by_email.subscriber:
        LOG.debug('We have a match!')
        if subscriber.sms_subscription.filter(id=1).count() == 1:
            sent = send_sms(template='sms/opt_in_success.html', 
                smsto=sms_message_received.smsfrom, 
                context={'site': consumer.site, 'consumer': consumer})
        else:
            LOG.debug('Not already subscribed')
            sent = send_sms(template='sms/request_double_opt_in.html', 
                smsto=sms_message_received.smsfrom)
    elif subscriber:
        LOG.debug('Mismatch.')
        sent = send_consumer_welcome(consumer_by_email, 
            sms_message_received.smsfrom)
    else:
        LOG.debug('New phone number for this consumer?')
        subscribe_sender(sms_message_received,
            consumer_by_email.consumer_zip_postal)
        sent = send_consumer_welcome(consumer_by_email, 
            sms_message_received.smsfrom)
    return sent
    
def con_not_sub_subhandler(sms_message_received, subscriber, consumer, 
        consumer_by_email):
    """
    Respond to an sms message that is an email address of a registered
    consumer who is not a subscriber.
    """
    if subscriber:
        if consumer:
            # Confict! We knew this subscriber by another email!
            LOG.info("""Subscriber %s sent %s which is consumer %s
                which didn't match %s""" % (subscriber, consumer_by_email.email, 
                consumer_by_email.id, consumer.id))
            sent = send_consumer_welcome(consumer_by_email, 
                sms_message_received.smsfrom)
        else:
            # Relate subscriber to consumer_by_email.
            consumer_by_email.subscriber = subscriber
            if subscriber.subscriber_zip_postal == '00000':
                subscriber.subscriber_zip_postal = consumer.consumer_zip_postal
                subscriber.save()
            elif consumer_by_email.consumer_zip_postal == '00000':
                consumer_by_email.consumer_zip_postal = \
                    subscriber.subscriber_zip_postal
            consumer_by_email.save()
            if subscriber.sms_subscription.filter(id=1):
                sent = send_sms(template='sms/opt_in_success.html', 
                    smsto=sms_message_received.smsfrom, 
                    context={'site': subscriber.site, 'consumer': consumer})
            else:
                sent = send_sms(template='sms/request_double_opt_in.html', 
                    smsto=sms_message_received.smsfrom)
    else:
        # Create a subscriber for consumer.
        LOG.debug('Creating a subscriber for this consumer')
        subscriber = subscribe_sender(sms_message_received, 
            consumer_by_email.consumer_zip_postal)
        consumer_by_email.subscriber = subscriber
        consumer_by_email.save()
        sent = send_sms(template='sms/request_double_opt_in.html', 
            smsto=sms_message_received.smsfrom)
    return sent
    
def no_consumer_subhandler(sms_message_received, subscriber, sms_subscription,
        consumer, email):
    """ 
    Respond to an sms_message that is an email address when we have no
    registered consumer by that address.
    
    This could be:
        - a new subscriber who should also become a consumer.
        - an existing subscriber who doesn't have a consumer yet.
        - an existing subscriber who already has a different consumer.
    """
    LOG.debug('In no_consumer_subhandler')
    if subscriber:
        if consumer:
            LOG.debug('Consumer needs to be updated with new email.')
            consumer.email = email
            consumer.save()
        else:
            LOG.debug('Calling create_consumer_from_email')
            consumer = create_consumer_from_email(email, subscriber)
            LOG.debug('Retured from create_consumer_from_email')
            LOG.debug('consumer: %s' % consumer)
        if subscriber.subscriber_zip_postal == '00000':
            sent = send_sms(template='sms/request_zip.html', 
                smsto=sms_message_received.smsfrom)
        else:
            # Send confirmation email for consumer...
            sent = send_consumer_welcome(consumer, 
                sms_message_received.smsfrom)
            # Record this reponse rel now, before sending 2nd response.
            create_response_relationship(
                received_smsid=sms_message_received.smsid, sent_smsid=sent)
            if sms_subscription:
                sent = send_sms(template='sms/opt_in_success.html', 
                    smsto=sms_message_received.smsfrom, 
                    context={'site': subscriber.site, 'consumer': consumer})
            else:
                sent = send_sms(template='sms/request_double_opt_in.html', 
                    smsto=sms_message_received.smsfrom)
    else:
        LOG.debug('Calling create_consumer_from_email')
        subscriber = subscribe_sender(sms_message_received, '00000')
        consumer = create_consumer_from_email(email, subscriber)
        LOG.debug('Retured from create_consumer_from_email')
        LOG.debug('consumer: %s' % consumer)
        sent = send_sms(template='sms/request_zip.html', 
            smsto=sms_message_received.smsfrom)
    return sent

def email_handler(smsmsg, sms_message_received, subscriber, sms_subscription, 
        consumer):
    """ Respond to an sms_message that is an email address. """
    for word in smsmsg.rsplit():
        if re.search('@', word):
            email = word
            break
    try:
        validators.validate_email(email)
    except ValidationError:
        error_message = 'Quit. Invalid email %s in message %s' % (email, 
            smsmsg)
        LOG.info(error_message)
        raise ValidationError(error_message)
    LOG.debug('process_received_sms matched @ %s' % smsmsg)
    # consumer can only be true if there was a subscriber, but check for
    # one now based on this email address.
    try:
        consumer_by_email = Consumer.objects.get(email=email)
    except Consumer.DoesNotExist:
        consumer_by_email = None
    LOG.debug('consumer_by_email: %s' % consumer_by_email)
    if consumer_by_email:
        if consumer_by_email.subscriber:
            sent = con_is_sub_subhandler(sms_message_received, subscriber, 
                consumer, consumer_by_email)
        else:    
            # We knew this consumer, but didn't have a mobile phone for him.
            sent = con_not_sub_subhandler(sms_message_received, subscriber, 
                consumer, consumer_by_email)
    else:
        sent = no_consumer_subhandler(sms_message_received, subscriber, 
            sms_subscription, consumer, email)
    return sent

def no_handler(sms_message_received, subscriber, sms_subscription, consumer):
    """ Respond to an sms message that is the word 'no'. """
    LOG.debug('matched no')
    if subscriber:
        if subscriber.subscriber_zip_postal == '00000':
            sent = send_sms(template='sms/request_zip.html',
                smsto=sms_message_received.smsfrom)
        else:
            if sms_subscription:
                subscriber.sms_subscription.clear()
                sent = send_sms(template='sms/opt_out_success.html',
                    smsto=sms_message_received.smsfrom)
            else:
                contest_is_running = check_contest_is_running()
                sms_context = {
                        'contest_is_running': contest_is_running,
                        'consumer': consumer,
                    }
                sent = send_sms(template='sms/verify_success.html',
                    smsto=sms_message_received.smsfrom, context=sms_context)
    else:
        subscribe_sender(sms_message_received, '00000')
        sent = send_sms(template='sms/request_zip.html',
            smsto=sms_message_received.smsfrom)
    return sent

def save_handler(sms_message_received, subscriber):
    """ Respond to an sms message that is the word 'save'. """
    LOG.debug('matched save')
    if subscriber:
        if subscriber.subscriber_zip_postal == '00000':
            sent = send_sms(template='sms/request_zip.html', 
                smsto=sms_message_received.smsfrom)
        else:
            sent = send_sms(template='sms/request_double_opt_in.html', 
                smsto=sms_message_received.smsfrom)
    else:
        subscribe_sender(sms_message_received, '00000')
        sent = send_sms(template='sms/request_zip.html', 
            smsto=sms_message_received.smsfrom)
    return sent
    
def unsubscribe_handler(sms_message_received, subscriber):
    """ Respond to an sms message that is a request to opt opt. """
    if subscriber:
        subscriber.sms_subscription.clear()
    else:
        # Can't send a response unless we have a subscriber and phone.
        subscribe_sender(sms_message_received, '00000')
    sent = send_sms(template='sms/opt_out_success.html', 
        smsto=sms_message_received.smsfrom)
    return sent

def word_email_handler(sms_message_received, subscriber, consumer):
    """ 
    Respond to an sms message that is the word 'email', as opposed to an
    email address.
    """
    LOG.debug('matched word email')
    if subscriber:
        if subscriber.subscriber_zip_postal == '00000':
            sent = send_sms(template='sms/request_zip.html', 
                smsto=sms_message_received.smsfrom)
        elif consumer:
            sent = send_consumer_welcome(consumer, sms_message_received.smsfrom)
        else:
            sent = send_sms(template='sms/request_email_address.html', 
                smsto=sms_message_received.smsfrom)
    else:
        # Can't send a response unless we have a subscriber and phone.
        subscribe_sender(sms_message_received, '00000')
        sent = send_sms(template='sms/request_zip.html', 
            smsto=sms_message_received.smsfrom)
    return sent
    
def yes_handler(sms_message_received, subscriber, sms_subscription,
        consumer):
    """ Respond to an sms message that is the word 'yes'. """
    LOG.debug('matched yes')
    if subscriber:
        if subscriber.subscriber_zip_postal == '00000':
            sent = send_sms(template='sms/request_zip.html', 
                smsto=sms_message_received.smsfrom)
        else:
            if sms_subscription:
                LOG.debug('Already subscribed')
            else:
                subscriber.sms_subscription.add(1)
                LOG.debug('Added sms subscription')
            sent = send_sms(template='sms/opt_in_success.html', 
                smsto=sms_message_received.smsfrom,
                context={'site': subscriber.site, 'consumer': consumer})
    else:
        subscribe_sender(sms_message_received, '00000')
        sent = send_sms(template='sms/request_zip.html', 
            smsto=sms_message_received.smsfrom)
    return sent

def zip_handler(smsmsg, sms_message_received, subscriber, sms_subscription, 
        consumer):
    """ Respond to an sms_message that is a zip code. """
    smsmsg = smsmsg[:5]
    LOG.debug('matched pattern for zip %s' % smsmsg)
    # It is a number, but is it a real zip?
    try:
        code = smsmsg
        USZip.objects.get(code=code)
        # Is this zip related to a market?
        try:
            site = Site.objects.get_sites_this_zip(code=code)[0]
            LOG.debug('matched site %s' % site.name)
        except IndexError:
            site = Site.objects.get(id=1)
            LOG.debug('default site %s' % site.name)
    except USZip.DoesNotExist:
        log_message = 'no matching zip code: %s' % smsmsg
        LOG.info(log_message)
        site = Site.objects.get(id=1)
        code = '00000'
    if subscriber:
        if site.id != 1:
            subscriber.site = site
        if code != '00000':
            subscriber.subscriber_zip_postal = code
        subscriber.save()
        if consumer:
            if site.id != 1:
                consumer.site = site
            if code != '00000':
                consumer.consumer_zip_postal = code
            consumer.save()
        if sms_subscription == False:
            LOG.debug('Adding sms subscription')
            subscriber.sms_subscription.add(1)
        sent = send_sms(template='sms/opt_in_success.html', 
            smsto=sms_message_received.smsfrom, 
            context={'site': site, 'consumer': consumer})
    else:
        subscribe_sender(sms_message_received, code)
        sent = send_sms(template='sms/request_double_opt_in.html', 
            smsto=sms_message_received.smsfrom)
    return sent

def info_collector(sms_message_received):
    """
    Return objects needed to make decisions. Perform initial processing on them.
    """
    is_mobile_phone_update = False
    mobile_phone = None
    subscriber = None
    sms_subscription = None
    consumer = None
    try:
        mobile_phone = MobilePhone.objects.get(
            mobile_phone_number=sms_message_received.smsfrom)
        subscriber = Subscriber.objects.get(mobile_phones=mobile_phone)
        sms_subscription = SMSSubscription.objects.filter(
            subscribers=subscriber, id=1).count()
        LOG.debug('subscriber %s' % subscriber)
        LOG.debug('subscriber.subscriber_zip_postal %s'
             % subscriber.subscriber_zip_postal)
        LOG.debug('sms_subscription %s' % sms_subscription)     
        try:
            consumer = Consumer.objects.get(subscriber=subscriber)
            LOG.debug('consumer %s' % consumer)
            LOG.debug('consumer.consumer_zip_postal %s' 
                % consumer.consumer_zip_postal)
        except Consumer.DoesNotExist:
            LOG.debug('no consumer')
    except (MobilePhone.DoesNotExist, Subscriber.DoesNotExist):
        LOG.debug('no subscriber')
    # Update mobile_phone.carrier if this info is different.
    if subscriber \
    and mobile_phone.carrier.carrier != sms_message_received.network:
        try:
            mobile_phone.carrier = Carrier.objects.get(
                carrier=sms_message_received.network)
        except Carrier.DoesNotExist:
            error_message = "No carrier matching %s" % (
                sms_message_received.network)
            LOG.error(error_message)
            raise Carrier.DoesNotExist(error_message)
        LOG.debug('replacing %s with %s' %
            (mobile_phone.carrier.carrier, sms_message_received.network))
        is_mobile_phone_update = True
    if mobile_phone and not mobile_phone.is_verified:
        mobile_phone.is_verified = True
        is_mobile_phone_update = True
    if is_mobile_phone_update:
        mobile_phone.save()
    return subscriber, sms_subscription, consumer

@task()
def process_received_sms(sms_message_received):
    """
    Process a received message.
    
    If sender requested an action, perform that action and send a response. 
    """
    LOG.debug('process_received_sms task running for %s' % 
        sms_message_received.id) 
    is_opt_out = False
    # Get info we will need to make decisions.
    subscriber, sms_subscription, consumer = info_collector(
        sms_message_received)
    # Parse the message to see if we need to respond.
    smsmsg = sms_message_received.smsmsg.lower().strip()
    # Remove a common prefix.
    if smsmsg[:4] == 're:|':
        smsmsg = smsmsg[4:]
    # help, help*, *elp
    if re.match('help|[a-z0-9]*elp$', smsmsg):
        sent = help_handler(sms_message_received, subscriber)
    # Spec to match: STOP, STOP*, *STOP, STOPALL, STOPALL*, *STOPALL, 
    # TOPALL, *TOPALL, STOPAL, STOPAL*, QUIT, QUIT*, *QUIT, QUI, UIT, END, 
    # END*, *END, CANCEL, CANCEL*, *CANCEL, ANCEL, *ANCEL, CANCE, CANCE*, 
    # UNSUBSCRIBE, UNSUBSCRIBE*, *UNSUBSCRIBE, NSUBSCRIBE, NSUBSCRIBE, 
    # UNSUB********
    elif re.match('stop|[a-z0-9]*stop(?:all)?$|[a-z0-9]*topall$|stopal', smsmsg) \
        or re.match('quit|qui$|[a-z0-9]*quit|uit$|end', smsmsg) \
        or re.match('[a-z0-9]*end$|cance|[a-z0-9]*ancel$', smsmsg) \
        or re.match('unsub|[a-z0-9]*unsubscribe$|nsubscribe$', smsmsg):
        LOG.debug('matched stop %s' % smsmsg)
        is_opt_out = True
        sent = unsubscribe_handler(sms_message_received, subscriber)
    elif smsmsg in ('save', 'sav', 'ave'):
        sent = save_handler(sms_message_received, subscriber)
    elif re.match('no', smsmsg):
        sent = no_handler(sms_message_received, subscriber, sms_subscription,
            consumer)
    elif re.match('y$|yes', smsmsg):
        sent = yes_handler(sms_message_received, subscriber, sms_subscription, 
            consumer)
    elif re.match("\d{5}", smsmsg):
        sent = zip_handler(smsmsg, sms_message_received, subscriber, 
            sms_subscription, consumer)
    elif re.search('@', smsmsg):
        try:
            sent = email_handler(smsmsg, sms_message_received, subscriber, 
                sms_subscription, consumer)
        except ValidationError:
            return
    elif smsmsg in ('ad', 'advert', 'advertise', 'advertiser'):
        sent = advertise_handler(sms_message_received, subscriber, consumer)
    # Not an actual email address, but the word 'EMAIL' etc. This needs to be
    # late as the regular expression is loose.
    elif re.match('email|coupon', smsmsg) :
        sent = word_email_handler(sms_message_received, subscriber, consumer)
    else:
        error_message = 'quit. No matching pattern: %s' % smsmsg
        LOG.info(error_message)
        return
    create_response_relationship(received_smsid=sms_message_received.smsid, 
        sent_smsid=sent, is_opt_out=is_opt_out)

@task()
def text_blast_coupon(coupon):
    """ Sends an SMS coupon to opted in subscribers. """
    LOG.info('Text blast beginning for coupon %s.' % (coupon.id))
    action_id = 11 # Text Blasted
    if coupon.coupon_type.coupon_type_name != 'Paid':
        LOG.debug('coupon is not Paid, is %s' % 
            coupon.coupon_type.coupon_type_name)
        return
    if coupon.subscriber_actions.filter(action__id = action_id).count() > 0:
        LOG.debug('coupon has already been blasted')
        return
    if coupon.is_redeemed_by_sms == False:
        LOG.debug('coupon does not allow sms')
        return
    if coupon.is_approved == False:
        LOG.debug('coupon is not approved')
        return
    # Get the relevant zipcode to blast to.
    try:
        zipcode = coupon.location.filter(
            location_zip_postal__gt=0)[0].location_zip_postal
    except IndexError:
        LOG.debug('coupon has no zipcode')
        return 
    LOG.debug('zipcode: %s' % (zipcode))
    # Exclude subscribers who who have already been blasted 4 times this month.
    today = datetime.datetime.today()
    first_of_month = today.strftime("%Y-%m-01")
    max_blasted = Subscriber.objects.filter(
            subscriber_actions__action__id=action_id,
            subscriber_actions__create_datetime__gt=first_of_month
        ).annotate(number_of_blasts=Count('subscriber_actions')).filter(
            number_of_blasts__gt=4)
    LOG.info('max blasted: %s' % (max_blasted.count()))
    # Exclude subscribers who have already been SMS blasted this coupon
    # or texted it to themselves.
    previously_blasted = Subscriber.objects.filter(
        subscriber_actions__coupon=coupon)
    LOG.info('previously blasted: %s' % (previously_blasted.count()))    
    # Exclude subscribers who have received a blast from this business in the 
    # past 30 days.
    thirty_days_ago = today - datetime.timedelta(days=30)
    previously_business_blasted = Subscriber.objects.filter(
        subscriber_actions__in=(
            SubscriberAction.objects.filter(
                coupon__offer__business=coupon.offer.business,
                create_datetime__gt=thirty_days_ago)))
    LOG.info('previously_business_blasted: %s' % (
        previously_business_blasted.count()))
    # Exclude subscribers who are inactive consumers.
    subscribers = Subscriber.objects.select_related(
            'mobile_phone__mobile_phone_number'
        ).filter(
            subscriber_zip_postal=zipcode, sms_subscription=1
        ).exclude(
            id__in=Consumer.objects.filter(
                    subscriber__id__gt=0, is_active=False
                ).values_list('subscriber__id', flat=True)
        ).exclude(
            id__in=previously_blasted
        ).exclude(
            id__in=previously_business_blasted
        ).exclude(
            id__in=max_blasted
        )
    LOG.info('so far to do %s subscribers' % (subscribers.count()))
    # Include the advertiser.
    if coupon.offer.business.advertiser.subscriber:
        advertiser_sub = Subscriber.objects.filter(
            id=coupon.offer.business.advertiser.subscriber.id)
        LOG.info('Also sending to advertiser sub: %s' % (advertiser_sub[0].id))
        subscribers = subscribers | advertiser_sub
    LOG.info('to do %s subscribers' % (subscribers.count()))
    for subscriber in subscribers:
        coupon_code = create_coupon_code(coupon, 4)
        context = { 'coupon': coupon, 'coupon_code': coupon_code }
        send_sms(template='sms/coupon.html', 
            smsto=subscriber.mobile_phones.all()[0].mobile_phone_number, 
            context=context)
        RecordAction().run(action_id, coupon.id, [], subscriber.id)

@task()
def text_blast_approved_coupons():
    """ 
    A housecleaning process to blast coupons that were not blasted 
    by normal method.
    """
    catchup_date = datetime.datetime.today() - datetime.timedelta(days=10)
    coupons = Coupon.objects.filter(is_approved=True, is_redeemed_by_sms=True,
        coupon_create_datetime__gt=catchup_date,
        coupon_type__coupon_type_name='Paid')
    for coupon in coupons:
        text_blast_coupon(coupon)
