""" Location Factory used to help create quick Business Location instances 
and/or Coupon Location instances for tests
"""
import random

from advertiser.models import Location
from common.utils import random_string_generator
from market.models import Site


class BusinessLocationFactory(object):
    """ Business Location Factory Class """
    def __init__(self):
        self.sites_list = Site.objects.exclude(id__in=[1, 131]).select_related(
            'default_state_province').values_list(
                'default_zip_postal',
                'default_state_province__abbreviation')

    def _create(self, business, **kwargs):
        """ Create a single business location instance with dummy 
        coordinates. Passes test_mode=True to save method to require
        geocoder service to use open street maps.
        """
        sites_list_choice = random.choice(self.sites_list)
        location = Location(business=business,
            location_address1='%s %s' % (
                random_string_generator(string_length=3, numeric_only=True),
                random_string_generator()),
            location_address2='%s %s' % (
                random_string_generator(), random_string_generator()),
            location_city=random_string_generator(lower_alpha_only=True),
            location_state_province=kwargs.get('location_state_province',
                sites_list_choice[1]),
            location_zip_postal=kwargs.get('location_zip_postal',
                sites_list_choice[0]),
            location_description='%s %s %s' % (
                random_string_generator(),
                random_string_generator(),
                random_string_generator()),
            location_area_code=random_string_generator(string_length=3,
                numeric_only=True),
            location_exchange=random_string_generator(string_length=3,
                numeric_only=True),
            location_number=random_string_generator(string_length=4,
                numeric_only=True))
        location.save()
        return location
    
    def create_business_location(self, business, **kwargs):
        """ Create one business_location for this business. """
        location = self._create(business, **kwargs)
        return location
        
    def create_business_locations(self, business, create_count=1, **kwargs):
        """ Create multiple Locations for this business. """
        location_list = []
        current_create_count = 0
        while current_create_count < create_count:
            location = self._create(business, **kwargs)
            current_create_count += 1
            location_list.append(location)
        return location_list


class CouponLocationFactory(object):
    """ Coupon Location Factory Class """
    
    @staticmethod
    def create_coupon_location(coupon):
        """ Associate one business_locations with this coupon. 
        Requirement:  A business must already have a location associated with
        it. This is already taken care of when create_business gets call in the
        BUSINESS_FACTORY.
        """
        location = coupon.offer.business.locations.all()[0]
        coupon.location = [location]
        return location
    
    @staticmethod
    def create_coupon_locations(coupon, create_all=True, 
            business_location_count=1, coupon_location_count=1):
        """ Create multiple locations for this coupon and business.
        
        ARG Definitions:
        create_all == True will ensure that every business_location will get 
            associated with this coupon. 
        business_location_count == the number of locations that the respective
            business of this coupon will have in total.
        coupon_location_count == The number of business_locations that will be
            associated with this coupon.
        """
        current_create_count = 1
        while current_create_count < business_location_count:
            BUSINESS_LOCATION_FACTORY.create_business_location(
                coupon.offer.business)
            current_create_count += 1
        all_business_locations = coupon.offer.business.locations.all()
        if create_all:
            location_list = coupon.offer.business.locations.all() 
        else:
            location_list = all_business_locations[:coupon_location_count]
        coupon.location = location_list
        return location_list

BUSINESS_LOCATION_FACTORY = BusinessLocationFactory()
COUPON_LOCATION_FACTORY = CouponLocationFactory()
