""" Session functions for project ten.

In the session dict, 'this_advertiser' is a dict. To get the instance use
Advertiser.objects,get(id=this_advertiser['advertiser_id'])
where this_advertiser = request.session['consumer']['advertiser'].

business, offer, and coupon are lists in the advertiser dict. The index of each
of these that you are working with at the moment (if any) are set at the root of
session as such:

current_business = request.session['current_business']
current_offer = request.session['current_offer']
current_coupon = request.session['current_coupon']

To get the working instance of coupon, then, do this:
Coupon.objects.get(
    id=this_advertiser['business'][current_business]['offer'][current_offer]
        ['coupon'][current_coupon]['coupon_id'])
"""
import logging

from django.contrib.auth import logout

from advertiser.models import Advertiser
from consumer.models import Consumer
from media_partner.models import MediaPartner

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def parse_curr_session_keys(session, _keys):
    """ Parse key objects from session, reduce number of arguments in a function
    by placing this_business, this_advertiser, this_coupon, this_offer, etc  in 
    a dict. _keys list parameter passed in to and looped over to specify which
    keys need be returned for the caller.
    KeyErrors will be handled by the caller to retain existing functionality.
    Sample call: parse_curr_session_keys(request.session, ['this_advertiser']
    Sample result: {'this_advertiser': {'advertiser_city': None, 
    'advertiser_address1': None, 'advertiser_area_code': u'', 
    'advertiser_name': None, 'business': [{'slogan': u'', 
    'short_business_name': u'Star Trek', 'is_active': True, 
    'business_id': 145L, 'web_url': None, 'show_web_snap': True, 
    'business_name': u'Star Trek', 'web_snap_path': None, 
    'show_map': True, 'categories': None}], 
    'approval_count': 0, 'advertiser_number': u'', 'advertiser_zip_postal': 
    None, 'advertiser_id': 385L, 'advertiser_state_province': None, 
    'advertiser_address2': None, 'advertiser_exchange': u''}}
    """
    LOG.debug('Logging to use session var explicitly for %s' % session)
    # Define session keys.
    key_dict = {'consumer': "session['consumer']",
    'advertiser': "['advertiser']",
    'business': "['business'][session['current_business']]",
    'location': "['location'][session['current_location']]",
    'offer': "['offer'][session['current_offer']]",
    'coupon': "['coupon'][session['current_coupon']]",
    'subscriber': "['subscriber']",
    'product_list': "session['product_list']",
    'advertiser_id': "['advertiser_id']",
    'business_id': "['business_id']",
    'coupon_id': "['coupon_id']",
    'offer_id': "['offer_id']",
    'mobile_phone_number': "['mobile_phone_number']",
    'subscriber_zip_postal': "['subscriber_zip_postal']",
    'carrier_id': "['carrier_id']",
    }

    session_translator_dict = {
        'advertiser_id': "%s%s%s" % (key_dict['consumer'], 
            key_dict['advertiser'], key_dict['advertiser_id']),
        'business_id': "%s%s%s%s" % (key_dict['consumer'],
            key_dict['advertiser'], key_dict['business'], 
            key_dict['business_id']),
        'carrier_id': "%s%s%s" % (key_dict['consumer'], 
            key_dict['subscriber'], key_dict['carrier_id']),
        'coupon_id': "%s%s%s%s%s%s" % (key_dict['consumer'], 
            key_dict['advertiser'], key_dict['business'], key_dict['offer'], 
            key_dict['coupon'], key_dict['coupon_id']),
        'mobile_phone_number': "%s%s%s" % (key_dict['consumer'], 
            key_dict['subscriber'], key_dict['mobile_phone_number']),
        'offer_id': "%s%s%s%s%s" % (key_dict['consumer'], 
            key_dict['advertiser'], key_dict['business'], key_dict['offer'],
            key_dict['offer_id']),
        'subscriber_zip_postal': "%s%s%s" % (key_dict['consumer'], 
            key_dict['subscriber'], key_dict['subscriber_zip_postal']),
        'this_advertiser': "%s%s" % (key_dict['consumer'], 
            key_dict['advertiser']),
        'this_business': "%s%s%s" % (key_dict['consumer'],
            key_dict['advertiser'], key_dict['business']),
        'this_consumer': key_dict['consumer'],
        'this_coupon': "%s%s%s%s%s" % (key_dict['consumer'], 
            key_dict['advertiser'], key_dict['business'], key_dict['offer'], 
            key_dict['coupon']), 'this_location': "%s%s%s%s" % 
            (key_dict['consumer'], key_dict['advertiser'], key_dict['business'], 
            key_dict['location']),
        'this_offer': "%s%s%s%s" % (key_dict['consumer'], 
            key_dict['advertiser'], key_dict['business'], key_dict['offer']),
        'product_list': "%s" % (key_dict['product_list']),
        'this_subscriber': "%s%s" % (key_dict['consumer'], 
            key_dict['subscriber'])}
    parsed_session_dict = {}
    for _key in _keys:
        parsed_session_dict[_key] = eval(session_translator_dict[_key])
    return parsed_session_dict

