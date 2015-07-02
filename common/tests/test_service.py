""" Test for the common app service functions. """
import datetime

from django.test.client import RequestFactory

from consumer.models import Consumer
from common.session import (create_consumer_in_session,
    create_subscriber_in_session)
from common.service.common_service import get_preferred_zip, get_home_data
from common.test_utils import EnhancedTestCase
from coupon.models import Coupon
from coupon.factories.slot_factory import SLOT_FACTORY
from market.models import Site
from subscriber.models import Subscriber


class TestService(EnhancedTestCase):
    """ Test case for common service functions. """
    
    fixtures = ['test_consumer', 'test_subscriber', 'test_geolocation']
    
    def test_preferred_zip_consumer(self):
        """ Assert that we pull the zip from the consumer in session when they
        share a common site. 
        """
        factory = RequestFactory()
        consumer = Consumer.objects.get(id=115)
        self.assertEqual(consumer.consumer_zip_postal, '12589')
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)       
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        site = Site.objects.get(id=2)
        preferred_zip = get_preferred_zip(request, site)
        self.assertEqual(preferred_zip, '12589')
        
    def test_preferred_zip_subscriber(self):
        """ Assert that we pull the zip from the subscriber in session when the
        sites are the same. 
        """
        factory = RequestFactory()
        subscriber = Subscriber.objects.get(id=4)
        self.assertEqual(subscriber.subscriber_zip_postal, '12543')
        create_subscriber_in_session(self, subscriber)
        self.assemble_session(self.session)       
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        site = Site.objects.get(id=2)
        preferred_zip = get_preferred_zip(request, site)
        self.assertEqual(preferred_zip, '12543')
    
    def test_preferred_zip_site_param(self):
        """ Assert that we pull the zip from the site passed into the session
        when no session.
        """
        factory = RequestFactory()      
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        site = Site.objects.get(id=3)
        request.META['site_id'] = 4
        preferred_zip = get_preferred_zip(request, site)
        self.assertEqual(preferred_zip, '27604')
    
    def test_preferred_zip_defaulted(self):
        """ Assert that we pull the zip from the site passed into the session.
        """
        factory = RequestFactory()      
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        request.META['site_id'] = 2
        preferred_zip = get_preferred_zip(request)
        self.assertEqual(preferred_zip, '12601')
    
    def test_preferred_zip_precedence(self):
        """  Assert that we pull the zip from the site when we have a consumer
        and they do not share a common site.
        """
        subscriber = Subscriber.objects.get(id=4)
        create_subscriber_in_session(self, subscriber)
        factory = RequestFactory()
        self.assemble_session(self.session)  
        request = factory.get('/hudson-valley/', follow=True)  
        request.session = self.session
        site = Site.objects.get(id=3)
        preferred_zip = get_preferred_zip(request, site)
        self.assertEqual(preferred_zip, '27604')


class TestGetHomeData(EnhancedTestCase):
    """ Test case for get_home_data. """
    fixtures = ['test_advertiser', 'test_coupon_views', 'test_coupon']
    
    def test_national_time_frame(self):
        """ Assert that if a National coupon also has a current time frame, that
        get_home_data uses a deduped list of sorted coupons.
        """
        factory = RequestFactory()
        request = factory.get('/hudson-valley/')
        request.META['site_id'] = 2
        coupon = Coupon.objects.get(id=6) # A National coupon.
        coupon.expiration_date = datetime.date.today() + datetime.timedelta(3)
        coupon.offer.business.advertiser.site.id = 2
        coupon.save()
        SLOT_FACTORY.create_slot(coupon=coupon)
        try:
            test_data = get_home_data(request)
        except AssertionError as e:
            self.fail(e)
        # Assert this coupon appears exactly once in this list of coupons.
        self.assertEqual(test_data['all_coupons'].count(coupon), 1)