""" Test location tasks. """
from random import randrange

from django.test import TestCase

from advertiser.business.location.tasks import create_location_coordinate
from advertiser.models import Location, LocationCoordinate

class TestLocationTasks(TestCase):
    """ Tests for tasks of advertiser/business/locations app. """ 
    fixtures = ['test_advertiser', 'test_coupon_views']
        
    def test_create_loc_coords_good(self):
        """ 
        Test creation and saving of location geo-coordinates with valid address.
        """
        test_location1 = Location.objects.get(id=120)
        street_number = randrange(2000, 2500, 1)
        test_location1.location_address1 = str(street_number) + ' Main Street'
        test_location1.location_address2 = ''
        test_location1.location_city = 'Wappingers Falls'
        test_location1.location_state_province = 'NY'
        test_location1.location_zip_postal = '12590'
        test_location1.save()
        try:
            test_location1.location_coordinate
        except LocationCoordinate.DoesNotExist:
            # Task didn't complete yet?
            try:
                test_location1.location_coordinate  
            except LocationCoordinate.DoesNotExist:
                self.fail('Task did not create location coordinate')
                 
    def test_create_loc_coords_bad(self):
        """ 
        Test creation and saving of location geo-coordinates with invalid
        address. 
        """
        test_location2 = Location.objects.get(id=120)
        create_location_coordinate(test_location2.id)
        try:
            coords2 = test_location2.location_coordinate
        except LocationCoordinate.DoesNotExist:
            coords2 = None
        self.assertEqual(coords2, None) 
        
