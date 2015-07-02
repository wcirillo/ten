""" Tests for coupon app service functions. """
#pylint: disable=C0103
import datetime
import logging

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from advertiser.models import Advertiser
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.service.coupon_performance import CouponPerformance
from coupon.service.twitter_service import TWITTER_SERVICE
from coupon.service.coupons_service import ALL_COUPONS, SORT_COUPONS
from coupon.service.expiration_date_service import default_expiration_date
from coupon.service.flyer_create_service import (append_coupon_to_flyer)
from coupon.service.flyer_service import get_coupons_scheduled_flyers
from coupon.models import Coupon, CouponAction, CouponType, Flyer, RankDateTime
from ecommerce.factories.order_factory import ORDER_FACTORY
from ecommerce.models import OrderItem, Product
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRepAdvertiser
from market.models import Site, TwitterAccount

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestService(EnhancedTestCase):
    """ Test case for service functions of coupon app. """

    fixtures = ['test_twitter_account']

    def test_build_coupon_locations(self):
        """ Assert coupon locations are read, parsed and formatted correctly.
        """
        coupon_1 = COUPON_FACTORY.create_coupon()
        coupon_1.location.clear()
        coupon_2 = COUPON_FACTORY.create_coupon_many_locations(
            business_location_count=2, coupon_location_count=2)
        location = ALL_COUPONS.build_coupon_location_list(
            [coupon_1.id, coupon_2.id])
        # Assert returned dict has one key; first coupon has no locations.
        LOG.debug('location: %s' % location)
        self.assertEquals(len(location), 1)
        # Check string formatting of locations.
        locations = coupon_2.location.all()
        # First city becomes proper cased.
        # It is not determined which order the cities will be returned in:
        try:
            self.assertEquals(location[coupon_2.id],
                [locations[0].location_city.title(),
                    locations[1].location_city])
        except AssertionError:
            self.assertEquals(location[coupon_2.id],
                [locations[1].location_city.title(),
                    locations[0].location_city])

    def test_blank_city_ignored(self):
        """ Assert for a coupon with two locations, one with a blank city."""
        coupon = COUPON_FACTORY.create_coupon_many_locations(
            business_location_count=2, coupon_location_count=2)
        (location_1, location_2) = coupon.location.all()
        location_1.location_city = ''
        location_1.save()
        location = ALL_COUPONS.build_coupon_location_list([coupon.id])
        self.assertEquals(len(location), 1)
        # City becomes proper cased.
        self.assertEquals(location[coupon.id],
            [location_2.location_city.title()])

    def test_coupon_location_w_dupes(self):
        """ Assert the build_coupon_locations method for duplicate cities. """
        coupon = COUPON_FACTORY.create_coupon_many_locations(
            business_location_count=3, coupon_location_count=3)
        locations = list(coupon.location.all())
        locations[1].location_city = locations[0].location_city
        locations[1].save()
        locations = ALL_COUPONS.build_coupon_location_list([coupon.id])
        for key in locations:
            temp = set()
            for x in locations[key]:
                if x in temp:
                    self.fail("Exclude duplicates in coupon location list.")
                else:
                    temp.add(x)
    
    def test_build_coup_loc_confirm(self):
        """ Confirm that locations pulled for coupon belong to THIS coupon. """
        coupons = COUPON_FACTORY.create_coupons_many_locations(create_count=3,
            business_location_count=3, coupon_location_count=3)
        locations = ALL_COUPONS.build_coupon_location_list(
            [coupon.id for coupon in coupons])
        test_list = []
        for loc in coupons[0].location.all():
            test_list.append(loc.location_city.lower())
        self.assertEqual(len(test_list), len(locations[coupons[0].id]))
        for loc in locations[coupons[0].id]:
            if loc.lower() not in test_list:
                self.fail('Invalid location in build_coupon_location result.')
        
    def test_build_tweet_message(self):
        """ Assert that Tweet message is built for this coupon """
        coupon = COUPON_FACTORY.create_coupon()
        message = TWITTER_SERVICE.build_tweet_message(coupon)
        LOG.debug(message)
        twitter_account = TwitterAccount.objects.get(
            site=coupon.offer.business.advertiser.site)
        self.assertTrue(twitter_account.twitter_name in message)
        self.assertTrue(coupon.offer.headline in message)
        self.assertTrue(coupon.offer.business.short_business_name in message)

    def test_get_media_partner_coupons(self):
        """ Assert that media partners coupons are returned """
        coupon = COUPON_FACTORY.create_coupon()
        coupon.coupon_type_id = 5 # MediaPartner
        coupon.expiration_date = default_expiration_date()
        coupon.save()
        coupons = ALL_COUPONS.get_media_partner_coupons(
            coupon.offer.business.advertiser.site)
        self.assertTrue(coupons.count(), 1)
    

