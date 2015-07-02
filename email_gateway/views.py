""" Views hit by links that we send out in emails. """

import logging
from esapi.core import ESAPI
from esapi.validation_error_list import ValidationErrorList

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect

from advertiser.models import Advertiser
from common.contest import check_contest_is_running
from common.service.login_service import process_login
from common.service.payload_signing import PAYLOAD_SIGNING
from common.session import (create_consumer_in_session, clear_session, 
    check_if_i_own_this_coupon, get_consumer_id_in_session)
from consumer.models import (Consumer, UniqueUserToken, EmailSubscription,
    UnEmailableReason, ConsumerHistoryEvent)
from consumer.service import (get_consumer_instance_type, 
    process_consumer_opt_out)
from email_gateway.process import flag_bouncing_email, email_hash_decypher
from email_gateway.service.stupid_spam_complainers import (
    stupid_spam_complainers_check)
from email_gateway.send import send_email
from firestorm.connector import FirestormConnector
from firestorm.models import AdRep

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def catch_reverify_email(request, email_string):
    """ Usrs who want a new verification email can send an email to 
    verify@10coupons.com.  This will get forwarded to the smtp01 server at 
    address verify@bounces.10coupons.com, passed into procmail and a script 
    which will extract the email address of the sender and hit this view with 
    said address.  We'll determine if the person is verified or needs to be 
    verified and send them a new verifcation email or a "you're already 
    verified" email accordingly.
    """
    try:
        consumer = Consumer.objects.get(email=email_string)
        if not consumer.is_emailable:
            # TODO: Check consumer history to see if we should bother with them
            consumer.is_emailable = True
            consumer.unemailable_reason = []
            consumer.save()    
        context = {'to_email': consumer.email,
                'subject': 'Verify Email Request - %s' % consumer.site.domain,
                'from_address': 'Coupons', 
                'ref_num': consumer.id,
                'contest_is_running': check_contest_is_running()}
        send_email(template='consumer_welcome', site=consumer.site,
                context=context)
        event = ConsumerHistoryEvent.objects.create(
            consumer=consumer, 
            ip=request.META['REMOTE_ADDR'],
            event_type='5',
            )
        event.save()
        return HttpResponse("0 re: %s" % (consumer.email))
    except Consumer.DoesNotExist:
        return HttpResponse("1 re: %s DoesnotExist" % (email_string))

    
def opt_out_nochoice(request, email_hash=None):
    """ Pending deprecation 1/1/12.
    
    Wrapper for opt-out to account for old-style optout links. Was put here so
    urls wouldn't bork for not supplying enough arguments.
    """
    return opt_out(request=request, email_hash=email_hash)

def opt_out(request, email_hash=None, listid='01'):
    """ Pending deprecation 1/1/12. See opt_out_payload for new functionality.
    Process optout link from email. 
    """
    clear_session(request)
    try:
        email_hash = email_hash_decypher(email_hash)
        # Check if user exists in database.
        consumer = Consumer.objects.get(email_hash=email_hash)
        # Opt out of proper subscription.
        if listid[0] == '0':
            mailinglist = listid[1]
        else:
            mailinglist = listid[0:2]
        consumer.email_subscription.remove(mailinglist)
        optout_type = EmailSubscription.objects.get(id=mailinglist
                ).email_subscription_name
        event = ConsumerHistoryEvent.objects.create(
            consumer=consumer, 
            ip=request.META['REMOTE_ADDR'],
            data="Optout list: %s" % optout_type,
            event_type='1',
            )
        event.save()
    except Consumer.DoesNotExist:
        return HttpResponseRedirect(reverse('unsubscribe'))
    create_consumer_in_session(request, consumer)
    if mailinglist > '1':
        request.session['optout_type'] = optout_type
    return HttpResponseRedirect(reverse('opt-out-confirmation'))

