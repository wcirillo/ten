#-*- coding: iso-8859-15 -*-
""" Test advertiser business location views. """
import logging

from django.core.urlresolvers import reverse

from advertiser.models import Advertiser, Location
from common.session import build_advertiser_session
from common.test_utils import EnhancedTestCase
from coupon.config import TEN_COUPON_RESTRICTIONS
from coupon.service.expiration_date_service import (
    frmt_expiration_date_for_dsp, default_expiration_date, 
    get_default_expiration_date)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class CreateLocationBase(EnhancedTestCase):
    """  Test case for Create Locations. """
    
    def check_original_location(self, response):
        """ Assert location display matches what was in the original location.
        """
        self.assertContains(response, '<div class="address1">10 Road</div>')
        self.assertContains(response, 
            '<div class="address2">Apartment 10</div>')
        self.assertContains(response, '<span class="city">City 10</span>')
        self.assertContains(response, '<span class="state">AL </span>')
        self.assertContains(response, '<span class="zip_postal">10101</span>')
        self.assertContains(response, 
            'class="description">Across from 10</div>')
        self.assertContains(response, '(<span class="area_code">101</span>)')
        self.assertContains(response, '<span class="exchange">101</span>')
        self.assertContains(response, '<span class="number">1010</span>')    
           
    def check_location_1(self, response):
        """ Assert location 1 display matches what was in POST """
        self.assertContains(response, '<div class="address1">123 Main St</div>')
        self.assertContains(response, '<div class="address2"></div>')
        self.assertContains(response, '<span class="city">Anytown</span>')
        self.assertContains(response, '<span class="state">NY </span>')
        self.assertContains(response, '<span class="zip_postal">12550</span>')
        self.assertContains(response, 
            'class="description">down on the corner, out in the street</div>')
        self.assertContains(response,
            '<span class="default_phone_paren_open">(</span>' +
            '<span class="area_code">845</span>' +
            '<span class="default_phone_paren_close">) </span>')
        self.assertContains(response, '<span class="exchange">555</span>')
        self.assertContains(response, '<span class="default_phone_hyphen">-' +
            '</span><span class="number">1234</span>')
        
    def check_location_2(self, response):
        """ Assert location 2 display matches what was in POST """
        self.assertContains(response,
            '<div class="address1">999 Broadway</div>')
        self.assertContains(response, 
            '<div class="address2">2nd Street Address</div>')
        self.assertContains(response, 
            '<span class="city">pretty how town</span>')
        self.assertContains(response, '<span class="state">FL </span>')
        self.assertContains(response, '<span class="zip_postal">12601</span>')
        self.assertContains(response, 
            'class="description">with up so floating many bells down</div>')
        self.assertContains(response,
            '<span class="default_phone_paren_open">(</span>' +
            '<span class="area_code">917</span>' +
            '<span class="default_phone_paren_close">) </span>')
        self.assertContains(response, '<span class="exchange">552</span>')
        self.assertContains(response, '<span class="default_phone_hyphen">-' + 
            '</span><span class="number">1100</span>')
            
    def check_location_3(self, response):
        """ Assert location 3 display matches with what was in POST """
        self.assertContains(response,
            '<div class="address1">Blue Jay Way</div>')
        self.assertContains(response, '<div class="address2"></div>')
        self.assertContains(response, '<span class="city"></span>')
        self.assertContains(response, '<span class="state">AZ </span>')
        self.assertContains(response, '<span class="zip_postal"></span>')
        self.assertContains(response, 
            'class="description">intersection with Abbey Road</div>')
        self.assertContains(response, '<span class="area_code"></span>')
        self.assertContains(response, '<span class="exchange"></span>')
        self.assertContains(response, '<span class="number"></span>')

    def check_template_ids_exist(self, response):
        """
        Check that the correct id's and classes printed on the create locations 
        page. This is a combination of the frm and the dsp id's and classes.
        """
        count = 0
        id_class_list = [
            'header_%s', 'loc_%s', 'loc_%s_txt', 'name="%s"',
           'location_address1_%s', 'id_location_address1_%s',
           'location_address2_%s', 'id_location_address2_%s',
           'location_city_%s', 'id_location_city_%s',
           'location_zip_postal_%s', 'id_location_zip_postal_%s',
           'location_area_code_%s', 'id_location_area_code_%s',
           'location_exchange_%s', 'id_location_exchange_%s',
           'location_number_%s', 'id_location_number_%s',
           'location_description_%s', 'id_location_description_%s',
           'location_%s']
        while count <= 11:
            for id_or_class in id_class_list:
                #item = id_or_class % str(count)
                if count in [0, 11]:
                    self.assertNotContains(response, id_or_class % str(count))
                else:
                    self.assertContains(response, id_or_class % str(count))
            count += 1
    