def clear_session(request):
    """ Wipe out every key value pair associated with this session. """
    request.session.clear()
    
def delete_key_from_session(request, key):
    """ This method deletes a single key from the request.session if it exists.
    """
    if key in request.session:
        del request.session[key]

def delete_all_session_keys_in_list(request, list_of_session_keys_to_delete):
    """ This method takes in a list of keys and deletes them in the 
    request.session if they exist.
    """
    key_count = len(list_of_session_keys_to_delete)
    current_list_position = 0
    while current_list_position < key_count:
        # If key is in session, delete it.
        delete_key_from_session(request, 
            key=list_of_session_keys_to_delete[current_list_position])
        current_list_position = current_list_position + 1
    return request

def check_required_session_keys(request, keys):
    """  Return True if all the keys are present in the session, else False.
    """
    is_valid = True
    for key in keys:
        try:
            request.session[key]
        except KeyError:
            is_valid = False
    return is_valid        

def get_key_from_dict(dictionary, key):
    """ If the key is in the dictionary, return it. """
    try:
        if key in dictionary:
            return dictionary.get(key)        
    except KeyError:
        pass
        
def get_consumer_id_in_session(request):
    """ Return Consumer id when in session.  """
    try:
        consumer_id = request.session['consumer']['consumer_id']    
    except KeyError:
        consumer_id = None
    return consumer_id

def build_session_from_user(request, user):
    """ Build this users session and determine user_type. """
    try:
        advertiser = Advertiser.objects.get(email=user.email)
        build_advertiser_session(request, advertiser)
        return 'advertiser'
    except Advertiser.DoesNotExist:
        try:
            media_partner = MediaPartner.objects.get(email=user.email)
            affiliates = media_partner.affiliates.all()
            media_groups = media_partner.media_groups.all()
            if media_groups:
                request.session['consumer'] = {'media_group_partner':{}, 
                    'email':user.email}
                return 'media_group_partner'
            if affiliates:
                request.session['consumer'] = {'affiliate_partner':{}, 
                    'email':user.email}
                return 'affiliate_partner'
        except MediaPartner.DoesNotExist:
            try:
                consumer = Consumer.objects.get(email=user.email)
                create_consumer_in_session(request, consumer)
                return 'consumer'
            except Consumer.DoesNotExist:
                return False

def create_consumer_dict(dictionary, is_advertiser=None):
    """ Create the consumer dictionary with some keys removed from the 
    objects Instance.
    """
    if is_advertiser:
        consumer_id = 'consumer_ptr_id'
    else:
        consumer_id = 'id'
    consumer_dict = { 
        # USER DATA
        'user_id':get_key_from_dict(dictionary, 'user_ptr_id'),
        'username':get_key_from_dict(dictionary, 'username'),
        'first_name':get_key_from_dict(dictionary, 'first_name'),
        'last_name':get_key_from_dict(dictionary, 'last_name'),
        'email':get_key_from_dict(dictionary, 'email'),
        'is_staff':get_key_from_dict(dictionary, 'is_staff'),
        'is_active':get_key_from_dict(dictionary, 'is_active'),
        'is_superuser':get_key_from_dict(dictionary, 'is_superuser'),
        # CONSUMER DATA
        'consumer_id':get_key_from_dict(dictionary, consumer_id),
        'site_id':get_key_from_dict(dictionary, 'site_id'),
        'is_email_verified':get_key_from_dict(dictionary, 'is_email_verified'),
        'consumer_zip_postal':get_key_from_dict(dictionary, 
            'consumer_zip_postal')
    }
    return consumer_dict

def create_subscriber_dict(subscriber_dict, mobile_phone_dict, carrier_dict):
    """ Create the subscriber dictionary with some keys removed from the 
    objects Instance.
    """
    subscriber_dict = {
        'subscriber_id':get_key_from_dict(subscriber_dict, 'id'),
        'subscriber_zip_postal':get_key_from_dict(subscriber_dict, 
            'subscriber_zip_postal'),
        'mobile_phone_number':get_key_from_dict(mobile_phone_dict, 
            'mobile_phone_number'),
        'carrier_id':get_key_from_dict(carrier_dict, 'id'),
    }
    return subscriber_dict

def create_subscriber_in_session(request, subscriber):
    """ Create this subscribers session. """
    subscriber_dict = subscriber.__dict__
    mobile_phones = subscriber.mobile_phones.all()[0]
    mobile_phone_dict = mobile_phones.__dict__
    carrier_dict = mobile_phones.carrier.__dict__
    # SUBSCRIBER DICTIONARY
    subscriber_dict = create_subscriber_dict(
        subscriber_dict=subscriber_dict, 
        mobile_phone_dict=mobile_phone_dict, 
        carrier_dict=carrier_dict
        )
    try:        
        request.session['consumer']
    except KeyError:
        request.session['consumer'] = {}
    request.session['consumer']['subscriber'] = subscriber_dict