class TestGetScheduledFlyer(TestCase):
    """ Test the coupon service to get a list of scheduled flyer dates. """
    @classmethod
    def setUpClass(cls):
        """ Set up flyers to be sent for a coupon (past and present) for
        testing.
        """
        super(TestGetScheduledFlyer, cls).setUpClass()
        site = Site.objects.get(id=2)
        flyer = Flyer.objects.create(site=site, send_status=2,
            send_date = datetime.datetime.now().date() - datetime.timedelta(7))
        cls.coupon = COUPON_FACTORY.create_coupon()
        slot = SLOT_FACTORY.create_slot(coupon=cls.coupon)
        append_coupon_to_flyer(flyer, cls.coupon)
        another_flyer = Flyer.objects.create(site=site)
        append_coupon_to_flyer(another_flyer, cls.coupon)
        future_flyer = Flyer.objects.create(site=site,
            send_date = datetime.date.today() + datetime.timedelta(7))
        append_coupon_to_flyer(future_flyer, cls.coupon)
        product = Product.objects.get(id=1)
        order = ORDER_FACTORY.create_order()
        counter = 0
        while counter < 1:
            OrderItem.objects.create(item_id=slot.id, product=product, 
                content_type=ContentType.objects.get(app_label='coupon', 
                    model='slot'), 
                site=slot.site, order=order, business=cls.coupon.offer.business,
                end_datetime=datetime.datetime.now() + datetime.timedelta(20))
            counter += 1

    def test_get_scheduled_flyers(self):
        """ Test the dates returned are correct. """
        flyer_dates1 = get_coupons_scheduled_flyers(self.coupon,
                ContentType.objects.get(app_label='coupon', model='slot'))
        self.assertEqual(2, len(flyer_dates1))
        # Only retrieve one with 'pack' parameter:
        flyer_dates2 = get_coupons_scheduled_flyers(self.coupon,
                ContentType.objects.get(app_label='coupon', model='slot'),
                pack=1)
        self.assertEqual(1, len(flyer_dates2))
        self.assertEqual(flyer_dates2[0], flyer_dates1[0])


class TestSortCoupons(TestCase):
    """ Test case for coupon service class SortCoupons. """

    def setUp(self):
        super(TestSortCoupons, self).setUp()
        slots = SLOT_FACTORY.create_slots(create_count=3)
        coupons = []
        create_datetime = datetime.datetime(2011, 1, 1)
        for slot in slots:
            coupon = slot.slot_time_frames.all()[0].coupon
            coupon.coupon_create_datetime = create_datetime
            coupon.save()
            coupons.append(coupon)
            create_datetime += datetime.timedelta(days=30)
        self.coupon_1, self.coupon_2, self.coupon_3 = coupons
        self.coupon_ids = [coupon.id for coupon in coupons]
        self.coupons = Coupon.objects.filter(id__in=self.coupon_ids)
        for coupon in self.coupons:
            rank_date_time, created = RankDateTime.objects.get_or_create(
                coupon=coupon)
            if not created:
                rank_date_time.save()

    def test_num_queries(self):
        """  Assert coupons are sorted by criteria including how new it is,
        how many times it has been printed, and how many times it has been
        shared.
        """
        self.assertNumQueries(4, SORT_COUPONS.sorted_coupons, self.coupon_ids)

    def test_sorted_coupons(self):
        """  Assert newer coupons are sorted first. """
        sorted_coupon_ids = SORT_COUPONS.sorted_coupons(self.coupon_ids)[0]
        self.assertEqual(len(sorted_coupon_ids), len(self.coupons))
        self.assertNotEqual(self.coupon_ids, sorted_coupon_ids)
        self.assertTrue(sorted_coupon_ids.index(self.coupon_ids[2]) <
            sorted_coupon_ids.index(self.coupon_ids[1]) <
            sorted_coupon_ids.index(self.coupon_ids[0]))

    def test_prints_preferred(self):
        """ Assert a coupon printed x times is considered 3x days "newer". """
        CouponAction.objects.create(coupon_id=self.coupon_ids[0], action_id=3,
            count=11)
        rank_datetime = RankDateTime.objects.get(coupon__id=self.coupon_ids[0])
        rank_datetime.save()
        sorted_coupon_ids = SORT_COUPONS.sorted_coupons(self.coupon_ids)[0]
        LOG.debug('sorted for print: %s' % sorted_coupon_ids)
        self.assertTrue(sorted_coupon_ids.index(self.coupon_ids[2]) <
            sorted_coupon_ids.index(self.coupon_ids[0]) <
            sorted_coupon_ids.index(self.coupon_ids[1]))

    def test_shared_preferred(self):
        """ Assert a coupon shared y times is considered 15x days "newer" """
        CouponAction.objects.create(coupon_id=self.coupon_ids[0], action_id=7,
            count=5)
        rank_datetime = RankDateTime.objects.get(coupon__id=self.coupon_ids[0])
        rank_datetime.save()
        sorted_coupon_ids = SORT_COUPONS.sorted_coupons(self.coupon_ids)[0]
        LOG.debug('sorted for shares: %s' % sorted_coupon_ids)
        self.assertTrue(sorted_coupon_ids.index(self.coupon_ids[0]) <
            sorted_coupon_ids.index(self.coupon_ids[2]) <
            sorted_coupon_ids.index(self.coupon_ids[1]))


