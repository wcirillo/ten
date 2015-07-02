""" Service functions for consumer app. """

import logging

from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from consumer.models import Consumer, SalesRep, ConsumerHistoryEvent
from geolocation.service import qry_consumer_count_spread
from market.models import Site
from subscriber.models import Subscriber, MobilePhone
from subscriber.service import (update_mobile_phone_if_diff,
    update_subscriber_if_diff)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

def add_or_update_consumer(email, zip_postal, site):
    """ Add consumer if it doesn't exist, update it if it has changed. """
    try:
        # Check if user exists already.
        consumer = Consumer.objects.get(email__iexact=email)
        if consumer.consumer_zip_postal != zip_postal and zip_postal:
            consumer.consumer_zip_postal = zip_postal
        if consumer.site.id != site.id and site.id != 1:
            consumer.site = site
        consumer.save()
    except Consumer.DoesNotExist:
        # Wrapped in try for race condition. 
        try:
            consumer = Consumer.objects.create_consumer(username=email, 
                email=email, consumer_zip_postal=zip_postal, site=site)
        except ValidationError:
            # Prevent race condition, where creation of consumer is 
            # attempted twice rapidly - grab the consumer.
            consumer = Consumer.objects.get(email__iexact=email)
        # Subscribe this consumer to the Flyer if they don't have this 
        # subscription already.
        consumer.email_subscription.add(1)
    return consumer
            
def get_consumer_instance_type(email):
    """ Determine the instance type of Consumer. """
    is_ad_rep = False
    try:
        instance = Consumer.objects.filter(email=email).values_list(
            'adrep__id', 'advertiser__id', 'mediapartner__media_groups',
            'mediapartner__affiliates')[0]
        user_type = 'consumer'
        if instance[0]:
            is_ad_rep = True
        if instance[1]:
            user_type = 'advertiser'
        elif instance[2]:
            user_type = 'media_group_partner'
        elif instance[3]:
            user_type = 'affiliate_partner'               
    except IndexError:
        user_type = None
    return user_type, is_ad_rep

def build_consumer_count_list(site_id):
    """ Build the consumer count for a site grouped by county and zip, include
    city names. Sort by county name, city name, zip code.
    """
    rs_counts = qry_consumer_count_spread(site_id)
    county_set = set()
    county_dict = {}
    county_list = []
    for record in rs_counts:
        row_county = record[0]
        row_county_id = record[1]
        row_city = record[2]
        row_city_id = record[3]
        row_zip = record[4]
        row_zip_id = record[5]
        row_count = record[6]
        county_set.add(row_county)
        try:
            county_dict[row_county]['county_count'] += row_count
            county_dict[row_county]['county_id'] = row_county_id
            city_index = len(county_dict[row_county]['cities'])
            
            if county_dict[row_county]['cities'][city_index - 1]['city'] == \
                row_city:
                county_dict[row_county]['cities'][city_index - 1]['city_count'] \
                    += row_count
            else: # City doesnt exist yet.
                county_dict[row_county]['cities'].append({'city': row_city,
                    'city_count': row_count, 'city_id': row_city_id,
                    'zips': []})
                city_index += 1
            county_dict[row_county]['cities'][city_index - 1]['zips'].append(
                    {'zip':row_zip, 'zip_id':row_zip_id, 'zip_count':row_count})
        except KeyError: # County doesnt exist yet.
            county_dict.update({'%s' % row_county: {
                'county': row_county,
                'cities': [
                           {'city': row_city,
                            'city_count': row_count,
                            'city_id': row_city_id,
                            'zips': [{'zip':row_zip, 'zip_id':row_zip_id,
                                'zip_count':row_count}]}],
                'county_count':row_count,
                'county_id':row_county_id
                }
            })
    for item in sorted(county_set):
        county_list.append(county_dict[item])
    return county_list

