""" Service functions for subscriber app. """

import logging

from subscriber.models import Subscriber, MobilePhone
from geolocation.service import check_code_is_valid
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

def update_mobile_phone_if_diff(mobile_phone, carrier_id):
    """ Update mobile phone if carrier_id is different. """
    if mobile_phone.carrier_id != carrier_id:
        mobile_phone.carrier_id = carrier_id
        mobile_phone.save()
    return mobile_phone

def update_subscriber_if_diff(subscriber, subscriber_zip_postal, site):
    """ Update the subscriber if code is different. """
    if subscriber.subscriber_zip_postal != subscriber_zip_postal \
    and check_code_is_valid(subscriber_zip_postal):
        subscriber.subscriber_zip_postal = subscriber_zip_postal
        subscriber.site = site
        subscriber.save()
    return subscriber

def add_update_subscriber(carrier_id, mobile_phone_number,
        subscriber_zip_postal, site):
    """ Creates or updates a subscriber. """
    LOG.debug('In add_update_subscriber')
    LOG.debug('carrier_id: %s' % carrier_id)
    LOG.debug('mobile_phone_number: %s' % mobile_phone_number)
    LOG.debug('subscriber_zip_postal: %s' % subscriber_zip_postal)
    LOG.debug('site: %s' % site)
    try: 
        # Check if phone record exists already.
        mobile_phone = MobilePhone.objects.get(
            mobile_phone_number=mobile_phone_number)
        subscriber = Subscriber.objects.get(mobile_phones=mobile_phone) 
        update_mobile_phone_if_diff(mobile_phone, carrier_id)
        subscriber = update_subscriber_if_diff(subscriber, 
            subscriber_zip_postal, site)
    except (MobilePhone.DoesNotExist, Subscriber.DoesNotExist):
        # Since MobilePhone.DoesNotExist, a Subscriber will not exist either. 
        # Create them both now with the appropriate relationship.
        subscriber = create_mobile_phone(carrier_id=carrier_id,
            mobile_phone_number=mobile_phone_number,
            subscriber_zip_postal=subscriber_zip_postal, site=site)
    return subscriber
        
def create_mobile_phone(carrier_id, mobile_phone_number,
        subscriber_zip_postal, site):
    """ Create a mobile phone record for an existing subscriber. """
    subscriber = Subscriber(site=site, 
        subscriber_zip_postal=subscriber_zip_postal)
    subscriber.save()
    mobile_phone = MobilePhone(mobile_phone_number=mobile_phone_number, 
        carrier_id=carrier_id, subscriber=subscriber)
    mobile_phone.save()
    return subscriber  

def update_default_site_subscribers():
    """
    This is a cleanup utility that takes all the subscribers associated with
    the default site (not a local site) and checks to see if their zip matches
    a local site. When there is a match the subscriber is updated.
    """
    LOG.debug('In update_default_site_subscribers')
    count = 0
    passed = 0
    for subscriber in Subscriber.objects.filter(site=1):
        try:
            site = Site.objects.get_sites_this_zip(
                subscriber.subscriber_zip_postal)[0]
            LOG.debug('site: %s' % site)
            subscriber.site = site
            subscriber.save()
            count += 1
        except IndexError:
            passed += 1
    LOG.debug('Updated %s subscribers, passed %s' % (count, passed))
    
def check_if_user_is_a_subscriber(request):
    """ Checks user in session to see if she is a consumer and a subscriber. """
    try:
        this_consumer = request.session['consumer']
        this_subscriber = this_consumer['subscriber']
        subscriber_id = this_subscriber['subscriber_id']
        if subscriber_id:
            return True
    except KeyError:
        return False

def check_if_subscriber_is_verified(request):
    """
    Return true is the consumer in session is a subscriber who has a
    mobile_phone that has been verified.
    """
    try:
        this_consumer = request.session['consumer']
        this_subscriber = this_consumer['subscriber']
        subscriber_id = this_subscriber['subscriber_id']
        if subscriber_id:
            return bool(Subscriber.objects.get(id=subscriber_id).is_verified())
    except KeyError:
        return False
