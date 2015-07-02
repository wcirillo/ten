""" Tests for service functions of geolocation app. """
#pylint: disable=C0103
from decimal import Decimal
from random import randrange

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.test import TestCase

from advertiser.models import Business, Location
from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from geolocation.geocode_address import GEOCODE_LOCATION
from geolocation.models import USCounty, USZip
from geolocation.service import (build_county_geometries, get_city_and_state,
    get_consumer_count_per_county, get_consumer_count_by_county,
    get_consumer_count_by_zip, build_zip_geometries, qry_consumer_count_spread)
from market.models import Site


class TestGeocodingService(EnhancedTestCase):
    """ Tests for service functions of geolocation app. """    

    fixtures = ['test_geolocation', 'test_consumer', 'test_advertiser']

    @classmethod
    def setUpClass(cls):
        """ Set environment variable for geocoder for prod gg method test. """
        super(TestGeocodingService, cls).setUpClass()
        settings.ENVIRONMENT['use_geo_method'] = 'osm'
    
    @classmethod
    def tearDownClass(cls):
        """ Reset environment setting for geocoder when class tears down. """
        super(TestGeocodingService, cls).tearDownClass()
        settings.ENVIRONMENT['use_geo_method'] = 'static'

    def prep_location(self):
        """ Prepare location for testing. """
        business = Business.objects.get(id=1)
        self.loc = Location()
        # Randomize number to make less likely to return 602 error.
        random_number = randrange(1000, 1050, 1)
        self.loc.business = business
        self.loc.location_address1 = str(random_number) + ' Main Street'
        self.loc.location_address2 = ''
        self.loc.location_city = ''
        self.loc.location_state_province = 'NY'
        self.loc.location_zip_postal = ''
        self.loc.save()

    def test_no_city_no_zip(self):
        """ Test osm geocoding address service, when no city and no state,
        no coord.
        """
        self.prep_location()
        coords = GEOCODE_LOCATION.get_coordinate(
            location=self.loc,)
        # No coords created if zip and city are blank.
        self.assertEqual(coords, None)
    
    def test_city_no_zip(self):
        """ Test osm geocoding service, when either zip or city is populated.
        """
        self.prep_location()
        self.loc.location_city = 'Fishkill'
        self.loc.save()
        # Creates coords if city or zip is populated.
        coords = GEOCODE_LOCATION.get_coordinate(location=self.loc)
        self.assertTrue(coords)
    
    def test_good_location(self):
        """ Assert when city state and zip are populated in address, we get a 
        good coordinate.
        """
        self.prep_location()
        # Create coords.
        self.loc.location_zip_postal = '12524'
        self.loc.save()
        coords = GEOCODE_LOCATION.get_coordinate(
            location=self.loc)
        # Test this is a reasonably valid response.
        self.assertTrue(Decimal(coords[0]) < Decimal('-73.5'))
        self.assertTrue(Decimal(coords[1]) > Decimal('41.4'))
    
    def test_production_geocoder(self):
        """ Assert in ONE test that google's geocoding service is accessible
        and processes a valid address. 
        """
        self.prep_location()
        self.loc.location_address1 = '1080 Main Street'
        self.loc.location_city = 'Fishkill'
        self.loc.location_zip_postal = '12524'
        use_geo_method = settings.ENVIRONMENT['use_geo_method']
        settings.ENVIRONMENT['use_geo_method'] = 'gg'
        # Save method calls get_coordinate, but we want to process in real time.
        self.loc.save()
        coords = GEOCODE_LOCATION.get_coordinate(location=self.loc)
        self.assertEqual(Decimal(coords[0]).quantize(Decimal(10) ** -6),
            Decimal('-73.903094'))
        self.assertEqual(Decimal(coords[1]).quantize(Decimal(10) ** -6),
            Decimal('41.534933'))
        settings.ENVIRONMENT['use_geo_method'] = use_geo_method