@transaction.commit_manually
def create_consumer_from_email(email, subscriber):
    """ Create a minimal Consumer from an email address and a subscriber.
    Return False if this email exists for another user.

    This function is used by the sms_gateway app when someone sends in an sms
    message which is an email address: we have a subscriber and need to create a
    consumer for the subscriber.
    """
    consumer_zip_postal = subscriber.subscriber_zip_postal
    site = subscriber.site
    try:
        consumer = Consumer.objects.get(email__iexact=email)
        LOG.error('Consumer by this email already exists.')
        transaction.commit()
        return False
    except Consumer.DoesNotExist:
        pass
    try:
        consumer = Consumer.objects.create_consumer(username=email, email=email,
            consumer_zip_postal=consumer_zip_postal, site=site)    
    except IntegrityError as error:
        transaction.rollback()
        LOG.error(error)
        return False
    if subscriber:
        # Associate this consumer with this subscriber.
        consumer.subscriber = subscriber
        consumer.save()
        ConsumerHistoryEvent.objects.create(
            consumer=consumer, 
            data={"Subscriber signup mobile number":  
                subscriber.mobile_phones.all()[0].mobile_phone_number},
            event_type='0',
            )
    transaction.commit()
    return consumer

@transaction.commit_manually
def create_subscriber_for_consumer(consumer, carrier_id, mobile_phone_number, 
        subscriber_zip_postal, site):
    """ Create a subscriber and relate to a preexisting consumer. """
    # Does consumer have a subscriber?
    if consumer.subscriber:
        try: 
            # Check if phone record exists already.
            mobile_phone = MobilePhone.objects.get(
                mobile_phone_number=mobile_phone_number)
            if mobile_phone.subscriber != consumer.subscriber:
                transaction.commit()
                return 1
            else:
                update_mobile_phone_if_diff(mobile_phone, carrier_id)
        except MobilePhone.DoesNotExist:
            MobilePhone.objects.create(mobile_phone_number=mobile_phone_number,
                    carrier_id=carrier_id, subscriber=consumer.subscriber)
        transaction.commit()
        return 0
    else:
        # Is phone number in use?
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones=MobilePhone.objects.get(
                    mobile_phone_number=mobile_phone_number))
            try:
                # Does subscriber with this number belong to another consumer? 
                Consumer.objects.exclude(id=consumer.id).get(
                    subscriber=subscriber)
                transaction.commit()
                return 1
            except Consumer.DoesNotExist:
                consumer.subscriber = subscriber
                consumer.save()
                update_subscriber_if_diff(subscriber,
                    subscriber_zip_postal, site)
            mobile_phone = MobilePhone.objects.get(
                mobile_phone_number=mobile_phone_number, 
                subscriber=consumer.subscriber)
            update_mobile_phone_if_diff(mobile_phone, carrier_id)
        except (MobilePhone.DoesNotExist, Subscriber.DoesNotExist):
            consumer = add_subscriber_to_this_consumer(consumer=consumer, 
                subscriber_zip_postal=subscriber_zip_postal, site=site)
            try:
                MobilePhone.objects.create(
                    mobile_phone_number=mobile_phone_number,
                    carrier_id=carrier_id, subscriber=consumer.subscriber)
            except IntegrityError:
                # Race condition.
                transaction.rollback()
        transaction.commit()
        return 0

def get_site_rep(site):
    """ Get the sales rep for this site, add attribute email_domain to obj. """
    try:
        sales_rep = SalesRep.objects.select_related(
            'consumer').get(sites=site)
        sales_rep.email_domain = site.domain
    except SalesRep.DoesNotExist:
        sales_rep = SalesRep.objects.select_related(
            'consumer').get(sites=Site.objects.get(id=1))
        sales_rep.email_domain = '10Coupons.com'       
    return sales_rep

def qry_verified_consumers():
    """ Return a QuerySet of consumers that have a verified email address and
    are opted in to the Email Flyer.
    """
    return Consumer.objects.filter(
                is_email_verified=True,
                email_subscription__id=1)

def qry_qualified_consumers():
    """ Return a QuerySet of fully qualified consumers that are verified,
    subscribed to the Email Flyer and have verified their mobile phone number.

    To be a qualified consumer is to be contest eligible.
    """
    return qry_verified_consumers().filter(
                subscriber__mobile_phones__is_verified=True,
                consumer_zip_postal__gt=0)