def create_subscriber_from_consumr(dictionary, consumer):
    """ Create this subscriber and associate it to this consumer level.
    Dict being passed in is the consumer.__dict__ or advertiser.__dict__.
    """
    try:
        # Check if this consumer is a subscriber.
        subscriber_dict = consumer.subscriber.__dict__
        mobile_phones = consumer.subscriber.mobile_phones.all()[0]
        mobile_phone_dict = mobile_phones.__dict__
        carrier_dict = mobile_phones.carrier.__dict__
        # SUBSCRIBER DICTIONARY
        subscriber_dict = create_subscriber_dict(
            subscriber_dict=subscriber_dict, 
            mobile_phone_dict=mobile_phone_dict, 
            carrier_dict=carrier_dict
            )
    except (AttributeError, IndexError):
        # This consumer is not a subscriber.
        subscriber_dict = {
            'subscriber_id':get_key_from_dict(dictionary, 'subscriber_id'),
        }
    return subscriber_dict

def create_consumer_in_session(request, consumer):
    """ Create this consumer in session. """
    dictionary = consumer.__dict__
    subscriber_dict = create_subscriber_from_consumr(dictionary,  consumer)
    # CONSUMER DICTIONARY
    consumer_dict = create_consumer_dict(dictionary)
    # Add subscriber and advertiser to consumer dictionary.
    consumer_dict['subscriber'] = subscriber_dict
                     
    # Delete old consumer session if exists.
    if 'consumer' in request.session:
        del request.session['consumer']
    # Place new consumer into session.
    request.session['consumer'] = consumer_dict

def create_consumer_from_adv(request, advertiser):
    """ Create this consumer in session from this advertiser object.  Getting
    called in build advertiser session method.
    """
    dictionary = advertiser.__dict__
    # SUBSCRIBER DICTIONARY
    subscriber_dict = create_subscriber_from_consumr(
        dictionary, 
        advertiser
        )
    # CONSUMER DICTIONARY
    consumer_dict = create_consumer_dict(dictionary, is_advertiser=1)
    # ADVERTISER DICTIONARY
    advertiser_dict = {
        'advertiser_id':get_key_from_dict(dictionary, 'id'),
        'advertiser_name':get_key_from_dict(dictionary, 'advertiser_name'),
        'advertiser_area_code':get_key_from_dict(dictionary, 'advertiser_area_code'),
        'advertiser_exchange':get_key_from_dict(dictionary, 'advertiser_exchange'),
        'advertiser_number':get_key_from_dict(dictionary, 'advertiser_number'),
        'approval_count':get_key_from_dict(dictionary, 'approval_count'),
        'advertiser_address1':get_key_from_dict(dictionary, 'advertiser_address1'),
        'advertiser_address2':get_key_from_dict(dictionary, 'advertiser_address2'),
        'advertiser_city':get_key_from_dict(dictionary, 'advertiser_city'),
        'advertiser_state_province':get_key_from_dict(dictionary, 
            'advertiser_state_province'),
        'advertiser_zip_postal':get_key_from_dict(dictionary, 
            'advertiser_zip_postal'),
    }
    # Add subscriber and advertiser to consumer dictionary.
    consumer_dict['subscriber'] = subscriber_dict
    consumer_dict['advertiser'] = advertiser_dict
                     
    # Delete old consumer session if exists.
    if 'consumer' in request.session:
        del request.session['consumer']
    # Place new consumer into session.
    request.session['consumer'] = consumer_dict

def add_update_business_session(request, business):
    """ Add/Update business for this advertiser. """
    try:
        dictionary = business.__dict__
    except AttributeError:
        dictionary = business
    business_dict = { 
        'business_id':get_key_from_dict(dictionary, 'id'),
        'business_name':get_key_from_dict(dictionary, 'business_name'),
        'short_business_name':get_key_from_dict(dictionary, 'short_business_name'),
        'slogan':get_key_from_dict(dictionary, 'slogan'),
        'is_active':get_key_from_dict(dictionary, 'is_active'),
        'web_url':get_key_from_dict(dictionary, 'web_url'),
        'web_snap_path':get_key_from_dict(dictionary, 'web_snap_path'),
        'show_web_snap':get_key_from_dict(dictionary, 'show_web_snap'),
        'show_map':get_key_from_dict(dictionary, 'show_map'),
        'categories':
            business.categories.all().values_list('id', flat=True) or None,
    }    
    if 'business' in request.session['consumer']['advertiser']:
        found_business_in_session = 0
        business_count = len(request.session['consumer']['advertiser']['business'])
        i = 0
        while i < business_count:
            session_business_dict = request.session['consumer']['advertiser']\
                ['business'][i]
            # Update business found in session.
            if business_dict['business_id'] == session_business_dict['business_id']:
                # Retain offer dict info from current_business in session.
                offer_dict = get_key_from_dict(session_business_dict, 'offer')
                if offer_dict:
                    business_dict['offer'] = offer_dict
                # Retain location dictionary information from current_business. 
                # in session.
                location_dict = get_key_from_dict(session_business_dict, 'location')
                if location_dict:
                    business_dict['location'] = location_dict
                request.session['consumer']['advertiser']['business'][i] = business_dict
                found_business_in_session = 1
                request.session['current_business'] = i
                break
            i = i + 1
        # Append business to end of all other businesses in session.
        if found_business_in_session == 0:
            request.session['consumer']['advertiser']['business'].append(business_dict)
            request.session['current_business'] = business_count
    else:
        # First business, add to session.
        business = [business_dict]
        request.session['consumer']['advertiser']['business'] = business
        request.session['current_business'] = 0
    