class TestService(TestCase):
    """ Tests for service functions of geolocation app. """    
    
    fixtures = ['test_geolocation', 'test_consumer', 'test_advertiser']
    
    def test_site_county_list(self):
        """ 
        Test service method that pulls all counties (name and geom) for a site 
        ordered by consumer count.
        """
        site = Site.objects.get(id=2)
        county_list, county_data = build_county_geometries(site)
        popular_county = USCounty.objects.get(name=county_list[0], sites__id=2)
        test_county_counts = get_consumer_count_per_county(site)
        self.assertEqual(test_county_counts[0][0], popular_county.name)
        # Ensure there are two ; delimiters per record.
        self.assertEqual(county_data.count(';') % 2, 0)
        county_list = county_data.split(';')
        self.assertEqual(county_list[1], popular_county.name)
        self.assertTrue(GEOSGeometry(county_list[0]).num_points > 10)

    def test_build_zip_geoms(self):
        """
        Test service that retrieves zip geoms if they exist or points if they 
        do not, simplifies them and appends them to a string which is returned.
        """
        site = Site.objects.get(id=2)
        zip_geoms = build_zip_geometries(site)
        self.assertTrue('|POINT' in zip_geoms)
        self.assertTrue('|POLYGON' in zip_geoms)
        self.assertTrue(';12604;' in zip_geoms)
        self.assertTrue(';12602;' in zip_geoms)
        self.assertTrue('|;' not in zip_geoms)
        self.assertTrue(';;;' not in zip_geoms)
        self.assertTrue('EMPTY' not in zip_geoms)
        self.assertEqual(len(zip_geoms), len(site.get_or_set_geometries('zip-geoms-data.txt')))

    def test_zip_detail_good(self):
        """ Assert service method returns city and state for this zip. """
        city, state = get_city_and_state('12550')
        self.assertEqual('Newburgh', city)
        self.assertEqual('NY', state)

    def test_zip_detail_bad(self):
        """ Assert service method returns blanked out city and state when zip
        not found.
        """
        city, state = get_city_and_state('99990')
        self.assertEqual('', city)
        self.assertEqual('', state)


class TestConsumerCounts(TestCase):
    """ Tests for service functions of geolocation app. """    
    
    fixtures = ['test_geolocation', 'test_consumer', 'test_advertiser']
        
    def test_count_dutchess(self):
        """ Asserts count for Dutchess county. """
        us_county = USCounty.objects.get(name='Dutchess', us_state__id=35)
        count = get_consumer_count_by_county(us_county)
        self.assertEquals(count, 1)
        
    def test_count_orange(self):
        """ Asserts count for Orange county. """
        us_county = USCounty.objects.get(name='Orange', us_state__id=35)
        count = get_consumer_count_by_county(us_county)
        self.assertEquals(count, 5)
        
    def test_count_12550(self):
        """ Asserts count for zip 12550. """    
        us_zip = USZip.objects.get(code='12550')
        count = get_consumer_count_by_zip(us_zip)
        self.assertEquals(count, 5)

    def test_county_consumer_count(self):
        """ Test the get_consumer_count_per_county method to ensure count is 
        accurate per county. 
        """
        dutchess_count = Consumer.objects.filter(consumer_zip_postal__in=
            USZip.objects.filter(us_county__name='Dutchess'
            ).values_list('code', flat=True)).count()
        orange_count = Consumer.objects.filter(consumer_zip_postal__in=
            USZip.objects.filter(us_county__name='Orange'
            ).values_list('code', flat=True)).count()
        site = Site.objects.get(id=2)
        test_county_counts = get_consumer_count_per_county(site)
        found_dutchess = False
        found_orange = False
        for row in test_county_counts:
            if row[0] == 'Dutchess':
                self.assertEqual(row[2], dutchess_count)
                found_dutchess = True
            elif row[0] == 'Orange':
                self.assertEqual(row[2], orange_count)
                found_orange = True
        self.assertTrue(found_dutchess)
        self.assertTrue(found_orange)

    def tally_counts(self):
        """ Tally city records in this market to check valid consumer count. """
        self.tally = 0
        for record in qry_consumer_count_spread(2):
            self.tally += record[6]
        return self.tally

    def test_site_consumer_count_spread(self):
        """ Assert count of consumer for sites when consumer added to county
        in site.
        """
        initial_count = self.tally_counts()
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.consumer_zip_postal = '12601'
        consumer.save()
        self.tally_counts()
        self.assertEqual(initial_count + 1, self.tally)
    
    def test_count_spread_mailable(self):
        """ Verify that consumers not emailable are not tallied. """
        initial_count = self.tally_counts()
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.consumer_zip_postal = '12601'
        consumer.is_emailable = False
        consumer.save()
        self.tally_counts()
        self.assertEqual(self.tally, initial_count)
