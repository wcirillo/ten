""" Holds the Base Classes for Coupon tests."""
import datetime

from django.core.urlresolvers import reverse

from advertiser.factories.location_factory import BUSINESS_LOCATION_FACTORY
from common.session import parse_curr_session_keys
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import (SLOT_FACTORY,
    SLOT_TIME_FRAME_FACTORY)
from coupon.models.coupon_models import Coupon, CouponType

class PreviewEditTestCase(EnhancedTestCase):
    """ 
    This is the base class for the tests of the preview edit functionality.
    """
    urls = 'urls_local.urls_2'

    def setUp(self):
        super(PreviewEditTestCase, self).setUp()
        self.coupon = COUPON_FACTORY.create_coupon()
        self.coupon.coupon_type = CouponType.objects.get(id=1)
        self.coupon.save()
        self.location = self.coupon.offer.business.locations.all()[0]
        self.advertiser = self.coupon.offer.business.advertiser
        self.request_data = None  

    def setup_post_data(self, advertiser, location_count=0):
        """ Setup the client for the tests. """
        business = advertiser.businesses.all()[0]
        offer = business.offers.all()[0]
        self.post_data = {
            'business_name': business.business_name, 
            'slogan':business.slogan,
            'web_url':business.web_url,
            'headline': offer.headline,
            'qualifier': offer.qualifier,
            'is_valid_monday':True,
            'is_valid_tuesday':True,
            'is_valid_wednesday':True,
            'is_valid_thursday':True,
            'is_valid_friday':True,
            'is_valid_saturday':True,
            'is_valid_sunday':True, 
            'default_restrictions':[2,3],
            'is_redeemed_by_sms':1,
            'expiration_date':'4/4/11'}

        count = 0
        while count != location_count:
            #location = business.locations.all()[count]
            location = BUSINESS_LOCATION_FACTORY.create_business_location(
                business)
            location_dict = {
                'location_address1_%s' %
                    str(count + 1):location.location_address1,
                'location_address2_%s' %
                    str(count + 1):location.location_address2,
                'location_city_%s' %
                    str(count + 1):location.location_city,
                'location_state_province_%s' %
                    str(count + 1):location.location_state_province,
                'location_zip_postal_%s' %
                    str(count + 1):location.location_zip_postal,
                'location_description_%s' %
                    str(count + 1):location.location_description,
                'location_area_code_%s' %
                    str(count + 1):location.location_area_code,
                'location_exchange_%s'
                    % str(count + 1):location.location_exchange,
                'location_number_%s'
                    % str(count + 1):location.location_number}
            self.post_data.update(location_dict)
            count += 1
    
    @classmethod
    def prep_slot(cls, coupon, slot_coupon):
        """ Prepare test with a valid slot. """
        slot0 = SLOT_FACTORY.create_slot(coupon=coupon,
            create_slot_time_frame=False)
        slot0.end_date = datetime.date(2012, 1, 2)
        slot0.save()
        SLOT_TIME_FRAME_FACTORY.create_expired_time_frame(slot=slot0,
            coupon=slot_coupon)

    def common_assertions(self, response, request_method):
        """ Test common assertions for TestPreviewEdit tests. """
        self.assertEqual(response.status_code, 200)
        if request_method == 'POST':
            self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
            self.assertContains(response, "frm_checkout_coupon_purchase")
    
    def assert_session_keys_current(self,
    current_biz=(0, 0), current_offer=(0, 0), current_coupon=(0, 0)):
        """ Assert the session keys updated correctly. Each parameter is a tuple
        with the first element used to test self.session, and the second 
        element used to test self.client.session.
        """
        self.assertEqual(current_biz[0], self.session['current_business'])
        self.assertEqual(current_biz[1], 
            self.client.session['current_business'])
        self.assertEqual(current_offer[0], self.session['current_offer'])
        self.assertEqual(current_offer[1], self.client.session['current_offer'])
        self.assertEqual(current_coupon[0], self.session['current_coupon'])
        self.assertEqual(current_coupon[1], 
            self.client.session['current_coupon'])

    def assert_session_update(self, **kwargs):
        """ Assert values in session. """
        business_id = kwargs.get('business_id', 0)
        offer_id = kwargs.get('offer_id', 0)
        coupon_id = kwargs.get('coupon_id', 0)

        if kwargs.get('headline'):
            self.assertEqual(kwargs['headline'],
                self.client.session['consumer']['advertiser']['business'][
                business_id]['offer'][offer_id]['headline'])
        
        if kwargs.get('qualifier'):
            self.assertEqual(kwargs['qualifier'],
                self.client.session['consumer']['advertiser']['business'][
                business_id]['offer'][offer_id]['qualifier'])
        
        if kwargs.get('coupon_type_id'):
            self.assertEqual(kwargs['coupon_type_id'],
                self.client.session['consumer']['advertiser']['business'][
                business_id]['offer'][offer_id]['coupon'][
                coupon_id]['coupon_type_id'])
        
        if kwargs.get('business_name'):
            self.assertEqual(kwargs['business_name'],
                self.client.session['consumer']['advertiser']['business'][
                business_id]['business_name'])

    def assert_new_coupon(self, new_coupon_id, **kwargs):
        """ Assert new coupon was created with field values specified in kwargs.
        """
        new_coupon = Coupon.objects.get(id=new_coupon_id)
        if kwargs.get('coupon_id'):
            self.assertEqual(int(kwargs['coupon_id']), new_coupon.id)
        if kwargs.get('coupon_type_id'):
            self.assertEqual(int(kwargs['coupon_type_id']), 
            new_coupon.coupon_type_id)
        if kwargs.get('offer_id'):
            self.assertEqual(int(kwargs['offer_id']), new_coupon.offer.id)
        if kwargs.get('headline'):
            self.assertEqual(kwargs['headline'], new_coupon.offer.headline)
        if kwargs.get('qualifier'):
            self.assertEqual(kwargs['qualifier'], new_coupon.offer.qualifier)
        if kwargs.get('business_id'):
            self.assertEqual(int(kwargs['business_id']), 
            new_coupon.offer.business.id)
        if kwargs.get('business_name'):
            self.assertEqual(kwargs['business_name'], 
            new_coupon.offer.business.business_name)