def strip_key_string(old_dict, strip_item):
    """ Remove the appended part of the dynamic variable """
    new_dict = {}
    for key in old_dict:
        item = key.replace(strip_item, '')
        new_dict.update({item:old_dict[key]})
    return new_dict

def get_location_dict_1():
    """ Build location 1 dict """
    return {'web_url': 'example.com',  
        'location_address1_1': '123 Main St',
        'location_address2_1': '',
        'location_city_1': 'Anytown', 
        'location_state_province_1': 'NY',
        'location_zip_postal_1': '12550', 
        'location_description_1': 'down on the corner, out in the street', 
        'location_area_code_1': '845',
        'location_exchange_1': '555', 
        'location_number_1': '1234',
         }

def get_location_dict_2():
    """ Build location 2 dict """
    return {'location_address1_2': '999 Broadway',
        'location_address2_2': '2nd Street Address',
        'location_city_2': 'pretty how town', 
        'location_state_province_2': 'FL', 
        'location_zip_postal_2': '12601',  
        'location_description_2': 'with up so floating many bells down', 
        'location_area_code_2': '917',
        'location_exchange_2': '552', 
        'location_number_2': '1100', 
        'add_location': 'Next Step »',
        }


class TestBusinessLocations(CreateLocationBase):
    """  Test case for showing the add-location page. """
    fixtures = ['test_advertiser', 'test_coupon_views', 'test_geolocation']  
    urls = 'urls_local.urls_2'
    
    def test_key_error_current_offer(self):
        """ Assert redirect when no current offer in session. """
        advertiser = Advertiser.objects.get(id=114)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('add-location'), follow=True) 
        # Redirected to home.
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')
        
    def test_get_no_locations(self):
        """ Assert the location form when an advertiser hits this form for the
        first time. That means there are no locations.
        """
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0]
        business.locations.all().delete()
        offer = business.offers.all()[0]
        offer.coupons.all()[0].delete()
        build_advertiser_session(self, advertiser)
        self.session['expiration_date'] = get_default_expiration_date()
        self.assemble_session(self.session)
        response = self.client.get(reverse('add-location'), follow=True)
        self.assertContains(response, 'frm_create_location')
        self.assertContains(response, business.business_name)
        self.assertContains(response, business.slogan)
        self.assertContains(response, offer.headline)
        self.assertContains(response, offer.qualifier)
        self.assertContains(response, get_default_expiration_date())
        self.assertContains(response, TEN_COUPON_RESTRICTIONS)
        self.assertContains(response, 'Offer good 7 days a week.')
        self.assertContains(response, '<option value="dash">----------' + 
            '-----------------------</option><option value="NY">' + 
            'New York</option><option value="NJ">New Jersey</option>' + 
            '<option value="dash">---------------------------' + 
            '------</option>')        
        self.assertContains(response, 'New Mexico</option><option ' + 
            'value="NY">New York</option><option value="NC">')
        self.check_template_ids_exist(response)
        self.assertContains(response, "$199/month")
         
    def test_get_business_locations(self):
        """ Assert a user hits the location page with a location in session. """
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0] 
        offer = business.offers.all()[0]
        coupon = offer.coupons.all()[0]
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('add-location'))
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/add-location/')
        self.check_template_ids_exist(response)
        # Ensure locations are displayed for editing.
        self.assertContains(response, '10 Road')
        self.assertContains(response, 'Apartment 10')
        self.assertContains(response, '1 Road')
        self.assertContains(response, '11111')
        self.assertContains(response, 'frm_create_location')
        self.assertContains(response, business.business_name)
        self.assertContains(response, business.slogan)
        self.assertContains(response, offer.headline)
        self.assertContains(response, offer.qualifier)
        self.assertContains(response, 
                        frmt_expiration_date_for_dsp(coupon.expiration_date))
        self.assertContains(response, TEN_COUPON_RESTRICTIONS)
        self.assertContains(response, '<option value="dash">--------' + 
            '-------------------------</option>' + 
            '<option value="NY">New York</option><option value="NJ">' + 
            'New Jersey</option><option value="dash">------------' + 
            '---------------------</option>')        
        self.assertContains(response, 'New Mexico</option>' +
            '<option value="NY">New York</option><option value="NC">')
  
        