def opt_out_payload(request, payload, listid=None):
    """ Process opt-out link from email. 
    Process changed 12/2011 to expect list in payload, backwards compatible
    to handle listid as string.
    """
    listid = listid or [1]
    payload_dict = PAYLOAD_SIGNING.handle_payload(request, payload)
    # Handle deprecated opt_out list format.
    subscription_list = payload_dict.get('subscription_list', listid)
    consumer_id = get_consumer_id_in_session(request)
    if consumer_id:
        try:
            # Check if user exists in database.
            consumer = Consumer.objects.get(id=consumer_id)
            # Opt out of proper subscription.
            process_consumer_opt_out(request, consumer, subscription_list)
        except (Consumer.DoesNotExist, ValueError):
            return HttpResponseRedirect(reverse('unsubscribe'))
    else:
        return HttpResponseRedirect(reverse('unsubscribe'))
    if type(subscription_list) in (unicode, str):
        try: # Deprecated version.
            if listid[0] == '0':
                subscription_list = [int(listid[1])]
            else:
                subscription_list = [int(listid[0:2])]
        except ValueError:
            # Ill formed listid, send to unsubscribe page.
            return HttpResponseRedirect(reverse('unsubscribe'))
    if sum(subscription_list) > 1:
        # Reset payload in case deprecated value was passed in so we dont have
        # to correct again.
        payload = PAYLOAD_SIGNING.create_payload(
            subscription_list=subscription_list)
        return HttpResponseRedirect(reverse('opt-out-confirmation', args=[
            payload]))
    return HttpResponseRedirect(reverse('opt-out-confirmation'))
    
def sale_redirect_with_session(request, payload, promo_code=None, 
        product_id=None, item_id=None):
    """ Process link from sale email to put a user and promo into session. """
    clear_session(request)
    PAYLOAD_SIGNING.handle_payload(request, payload)
    instance = ESAPI.validator()
    error_list = ValidationErrorList()
    promo_code = instance.get_valid_input('promo_code', promo_code, 
        'SafeDisplay', 20, True, error_list)
    if error_list:
        LOG.error(error_list)
    else:
        if promo_code:
            request.session['promo_code'] = promo_code
    if product_id and item_id:
        # Update session to make this item current.
        if int(product_id) == 2: 
            coupon_id = int(item_id)
            if check_if_i_own_this_coupon(request, coupon_id):
                # Set coupon_mode to RENEWAL so that coupon offer will display.
                request.session['coupon_mode'] = 'RENEWAL'
                return HttpResponseRedirect(reverse('preview-coupon'))
    return HttpResponseRedirect(reverse('advertiser-registration'))

def email_verify_consumer(request, payload):
    """ Process consumer double opt-in. """
    PAYLOAD_SIGNING.handle_payload(request, payload, opting=True)
    return HttpResponseRedirect(reverse('all-coupons'))

def email_add_subscriber(request, payload):
    """ Add consumer to session and load subscriber registration form. """
    PAYLOAD_SIGNING.handle_payload(request, payload, opting=False)
    return HttpResponseRedirect(reverse('subscriber-registration'))

def login_ad_rep_from_email(request, payload):
    """ Login ad_rep from payload, used primarily from email links. """
    PAYLOAD_SIGNING.handle_payload(request, payload)
    try:
        # Check if user exists in database.
        ad_rep = AdRep.objects.get(
            id=request.session['consumer']['consumer_id'])
    except (KeyError, AdRep.DoesNotExist):
        return HttpResponseRedirect(reverse('all-coupons'))
    return process_login_from_email(request, ad_rep.id)

def login_advertiser_from_email(request, payload):
    """ Process "go to account" login link from receipt. """
    PAYLOAD_SIGNING.handle_payload(request, payload)
    try:
        # Check if user exists in database.
        advertiser = Advertiser.objects.get(
                id=request.session['consumer']['advertiser']['advertiser_id'])
    except (KeyError, Advertiser.DoesNotExist):
        return HttpResponseRedirect(reverse('all-coupons'))
    return process_login_from_email(request, advertiser.id)

def process_login_from_email(request, user_id):
    """ Process the user that came from the payload in an email, log them in
    and perform necessary redirect.
    """
    user = User.objects.get(id=user_id)
    user.backend = 'django.contrib.auth.backends.ModelBackend'
    is_ad_rep = get_consumer_instance_type(user.email)[1]
    if is_ad_rep:
        # Do *not* authenticate them just redirect to firestorm back office.
        ad_rep = AdRep.objects.get(email=user.email)
        request.session['ad_rep_id'] = ad_rep.id
        redirect_path = reverse('ad-rep-account')
    else:
        redirect_path = process_login(request, user)
    return HttpResponseRedirect(redirect_path)

