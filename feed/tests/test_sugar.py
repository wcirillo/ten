""" Tests for sugar of the feed app """

import datetime

from advertiser.models import Advertiser, Business, Location
from common.test_utils import EnhancedTestCase
from coupon.models import Coupon
from feed.sugar import (Sugar, get_sugar_module_fields, dict_to_name_value,
    name_value_to_dict, select_sugar_module_fields)
from feed.sugar_in import sync_sugar_account, get_business_location_phone
from feed.tasks.tasks import sync_coupon_business
from feed.tests.feed_test_case import FeedTestCase


class TestSugar(EnhancedTestCase):
    """ Test sugar web service. These tests need login to live SugarCRM website. 
    """
    fixtures = ['test_advertiser', 'test_coupon', 'test_coupon_views', 
        'test_slot', 'test_sales_rep']
    sugar = Sugar()
      
    def test_get_sugar_module_fields(self):
        """ Test login, logout, and sugar web service get_module_fields. """
        module = 'Accounts'
        response = get_sugar_module_fields(self.sugar, module)
        self.assertTrue(response != None)
        
    def test_get_entry_list(self):
        """ Test get_entry_list return of module entries. """
        module = 'Accounts'
        query = "accounts.name = 'testing testers test'"
        sugar_list = self.sugar.get_entry_list(module, query)
        self.assertEqual(sugar_list, None)
        
    def test_sync_sugar_account_site(self):
        """ Test that advertiser and business does not sync due to site 1. """
        advertiser = Advertiser.objects.get(id=1)
        business = Business(advertiser_id=advertiser.id, business_name='test') 
        business.save()
        account_id = sync_sugar_account(self.sugar, business=business)
        self.assertEquals(account_id, None)


class MockSugar(Sugar):
    """ A Mock version of Sugar, the class that connects to SugarCRM""" 
    def get_entry_list(self, module, query, order_by='', args_dict=None):
        """ Mock get_entry_list. """
        return [{'id': 'test_id', 'salesforce_id_c': 'test1',
                'Contact ID': 'test2', 'assigned_user_id': 'user_id',
                'email1': 'test@test.com'}]

    def set_entry(self, module, name_value_list):
        """ Mock set_entry. """
        return {'id': []}

    def get_relationships(self, module_name, module_id, related_module):
        """ Mock get relationship. """
        return {'ids': []}

    def set_relationship(self, relationship):
        """ Mock set relationship. """
        pass


