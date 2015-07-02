""" This file has the SugarCRM web service integration feed import functions """

import logging
import datetime

from django.core.urlresolvers import reverse

from advertiser.models import Business
from common.utils import remove_non_ascii_chars
from consumer.models import SalesRep
from feed import config
from feed.sugar import dict_to_name_value, set_sugar_email_query
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def sync_sugar_account(sugar, coupon=None, offer=None, business=None):
    """ 
    Map coupon data with Sugar Account fields and create a Sugar account. 
    Sugar tries to stop more than one account with the same business name.
    Business_name (case-sensitive) and advertiser email makes this Sugar 
    Account unique.
    """
    LOG.debug('sync_sugar_account')
    account_dict = {}
    if coupon:
        business = coupon.offer.business
        account_dict.update({'site_c': coupon.get_site().domain,
            'is_customer_c': (coupon.coupon_type.coupon_type_name == 'Paid')})
    else:
        if offer:
            business = offer.business
        account_dict['site_c'] = business.advertiser.site.domain
        account_dict['assigned_user_id'] = get_sugar_user(sugar, 
            site=business.advertiser.site)
    if business.advertiser.site.id == 1:
        LOG.error('Sugar Account not created due to site 1')
        return
    if business.business_name == '':
        return
    account_dict.update({'name': business.business_name.strip(),
        'email1' : business.advertiser.email,
        'business_id_c': business.id,
        'biz_admin_url_c': ('https://10coupons.com' + reverse('admin:index') + 
            'advertiser/business/%s/' % str(business.id))})
    if business.web_url:
        account_dict['website'] = business.web_url
    location, phone = get_business_location_phone(coupon=coupon, 
            business=business)
    if location:
        LOG.debug(location)
    if phone:
        account_dict['phone_office'] = phone
    if len(business.billing_records.all()) != 0: 
        billing_record = business.billing_records.all().order_by('-id')[0]
        billing_address = billing_record.billing_address1
        if billing_record.billing_address2:
            billing_address += '\n' + billing_record.billing_address2
        account_dict.update({
            'billing_address_street': billing_address,
            'billing_address_city': billing_record.billing_city,
            'billing_address_state': billing_record.billing_state_province,
            'billing_address_postalcode': billing_record.billing_zip_postal})
    account_id = get_sugar_account(sugar, account_dict)
    return account_id

def get_sugar_user(sugar, site):
    """
    Return sugar user id based on sales rep for coupon site. 
    """
    try:
        rep = SalesRep.objects.get(sites=site)
    except SalesRep.DoesNotExist:
        try:
            rep = SalesRep.objects.get(sites=Site.objects.get(id=1))
        except SalesRep.DoesNotExist:
            LOG.error('SalesRep for local not found')
            return None
    module = "Users"
    query = "users.first_name = '%s' and users.last_name = '%s'" % (
        rep.consumer.first_name, rep.consumer.last_name)
    args_dict = {'selection': ['id']} 
    sugar_list = sugar.get_entry_list(module, query, '', args_dict)
    if sugar_list:
        return sugar_list[0]['id']

def sync_sugar_contact(sugar, coupon=None, offer=None, business=None):
    """ 
    Map coupon data with Sugar Contact fields and create a Sugar Contact.
    Sugar tries to stop more than one contact with the same first name last 
    name combination. Advertiser email makes this Sugar Contact unique.
    """
    LOG.debug('sync_sugar_contact')
    contact_dict = {}
    if coupon:
        business = coupon.offer.business
    else:
        if offer:
            business = offer.business
    contact_id = None
    advertiser_name = business.advertiser.advertiser_name
    if advertiser_name and len(advertiser_name) > 0:
        if advertiser_name.find(' ') == -1:
            contact_dict['first_name'] = advertiser_name
        else:
            contact_dict['first_name'], contact_dict['last_name'] = \
                advertiser_name.split(' ', 1)
    else:
        contact_dict['first_name'] = business.business_name
    contact_dict['email1'] = business.advertiser.email
    contact_dict['advertiser_id_c'] = business.advertiser.id
    contact_dict['advertiser_admin_url_c'] = ('https://10coupons.com' + 
        reverse('admin:index') + 'advertiser/advertiser/%s/' % str(
        business.advertiser.id))
    location, phone = get_business_location_phone(coupon=coupon, 
        business=business)
    if phone:
        contact_dict['phone_work'] = phone
    if location:
        location_address1 = location.location_address1
        if location.location_address2:
            location_address1 += '\n' + location.location_address2
        contact_dict.update({'primary_address_street': location_address1,               
            'primary_address_city': location.location_city,
            'primary_address_state': location.location_state_province,
            'primary_address_postalcode': location.location_zip_postal})
    contact_id = get_sugar_contact(sugar, contact_dict)
    return contact_id