def add_update_business_offer(request, offer, category_id=None):
    """ Add/Update this offer for this business. """
    dictionary = offer.__dict__
    current_business = request.session['current_business']
    offer_dict = {  
        'offer_id':get_key_from_dict(dictionary, 'id'),
        'headline':get_key_from_dict(dictionary, 'headline'),
        'qualifier':get_key_from_dict(dictionary, 'qualifier'),
        'offer_create_datetime':get_key_from_dict(dictionary, 
            'offer_create_datetime'),
    }
    if 'offer' in request.session['consumer']['advertiser']['business']\
    [current_business]:
        found_offer_in_session = 0
        offer_count = len(request.session['consumer']['advertiser']['business']\
            [current_business]['offer'])
        i = 0
        while i < offer_count:
            session_offer_dict = request.session['consumer']['advertiser']\
                ['business'][current_business]['offer'][i]
            # Update offer found in session.
            if offer_dict['offer_id'] == request.session['consumer']\
                    ['advertiser']['business'][current_business]['offer'][i]\
                    ['offer_id']:
                # Retain coupon dictionary info from current_offer in session.
                coupon_dict = get_key_from_dict(session_offer_dict, 'coupon')
                if coupon_dict:
                    offer_dict['coupon'] = coupon_dict
                request.session['consumer']['advertiser']['business']\
                    [current_business]['offer'][i] = offer_dict
                found_offer_in_session = 1
                request.session['current_offer'] = i
                break
            i = i + 1
        # Append offer to end of all other offers in session.
        if found_offer_in_session == 0:
            request.session['consumer']['advertiser']['business']\
                [current_business]['offer'].append(offer_dict)
            request.session['current_offer'] = offer_count
    else:
        # First offer, add to session.
        offer = [offer_dict]
        request.session['consumer']['advertiser']['business'][current_business]\
            ['offer'] = offer
        request.session['current_offer'] = 0
    if category_id:
        request.session['consumer']['advertiser']['business'][current_business]\
            ['categories'] = [category_id]

def move_coupon_to_offer(request, old_current_offer, coupon):
    """ Move this coupon in session from offer that doesn't match to new offer that 
    matches.    
    """
    current_business = request.session['current_business']
    current_coupon = request.session['current_coupon']
    this_business = request.session['consumer']['advertiser']['business']\
        [current_business]
    # Add the coupon to the matching offer
    add_coupon_to_offer_in_session(request, coupon)
    # Remove coupon from the previous offer
    coupon_count = len(this_business['offer'][old_current_offer]['coupon'])
    if coupon_count > 1:
        # Only delete the coupon we are moving.
        del this_business['offer'][old_current_offer]['coupon'][current_coupon]
    else:
        # Only 1 coupon in session for this offer.  Remove the coupon and the
        # 'coupon' key for this offer.
        del this_business['offer'][old_current_offer]['coupon']

def find_lonely_offer(request):
    """ Check if this business has an offer with no coupon association and reset the 
    current offer to that position of the lonely offer so we may utilize this 
    record so it doesn't go to waste. 
    """
    has_lonely_offer = False
    session_dict = parse_curr_session_keys(request.session, ['this_business'])
    try:
        these_offers = session_dict['this_business']['offer']
        this_offer_count = len(session_dict['this_business']['offer']) - 1
        while 0 <= this_offer_count:
            try:
                these_offers[this_offer_count]['coupon']
            except KeyError:
                has_lonely_offer = True
                request.session['current_offer'] = this_offer_count
                break
            this_offer_count = this_offer_count - 1
    except KeyError:
        # This business has no offers.
        pass 
    return has_lonely_offer 