class TestSugarMode(FeedTestCase): 
    """ Test SugarCRM create and modify mode (of SugarCRM businesses to us) 
    without connecting to the SugarCRM server. """
    
    fixtures = ['test_geolocation', 'test_advertiser', 'test_coupon',
        'test_coupon_views', 'test_slot']

    sugar = Sugar()
    
    def test_dict_to_name_value(self):
        """ Test conversion of dict to list of name values pairs for set_entry 
        function. Test 3 values: int, string, None.
        """
        values_dict = {'name1': 'value1', 'name2': 'value2'}
        name_value_list = dict_to_name_value(values_dict)
        self.assertEqual(str(name_value_list), 
            "[{'name': 'name2', 'value': 'value2'}, " + \
            "{'name': 'name1', 'value': 'value1'}]")
    
    def test_name_value_to_dict(self):
        """ Test conversion of get_entry_list name value value pairs and their 
        conversion to a standard python dict.
        """
        name_value_dict = {('name', 'business_id_c'): ('value', 131)}
        self.assertEqual(str(name_value_to_dict(name_value_dict)), 
            "{'business_id_c': 131}")
        name_value_dict = {('name', 'business'): ('value', None)}
        self.assertEqual(str(name_value_to_dict(name_value_dict)), 
            "{'business': None}")
        name_value_dict = {('name', 'business_name'): ('value', 
            "test2 &gt; test1")}
        self.assertEqual(str(name_value_to_dict(name_value_dict)), 
            "{'business_name': 'test2 > test1'}")

    def test_select_sugar_module_fields(self):
        """ Test that correct module fields are returned """
        field_list = select_sugar_module_fields(module="Accounts")
        self.assertTrue('business_id_c' in str(field_list))
        field_list = select_sugar_module_fields(module="Contacts")
        self.assertTrue('first_name' in str(field_list))

    def test_get_biz_location_phone(self):
        """ Test get coupon business_location function. """
        coupon = Coupon.objects.get(id=2)
        location = coupon.location.all()[0]
        location.location_area_code = '800'
        location.location_exchange = '555'
        location.location_number = '1244'
        location.save()
        location, phone = get_business_location_phone(coupon=coupon)
        self.assertTrue(location)
        self.assertTrue(phone == '(800) 555-1244')
        business = Business.objects.get(id=114)
        location, phone = get_business_location_phone(business=business)
        # no location or phone for this business
        self.assertTrue(location is None)
        self.assertTrue(phone is None)

    def test_create_coupon_business(self):
        """ Test create of advertiser, business and location on website. 
        Initialize the function with test data that would have been retrieved 
        from Sugar. 
        """
        email = 'test123456@example.com'
        postal_code = '12601'
        contact_dict = {}
        account_dict = {} 
        for field in select_sugar_module_fields(module='Contacts'):
            contact_dict[field] = None
        for field in select_sugar_module_fields(module='Accounts'):
            account_dict[field] = None      
        account_dict.update({'name': 'Test business name', 
            'phone_office': '800-555-1234', 'email1': email, 'modify': None})
        contact_dict.update({'primary_address_postalcode': postal_code, 
            'last_name': 'LastName', 'primary_address_city': 'city', 
            'first_name': 'FirstName', 'primary_address_state': 'st', 
            'primary_address_street': 'addr1 addr2 addr3 addr4 addr5 addr6', 
            'modify': None})
        sync_coupon_business(self.sugar, account_dict, contact_dict)
        # test coupon business created
        advertiser = Advertiser.objects.get(email=email)
        self.assertTrue(advertiser is not None)
        business = advertiser.businesses.all()[0]
        self.assertTrue(business is not None)
        self.assertEquals(business.locations.all()[0].location_zip_postal, 
            postal_code)
        
    def test_modify_coupon_business(self):
        """ Test modify of advertiser, business and location on website. 
        Initialize the function with test data that would have been retrieved 
        from Sugar. 1. Do not update business_name or short_business_name 
        2. Update website.
        """
        email = 'user114@company.com' # must match email of advertiser.id: 114
        postal_code = '12601'
        business_name = 'New "business name" replaces this old business'
        phone = '201-444-1223'
        website = 'http://10testing455.com'
        now = datetime.datetime.now()
        datetime_format = '%Y-%m-%d %H:%M:%S'
        now_format = now.strftime(datetime_format)
        account_dict = {'name': business_name, 
            'phone_office': phone, 'email1': email, 
            'business_id_c': 114, 'website': website,
            'date_modified': now_format, 'modify': True}
        contact_dict = {'primary_address_postalcode': postal_code, 
            'last_name': 'LastName', 'primary_address_city': 'city', 
            'first_name': 'FirstName', 'primary_address_state': 'st', 
            'primary_address_street': 'addr1 addr2', 'advertiser_id_c': 114,  
            'email1': email, 'date_modified': now_format, 'phone_work': phone,
            'modify': True}
        sync_coupon_business(self.sugar, account_dict, contact_dict, 
            modify_mode=True)
        advertiser = Advertiser.objects.get(email=email)
        self.assertTrue(advertiser is not None)
        business = advertiser.businesses.all()[0]
        # business name not changed
        self.assertEquals(business.business_name, 'Test14 Biz')
        self.assertEquals(business.short_business_name, 'Test14 Biz')
        # business url changed
        self.assertEquals(business.web_url, website)
        # new location is created
        location = business.locations.all()[0]
        self.assertEquals(location.location_zip_postal, postal_code)
        self.assertEquals(location.location_address1, 'addr1 addr2')
        self.assertEquals(location.location_address2, '')

    def test_modify_coupon_biz_location(self):
        """ Test modify of advertiser, business and location on website. 
        Initialize the function with test data that would have been retrieved 
        from Sugar. Update location phone from '800-555-1234' to '201-444-1223'.
        """
        email = 'user114@company.com' # must match email of advertiser.id: 114
        postal_code = '12601'
        advertiser = Advertiser.objects.get(email=email)
        self.assertTrue(advertiser is not None)
        business = advertiser.businesses.all()[0]
        location = Location(business=business, 
            location_address1='address1', location_address2='address2',
            location_city='primary_address_city',
            location_state_province='NY',
            location_zip_postal=postal_code,
            location_url='')
        location.save()
        phone = '201-444-1223'
        website = 'http://10testing455.com'
        # soap modify time is more recent than location create date time
        now = datetime.datetime.now() + datetime.timedelta(days=1)
        datetime_format = '%Y-%m-%d %H:%M:%S'
        now_format = now.strftime(datetime_format)
        account_dict = {'name': business.business_name, 
            'phone_office': phone, 'email1': email, 
            'business_id_c': 114, 'website': website,
            'date_modified': now_format, 'modify': True}
        contact_dict = {'primary_address_postalcode': postal_code, 
            'last_name': 'LastName', 'primary_address_city': 'city', 
            'first_name': 'FirstName', 'primary_address_state': 'st', 
            'primary_address_street': '13 addr1 st\nPO BOX addr2\naddr3', 
            'advertiser_id_c': 114, 'email1': email, 
            'date_modified': now_format, 'phone_work': phone, 'modify': True}
        sync_coupon_business(self.sugar, account_dict, contact_dict, 
            modify_mode=True)
        # test for location modification
        for location in business.locations.all():
            if (location.location_area_code + '-' + 
                location.location_exchange + '-' +
                location.location_number) == phone:
                break
        if location:
            self.assertTrue(location.location_number in phone)
            self.assertEquals(location.location_zip_postal, postal_code)
            self.assertEquals(location.location_url, website)
            self.assertEquals(location.location_address1 + 
                location.location_address2 + location.location_city + 
                location.location_state_province, 
                    '13 addr1 stPO BOX addr2 addr3cityst')
        else:
            self.fail('No location.')