@transaction.commit_manually
def update_subscriber_of_consumer(consumer, carrier_id, mobile_phone_number, 
        subscriber_zip_postal, site):
    """ Update subscriber for a given consumer. """
    subscriber = Subscriber.objects.get(pk=consumer.subscriber_id)
    # Check if mobile phone is already in use for another subscriber.
    if Subscriber.objects.filter(
        mobile_phones__mobile_phone_number=mobile_phone_number).exclude(
        id=subscriber.id).count():
        transaction.commit()
        return 1
    try:
        mobile_phone = subscriber.mobile_phones.all()[0]
    except IndexError:
        try:
            mobile_phone = MobilePhone.objects.create(
                mobile_phone_number=mobile_phone_number,
                carrier_id=carrier_id, subscriber=subscriber)
        except IntegrityError:
            # Race condition?
            transaction.rollback()
            mobile_phone = subscriber.mobile_phones.all()[0]
    # Check to see if the mobile_phone_number or carrier has changed.
    if mobile_phone.mobile_phone_number != mobile_phone_number:
        mobile_phone.mobile_phone_number = mobile_phone_number
        mobile_phone.carrier_id = carrier_id
        mobile_phone.save()
    else:
        update_mobile_phone_if_diff(mobile_phone, carrier_id)
    update_subscriber_if_diff(subscriber, subscriber_zip_postal, site)
    transaction.commit()
    return 0
 
def add_subscriber_to_this_consumer(consumer, subscriber_zip_postal, site):
    """ Create a subscriber and relate to a preexisting consumer. """
    consumer.subscriber = Subscriber.objects.create(site=site,
        subscriber_zip_postal=subscriber_zip_postal)
    consumer.save()
    return consumer  

def get_opted_in_count_by_site(site):
    """ Get the count of opted in consumers for a given site. """
    return site.consumers.filter(email_subscription=1).count()
        
def update_default_site_consumers():
    """
    This is a cleanup utility that takes all the consumers associated with
    the default site (not a local site) and checks to see if their zip matches
    a local site. When there is a match the consumer (and related subscriber,
    if any) is updated.
    """
    LOG.error('Consumers on site 1, before: %s' % Consumer.objects.filter(
        site=1).count())
    for consumer in Consumer.objects.filter(site=1):
        try:
            site = Site.objects.get_sites_this_zip(
                consumer.consumer_zip_postal)[0]
            consumer.site = site
            consumer.save()
            if consumer.subscriber:
                consumer.subscriber.site = site
                consumer.subscriber.save()
        except IndexError:
            pass
    LOG.error('Consumers on site 1, after: %s' % Consumer.objects.filter(
        site=1).count())

def process_consumer_opt_out(request, consumer, subscription_list):
    """ Opt out this consumer from email subscriptions in the subscription list.
    Calling view needs to trap for ValueError for failed deprecated listID 
    conversions to int (and redirect to unsubscribe view).
    """
    # Deprecated versions use listid logic that passed in the subscription id
    # as a random 5 digit code with only the first to being used. Convert these
    # strings to conform to list format:
    if type(subscription_list) in (unicode, str):
        if subscription_list[0] == '0':
            subscription_list = [int(subscription_list[1])]
        else:
            subscription_list = [int(subscription_list[:2])]
    if subscription_list:
        unsubscribed_list = [] # Id list for ConsumerHistory log.
        for list_id in subscription_list:
            if list_id == 1 or list_id == 'ALL':
                # Unsubscribe from everything!
                consumer.email_subscription.clear()
                unsubscribed_list.append('ALL')
                break
            elif list_id == 5:
                # Remove from adreplead & ad rep meeting reminder.
                consumer.email_subscription.remove(5, 6)
                unsubscribed_list += [5, 6]
            else:
                # Remove per id in list.
                consumer.email_subscription.remove(list_id)
                unsubscribed_list.append(list_id)
        event = ConsumerHistoryEvent.objects.create(
            consumer=consumer, 
            ip=request.META['REMOTE_ADDR'],
            data={'requested_list': subscription_list,
                  'unsubscribed_list': list(set(unsubscribed_list))},
            event_type='1')
        event.save()
    