def add_update_business_location(request, location):
    """ Add/Update location for business depending upon if it exists in session
    already or not for this business.
    """
    dictionary = location.__dict__
    current_business = request.session['current_business']
    location_dict = {  
        'location_id':get_key_from_dict(dictionary, 'id'),
        'location_address1':get_key_from_dict(dictionary, 'location_address1'),
        'location_address2':get_key_from_dict(dictionary, 'location_address2'),
        'location_city':get_key_from_dict(dictionary, 'location_city'),
        'location_state_province':get_key_from_dict(dictionary, 
            'location_state_province'),
        'location_zip_postal':get_key_from_dict(dictionary, 
            'location_zip_postal'),
        'location_area_code':get_key_from_dict(dictionary, 
            'location_area_code'),
        'location_exchange':get_key_from_dict(dictionary, 'location_exchange'),
        'location_number':get_key_from_dict(dictionary, 'location_number'),
        'location_description':get_key_from_dict(dictionary, 
            'location_description')}
    if 'location' in request.session['consumer']['advertiser']['business']\
            [current_business]:
        found_location_in_session = 0
        location_count = len(request.session['consumer']['advertiser']\
            ['business'][current_business]['location'])
        i = 0
        while i < location_count:
            # Update location found in session.
            if location_dict['location_id'] == request.session['consumer']\
                    ['advertiser']['business'][current_business]['location'][i]\
                    ['location_id']:
                request.session['consumer']['advertiser']['business']\
                    [current_business]['location'][i] = location_dict
                found_location_in_session = 1
                request.session['current_location'] = i
                break
            i = i + 1
        # Append location to end of all other locations in session.
        if found_location_in_session == 0:
            request.session['consumer']['advertiser']['business']\
                [current_business]['location'].append(location_dict)
            request.session['current_location'] = location_count
    else:
        # First location, add to session.
        location = [location_dict]
        request.session['consumer']['advertiser']['business'][current_business]\
            ['location'] = location
        request.session['current_location'] = 0

def add_coupon_to_offer_in_session(request, coupon):
    """ Add this coupon to the current offer position. """
    dictionary = coupon.__dict__
    current_business = request.session['current_business']
    current_offer = request.session['current_offer']
    coupon_dict = {  
        'coupon_id':get_key_from_dict(dictionary, 'id'),
        'is_approved':get_key_from_dict(dictionary, 'is_approved'),
        'is_valid_monday':get_key_from_dict(dictionary, 'is_valid_monday'),
        'is_valid_tuesday':get_key_from_dict(dictionary, 'is_valid_tuesday'),
        'is_valid_wednesday':get_key_from_dict(dictionary, 
            'is_valid_wednesday'),
        'is_valid_thursday':get_key_from_dict(dictionary, 'is_valid_thursday'),
        'is_valid_friday':get_key_from_dict(dictionary, 'is_valid_friday'),
        'is_valid_saturday':get_key_from_dict(dictionary, 'is_valid_saturday'),
        'is_valid_sunday':get_key_from_dict(dictionary, 'is_valid_sunday'),
        'is_redeemed_by_sms':get_key_from_dict(dictionary, 
            'is_redeemed_by_sms'),
        'custom_restrictions':get_key_from_dict(dictionary, 
            'custom_restrictions'),
        'simple_code':get_key_from_dict(dictionary, 'simple_code'),
        'is_coupon_code_displayed':get_key_from_dict(dictionary,
            'is_coupon_code_displayed'),
        'coupon_type_id':get_key_from_dict(dictionary, 'coupon_type_id'),
        'precise_url':get_key_from_dict(dictionary, 'precise_url'),
        'start_date':get_key_from_dict(dictionary, 'start_date'),
        'expiration_date':get_key_from_dict(dictionary, 'expiration_date'),
        'sms':get_key_from_dict(dictionary, 'sms'),
        'coupon_create_datetime':get_key_from_dict(dictionary, 
            'coupon_create_datetime'),
        'coupon_modified_datetime':get_key_from_dict(dictionary,
            'coupon_modified_datetime')}
    if 'coupon' in request.session['consumer']['advertiser']['business']\
            [current_business]['offer'][current_offer]:
        found_coupon_in_session = 0
        coupon_count = len(request.session['consumer']['advertiser']\
            ['business'][current_business]['offer'][current_offer]['coupon'])
        i = 0
        while i < coupon_count:
            # Update coupon found in session.
            if coupon_dict['coupon_id'] == request.session['consumer']\
                    ['advertiser']['business'][current_business]['offer']\
                    [current_offer]['coupon'][i]['coupon_id']:
                try:
                    location_list = [id_dict['id'] for id_dict \
                        in coupon.location.all().values('id').order_by('id')]
                    # Check if this coupon has location(s) associated with it.
                    #location_list = request.session['consumer']['advertiser']\
                    #    ['business'][current_business]['offer'][current_offer]\
                    #    ['coupon'][i]['location']
                    if location_list:
                        # Retain location dictionary information from 
                        # current_coupon in session.
                        coupon_dict['location'] = location_list
                except KeyError:
                    # No location(s) associated with this coupon.  So, we don't 
                    # have to add the location_list to the coupon_dict.
                    pass
                request.session['consumer']['advertiser']['business']\
                    [current_business]['offer'][current_offer]\
                    ['coupon'][i] = coupon_dict
                found_coupon_in_session = 1
                request.session['current_coupon'] = i
                break
            i = i + 1
        # Append coupon to end of all other coupons in session.
        if found_coupon_in_session == 0:
            request.session['consumer']['advertiser']['business']\
                [current_business]['offer'][current_offer]\
                ['coupon'].append(coupon_dict)
            request.session['current_coupon'] = coupon_count
    else:
        # First coupon, add to session.
        coupon = [coupon_dict]
        request.session['consumer']['advertiser']['business'][current_business]\
            ['offer'][current_offer]['coupon'] = coupon
        request.session['current_coupon'] = 0