def get_business_location_phone(coupon=None, business=None):
    """ Get business location and phone number """
    location = None
    phone = None
    if coupon:
        location_list = coupon.location.all().order_by('id')
    else:
        location_list = business.locations.all().order_by('id')
    if len(location_list) > 0:
        location = location_list[0]
        if location.location_area_code and location.location_exchange and \
            location.location_number:
            phone = '(' + location.location_area_code + ') ' + \
                location.location_exchange + '-' + location.location_number
    return location, phone

def get_sugar_account(sugar, values_dict):
    """
    Query sugar for matching 10coupons business. Query based on:
    1) business id then 2) email then check for business name 3) business name 
    and (phone and/or city, state combo).
    """
    # query business in sugar with business_id_c
    LOG.debug(values_dict)
    module = "Accounts"
    query = "%s_cstm.business_id_c = '%s'" % (str.lower(module), 
        values_dict['business_id_c'])
    args_dict = {'selection': ['id', 'name']}
    sugar_list = sugar.get_entry_list(module, query, '', args_dict)
    if sugar_list:
        values_dict['id'] = sugar_list[0]['id']
    else:
        query = set_sugar_email_query(module=module, 
            email=values_dict['email1']) + \
            " and %s_cstm.business_id_c is null" % str.lower(module)
        sugar_list = sugar.get_entry_list(module, query, '', args_dict)
        if sugar_list and (sugar_list[0]['name'].strip() == 
            values_dict['name']):
            values_dict['id'] = sugar_list[0]['id']
        elif sugar_list and (remove_non_ascii_chars(values_dict['name']) == 
            values_dict['name'] and values_dict['name'].lower() == 
            sugar_list[0]['name'].strip().lower()):
            # match on case insensitive business name
            business_count = Business.objects.filter(
                business_name__iexact=values_dict['name'], 
                advertiser__email=values_dict['email1']).count()
            if business_count == 1:
                values_dict['id'] = sugar_list[0]['id']
        try:
            values_dict.get('id')
        except KeyError:
            # query biz name, like phone, city, state, and biz id is null
            query = "BINARY %s.name = '%s'" % (str.lower(module), 
                values_dict['name'].strip().replace("'","\\'")) + \
                " and %s_cstm.business_id_c is null" % str.lower(module) 
            try:
                query += " and %s.office_phone like '%s%%'" % (
                    str.lower(module), values_dict['office_phone'])
            except KeyError:
                pass
            try:
                if values_dict['billing_address_city'] != '':
                    query += " and %s.billing_address_city = '%s'" % (
                        str.lower(module), 
                        values_dict['billing_address_city']) + \
                        " and %s.billing_address_state = '%s'" % (
                        str.lower(module), values_dict['billing_address_state'])     
            except KeyError:
                pass 
            if 'office_phone' in query:           
                sugar_list = sugar.get_entry_list(module, query, '', args_dict)
                if sugar_list:
                    values_dict['id'] = sugar_list[0]['id']
    try:
        LOG.debug('update %s' % values_dict['id'])
    except KeyError:
        LOG.debug('create')
    # if values_dict doesn't have acct id then create acct
    response = sugar.set_entry(module, dict_to_name_value(values_dict))
    module_id = response['id']
    LOG.debug('%s.id: %s' % (module, module_id))
    return module_id 

