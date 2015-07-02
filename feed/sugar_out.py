""" This file has the SugarCRM web service integration feed export functions """

import datetime
import logging

from django.db import DatabaseError

from advertiser.models import Advertiser, Business, Location
from consumer.models import Consumer
from feed import config 
from feed.service import split_string
from feed.sugar import select_sugar_module_fields, dict_to_name_value, \
    set_sugar_email_query
from common.utils import is_gmtime_recent

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def get_recent_sugar_entry(sugar, module, get_modified, test_mode, 
    offset_minutes):
    """
    Get most recently entries with today's date in this Sugar module. 
    Make sure to only get records that are created and don't have a 
    business_id_c value yet. (i.e. aren't synced yet)
    minutes = from now to the past (should match celery task schedule interval) 
    Don't get any records modified by username (doing the syncing), only users.
    if a module_dict has a modify key value of True, then a sugar user has 
    modified a field in this module.
    """
    max_result = 50 # MySQL query performance optimization variable
    LOG.debug('get_recent_sugar_entry')
    LOG.debug('offset_minutes: %s' % offset_minutes)
    # Do not adjust GMT for DST! (since only US times are affected)
    start = datetime.datetime.utcnow() + \
        datetime.timedelta(minutes=-offset_minutes) # negative offset
    datetime_format = '%Y-%m-%d %H:%M:%S'
    start = start.strftime(datetime_format)
    query = build_recent_entry_query(module, test_mode, get_modified, start)
    module_list = []
    if query:
        sugar_list = sugar.get_entry_list(module=module, 
            query=query, order_by='date_modified desc', 
            args_dict={'max_result': max_result})
        if sugar_list:
            for sugar_dict in sugar_list:
                # exclude all records modified by the sync username
                if sugar_dict['modified_by_name'] != config.SUGAR_USERNAME:  
                    sugar_dict['modify'] = get_modified
                    module_list.append(sugar_dict)
    return module_list

def build_recent_entry_query(module, test_mode, get_modified, start):
    """
    Create the 'where' clause of a soap query that gets recent entries either 
    modified or created within a time frame.
    """
    if test_mode:
        query = set_sugar_email_query(module=module, 
            email='user114@company.com')
    else: 
        if get_modified:
            LOG.debug('get_modified')
            select_operand = ">="
            date_field = "date_modified"
            query = ""
        else: # created
            select_operand = "="
            date_field = "date_entered"
            if str.lower(module) == 'accounts':
                id_field = "business"
            else:
                id_field = "advertiser"
            query = "%s_cstm.%s_id_c is null and " % (
                    str.lower(module), id_field)
        query += "%s.modified_user_id != '%s' and " % (str.lower(module), 
            config.SUGAR_USER_ID) + \
            "%s.date_modified %s %s.date_entered and " % (
            str.lower(module), select_operand, str.lower(module)) + \
            "%s.%s > '%s'" % (str.lower(module), date_field, start)
    return query

def prepare_sync_business(sugar, module1, module2, module1_dict):
    """
    Prepare account_dict and contact_dict for sync_coupon_business.  
    """
    module2_dict = None
    LOG.debug('get %s with email: %s' % (module2, module1_dict['email1']))
    module2_id = get_sugar_relationship(sugar, module1=module1, 
        module1_id=module1_dict['id'], module2=module2)
    if module2_id:
        # for this module id, get all field values 
        query = "%s.id = '%s'" % (str.lower(module2), module2_id)
        sugar_list = sugar.get_entry_list(module=module2, query=query, 
            order_by='', args_dict={'selection': (
            select_sugar_module_fields(module=module2))})
        if sugar_list:
            module2_dict = sugar_list[0]
            if module2_dict:
                # changes were not done to this module...?  
                module2_dict['modify'] = None 
    return module2_dict

def sync_business(sugar, advertiser, account_dict):
    """
    For this coupon advertiser, create or update a coupon business. Compare 
    Sugar modified date with business.modified date and update fields
    for this business as necessary.
    """
    LOG.debug("sync_business")
    business_name = account_dict['name'].strip()[:50]
    business = None
    if account_dict['business_id_c']:
        try:
            business = Business.objects.get(advertiser=advertiser, 
                id=account_dict['business_id_c']) 
        except Business.DoesNotExist:
            pass
    if business:
        # update existing business record here
        if business and account_dict['modify'] and is_gmtime_recent(
            account_dict['date_modified'], business.business_modified_datetime):
            if account_dict['website'] and \
                business.web_url != account_dict['website']:
                business.web_url = account_dict['website'].strip()  
                business.save()
    else:
        business = Business(advertiser=advertiser, 
            business_name=business_name)
        business.short_business_name = business_name[:25]
        business.slogan = None 
        business.web_url = account_dict['website']
        business.save()
        if not config.TEST_MODE:
            account_dict['business_id_c'] = business.id
            module = 'Accounts'
            sugar.set_entry(module, dict_to_name_value(account_dict))
    LOG.debug(business)
    return business