def add_location_id_to_coupon(request, location_id):
    """ Add this businesses location_id to the this coupon. """
    current_business = request.session['current_business']
    current_offer = request.session['current_offer']
    current_coupon = request.session['current_coupon']
    if 'location' in request.session['consumer']['advertiser']['business']\
            [current_business]['offer'][current_offer]['coupon']\
            [current_coupon]:
        if location_id not in request.session['consumer']['advertiser']\
            ['business'][current_business]['offer'][current_offer]['coupon']\
            [current_coupon]['location']:
            # Append location_id to end of all other location_id's in session.
            request.session['consumer']['advertiser']['business']\
                [current_business]['offer'][current_offer]['coupon']\
                [current_coupon]['location'].append(location_id)
    else:
        # First location added for this coupon.
        location = [location_id]
        request.session['consumer']['advertiser']['business'][current_business]\
            ['offer'][current_offer]['coupon']\
            [current_coupon]['location'] = location
        
def build_advertiser_session(request, advertiser):
    """ Build the session for this advertiser. """
    advertiser = Advertiser.objects.select_related('business', 
        'business__location', 'business__offer', 'business__offer__coupon',
        'business__offer__coupon__location').get(id=advertiser.id)
    create_consumer_from_adv(request, advertiser)
    if advertiser.businesses:
        b_index = 0
        for business in advertiser.businesses.select_related().all(
                                                            ).order_by('id'):
            request.session['current_business'] = b_index
            add_update_business_session(request, business)
            if business.locations:
                lb_index = 0
                for location in business.locations.all().order_by('id'):
                    request.session['current_location'] = lb_index
                    add_update_business_location(request, location)
                    lb_index = lb_index + 1
            if business.offers:
                off_index = 0
                for offer in business.offers.all().order_by('id'):
                    request.session['current_offer'] = off_index
                    add_update_business_offer(request, offer)
                    if offer.coupons:
                        c_index = 0
                        for coupon in offer.coupons.all().order_by('id'):
                            request.session['current_coupon'] = c_index
                            add_coupon_to_offer_in_session(request, coupon)
                            if coupon.location:
                                lc_index = 0
                                for location in coupon.location.all(
                                        ).order_by('id'):
                                    location_id = location.id
                                    add_location_id_to_coupon(request, 
                                        location_id)
                                    lc_index = lc_index + 1
                            c_index = c_index + 1
                    off_index = off_index + 1
            b_index = b_index + 1


def update_session_by_dictionary(request, session_key_value_dictionary):
    """ This method takes in a dictionary of key:value pairs and add/updates 
    them in the request.session appropriately.
    """
    key_count = len(session_key_value_dictionary)
    current_dictionary_position = 0
    while current_dictionary_position < key_count:
        # If key is in session already, delete it and replace with latest key 
        # value pair.
        key_list = list(session_key_value_dictionary.keys())
        key = key_list[current_dictionary_position]
        delete_key_from_session(request, key=key)
        # Add the latest key value pair into the session.
        request.session[key] = session_key_value_dictionary[key]
        current_dictionary_position += 1
    return request

def check_advertiser_owns_business(request, business_name):
    """ Check if this business exists for this advertiser. """
    business_exists_for_advertiser = False
    this_advertiser = request.session['consumer']['advertiser']
    try:
        this_business_count = len(this_advertiser['business']) - 1
        while 0 <= this_business_count:
            this_business_name = this_advertiser['business'][this_business_count]\
                ['business_name']
            if this_business_name == business_name:
                request.session['current_business'] = this_business_count
                business_exists_for_advertiser = True
                break
            this_business_count = this_business_count - 1
    except KeyError:
        # This advertiser has no businesses associated with it. Could have 
        #been added via admin or texted in ad via sms to create the 
        #advertiser without a business association.
        pass
    return business_exists_for_advertiser

def check_if_i_own_this_business(request, business_id):
    """ Check if this user owns this business. """
    i_own_this_business = False
    try:
        this_advertiser = request.session['consumer']['advertiser']
        this_business_count = len(this_advertiser['business']) - 1
        while 0 <= this_business_count:
            this_business_id = this_advertiser['business'][this_business_count]\
                ['business_id']
            if this_business_id == business_id:
                request.session['current_business'] = this_business_count
                i_own_this_business = True
                break
            this_business_count = this_business_count - 1
    except KeyError:
        #This user is not an advertiser.
        pass
    return i_own_this_business