class ValidDaysTestCase(EnhancedTestCase):
    """ This is a base class for Valid Days tests. """

    def valid_days_post_response(self, post_path, coupon):
        """ 
        This method passes in a coupon and uses the coupon valid days data to 
        POST, then asserts the posted data matches the database and the 
        session. 
        """
        response = self.client.post(reverse(post_path), 
            data={
                "is_redeemed_by_sms" : 1,
                "is_valid_monday" : coupon.is_valid_monday,
                "is_valid_tuesday" : coupon.is_valid_tuesday,
                "is_valid_wednesday" : coupon.is_valid_wednesday,
                "is_valid_thursday" : coupon.is_valid_thursday,
                "is_valid_friday" : coupon.is_valid_friday,
                "is_valid_saturday" : coupon.is_valid_saturday,
                "is_valid_sunday" : coupon.is_valid_sunday,},
            follow=True)
        session_dict = parse_curr_session_keys(
            self.client.session, ['this_coupon'])
        only_compare_these_keys_list = [
            'is_valid_monday',
            'is_valid_tuesday',
            'is_valid_wednesday',
            'is_valid_thursday',
            'is_valid_friday',
            'is_valid_saturday',
            'is_valid_sunday']
        # Compare what got posted to what is now in the session.
        self.compare_these_objects(coupon, session_dict['this_coupon'],
                    only_compare_these_keys_list=only_compare_these_keys_list)
        updated_coupon = Coupon.objects.get(id=coupon.id)
        # Compare what got posted to what is now in the database.
        self.compare_these_objects(coupon, updated_coupon,
            only_compare_these_keys_list=only_compare_these_keys_list)
        return response