class TestCouponPerformance(TestCase):
    """ Test case for coupon service class CouponPerformance. This class's
    methods retrieve and display all the coupons related to this user."""

    @classmethod
    def setUpClass(cls):
        """ Set up coupons to be retrieved for the following tests. """
        super(TestCouponPerformance, cls).setUpClass()
        coupon = COUPON_FACTORY.create_coupon()
        expiring_coupon = COUPON_FACTORY.create_coupon()
        expiring_coupon.expiration_date = (
            datetime.date.today() + datetime.timedelta(1))
        expiring_coupon.save()
        coupon_w_locations = COUPON_FACTORY.create_coupons_many_locations()[0]
        second_coupon_this_biz = COUPON_FACTORY.create_coupon()
        offer = second_coupon_this_biz.offer
        offer.business = expiring_coupon.offer.business
        offer.save()
        SLOT_FACTORY.create_slot(coupon=coupon)
        SLOT_FACTORY.create_slot(coupon=expiring_coupon)
        SLOT_FACTORY.create_slot(coupon=coupon_w_locations)
        SLOT_FACTORY.create_slot(coupon=second_coupon_this_biz)
        
        # Move coupon to share advertiser with  second_coupon_this_biz.
        business = coupon.offer.business
        business.advertiser = second_coupon_this_biz.offer.business.advertiser
        business.save()

        # Relate all of these businesses except one to these coupons advertisers.
        cls.ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create(ad_rep=cls.ad_rep, 
            advertiser=expiring_coupon.offer.business.advertiser)
        AdRepAdvertiser.objects.create(ad_rep=cls.ad_rep, 
            advertiser=coupon_w_locations.offer.business.advertiser)
        # Set vars for testing:
        cls.advertiser_not_related = coupon.offer.business.advertiser
        cls.expiring_coupon = expiring_coupon
        cls.coupon_w_locations = coupon_w_locations
        cls.business_w_2_coupons = second_coupon_this_biz

    def test_exp_date_highlight(self):
        """ Assert that coupons expiring in the next 5 days are flagged to 
        highlight. 
        """
        coupon_performance = CouponPerformance(
            size_limit=20, render_preview=False)
        coupon_list = coupon_performance.get_coupon_list(
            business_id=self.expiring_coupon.offer.business.id)
        # Last element of list is coupon_count.
        self.assertEqual(len(coupon_list), 3)
        # Get coupon index that is expiring:
        if coupon_list[0]['expiration_date'] < coupon_list[1]['expiration_date']:
            index = 0
        else:
            index = 1
        self.assertEqual(coupon_list[index]['expiring_soon'], True)
        self.assertEqual(coupon_list[2]['coupon_count'], 0)

    def test_size_limit(self):
        """ Assert that the max number of coupons retrieved respects the size
        limit submitted.
        """
        advertiser_ids = Advertiser.objects.filter(
        ad_rep_advertiser__ad_rep=self.ad_rep).values_list('id', flat=True)
        coupon_performance = CouponPerformance(
            size_limit=2, render_preview=False)
        coupon_list = coupon_performance.get_coupon_list(
            advertiser_ids=advertiser_ids)
        # Last element of list is coupon_count.
        self.assertEqual(3, len(coupon_list)) # (size_limit + 1).

    def test_locations(self):
        """ Assert that locations are only appended to the coupon list dict
        when the render_preview optional parameter is supplied True. 
        """
        coupon_performance = CouponPerformance(
            size_limit=5, render_preview=True)
        coupon_list = coupon_performance.get_coupon_list(
            business_id=self.coupon_w_locations.offer.business.id)
        self.assertEqual(2, len(coupon_list))
        self.assertTrue(coupon_list[0].get('location'))
        self.assertTrue(coupon_list[0]['location'][0].get('location_city'))
        self.assertTrue(
            coupon_list[0]['location'][0].get('location_state_province'))
        self.assertTrue(
            coupon_list[0]['location'][0].get('location_zip_postal'))
        self.assertTrue(coupon_list[0]['location'][0].get('location_exchange'))
        self.assertTrue(coupon_list[0]['location'][0].get('location_area_code'))
        self.assertTrue(coupon_list[0]['location'][0].get('location_number'))
        self.assertTrue(coupon_list[0]['location'][0].get('location_address1'))
        self.assertTrue(coupon_list[0]['location'][0].get('location_address2'))
    
    def test_coupons_by_business(self):
        """ Assert coupons in list all belong to the business_id passed in. """
        coupon_performance = CouponPerformance(
            size_limit=20, render_preview=False)
        coupon_list = coupon_performance.get_coupon_list(
            business_id=self.business_w_2_coupons.offer.business.id)
        self.assertEqual(3, len(coupon_list))
        business_name = coupon_list[0]['business_name']
        for coupon in coupon_list:
            if coupon.get('coupon_count', 1) != 0:
                self.assertEqual(business_name, coupon['business_name'])
                self.assertFalse(coupon.get('location', False))
    
    def test_coupons_by_advertisers(self):
        """ Assert that coupons retrieved belong to one of the advertisers
        passed in. """
        coupon_performance = CouponPerformance(size_limit=5)
        coupon_list = coupon_performance.get_coupon_list(
            advertiser_ids=
            [self.business_w_2_coupons.offer.business.advertiser.id])
        self.assertEqual(len(coupon_list), 4)
        advertiser_id = Advertiser.objects.get(id=
            self.business_w_2_coupons.offer.business.advertiser.id).id
        
        for coupon in coupon_list:
            if coupon.get('coupon_count', 1) != 0:
                coupon = Coupon.objects.get(id=coupon['coupon_id'])
                self.assertEqual(advertiser_id, 
                    coupon.offer.business.advertiser.id)
    
    def test_coupon_exclusion(self):
        """ Assert that coupons already retrieved will not be pulled again. """
        coupon_performance = CouponPerformance(size_limit=5)
        first_list = coupon_performance.get_coupon_list(
            advertiser_ids=
            [self.business_w_2_coupons.offer.business.advertiser.id])
        self.assertEqual(len(first_list), 4)
        exclusion_list = []
        for coupon in first_list:
            if coupon.get('coupon_count', 1) != 0:
                exclusion_list.append(coupon['coupon_id'])
        # Final coupon list should be empty.
        coupon_list = coupon_performance.get_coupon_list(
            advertiser_ids=
            [self.business_w_2_coupons.offer.business.advertiser.id],
            coupon_list=exclusion_list)
        self.assertEqual(len(coupon_list), 1)
        self.assertEqual(coupon_list[0]['coupon_count'], 0)
        
    def test_unpublished_exclusion(self):
        """ Assert that unpublished exclusion is invoked, we do not pull coupons
        that have not been published. """
        coupon = self.business_w_2_coupons
        coupon.coupon_type = CouponType.objects.get(id=1)
        coupon.save()
        coupon_performance = CouponPerformance(size_limit=5, 
            exclude_unpublished=True)
        coupon_list = coupon_performance.get_coupon_list(
            advertiser_ids=
            [self.business_w_2_coupons.offer.business.advertiser.id])
        self.assertEqual(len(coupon_list), 3)
        for coupon_ in coupon_list:
            self.assertTrue( coupon_.get('coupon_id', 0) != coupon.id)