def check_if_i_own_this_coupon(request, coupon_id):
    """ Check if this user owns this coupon. """
    i_own_this_coupon = False
    try:
        this_advertiser = request.session['consumer']['advertiser']
        this_business_count = len(this_advertiser['business']) - 1
        while 0 <= this_business_count:
            try:
                this_business = this_advertiser['business'][this_business_count]
                this_offer_count = len(this_business['offer']) - 1
                while 0 <= this_offer_count:
                    try:
                        this_offer = this_business['offer'][this_offer_count]
                        this_coupon_count = len(this_offer['coupon']) - 1
                        while 0 <= this_coupon_count:
                            try:
                                this_coupon_id = this_offer['coupon']\
                                    [this_coupon_count]['coupon_id']
                                if this_coupon_id == coupon_id:
                                    request.session['current_business'] = \
                                        this_business_count
                                    request.session['current_offer'] = \
                                        this_offer_count
                                    request.session['current_coupon'] = \
                                        this_coupon_count
                                    i_own_this_coupon = True
                                    break
                            except KeyError:
                                # This offer has no coupons.
                                pass
                            this_coupon_count = this_coupon_count - 1                    
                    except KeyError:
                        # This business has no offers.
                        pass
                    this_offer_count = this_offer_count - 1
            except KeyError:
                # This advertiser has no businesses.
                pass
            this_business_count = this_business_count - 1
    except KeyError:
        # This user is not an advertiser.
        pass
    return i_own_this_coupon

def check_business_has_this_offer(request, headline, qualifier):
    """ Check all the offers that a business has to 
    see if we have an exact match for that headline and 
    qualifier so we can reposition our pointer position in session to
    the appropriate position.
    """
    offer_exists = False
    session_dict = parse_curr_session_keys(request.session, ['this_business'])
    try:
        this_offer_count = len(session_dict['this_business']['offer']) - 1
        while 0 <= this_offer_count:
            this_headline = \
                session_dict['this_business']['offer'][this_offer_count]['headline']
            this_qualifier = session_dict['this_business']['offer']\
                [this_offer_count]['qualifier']
            if this_headline == headline and this_qualifier == qualifier:
                # Reposition the current offer with the matching offer found for 
                # this business.
                request.session['current_offer'] = this_offer_count
                offer_exists = True
                break
            this_offer_count = this_offer_count - 1
    except KeyError:
        # This business has no offers associated with it.
        pass
    return offer_exists

def check_offer_has_in_progress(request):
    """ Does this offer have an in progress coupon. """
    in_progress_coupon_exists = False
    session_dict = parse_curr_session_keys(request.session, ['this_offer'])
    this_coupon_count = len(session_dict['this_offer']['coupon']) - 1
    coupon_count = 0
    while coupon_count <= this_coupon_count:
        this_coupon_type_id = session_dict['this_offer']['coupon']\
        [this_coupon_count]['coupon_type_id']
        if this_coupon_type_id == 1:
            request.session['current_coupon'] = coupon_count
            in_progress_coupon_exists = True
            break
        this_coupon_count = this_coupon_count - 1
    return in_progress_coupon_exists

def check_business_has_in_progress(request):
    """ Check for in progress coupon for this business. """
    in_progress_coupon_exists = False
    session_dict = parse_curr_session_keys(request.session, ['this_business'])
    try:
        these_offers = session_dict['this_business']['offer']
        this_offer_count = len(these_offers) - 1
        while 0 <= this_offer_count:
            try:
                these_coupons = these_offers[this_offer_count]['coupon']
                this_coupon_count = len(these_coupons) - 1
                while 0 <= this_coupon_count:
                    coupon_type_id = these_coupons[this_coupon_count]['coupon_type_id']
                    if coupon_type_id == 1:
                        request.session['current_offer'] = this_offer_count
                        request.session['current_coupon'] = this_coupon_count
                        in_progress_coupon_exists = True
                        break
                    this_coupon_count = this_coupon_count - 1
            except KeyError:
                # There are no coupons associated with this offer.
                pass
            this_offer_count = this_offer_count - 1
    except KeyError:
        # This business has no offers associated with it.
        pass
    return in_progress_coupon_exists