def remote_bounce_report(request, email_string, nomail_reason, 
                            email_type='N/A'):
    """
    Process bounces from the mail server.
    Gets hit with 10coupons/report-bouncing/INPUT/N/
      where input is an email address (for submitting by hand)
      or a signed payload from ten.common.payload_signing
      and N is the Consumer.UnEmailableReason for which this
      'bounce' applies
    """
    LOG.debug("Called remote_bounce_report( %s, %s)" % (email_string,
        nomail_reason))
    def do_flag(consumer, nomail_reason):
        """
        Response statuses:
        x type  value
        -x-
           0 - consumer found, set to bouncing
           1 - consumer found, already bouncing
           2 - consumer not found
        -type-
           email - value was interpreted as an email address
           hash - value was interpreted as a hash value
        -value-
           The input from the uri
        """

        email = consumer.email
        result = flag_bouncing_email(email, nomail_reason)
        LOG.debug("Called do_flag %s %s %s" % (email, nomail_reason, result))
        verbose_reason = UnEmailableReason.objects.get(id=nomail_reason)
        if nomail_reason == '3':
            # Spam report
            event_type = '3'
            stupid_spam_complainers_check(consumer, email_type)
        else:
            # Bounce report
            event_type = '4'
        event = ConsumerHistoryEvent.objects.create(
            consumer=consumer, 
            ip=request.META['REMOTE_ADDR'],
            data={  "nomail_reason": verbose_reason.name,
                    "email_type": email_type},
            event_type=event_type,
            )
        event.save()
        if result == 1:
            return HttpResponse("1 re: %s %s" % (email, verbose_reason.name))
        if result == 0:
            return HttpResponse("0 re: %s %s" % (email, verbose_reason.name))
    LOG.debug("do_flag defined")
    # Make sure we've received a valid unemailable reason.
    try: 
        UnEmailableReason.objects.get(id=nomail_reason)
    except UnEmailableReason.DoesNotExist:
        LOG.warning("nonexistant unemailable reason specified!!! %s" % 
            email_string)
        return HttpResponse("2 re: %s --bad reason--" % email_string) 
    # Check if email_string is an email address or an email_hash.
    # Hash won't have an @ symbol.
    try:
        email_string.index('@')
        # If we made it past that, try to grab the consumer.
        email = email_string
        try:
            consumer = Consumer.objects.get(email=email)
        except Consumer.DoesNotExist:
            LOG.warning("Email-string doesn't match any consumer! %s" %
                    email_string)
            return HttpResponse("2 re: %s" % email_string)
    except ValueError:
        try:
            if len(email_string) < 55:
                LOG.debug("assuming email_hash from %s, length %d" % (
                    email_string, len(email_string)))
                email_hash = email_hash_decypher(email_string)
                consumer = Consumer.objects.get(email_hash=email_hash)
                email = consumer.email
            else:
                LOG.debug("assuming PAYLOAD from %s, length %d" % (
                    email_string, len(email_string)))
                email_hash = 'payload -- %s' % email_string
                try:
                    email = PAYLOAD_SIGNING.parse_payload(email_string)['email']
                except KeyError:
                    LOG.warning(
                        "Payload apparently invalid %s, couldn't find email" % (
                            email_string))
                    return HttpResponse("2 re: %s" % email_string)
                consumer = Consumer.objects.get(email=email)
        except Consumer.DoesNotExist:
            LOG.warning("Hash doesn't match any consumer! %s" % email_hash)
            return HttpResponse("2 re: %s" % email_hash)
    return do_flag(consumer, nomail_reason)

def reset_password_from_email(request, email_token):
    """ Process link from reset-password email. """
    clear_session(request)
    _next = request.GET.get('_next', None)
    try:
        uniquetoken = UniqueUserToken.objects.get(hashstamp=email_token)
        if uniquetoken.is_expired():
            return HttpResponseRedirect(reverse('forgot-password'))
        else:
            user = uniquetoken.user
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            uniquetoken.delete()
            user.is_email_verified = True
            user.save()
            is_ad_rep = get_consumer_instance_type(user.email)[1]
            consumer = Consumer.objects.get(id=user.id)
            event = ConsumerHistoryEvent.objects.create(
                consumer=consumer, 
                ip=request.META['REMOTE_ADDR'],
                event_type='7',
                )
            event.save()
            if is_ad_rep:
                # Do *not* authenticate them; just redirect to firestorm back
                # office.
                ad_rep = AdRep.objects.get(email=user.email)
                return HttpResponseRedirect(
                    FirestormConnector().login_ad_rep(
                        request, ad_rep, user.password))
            else:
                redirect_path = process_login(request, user)
                return HttpResponseRedirect('%s?next=%s' %
                    (reverse('set-password'), redirect_path))
    except UniqueUserToken.DoesNotExist:
        return HttpResponseRedirect(reverse('forgot-password'))

def email_link_redirect(request, redir_path, payload):
    """ 
    Redirect user to the page specified by redir_path after building their
    session.
    """
    PAYLOAD_SIGNING.handle_payload(request, payload)
    return HttpResponseRedirect(redir_path)
