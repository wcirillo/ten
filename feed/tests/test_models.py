""" Test for the coupon app models. """

from django.test import TestCase

from coupon.models import Coupon
from advertiser.models import Advertiser
from feed.models import FeedProvider, FeedCoupon, FeedRelationship

class TestModels(TestCase):
    """ Test case for selecting coupons using a custom manager. """
    fixtures = ['test_advertiser', 'test_coupon']
    
    def test_feed_models(self):
        """ Assert feed provider, feed coupon, feed relationship added. """
        self.assertEqual(FeedProvider.objects.all().count(), 0)
        advertiser = Advertiser.objects.get(id=113)
        feed_provider = FeedProvider.objects.create(
            name="test feed provider name", advertiser=advertiser)
        self.assertEqual(feed_provider.advertiser, advertiser)
        # test FeedCoupon, needs feed provider
        self.assertEqual(FeedCoupon.objects.all().count(), 0)
        feed_coupon = FeedCoupon.objects.create(feed_provider=feed_provider, 
            business_name="test business name")
        self.assertEqual(feed_coupon.feed_provider, feed_provider)
        # test FeedRelationship, needs feed provider, feed coupon, coupon
        coupon = Coupon.objects.get(id=3)
        self.assertEqual(FeedRelationship.objects.all().count(), 0)
        FeedRelationship.objects.create(feed_provider=feed_provider, 
            feed_coupon=feed_coupon, coupon=coupon)
        self.assertEqual(FeedRelationship.objects.all().count(), 1)