class TestCreateLocation(CreateLocationBase):
    """ TestCase for the functional flow of the Create Coupon process. """
    
    fixtures = ['test_advertiser', 'test_coupon_views', 'test_geolocation']

    def test_invalid_web_url(self):
        """ Assert POST to create locations with a bad web_url reloads the page.
        """
        advertiser = Advertiser.objects.get(id=12)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        location_dict_1 = get_location_dict_1()
        location_dict_1['web_url'] = 'abcdefghijklmnopqrstuvwxyz'
        response = self.client.post(
            '/hudson-valley/create-coupon/add-location/',
            location_dict_1, follow=True)
        self.assertContains(response, '<li>Enter a valid URL.</li>')
        self.assertContains(response, 'frm_create_location')
        for key in location_dict_1:
            self.assertContains(response, location_dict_1[key])

    def test_first_location(self):
        """ Create an advertiser with no coupon yet for this business offer adds
        the first location and creates a coupon.
        """
        advertiser = Advertiser.objects.get(id=12)
        business = advertiser.businesses.all()[0]
        business.locations.all().delete()
        business.offers.all()[1].coupons.all().delete()
        build_advertiser_session(self, advertiser)
        self.session['expiration_date'] = default_expiration_date()
        self.assemble_session(self.session)
        location_dict_1 = get_location_dict_1()
        response = self.client.post(
            '/hudson-valley/create-coupon/add-location/',
            location_dict_1, follow=True)
        new_location = business.locations.all()[0]
        this_new_location = self.client.session['consumer']['advertiser'] \
            ['business'][0]['location'][0]
        self.assertContains(response, 'frm_create_restrictions')
        # Check this location is now displaying on the page
        self.check_location_1(response)
        self.assertEqual(advertiser.businesses.latest('id').locations.count(),
            1)
        LOG.debug("""--Make sure the new location in the database was added
            with the correct info.""")
        strip_location_dict_1 = strip_key_string(location_dict_1, '_1')
        self.compare_these_objects(new_location, strip_location_dict_1)
        LOG.debug("""--Make sure the location posted is now the location in
            session that was added.""")
        self.compare_these_objects(this_new_location, strip_location_dict_1, 
            dont_compare_keys_list=['location_id'])
        
    def test_coupon_first_location(self):
        """ Assert an advertiser that has a coupon in the db adds the first
        location to the business and the coupon for the first time.
        """
        advertiser = Advertiser.objects.get(id=12)
        business = advertiser.businesses.all()[0]
        business.locations.all().delete()
        build_advertiser_session(self, advertiser)
        self.session['expiration_date'] = default_expiration_date()
        self.assemble_session(self.session)
        location_dict_1 = get_location_dict_1()
        response = self.client.post(
            '/hudson-valley/create-coupon/add-location/',
            location_dict_1, follow=True)
        advertiser = Advertiser.objects.get(id=12)
        new_location = business.locations.all()[0]
        this_new_location = self.client.session['consumer']['advertiser'] \
            ['business'][0]['location'][0]
        self.assertContains(response, 'frm_create_restrictions')
        # Check this location is now displaying on the page
        self.check_location_1(response)
        self.assertEqual(advertiser.businesses.latest('id').locations.count(),
            1)
        LOG.debug("""--Make sure the new location in the database was added with
            the correct info.""")
        strip_location_dict_1 = strip_key_string(location_dict_1, '_1')
        self.compare_these_objects(new_location, strip_location_dict_1)
        LOG.debug("""--Make sure the location posted is now the location in
            session that was added.""")
        self.compare_these_objects(this_new_location, strip_location_dict_1, 
            dont_compare_keys_list=['location_id'])

    def test_update_this_location(self):
        """ Assert updating the current location. Advertiser 12 business[0]
        offer[1] coupon[0] has 1 location already. Update the current
        location.
        """
        advertiser = Advertiser.objects.get(id=12)
        business = advertiser.businesses.all()[0]
        orig_location = business.locations.all()[0]
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        this_orig_location = self.client.session['consumer']['advertiser'] \
            ['business'][0]['location'][0]
        # Modify an existing location:
        self.assertEqual(advertiser.businesses.latest('id').locations.count(), 
            1)
        location_dict_1 = get_location_dict_1()
        response = self.client.post(
            '/hudson-valley/create-coupon/add-location/',
            location_dict_1, follow=True)
        new_location = business.locations.all()[0]
        this_new_location = self.client.session['consumer']['advertiser'] \
            ['business'][0]['location'][0]
        self.assertContains(response, 'frm_create_restrictions')
        # Check this location is now displaying on the page
        self.check_location_1(response)
        self.assertEqual(advertiser.businesses.latest('id').locations.count(),
            1)
        LOG.debug(
            '--Make sure the location info in the database is different now.')
        # This helps verify it was an update and not an insert.
        self.compare_these_objects(orig_location, new_location, 
                                   assert_equal=False)
        LOG.debug("""--Make sure the new location in the database was updated
                    with the correct info.""")
        strip_location_dict_1 = strip_key_string(location_dict_1, '_1')
        self.compare_these_objects(new_location, strip_location_dict_1)
        LOG.debug("""--Make sure the old location in session is different from
            the new location now in session.""")
        # This helps verify it was an update to the same location in session and
        # not a brand new location added.
        self.compare_these_objects(this_orig_location, this_new_location, 
           assert_equal=False, dont_compare_keys_list=['location_id'])
        LOG.debug("""--Make sure the location posted is now the location in
            session that was updated.""")
        self.compare_these_objects(this_new_location, strip_location_dict_1, 
            dont_compare_keys_list=['location_id'])
        self.assertContains(response, TEN_COUPON_RESTRICTIONS)

    def test_create_multiple_locations(self):
        """ Assert adding another location. Advertiser 12 business[0]offer[1]
         coupon[0] has 1 location already. Update 1st location and add a second
         location.
        """
        advertiser = Advertiser.objects.get(id=12)
        business = advertiser.businesses.all()[0]
        orig_location_1 = business.locations.all()[0]
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Verify this advertiser only has 1 business.
        if advertiser.businesses.count() > 1:
            self.fail('Expected one location, got 2.')
        # Verify this advertiser only has 1 business in session.
        if len(self.client.session['consumer']['advertiser']['business'][0] \
            ['location']) > 1:
            self.fail('Expected one location, got 2.')
        this_location_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][1]['coupon'][0]['location'])
        this_orig_location_1 = self.client.session['consumer']['advertiser'] \
            ['business'][0]['location'][0]
        # Add a new location:  
        self.session['add_location'] = 1
        self.assemble_session(self.session)
        both_locations_dict = {}
        loc_list = [get_location_dict_1(), get_location_dict_2()]
        both_locations_dict.update(loc_list[0])
        both_locations_dict.update(loc_list[1])
        response = self.client.post(
            '/hudson-valley/create-coupon/add-location/', 
            both_locations_dict, follow=True)
        new_location_count = len(self.client.session['consumer']['advertiser'] \
            ['business'][0]['offer'][1]['coupon'][0]['location'])
        self.assertEqual(new_location_count, this_location_count+1)
        # Check that we now have 2 locations.
        self.assertEqual(advertiser.businesses.latest('id').locations.count(),
            2)
        # First check the correct form is on the page and both locations
        self.assertContains(response, 'frm_create_restrictions')
        LOG.debug('--Check location 1, the original location is on the page.')
        self.check_location_1(response)
        LOG.debug('--Check location 2 is on the page.')
        self.check_location_2(response)
        LOG.debug('--Check original location in database has been modified.')
        location_1 = business.locations.all().order_by('id')[0]
        self.compare_these_objects(orig_location_1, location_1,
            assert_equal=False)
        #Check original location in the session has not been modified.
        this_location_1 = self.client.session['consumer']['advertiser'] \
            ['business'][0]['location'][0]
        self.compare_these_objects(this_orig_location_1, this_location_1, 
            dont_compare_keys_list=['location_id'], assert_equal=False)
        try:
            # Now we do not want an IndexError since we should now have 2
            # locations in the database.
            locations = business.locations.order_by('id')
            location_1, location_2 = locations[0], locations[1]
        except IndexError:
            self.fail('Locations not created in database.')
        try:
            # Now we do not want an KeyError since we should now have 2
            # locations in the session.
            this_location_2 = self.client.session['consumer']['advertiser'] \
                ['business'][0]['location'][1]
        except IndexError:
            self.fail('Locations not created in session.')
        LOG.debug("""--Make sure the Post data matches what got inserted into
            the database.""")
        strip_location_dict_1 = strip_key_string(loc_list[0], '_1')
        self.compare_these_objects(location_1, strip_location_dict_1)
        strip_location_dict_2 = strip_key_string(loc_list[1], '_2')
        self.compare_these_objects(location_2, strip_location_dict_2)
        LOG.debug("""--Make sure the Post data matches the second location that
            should now be in the session.""")
        self.compare_these_objects(this_location_1, strip_location_dict_1, 
            dont_compare_keys_list=['location_id'])
        self.compare_these_objects(this_location_2, strip_location_dict_2, 
            dont_compare_keys_list=['location_id'])
        self.assertContains(response, TEN_COUPON_RESTRICTIONS)
        
    def test_minus_one_location(self):
        """ Assert advertiser has 2 locations and only POSTs 1. Update the first
        business location only.  Then make sure you remove the second location
        id out of the coupon location table.
        """
        advertiser = Advertiser.objects.get(id=12)
        business = advertiser.businesses.all()[0]
        location_2 = Location.objects.get(id=112)
        location_2.business_id = business.id
        location_2.save()
        second_offer = business.offers.all().order_by('id')[1]
        second_offer.coupons.all()[0].location.add(location_2.id)
        business_locations = business.locations.all().order_by('id')
        orig_business_location_1 = business_locations[0]
        orig_business_location_2 = business_locations[1]
        orig_coupon_locations = second_offer.coupons.all()[0].location.all()
        orig_coupon_count = len(orig_coupon_locations)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        this_orig_business_location_1 = self.client.session['consumer']\
            ['advertiser']['business'][0]['location'][0]
        this_orig_business_location_2 = self.client.session['consumer']\
            ['advertiser']['business'][0]['location'][1]
        these_orig_coupon_locations = self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][1]['coupon'][0]['location']
        location_dict_1 = get_location_dict_1()
        self.client.post('/hudson-valley/create-coupon/add-location/',
            location_dict_1, follow=True)
        business_locations = business.locations.all().order_by('id')
        business_location_1 = business_locations[0]
        business_location_2 = business_locations[1]        
        coupon_locations = second_offer.coupons.all()[0].location.all()
        this_business_location_1 = self.client.session['consumer']\
            ['advertiser']['business'][0]['location'][0]
        this_business_location_2 = self.client.session['consumer']\
            ['advertiser']['business'][0]['location'][1]
        this_coupon_location = self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][1]['coupon'][0]['location']
        strip_location_dict_1 = strip_key_string(location_dict_1, '_1')
        # Check the database business_location_1 is different
        self.compare_these_objects(orig_business_location_1,
            business_location_1, dont_compare_keys_list=['location_id'],
            assert_equal=False)
        # Check the database business_location_1 has the POSTed values.
        self.compare_these_objects(business_location_1, strip_location_dict_1) 
        # Check the database business_location_2 is the same
        self.compare_these_objects(orig_business_location_2,
            business_location_2)
        # Check the database coupon_locations count are different
        self.assertEqual(orig_coupon_count-1, len(coupon_locations))
        self.assertEqual(len(coupon_locations), 1)
        # Check the database coupon_location id == 111
        self.assertEqual(coupon_locations[0].id, 111)        
        # Check the session business_location_1 is different
        self.compare_these_objects(this_orig_business_location_1, 
            this_business_location_1,
            dont_compare_keys_list=['location_id'],
            assert_equal=False)
        # Check the session business_location_1 has the POSTed values.
        self.compare_these_objects(this_business_location_1,
            strip_location_dict_1, dont_compare_keys_list=['location_id'])
        # Check the session business_location_2 is the same
        self.compare_these_objects(this_orig_business_location_2, 
            this_business_location_2)
        # Check the session coupon_locations count are different
        self.assertEqual(len(these_orig_coupon_locations)-1, 
            len(this_coupon_location))
        self.assertEqual(len(this_coupon_location), 1)
        # Check the session coupon_location id == 111
        self.assertEqual(this_coupon_location[0], 111)
