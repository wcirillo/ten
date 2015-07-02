""" Test advertiser models. """
from django.db import IntegrityError
from django.test import TestCase

from advertiser.factories.business_factory import BUSINESS_FACTORY
from advertiser.models import BusinessProfileDescription, Location
from coupon.factories.coupon_factory import COUPON_FACTORY


class TestLocationModel(TestCase):
    """ Tests for advertiser model of advertiser app. """

    def test_location_model_no_biz(self):
        """ Assert location needs a valid business to be created. """
        with self.assertRaises(IntegrityError):
            Location.objects.create(
                location_state_province='NY',
                location_address1='',
                location_address2='',
                location_city='',
                location_zip_postal='')

    def test_location_model_only_state(self):
        """ Assert location with just a state populated won't generate coords.
        """
        business = BUSINESS_FACTORY.create_business()
        location = Location.objects.create(
            business=business,
            location_state_province='NY',
            location_address1='',
            location_address2='',
            location_city='',
            location_zip_postal='')
        coords = location.get_coords()
        self.assertEquals(coords, None)

    def test_location_model_creation(self):
        """ Assert coordinates created for a location having a city and zip. """
        business = BUSINESS_FACTORY.create_business()
        location = Location.objects.create(
            business=business,
            location_state_province='NY',
            location_address1='',
            location_address2='',
            location_city='Wallkill',
            location_zip_postal='12589')
        self.assertTrue(location.id)
        coords_2 = location.get_coords()
        # Ensure coordinates are not None.
        self.assertTrue(coords_2)
    
    def test_loc_get_existing_coords(self):
        """ Test get_coords method when they already exist. """
        business = BUSINESS_FACTORY.create_business()
        location = business.locations.all()[0]
        location_coordinate = location.location_coordinate
        location_coordinate.location_longitude = \
            location_coordinate.location_latitude
        location_coordinate.save()
        test_coords = Location.objects.get(id=location.id).get_coords()
        # Get_coords should retrieve what we placed and not fetch new ones.
        self.assertEqual(test_coords[0], test_coords[1])
    
    def test_loc_geo_purge_none(self):
        """ Test geo_purge method to return none when missing fields. """
        business = BUSINESS_FACTORY.create_business(create_location=False)
        location = Location.objects.create(business=business)
        location_address = location.geo_purge()
        self.assertEqual(location_address, None)
    
    def test_loc_geo_purge_valid(self):
        """ Test geo_purge method to return address string. """
        business = BUSINESS_FACTORY.create_business(create_location=False)
        location = Location.objects.create(business=business,
            location_state_province='NY',
            location_address1='',
            location_address2='',
            location_city='',
            location_zip_postal='12550')
        location_address = location.geo_purge()
        self.assertEqual(location_address, "NY 12550")


class TestBusinessProfileModel(TestCase):
    """ Tests for advertiser model of advertiser app. """

    def test_get_biz_profile_none(self):
        """ 
        Test business method that returns business profile description None as 
        default (from coupon)
        """
        coupon = COUPON_FACTORY.create_coupon()
        self.assertEqual(coupon.offer.business.get_business_description(), '')
    
    def test_get_biz_profile_valid(self):
        """ 
        Test business method that returns business profile description 
        (from coupon)
        """
        coupon = COUPON_FACTORY.create_coupon()
        test_desc = "All about this business and the way it runs and " + \
        "it's history..."
        BusinessProfileDescription.objects.create(
            business_description=test_desc,
            business=coupon.offer.business)
        self.assertEqual(coupon.offer.business.get_business_description(), 
            test_desc)
    
    def test_get_biz_profile_integrity(self):
        """ Assert business can have at most one business_profile_description.
        """
        # Add business profile to business that doesn't have one.
        business = BUSINESS_FACTORY.create_business()
        BusinessProfileDescription.objects.create(
            business_description="All about this business...",
            business=business)
        # Test save was successful.
        self.assertEqual(BusinessProfileDescription.objects.filter(
            business=business).count(), 1)
        # Try to create and save another business profile for this business.
        with self.assertRaises(IntegrityError):
            BusinessProfileDescription.objects.create(
                business_description="More about this business...",
                business=business)