def check_for_unpublished_offer(request, delete_keys=True):
    """ Check for unpublished coupon for this business. """
    business_has_offer = False
    business_has_unpublished_offer = False
    offer_has_coupon_association = False
    session_dict = parse_curr_session_keys(request.session, ['this_business'])
    try:
        these_offers = session_dict['this_business']['offer']
        business_has_offer = True
        this_offer_count = len(these_offers) - 1
        while 0 <= this_offer_count:
            try:
                these_coupons = these_offers[this_offer_count]['coupon']
                this_coupon_count = len(these_coupons) - 1
                while 0 <= this_coupon_count:
                    coupon_type_id = these_coupons[this_coupon_count]\
                        ['coupon_type_id']
                    if coupon_type_id == 1:
                        # This offer_coupon is not published yet. Let's see if 
                        # we can use these records and convert them to a 
                        # published coupon and offer.
                        request.session['current_offer'] = this_offer_count
                        request.session['current_coupon'] = this_coupon_count
                        business_has_unpublished_offer = True
                        offer_has_coupon_association = True
                        break
                    this_coupon_count = this_coupon_count - 1
            except KeyError:
                # This offer is not published and has no related coupon.
                request.session['current_offer'] = this_offer_count
                request.session['current_coupon'] = 0
                business_has_unpublished_offer = True
                break
            this_offer_count = this_offer_count - 1   
        if not business_has_unpublished_offer \
        and not offer_has_coupon_association:
            # Move to the next offer position.
            # All other offers checked out to be published.
            request.session['current_offer'] = len(these_offers) - 1
            if delete_keys:
                delete_key_from_session(request, key='current_coupon')
            else:
                request.session['current_coupon'] = 0
    except KeyError:
        # No offers for this business exist.
        if delete_keys:
            delete_key_from_session(request, key='current_offer')
            delete_key_from_session(request, key='current_coupon')
        else:
            request.session['current_offer'] = 0
            request.session['current_coupon'] = 0
    return business_has_offer, business_has_unpublished_offer, offer_has_coupon_association

def check_for_unpublished_business(request):
    """ Check if this advertiser has an unpublished business that we can convert.
    """
    this_advertiser = parse_curr_session_keys(request.session, ['this_advertiser'])['this_advertiser']
    has_unpublished_business = False
    try:
        these_businesses = this_advertiser['business']
        this_business_count = len(these_businesses) - 1
        while 0 <= this_business_count:
            if not check_business_was_published(request,
                these_businesses[this_business_count]):
                request.session['current_business'] = this_business_count
                has_unpublished_business = True
                break
            this_business_count = this_business_count - 1
    except KeyError:
        #This advertiser has no businesses associated with it!
        pass
    return has_unpublished_business

def check_business_was_published(request, this_business=None):
    """ Check if this business has been published before. """
    if not this_business:
        this_business = parse_curr_session_keys(request.session, ['this_business'])['this_business']
    business_has_been_published = False
    try:
        these_offers = this_business['offer']
        this_offer_count = len(these_offers) - 1
        while 0 <= this_offer_count:
            if check_offer_has_been_published(request,
                these_offers[this_offer_count]):
                business_has_been_published = True
                break
            this_offer_count = this_offer_count - 1
    except KeyError:
        #This business has no offers associated with it!
        pass
    return business_has_been_published


def check_offer_has_been_published(request, this_offer=None):
    """ Check if this offer has been published before. """
    if not this_offer:
        this_offer = parse_curr_session_keys(request.session, ['this_offer'])['this_offer']
    offer_has_been_published = False
    try:
        these_coupons = this_offer['coupon']
        this_coupon_count = len(these_coupons) - 1
        while 0 <= this_coupon_count:
            coupon_type_id = these_coupons[this_coupon_count]['coupon_type_id']
            if coupon_type_id == 3:
                offer_has_been_published = True
                break
            this_coupon_count = this_coupon_count - 1
    except KeyError:
        #This offer has no coupons associated with it!
        pass
    return offer_has_been_published

def check_other_coupon_published(request, coupon_id):
    """ Check if this offer has a published coupon other than the
    current_coupon. 
    """
    session_dict = parse_curr_session_keys(request.session, ['this_offer'])
    other_coupon_published = False
    try:
        these_coupons = session_dict['this_offer']['coupon']
        this_coupon_count = len(these_coupons) - 1
        while 0 <= this_coupon_count:
            coupon_type_id = these_coupons[this_coupon_count]['coupon_type_id']
            this_coupon_id = these_coupons[this_coupon_count]['coupon_id']
            if coupon_type_id == 3 and this_coupon_id != coupon_id:
                other_coupon_published = True
                break
            this_coupon_count = this_coupon_count - 1
    except KeyError:
        # This offer has no coupons associated with it!
        pass
    return other_coupon_published
    
def get_this_coupon_data(request):
    """ Get a coupon from session, without checking for KeyErrors. """
    current_coupon = request.session['current_coupon']
    session_dict = parse_curr_session_keys(request.session, ['this_coupon'])
    expiration_date = session_dict['this_coupon']['expiration_date']
    return current_coupon, session_dict['this_coupon'], expiration_date
    
def get_coupon_id(request):
    """ Get the id of the current coupon from session. """
    session_dict = parse_curr_session_keys(request.session, ['coupon_id'])
    return session_dict['coupon_id']

def process_sign_out(request):
    """ Sign user out of session. Retain ad_rep_id if present. """
    ad_rep_id = request.session.get('ad_rep_id')
    logout(request)
    clear_session(request)
    if ad_rep_id: # Add Ad Rep back to session.
        request.session['ad_rep_id'] = ad_rep_id