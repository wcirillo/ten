""" Test advertiser business location services. """
from advertiser.business.location.service import (get_locations_for_coupons,
    get_location_coords_list)
from coupon.models import Coupon
from geolocation.tests.geolocation_test_case import GeoTestCase


class TestLocationServices(GeoTestCase):
    """ Test case for advertiser biz location services. """
    fixtures = ['test_advertiser', 'test_coupon_views']
        
    def test_get_loc_for_coupons(self):
        """ Assert locations returned for multiple coupons. """
        all_coupons = Coupon.objects.filter(id__in=[110, 111])
        num_locations = all_coupons[0].location.count() + \
            all_coupons[1].location.count()
        location_list = get_locations_for_coupons(all_coupons)
        self.assertEquals(len(location_list), num_locations)

    def test_get_loc_no_coupons(self):
        """ Assert locations returned for no coupons. """
        null_coupons = Coupon.objects.filter(id__in=[0])
        null_list = get_locations_for_coupons(null_coupons)
        self.assertEqual(len(null_list), 0)
        self.assertEqual(type(null_list).__name__, 'list')
        
    def test_get_loc_coords_dict(self):
        """ Test method get_locations_for_coupons. """
        # Test result when no coordinates exist (will get them now):
        all_coupons = Coupon.objects.filter(id__in=[119])
        location_list = get_locations_for_coupons(all_coupons)
        location_coords = get_location_coords_list(location_list)
        self.assertEqual(len(location_coords), 2)
        # Test result when coordinates do exist:
        all_coupons = Coupon.objects.filter(id__in=[117])
        location_list = get_locations_for_coupons(all_coupons)      
        location_coords = get_location_coords_list(location_list)
        self.assertEqual(len(location_coords), 1)
