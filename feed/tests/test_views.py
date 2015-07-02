""" Tests for feed views """

import logging
import os
import xml.dom.minidom

from django.core.urlresolvers import reverse

from advertiser.factories.location_factory import COUPON_LOCATION_FACTORY
from common.test_utils import EnhancedTestCase
from coupon.factories.slot_factory import SLOT_FACTORY
from feed.tasks.coupon_feed_tasks import ShoogerCouponFeed, GenericCouponFeed

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestViews(EnhancedTestCase):
    """ Tests for feed views """
    fixtures = ['test_advertiser', 'test_coupon', 'test_slot', 'test_flyer']
   
    def tearDown(self):
        """ Cleanup files after each test is run. """
        super(TestViews, self).tearDown()
        LOG.debug('Removing files from tests')
        shooger_coupon_feed = ShoogerCouponFeed()
        if os.path.exists(shooger_coupon_feed.file_name):
            os.remove(shooger_coupon_feed.file_name)
   
    def common_asserts(self, response):
        """ Common asserts. """
        LOG.debug(response)
        self.assertEquals(response.status_code, 200)
        self.assertTrue(xml.dom.minidom.parseString(response.content))
        self.assertContains(response, '<promoTitle>')
        self.assertContains(response, '</business>')
        self.assertContains(response, 
            '<url>http://10Coupons.com/hudson-valley/coupon-')
        self.assertContains(response, 
            '10HudsonValleyCoupons.com</promoText>')
   
    def test_show_feed(self):
        """ Assert display of feed xml. """
        response = self.client.get('/feed/shooger.xml', follow=True)
        self.common_asserts(response)
        
    def test_show_cached_feed(self):
        """ Assert display of cached feed xml from file. """
        shooger_coupon_feed = ShoogerCouponFeed()
        response = self.client.get('/feed/shooger.xml', follow=True)
        my_file = open(shooger_coupon_feed.file_name, 'w')
        my_file.write(response.content.replace('businesses', 'cached'))
        my_file.close()
        response = self.client.get('/feed/shooger.xml', follow=True)
        self.common_asserts(response)
        self.assertContains(response, '<cached ')

    def test_show_feed_unicode_char(self):
        """ Assert display of feed with unicode character. """
        shooger_coupon_feed = ShoogerCouponFeed()
        context = shooger_coupon_feed.generate_context()
        offer = context['coupons'][0].offer
        offer.headline = 'Unicode string: ' + u'\u2019'
        offer.save()
        response = self.client.get('/feed/shooger.xml', follow=True)
        self.common_asserts(response)


class TestGenericFeedView(EnhancedTestCase):
    """ Test case for show_generic_coupon_feed view. """

    def setUp(self):
        """ Prep data for each test. """
        super(TestGenericFeedView, self).setUp()
        self.slots = SLOT_FACTORY.create_slots(2)
        self.coupon_1 = self.slots[0].slot_time_frames.all()[0].coupon
        self.coupon_1.is_redeemed_by_sms = True
        self.coupon_1.save()
        COUPON_LOCATION_FACTORY.create_coupon_location(coupon=self.coupon_1)
        self.coupon_2 = self.slots[1].slot_time_frames.all()[0].coupon
        self.coupon_2.is_redeemed_by_sms = True
        self.coupon_2.save()
        COUPON_LOCATION_FACTORY.create_coupon_locations(coupon=self.coupon_2,
            create_all=True, coupon_location_count=2)
        self.generic_coupon_feed = GenericCouponFeed()

    def tearDown(self):
        """ Cleanup files after each test is run. """
        super(TestGenericFeedView, self).tearDown()
        LOG.debug('Removing files from tests')
        if os.path.exists(self.generic_coupon_feed.file_name):
            os.remove(self.generic_coupon_feed.file_name)

    def test_show_feed(self):
        """ Assert display of feed xml. """
        response = self.client.get(reverse('show-generic-coupon-feed'),
            follow=True)
        # Depending on previous tests, this might be served from cache:
        self.assertTrue(xml.dom.minidom.parseString(response.content))
        LOG.debug(response)
        self.assertContains(response, '<business><name>')

    def test_feed_data(self):
        """ Assert contents of generic feed is correct. """
        data = self.generic_coupon_feed.get_rendered_data()
        LOG.debug(data)
        self.assertTrue('<name>%s</name>' %
            self.coupon_1.offer.business.business_name in data)
        self.assertTrue('<headline>%s</headline>' %
            self.coupon_1.offer.headline in data)
        self.assertTrue('<qualifier>%s</qualifier>' %
            self.coupon_1.offer.qualifier in data)
        # Factory produces static coordinates.
        self.assertEqual(
            data.count('<latitude>41.1380690000000000</latitude>'), 2)
        self.assertEqual(
            data.count('<longitude>-73.7847090000000000</longitude>'), 2)
        self.assertTrue('<name>%s</name>' %
            self.coupon_2.offer.business.business_name in data)
        self.assertTrue('<headline>%s</headline>' %
            self.coupon_1.offer.headline in data)
        self.assertTrue('<qualifier>%s</qualifier>' %
            self.coupon_1.offer.qualifier in data)
