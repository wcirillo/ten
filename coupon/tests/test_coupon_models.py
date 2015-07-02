""" Test for the coupon app models. """
import logging

from django.core.exceptions import ValidationError
from django.test import TestCase

from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.models import Coupon, CouponCode, CouponAction
from coupon.service.coupon_code_service import create_coupon_code
from coupon.factories.slot_factory import SLOT_FACTORY

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestCurrentCouponManager(TestCase):
    """ Test case for selecting coupons using a custom manager. """
    urls = 'urls_local.urls_2'
        
    def test_get_current_coupons(self):
        """ Assert coupon in slot is selected. """
        SLOT_FACTORY.create_slot()
        # If *any* tests have loaded fixtures with current coupons, this count
        # will be higher than 1.
        initial_count = Coupon.current_coupons.count()
        self.assertTrue(initial_count > 0)
        SLOT_FACTORY.create_slot()
        self.assertEqual(Coupon.current_coupons.count(), initial_count + 1)


class TestCouponModels(EnhancedTestCase):
    """ Tests for coupon models of coupon app. """

    def test_increment_decr_used_count(self):
        """ Assert used_count of CouponCode is incremented and decremented. """
        coupon = COUPON_FACTORY.create_coupon()
        coupon_code = create_coupon_code(coupon)
        self.assertEqual(
            CouponCode.objects.get(id=coupon_code.id).used_count, 0)
        coupon_code.increment_used_count()
        self.assertEqual(
            CouponCode.objects.get(id=coupon_code.id).used_count, 1)
        coupon_code.increment_used_count()
        self.assertEqual(
            CouponCode.objects.get(id=coupon_code.id).used_count, 2)
        coupon_code.decrement_used_count()
        self.assertEqual(
            CouponCode.objects.get(id=coupon_code.id).used_count, 1)
        coupon_code.decrement_used_count()
        self.assertEqual(
            CouponCode.objects.get(id=coupon_code.id).used_count, 0)

    def test_del_coupon_code(self):
        """ Assert delete conditions of CouponCode. """
        coupon = COUPON_FACTORY.create_coupon()
        coupon_code = create_coupon_code(coupon)
        coupon_code.increment_used_count()
        try:
            coupon_code.delete()
            self.fail('CouponCode with used_count > 0 was deleted!')
        except ValidationError:
            pass
        coupon_code.decrement_used_count()
        coupon_code = CouponCode.objects.get(id=coupon_code.id)
        LOG.debug('used_count: %s' % coupon_code.used_count)
        try:
            coupon_code.delete()
        except ValidationError:
            self.fail('CouponCode with used_count = 0 was not deleted!')
            
    def test_coupon_action_increment(self):
        """ Assert coupon action count is incremented. """
        coupon = COUPON_FACTORY.create_coupon()
        coupon_action = CouponAction.objects.create(coupon=coupon, action_id=1)
        coupon_action = CouponAction.objects.get(id=coupon_action.id)
        self.assertEqual(coupon_action.count, 0)
        coupon_action.increment_count()
        coupon_action = CouponAction.objects.get(coupon=coupon, action__id=1)
        self.assertEqual(coupon_action.count, 1)
        
    def test_get_coords_list_valid(self):
        """ Assert the get_location_coords_list method returns all location
        coords for a given coupon.
        """
        coupon = COUPON_FACTORY.create_coupon()
        coords_list = coupon.get_location_coords_list()
        self.assertAlmostEqual(int(float(coords_list[0][0])), -73)
        self.assertAlmostEqual(int(float(coords_list[0][1])), 41)
        
    def test_get_loc_list_none(self):
        """ Assert get_location_list when there are no locations returns empty
        list.
        """
        coupon = COUPON_FACTORY.create_coupon()
        coupon.location.all().delete()
        display_location, display_city = coupon.get_location_string()
        self.assertEqual(display_location, [])
        self.assertEqual(display_city, None)
        
    def test_get_loc_list_one(self):
        """ Assert get_location_list when there is one location. """
        coupon = COUPON_FACTORY.create_coupon()
        location = coupon.location.all()[0]
        display_location, display_city = coupon.get_location_string()
        string = '%s, %s' % (location.location_city,
            location.location_state_province)
        self.assertEqual(display_location, [string])
        self.assertEqual(display_city, string)
    
    def test_get_loc_list_two(self):
        """ Assert get_location_list when there are less then or equal to three
        locations returns all locations concatenated with "&".
        """
        coupon = COUPON_FACTORY.create_coupon_many_locations(
            business_location_count=2)
        COUPON_FACTORY.normalize_coupon_locations(coupon)
        [location_0, location_1] = coupon.location.all()
        string_0 = '%s, %s' % (location_0.location_city,
            location_0.location_state_province)
        string_1 = '%s, %s' % (location_1.location_city,
            location_1.location_state_province)
        display_location, display_city = coupon.get_location_string()
        # Order of locations is not determined:
        self.assertTrue(display_location == [location_0.location_city, string_1]
            or display_location == [location_1.location_city, string_0])
        self.assertEqual(display_city, string_0)
    
    def test_get_loc_list_many(self):
        """ Assert get_location_list when there are 8 locations returns all
        locations concatenated with a comma.
        """
        coupon = COUPON_FACTORY.create_coupon_many_locations(
            business_location_count=8)
        COUPON_FACTORY.normalize_coupon_locations(coupon)
        locations = coupon.location.all()
        display_location, display_city = coupon.get_location_string()
        LOG.debug('display_location: %s' % display_location)
        LOG.debug('display_city: %s' % display_city)
        LOG.debug('locations: %s' %
            [(loc.location_city, loc.location_state_province)
            for loc in locations])
        self.assertEqual(display_location, [
            locations[0].location_city,
            locations[1].location_city,
            locations[2].location_city,
            locations[3].location_city,
            locations[4].location_city,
            locations[5].location_city,
            locations[6].location_city,
            '%s, %s' % (locations[7].location_city,
                locations[7].location_state_province)])
        self.assertEqual(display_city, '%s, %s' % (
            locations[0].location_city, locations[0].location_state_province))
