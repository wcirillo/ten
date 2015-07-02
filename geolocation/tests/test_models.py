""" Tests models of geolocation app """

from django.core.exceptions import ValidationError
from django.test import TestCase

from geolocation.models import Coordinate, USState, USCounty, USCity, USZip
from market.models import Site


class TestModels(TestCase):
    """ Tests for models of geolocation app. """

    def test_coord_delete(self):
        """ Tests coordinate deletes are prevented. """
        obj = Coordinate.objects.all()[0]
        print(obj)
        try:
            obj.delete()
            self.fail('Coordinate was deleted.')
        except ValidationError:
            pass  

    def test_state_save(self):
        """ Tests USState saves are prevented. """
        obj = USState()
        try:
            obj.save()
            self.fail('US State was saved.')
        except ValidationError:
            pass
            
    def test_state_delete(self):
        """ Tests USState deletes are prevented. """
        obj = USState.objects.all()[0]
        print(obj)
        try:
            obj.delete()
            self.fail('US State was deleted.')
        except ValidationError:
            pass
            
    def test_county_save(self):
        """ Tests USCounty saves are prevented. """
        obj = USCounty()
        try:
            obj.save()
            self.fail('US County was saved.')
        except ValidationError:
            pass

    def test_county_delete(self):
        """ Tests USCounty deletes are prevented. """
        obj = USCounty.objects.all()[0]
        print(obj)
        try:
            obj.delete()
            self.fail('US County was deleted.')
        except ValidationError:
            pass

    def test_city_save(self):
        """ Tests USCounty saves are prevented. """
        obj = USCity()
        try:
            obj.save()
            self.fail('US City was saved.')
        except ValidationError:
            pass

    def test_city_delete(self):
        """ Tests USCounty deletes are prevented. """
        obj = USCity.objects.all()[0]
        print(obj)
        try:
            obj.delete()
            self.fail('US City was deleted.')
        except ValidationError:
            pass

    def test_get_municipality_type(self):
        """ Tests model USState method get_municipality_division. """
        new_york = USState.objects.get(id=35)
        alaska = USState.objects.get(id=2)
        louisiana = USState.objects.get(id=21)
        self.assertEqual(new_york.get_municipality_division(), 'county')
        self.assertEqual(alaska.get_municipality_division(), 'borough')
        self.assertEqual(louisiana.get_municipality_division(), 'parish')
        self.assertEqual(new_york.get_municipality_division(True), 'counties')
        self.assertEqual(alaska.get_municipality_division(True), 'boroughs')
        self.assertEqual(louisiana.get_municipality_division(True), 'parishes')


class TestUSZipModel(TestCase):
    """ Tests for model and methods of USZip in geolocation app. """

    def test_zip_save(self):
        """ Tests USZip save are prevented. """
        obj = USZip()
        try:
            obj.save()
            self.fail('US Zip was save.')
        except ValidationError:
            pass

    def test_zip_delete(self):
        """ Tests USZip deletes are prevented. """
        obj = USZip.objects.all()[0]
        try:
            obj.delete()
            self.fail('US Zip was deleted.')
        except ValidationError:
            pass

    def test_get_zips_this_site(self):
        """ Tests a method of the USZip model manager, get_zips_this_site(site).
        """
        # Check if zip 12550 belongs to site 2.
        site = Site.objects.get(id=2)
        zip_postals = list(USZip.objects.get_zips_this_site(site))
        zip_codes = [zip_postal.code for zip_postal in zip_postals]
        self.assertTrue('12550' in zip_codes)

    def test_good_coordinate_12550(self):
        """ Assert USZip method returns 12550 when a valid coordinate resides
        within it.
        """
        lat = '41.502132349936126'
        lon = '-74.01987075805664'
        zip_code = USZip.objects.get_zip_this_coordinate(lat, lon)
        self.assertEqual(zip_code.code, '12550')

    def test_zip_by_bad_coordinate(self):
        """ Assert USZip method handles a bad coordinate resides that doesn't
        have a zip associated with it.
        """
        # This test requires that we don't have zips in Puerto Rico loaded.
        lat = '18.25508897088302'
        lon = '-66.368408203125'
        zip_code = USZip.objects.get_zip_this_coordinate(lat, lon)
        self.assertEqual(zip_code, None)
        