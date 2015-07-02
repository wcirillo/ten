""" Module to store utilities used by Hudson or other testing methods. """
#pylint: disable=C0103
from BeautifulSoup import BeautifulSoup
import logging

from django.conf import settings
from django.contrib.sessions.backends.base import SessionBase
from django.core.mail.backends.locmem import EmailBackend
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.importlib import import_module

from advertiser.models import Advertiser, Business
from common.service.payload_signing import PAYLOAD_SIGNING
from common.session import build_advertiser_session
from coupon.models import Coupon, CouponType, Offer
from ecommerce.service.locking_service import (get_locked_data,
    get_incremented_pricing)
from ecommerce.service.product_list import create_products_list
from email_gateway.service.email_service import process_message

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class EnhancedEmailBackend(EmailBackend):
    """ Custom class to handle emails and apply our custom logic to control
    TO and CC header keys. This class is derived from:
        django.core.mail.backends.locmem.EmailBackend
    """
    def send_messages(self, messages):
        """ Custom message method to modify the "TO" and "CC" headers in our
        emails in tests. 
        """
        for index, msg in enumerate(messages):
            messages[index] = process_message(msg)
        return EmailBackend.send_messages(self, messages)


class EnhancedTestCase(TestCase):
    """ Provide base class methods for test classes, with some customization
    for ten project. 
    
    If you use the django test client directly, and then do a reverse like
    client.get(reverse('all-coupons')), the url of the request is
    http://testerver/home/ and market.middleware will 301 redirect that to
    http://10coupons.com/home/ and the test client cannot follow to live site.
    
    This class fixes that behavior by specifying HTTP_HOST from settings.
    """

    @classmethod
    def setUpClass(cls):
        """ These settings are global for all tests we run when inheriting 
        the EnhancedTestCase class.
        """
        super(EnhancedTestCase, cls).setUpClass()
        settings.ENVIRONMENT['is_test'] = True
        cls.old_email_gateway = settings.EMAIL_BACKEND
        settings.EMAIL_BACKEND = 'common.test_utils.EnhancedEmailBackend'
        cls.old_send_sale_notifications = settings.SEND_SALE_NOTIFICATIONS
        settings.SEND_SALE_NOTIFICATIONS = True
        settings.LIVE_EMAIL_DOMAINS = []

    @classmethod
    def tearDownClass(cls):
        """ Rollback some of the seUpClass settings after the class is finished 
        running all test methods inside of it.
        """
        super(EnhancedTestCase, cls).tearDownClass()
        settings.EMAIL_BACKEND = cls.old_email_gateway
        settings.SEND_SALE_NOTIFICATIONS = cls.old_send_sale_notifications
    
    def setUp(self):
        """ Setup the client for the tests. """
        super(EnhancedTestCase, self).setUp()
        self.client.defaults = {'HTTP_HOST':settings.HTTP_HOST}
        self.session = {"tlc_sandbox_testing" : True}
        
    def tearDown(self):
        """ tearDown method for the EnhancedTestClass """
        super(EnhancedTestCase, self).tearDown()
        self.client = None
    
    def add_ad_rep_to_session(self, ad_rep):
        """ Add a referring ad rep to the session. """
        self.session['ad_rep_id'] = ad_rep.id
        self.session['referring_ad_rep_dict'] = ad_rep
        self.assemble_session(self.session)
    
    def add_session_to_request(self, request, ad_rep=None, site_id=2):
        """ Create session for artificial request (built from RequestFactory()
        and append an ad rep to it.
        """
        request.session = self.client.session
        if ad_rep:
            request.session['ad_rep_id'] = ad_rep.id
            request.session['referring_ad_rep_dict'] = ad_rep
        request.META['site_id'] = site_id
        return request

    def assemble_session(self, dictionary):
        """ Add dictionary to session for testing, makes session available in
        self.session.
        """
        try:
            session_key = self.client.session._session_key
        except AttributeError:
            session_key = None
        engine = import_module(settings.SESSION_ENGINE)
        store = engine.SessionStore(session_key)
        store.save()  # We need to make load() work, or the cookie is worthless.
        self.client.cookies[settings.SESSION_COOKIE_NAME] = store.session_key
        session = self.client.session
        session.update(dictionary)
        session.save()
        
    def login(self, email='ten@example.com', password='password', 
            is_ad_rep=False):
        """ Login method for this user, taken from media_partner.tests. Only use
        this method for testing sign-in. -I have not been able to modify the
        session that is created to test other scenarios.
        """
        post_data = {'email': email, 'password': password}
        if is_ad_rep:
            post_data.update({'ad_rep_sign_in': 1})
        response = self.client.post(reverse('sign-in'), post_data)
        self.assertEqual(response.status_code, 302)
        
    def create_product_list(self, site):
        """ Create the product_list for tests in session so we can use the
        correct assertions based on the dynamic values populated in the
        product_list tuple.
        """
        self.set_locked_data(site)
        session_dict = {'product_list':create_products_list(self, site)}
        self.session.update(session_dict)
        
    def set_locked_data(self, site):
        """ Set locked data in session. """
        locked_consumer_count = get_locked_data(self, site)[2]
        incremented_pricing = get_incremented_pricing(locked_consumer_count)
        self.session.update(incremented_pricing)
        
    def login_build_set_assemble(self, advertiser, is_ad_rep=False):
        """ Login the advertiser, build the session, set locked data, and
        assemble the session.
        """
        self.login(advertiser.email, is_ad_rep=is_ad_rep)
        build_advertiser_session(self, advertiser)
        self.set_locked_data(advertiser.site)
        self.assemble_session(self.session)
        
    def compare_these_objects(self, object_1, object_2, assert_equal=True, 
                              dont_compare_keys_list=None,
                              only_compare_these_keys_list=None):
        """ Assert model_1 and model_2 are either equal or not equal. This
        method will check that all the keys in object_1 match items in
        object_2. So if there are keys in object_2 you don't want to check,
        make sure object_1 gets passed in first. If that isn't possible, pass 
        the key into the dont_compare_keys_list to make sure that key
        doesn't get compared.
        """
        # Turn the db objects into dicts.
        if type(object_1) != type(dict()):
            object_1 = object_1.to_dict()
        if type(object_2) != type(dict()):
            object_2 = object_2.to_dict()
        if only_compare_these_keys_list != None:
            # Rebuild object_1 only with the keys in the 
            # only_compare_these_keys_list.
            temp_object_1 = {}
            for compare_key in only_compare_these_keys_list:
                temp_object_1.update({compare_key:object_1[compare_key]})
            object_1 = temp_object_1
        if dont_compare_keys_list == None:
            dont_compare_keys_list = []
        for key in object_1:
            # Only run this key if it is not in the dont_compare_keys_list.
            if key not in dont_compare_keys_list:
                LOG.debug("key='%s'" % key)
                if assert_equal:
                    self.assertEqual(object_1[key], object_2[key])
                    LOG.debug("%s ('%s'=='%s')" % (
                        key, object_1[key], object_2[key]))
                else:
                    self.assertNotEqual(object_1[key], object_2[key])
                    LOG.debug("%s ('%s'!='%s')" % (
                        key, object_1[key], object_2[key]))
        LOG.debug('-------------------------------')

    @classmethod
    def make_advrt_with_coupon(cls, **kwargs):
        """  Assert request with a valid coupon displays the add slot form. """
        advertiser = Advertiser.objects.create(username=kwargs['email'],
            email=kwargs['email'],
            consumer_zip_postal=kwargs['consumer_zip_postal'],
            site_id=2)
        advertiser.set_password('password')
        advertiser.save()
        business = Business.objects.create(advertiser_id=advertiser.id, 
            business_name=kwargs['business_name'], 
            short_business_name=kwargs['short_business_name'])
        business.save()
        offer = Offer.objects.create(business=business, 
            headline=kwargs['headline'])
        offer.save()
        coupon = Coupon.objects.create(offer=offer, 
            coupon_type=CouponType.objects.get(id=1))
        coupon.save()
        return advertiser
    
    def add_mock_cycle_key(self, request):
        """ Method cycle_key() is missing from session when doing tests with
        request factory. This is a mock function we can set to bypass the error
        that would raise if logging in.
        """
        self.session = SessionBase()
        for key in request.session:
            self.session[key] = request.session[key]
        self.session.cycle_key = lambda: '' # Complacent function.
        return self.session
    
    @staticmethod
    def verify_email_sub_list(email_html_body, email_sub_list_id):
        """ Verify if the email subscription list id is in this email. This 
        looks for link in html part only, not text part. """
        soup = BeautifulSoup(email_html_body)
        for anchor in soup.findAll('a'):
            if '/opt-out-list/' in str(anchor):
                web_url = anchor['href']
                break
        payload = web_url.split('/')[-2]
        payload_dict = PAYLOAD_SIGNING.parse_payload(payload)
        email_subscription_list_id = payload_dict.get('subscription_list')[0]
        LOG.debug('Found list id: %s' % email_subscription_list_id)
        return email_subscription_list_id == email_sub_list_id
             