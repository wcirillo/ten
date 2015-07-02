""" Tests for feed service """

import datetime
import logging


from common.test_utils import EnhancedTestCase
from coupon.models import Coupon
from coupon.service.expiration_date_service import default_expiration_date
from feed.models import FeedProvider, FeedRelationship
from feed.service import manage_feed_coupons, split_string, get_web_page

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

class TestService(EnhancedTestCase):
    """ Test feed service """
    fixtures = ['test_advertiser', 'test_feed', 'test_coupon']
       
    def test_manage_coupons(self):
        """ Test for manage feed coupons"""
        self.assertEqual(FeedRelationship.objects.all().count(), 1)
        #create_coupons(FeedProvider.objects.get(id=1))
        coupon = Coupon.objects.get(id=301)
        coupon.expiration_date = default_expiration_date()
        coupon.save()
        feed_relationship = FeedRelationship.objects.get(coupon=coupon)
        self.assertTrue(
            feed_relationship.coupon.expiration_date > datetime.date.today())
        manage_feed_coupons(FeedProvider.objects.get(id=1))
        self.assertEqual(FeedRelationship.objects.all().count(), 2)
        feed_relationship = FeedRelationship.objects.get(coupon=coupon)
        self.assertTrue(
            feed_relationship.coupon.expiration_date < datetime.date.today())
        
    def test_split_string(self):
        """ Test for split string """
        mytext = '2011 Senior PGA Championship presented by'
        string1, string2 = split_string(mytext, 25, 25)
        self.assertEqual(string1, '2011 Senior PGA')
        self.assertEqual(string2, 'Championship presented')
    
    def test_feed_web_cache(self):
        """ Test for get_web_page """
        web_page = get_web_page('http://bmlnm.incentrev.com')
        self.assertTrue(web_page != None)