""" Test functions of the common session module. """
from django.test.client import RequestFactory

from advertiser.models import Advertiser
from common.session import (build_advertiser_session, create_consumer_in_session,
    parse_curr_session_keys)
from common.test_utils import EnhancedTestCase
from consumer.models import Consumer
from ecommerce.models import Product


class TestSessionKeyParser(EnhancedTestCase):
    """ Tests for parse_curr_session_keys to assert it grabs the proper key
    from the session, passes KeyErrors back to the caller and maintains a proper
    relationship with request.session (when updated).
    """
    fixtures = ['test_advertiser', 'test_consumer', 'test_coupon', 
        'test_coupon_views', 'test_subscriber', 'test_offer_views', 
        'test_ecommerce_views', 'test_flyer']
    
    def setUp(self):
        super(TestSessionKeyParser, self).setUp()
        self.factory = RequestFactory()
    
    def build_test_session(self, this_id):
        """ Build an advertiser session to test with. """
        advertiser = Advertiser.objects.get(id=this_id)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        
    def test_get_consumer_key(self):
        """ Test consumer key returns consumer key from session. """
        self.build_test_session(1)
        request = self.factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(
            request.session, ['this_consumer'])
        self.assertEqual(session_dict['this_consumer']['consumer_id'], 1)
        self.assertEqual(session_dict['this_consumer']['site_id'], 1)

    def test_get_product_list_key(self):
        """ Test product_list key returns product_list from session. """
        advertiser = Advertiser.objects.get(id=1)  
        build_advertiser_session(self, advertiser) 
        self.session['add_slot_choice'] = '2'
        self.create_product_list(advertiser.site)
        request = self.factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(
            request.session, ['product_list'])
        self.assertEqual(session_dict['product_list'][0][0], 2)
        self.assertEqual(session_dict['product_list'][0][1],
            Product.objects.get(id=2).base_rate)
    
    def test_get_advertiser_keys(self):
        """ Test advertiser key returns advertiser key from session and location
        key returns location in session.
        """
        self.build_test_session(1)
        request = self.factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(request.session,
            ['this_advertiser', 'this_location', 'advertiser_id'])
        self.assertEqual(session_dict['this_advertiser']['advertiser_id'], 1)
        self.assertEqual(session_dict['advertiser_id'], 1)
        self.assertEqual(len(session_dict['this_advertiser']['business']), 1)
        self.assertEqual(session_dict['this_location']['location_id'], 501)

    def test_business_key(self):
        """ Test business key returns current business in session. """
        self.build_test_session(124)
        request = self.factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(request.session, 
            ['this_advertiser', 'this_business', 'business_id'])
        self.assertEqual(session_dict['this_advertiser']['advertiser_id'], 124)
        self.assertEqual(len(session_dict['this_advertiser']['business']), 2)
        self.assertEqual(session_dict[
            'this_business']['business_name'], 'Test124 Capri Sun')
        self.assertEqual(session_dict['business_id'], 122)

    def test_get_subscriber_key(self):
        """ Test session subscriber key returns subscriber in session. """
        consumer = Consumer.objects.get(id=1100)
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        request = self.factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(request.session, 
            ['this_subscriber', 'this_consumer', 'mobile_phone_number', 
             'carrier_id', 'subscriber_zip_postal'])
        self.assertEqual(session_dict['this_subscriber']['subscriber_id'], 5)
        self.assertEqual(session_dict['this_consumer']['consumer_zip_postal'], 
            '12550')
        self.assertEqual(session_dict['mobile_phone_number'], '8455550002')
        self.assertEqual(session_dict['carrier_id'], 5)
        self.assertEqual(session_dict['subscriber_zip_postal'], '12550')

    def test_get_coupon_offer_keys(self):
        """ Test offer and coupon keys return correct keys from session. """
        self.build_test_session(1)
        request = self.factory.get('/hudson-valley/coupons/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(request.session, ['this_coupon',
            'this_offer', 'coupon_id', 'offer_id'])
        self.assertEqual(len(session_dict['this_offer']['coupon']), 17)
        self.assertEqual(session_dict['this_offer']['headline'], 'More cowbell')
        self.assertEqual(session_dict['this_coupon']['coupon_id'], 421)
        self.assertEqual(session_dict['coupon_id'], 421)
        self.assertEqual(session_dict['offer_id'], 1)
    
    def test_session_update_in_key(self):
        """ Test if parsed session dict key will retain changes to the session
        in request after the session has been parsed. 
        """
        self.build_test_session(1)
        request = self.factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(request.session,
            ['this_business'])
        self.assertEqual(session_dict['this_business']['slogan'], '')
        self.assertEqual(request.session['consumer']
            ['advertiser']['business'][0]['slogan'], '')
        request.session['consumer']['advertiser']['business'][0]['slogan'] = \
            'Never too late'
        self.assertEqual(session_dict['this_business']['slogan'], 
            'Never too late')
    
    def test_key_update_in_session(self):
        """ Test if changes to parsed session dict keys will be shared with
        keys in request.session. 
        """
        self.build_test_session(1)
        request = self.factory.get('/hudson-valley/coupons/', follow=True)
        request.session = self.session
        session_dict = parse_curr_session_keys(request.session, 
            ['this_business'])
        self.assertEqual(session_dict['this_business']['short_business_name'], 
            None)
        self.assertEqual(request.session['consumer']
            ['advertiser']['business'][0]['short_business_name'], None)
        session_dict['this_business']['short_business_name'] = 'TLC'
        self.assertEqual(request.session['consumer']['advertiser']['business']\
            [0]['short_business_name'], 'TLC')