def get_sugar_contact(sugar, values_dict):
    """
    Query sugar for matching 10coupons business. Query based on:
    1) advertiser_id_c then 2) email
    """
    module = "Contacts"
    try:
        query = "%s_cstm.advertiser_id_c = '%s'" % (str.lower(module), 
            values_dict['advertiser_id_c'])
        args_dict = {'selection': ['id', 'email1']}
        sugar_list = sugar.get_entry_list(module, query, '', args_dict)
    except KeyError:
        sugar_list = None
    if sugar_list and sugar_list[0]['email1'].strip() == values_dict['email1']:
        values_dict['id'] = sugar_list[0]['id']
    else:
        # query contact email and no adv id
        query = set_sugar_email_query(module=module, 
            email=values_dict['email1']) + \
            " and %s_cstm.advertiser_id_c is null" % str.lower(module)
        sugar_list = sugar.get_entry_list(module, query, '', args_dict)
        if sugar_list:
            values_dict['id'] = sugar_list[0]['id']
    try:
        LOG.debug('update %s' % values_dict['id'])
    except KeyError:
        LOG.debug('create')
    # if values_dict doesn't have contact id then create contact
    response = sugar.set_entry(module, dict_to_name_value(values_dict))
    module_id = response['id']
    LOG.debug('%s.id: %s' % (module, module_id))
    return module_id

def set_sugar_relationship(sugar, module1, module1_id,  module2, module2_id):
    """ Set relationship between two different Sugar module ids. """
    LOG.debug('set_sugar_relationship')
    if module1 != module2 and module1_id != module2_id and module2_id:
        relationship = sugar.client.factory.create("set_relationship_value")
        relationship.module1 = module1
        relationship.module1_id = module1_id
        relationship.module2 = module2
        relationship.module2_id = module2_id
        sugar.set_relationship(relationship)
    return

def create_sugar_reminder_task(sugar, business, subject, offset_days):
    """ Create sugar reminder task. """
    date_due = datetime.datetime.today() + \
        datetime.timedelta(days=offset_days)
    # check to see if reminder task exists
    start_date = datetime.datetime.today() + datetime.timedelta(days=-1)
    start_date = start_date.strftime('%Y-%m-%d')
    query = "tasks.modified_user_id = '%s' and " % config.SUGAR_USER_ID + \
        "BINARY tasks.name = '%s'" % subject
    args_dict = {'selection': ['id']}
    sugar_datetime_format = '%Y-%m-%d %H:%M:%S'
    this_query = query + " and tasks.description = '%s'" % business.id 
    sugar_list = sugar.get_entry_list(module='Tasks', query=this_query, 
        order_by='', args_dict=args_dict)
    if sugar_list and sugar_list[0]['id']:
        LOG.debug('sugar task exists')
        return
    # create the task related to contact and account
    values_dict = {'description': business.id, 'name': subject, 
        'status': 'Not Started', 'priority': 'High', 
        'parent_type': 'Accounts', 'parent_id': None, 
        'assigned_user_id': None, 'contact_id': None, 
        'date_due': date_due.strftime(sugar_datetime_format),
        'date_start': datetime.datetime.today().strftime(sugar_datetime_format)}
    # get the contact_id with advertiser email        
    module = 'Contacts'
    query = set_sugar_email_query(module=module, 
        email=business.advertiser.email)
    sugar_list = sugar.get_entry_list(module, query, '', args_dict)
    if sugar_list:
        values_dict['contact_id'] = sugar_list[0]['id']    
    # get the account id with business name and email
    module = 'Accounts'
    query = query.replace('contacts.id', '%s.id' % str.lower(module))
    query += " and BINARY %s.name = '%s'" % (str.lower(module), 
        business.business_name.replace("'","\\'"))
    sugar_list = sugar.get_entry_list(module, query, '', 
        args_dict={'selection': ['id', 'assigned_user_id']})
    if sugar_list:
        values_dict['parent_id'] = sugar_list[0]['id']
        values_dict['assigned_user_id'] = sugar_list[0]['assigned_user_id']
    # create this SugarCRM task 
    if values_dict['contact_id'] and values_dict['parent_id'] and \
        values_dict['assigned_user_id']:
        sugar.set_entry(module='Tasks', 
            name_value_list=dict_to_name_value(values_dict))
    return