def sync_business_location(business, postal_code, contact_dict, account_dict, 
        phone_dict):
    """
    For this coupon business, create or update a coupon business location. A 
    unique location is matched on postal code. 
    """
    LOG.debug("sync_business_location")
    state = contact_dict.get('primary_address_state', '').strip()[:2]
    city = contact_dict.get('primary_address_city', '').strip()[:50]
    address1, address2 = split_string(contact_dict['primary_address_street'], 
        50, 50)
    if address1 and '\n' in address1:
        address1, address2 = contact_dict['primary_address_street'].split(
            '\n', 1)
    address1 = address1.replace('\n', ' ')
    address2 = address2.replace('\n', ' ')
    create_location = False
    try: 
        location = Location.objects.get(business=business, 
            location_zip_postal=postal_code)
    except Location.DoesNotExist:
        create_location = True
    update_phone = False
    if create_location:
        location = Location(business=business, 
            location_address1=address1, location_address2=address2,
            location_city=city, location_state_province=state,
            location_zip_postal=postal_code,
            location_url=account_dict['website'])
        update_phone = True
    else: # modify this location 
        if contact_dict['modify'] and is_gmtime_recent(
            contact_dict['date_modified'], location.location_create_datetime):
            location.location_address1 = address1 
            location.location_address2 = address2
            location.location_city = city
            location.location_state_province = state
            location.location_zip_postal = postal_code
            update_phone = True
        if account_dict['website'] and account_dict['modify'] and \
            is_gmtime_recent(account_dict['date_modified'], 
            location.location_create_datetime):
            location.location_url = account_dict['website'] 
    if update_phone and phone_dict:    
        location.location_area_code = phone_dict.get('area_code', '')
        location.location_exchange = phone_dict.get('exchange', '')
        location.location_number = phone_dict.get('number', '')
    try:
        location.save()
    except DatabaseError:
        LOG.error('Error saving location')
    LOG.debug('location = %s' % str(location))
    LOG.debug('created = %s' % create_location)
    return

def sync_advertiser(sugar, email, advertiser_name, site, contact_dict):
    """ Create or get coupon advertiser from external business data. """
    
    try:
        advertiser = Advertiser.objects.get(email__iexact=email)
        # update existing advertiser records here
        if advertiser and contact_dict['modify'] and is_gmtime_recent(
            contact_dict['date_modified'], 
            advertiser.advertiser_modified_datetime):
            if advertiser.advertiser_name != advertiser_name:
                advertiser.advertiser_name = advertiser_name
                advertiser.save()
    except Advertiser.DoesNotExist:
        try: 
            # Check if consumer exists already
            consumer = Consumer.objects.get(email__iexact=email)
            # Associate this consumer with advertiser
            advertiser = Advertiser.objects.create_advertiser_from_consumer(
                consumer=consumer, advertiser_name=advertiser_name)
        except Consumer.DoesNotExist:
            # .. and Advertiser doesn't exist, so create one here
            advertiser = Advertiser(username=email, email=email.strip().lower(),
                advertiser_name=advertiser_name, advertiser_area_code=None,
                advertiser_exchange=None, advertiser_number=None, 
                last_login=datetime.datetime.now(), 
                date_joined=datetime.datetime.now(), site=site)
            advertiser.set_unusable_password()
            advertiser.save()
            LOG.debug(advertiser)
            advertiser.email_subscription.add(2)
            advertiser.email_subscription.add(4)
            advertiser.email_subscription.add(1)
            if not config.TEST_MODE:
                # mark Sugar Contact with advertiser_id_c
                contact_dict['advertiser_id_c'] = advertiser.id
                module = 'Contacts'
                sugar.set_entry(module, dict_to_name_value(contact_dict))
        advertiser.groups.add(1) # cold_call_leads
        advertiser.save()
    return advertiser

def get_sugar_relationship(sugar, module1, module1_id, module2):
    """ 
    Get relationship between two different Sugar modules. Return id 
    of related module. 
    """
    LOG.debug('get_sugar_relationship')
    if module1 != module2:
        response = sugar.get_relationships(module_name=module1, 
            module_id=module1_id, related_module=module2)
        #error_check_response(sugar, response)
        if len(response['ids']) == 0:
            return None
        if len(response['ids']) > 1:
            LOG.error("More than one relationship record was returned.")
            # check to see if both modules ids have the same email
            related_module_id = check_sugar_relationship(sugar, module1, 
                module1_id, related_id_list=response['ids'], 
                module2=module2)
        else:
            try:
                related_module_id = response['ids'][0]['id']
            except AttributeError:
                related_module_id = None
        return related_module_id
    return None

def check_sugar_relationship(sugar, module1, module1_id, related_id_list, 
    module2):
    """
    For each module1 entry, get the related contact email from module2 and 
    check for match to module1 email and return it. Stop at first match.
    The email1 field in each module will match only it is a primary module key. 
    """
    field = 'email1'
    args_dict = {'selection': [field]}
    sugar_list = sugar.get_entry_list(module=module1, 
            query="%s.id = '%s'" % (str.lower(module1), module1_id), 
            args_dict=args_dict)
    module1_email = sugar_list[0][field]
    
    for module2_id in related_id_list:
        sugar_list = sugar.get_entry_list(module=module2, 
            query="%s.id = '%s'" % (str.lower(module2), module2_id['id']), 
            args_dict=args_dict)
        if module1_email == sugar_list[0][field]:
            LOG.debug('primary email match found')
            return module1_id
    return None
