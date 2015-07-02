""" Tests for flyer models of coupon app. """

import datetime
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, TransactionTestCase

from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import (Flyer, FlyerCoupon, FlyerSubdivision, FlyerPlacement,
    FlyerPlacementSubdivision, FlyerSubject)
from coupon.service.flyer_service import next_flyer_date

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestFlyerModel(TransactionTestCase):
    """ These are tests that require transactional rollbacks. """

    def test_flyer_unicity(self):
        """ Test unique constraints of flyers. """
        flyer = Flyer.objects.create(site_id=2)
        coupons = COUPON_FACTORY.create_coupons(create_count=2)
        FlyerCoupon.objects.create(flyer_id=flyer.id, coupon_id=coupons[0].id,
            rank=1)
        with self.assertRaises(IntegrityError):
            FlyerCoupon.objects.create(flyer_id=flyer.id,
                coupon_id=coupons[0].id, rank=2)
            self.fail('A coupon cannot be related to a flyer more than once.')
        transaction.rollback()
        with self.assertRaises(IntegrityError):
            FlyerCoupon.objects.create(flyer_id=flyer.id,
                coupon_id=coupons[1].id, rank=1)
            self.fail('A flyer cannot have two coupons of the same rank.')
        transaction.rollback()


class TestFlyerSubdivisionModel(TestCase):
    """ Test case for FlyerSubdivisionModel. Note this class and
    FlyerPlacementSubdivision model both subclass the Subdivision model, so
    the testing of Subdivision can occur in either subclass.
    """
    fixtures = ['test_geolocation']

    def setUp(self):
        self.county_type = ContentType.objects.get(model='uscounty')
        self.city_type = ContentType.objects.get(model='uscity')
        self.zip_type = ContentType.objects.get(model='uszip')
        self.good_flyer = Flyer.objects.create(site_id=2)
        self.bad_flyer = Flyer.objects.create(site_id=2)

    def test_county_flyer_zip_flyer(self):
        """ Assert a zip subdivision is not allowed for a flyer if another flyer
        for the same send_date and the same site has a subdivision that is the
        county that contains this zip.
        """
        FlyerSubdivision.objects.create(flyer=self.good_flyer,
            geolocation_type=self.county_type, geolocation_id=1866)
        with self.assertRaises(ValidationError) as context_manager:
            FlyerSubdivision.objects.create(flyer=self.bad_flyer,
                geolocation_type=self.zip_type, geolocation_id=23181)
            self.fail('Flyer for 12550 created, Orange County flyer existed.')
        LOG.debug(context_manager.exception)

    def test_county_flyer_city_flyer(self):
        """ Assert a city is not allowed for a flyer if another flyer for the
        same send_date and the same site has a subdivision that is the county
        that contains this city.
        """
        FlyerSubdivision.objects.create(flyer=self.good_flyer,
            geolocation_type=self.county_type, geolocation_id=1866)
        with self.assertRaises(ValidationError) as context_manager:
            FlyerSubdivision.objects.create(flyer=self.bad_flyer,
                geolocation_type=self.city_type, geolocation_id=17552)
            self.fail('Newburgh flyer created, Orange County flyer existed.')
        LOG.debug(context_manager.exception)

    def test_city_flyer_zip_flyer(self):
        """ Assert a zip is not allowed for a flyer if another flyer for the
        same send_date and the same site has a subdivision that is the city that
        contains this zip.
        """
        FlyerSubdivision.objects.create(flyer=self.good_flyer,
            geolocation_type=self.city_type, geolocation_id=17552)
        with self.assertRaises(ValidationError) as context_manager:
            FlyerSubdivision.objects.create(flyer=self.bad_flyer,
                geolocation_type=self.zip_type, geolocation_id=23181)
            self.fail('Flyer for 12550 created, Newburgh flyer existed.')
        LOG.debug(context_manager.exception)

    def test_zip_flyer_county_flyer(self):
        """ Assert a county is not allowed for a flyer if another flyer for the
        same send_date and the same site has a subdivision that is a zip within
        this county.
        """
        FlyerSubdivision.objects.create(flyer=self.good_flyer,
            geolocation_type=self.zip_type, geolocation_id=23181)
        with self.assertRaises(ValidationError) as context_manager:
            FlyerSubdivision.objects.create(flyer=self.bad_flyer,
                geolocation_type=self.county_type, geolocation_id=1866)
            self.fail('Flyer for Orange created, 12550 flyer existed.')
        LOG.debug(context_manager.exception)

    def test_zip_flyer_city_flyer(self):
        """ Assert a city is not allowed for a flyer if another flyer for the
        same send_date and the same site has a subdivision that is a zip within
        this city.
        """
        FlyerSubdivision.objects.create(flyer=self.good_flyer,
            geolocation_type=self.zip_type, geolocation_id=23181)
        with self.assertRaises(ValidationError) as context_manager:
            FlyerSubdivision.objects.create(flyer=self.bad_flyer,
                geolocation_type=self.city_type, geolocation_id=17552)
            self.fail('Flyer for Newburgh created, 12550 flyer existed.')
        LOG.debug(context_manager.exception)

    def test_city_flyer_county_flyer(self):
        """ Assert a county is not allowed for a flyer if another flyer for the
        same send_date and the same site has a subdivision that is a city within
        this county.
        """
        FlyerSubdivision.objects.create(flyer=self.good_flyer,
            geolocation_type=self.city_type, geolocation_id=17552)
        with self.assertRaises(ValidationError) as context_manager:
            FlyerSubdivision.objects.create(flyer=self.bad_flyer,
                geolocation_type=self.county_type, geolocation_id=1866)
            self.fail('Flyer for Orange created, Newburgh flyer existed.')
        LOG.debug(context_manager.exception)


class TestFlyerPlacementModel(TestCase):
    """ Assertions for the model FlyerPlacement. """
    
    def test_site_match(self):
        """ Assert the site of a FlyerPlacement must be the same as its slot.
        """
        slot = SLOT_FACTORY.create_slot() # This slot is on site 2.
        flyer_placement = FlyerPlacement(site_id=3, slot=slot,
            send_date=next_flyer_date())
        with self.assertRaises(ValidationError) as context_manager:
            flyer_placement.save()
            self.fail('A flyer placement site must match slot site.')
        LOG.debug(context_manager.exception)

    def test_send_date_thursday(self):
        """ Assert the site of a FlyerPlacement must be a Thursday. """
        slot = SLOT_FACTORY.create_slot() # This slot is on site 2.
        flyer_placement = FlyerPlacement(site_id=2, slot=slot,
            send_date=next_flyer_date() + datetime.timedelta(1))
        with self.assertRaises(ValidationError) as context_manager:
            flyer_placement.save()
            self.fail('Send date must be a Thurdsay')
        LOG.debug(context_manager.exception)


class TestFlyerPlacementSubdivisionModel(TestCase):
    """ Assertions for the model FlyerPlacementSubdivision. """
    
    def example_flyer_placement(self):
        """ Create a flyer_placement for testing. """
        slot = SLOT_FACTORY.create_slot()
        self.flyer_placement = FlyerPlacement.objects.create(site_id=2,
            slot=slot, send_date=next_flyer_date())

    def example_zip_subdivision(self):
        """ Create a flyer_placement for testing in 12550 """
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=self.flyer_placement,
            geolocation_type=ContentType.objects.get(model='uszip'),
            geolocation_id=23181)

    def example_city_subdivision(self):
        """ Create a flyer_placement for testing in Orange County NY """
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=self.flyer_placement,
            geolocation_type=ContentType.objects.get(model='uscity'),
            geolocation_id=17552)

    def example_county_subdivision(self):
        """ Create a flyer_placement for testing in Orange County NY """
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=self.flyer_placement,
            geolocation_type=ContentType.objects.get(model='uscounty'),
            geolocation_id=1866)

    def test_subdivision_match(self):
        """ Assert the subdivision of a FlyerPlacement must be in the site. """
        slot = SLOT_FACTORY.create_slot()
        flyer_placement = FlyerPlacement.objects.create(site_id=2, slot=slot,
            send_date=next_flyer_date())
        flyer_placement_subdivision = FlyerPlacementSubdivision(
            flyer_placement=flyer_placement, 
            geolocation_type=ContentType.objects.get(model='uszip'),
            geolocation_id=33013)
        with self.assertRaises(ValidationError):
            flyer_placement_subdivision.save()

    def test_zip_within_county(self):
        """ Assert 12550 cannot be added to an instance with Orange County. """
        self.example_flyer_placement()
        self.example_county_subdivision()
        with self.assertRaises(ValidationError) as context_manager:
            self.example_zip_subdivision()
        LOG.debug(context_manager.exception)

    def test_zip_within_city(self):
        """ Assert 12550 cannot be added to an instance with Newburgh. """
        self.example_flyer_placement()
        self.example_city_subdivision()
        with self.assertRaises(ValidationError) as context_manager:
            self.example_zip_subdivision()
            self.fail('Subdivision w/i another subdivision allowed.')
        LOG.debug(context_manager.exception)

    def test_city_within_county(self):
        """ Assert Newburgh cannot be added to an instance with Orange County.
        """
        self.example_flyer_placement()
        self.example_county_subdivision()
        with self.assertRaises(ValidationError) as context_manager:
            self.example_city_subdivision()
            self.fail('Subdivision w/i another subdivision allowed.')
        LOG.debug(context_manager.exception)

    def test_county_containing_zip(self):
        """ Assert Orange County cannot be added to an instance with 12550. """
        self.example_flyer_placement()
        self.example_zip_subdivision()
        with self.assertRaises(ValidationError) as context_manager:
            self.example_county_subdivision()
            self.fail('Subdivision containing another subdivision allowed.')
        LOG.debug(context_manager.exception)

    def test_county_containing_city(self):
        """ Assert Orange County cannot be added to an instance with Newburgh.
        """
        self.example_flyer_placement()
        self.example_city_subdivision()
        with self.assertRaises(ValidationError) as context_manager:
            self.example_county_subdivision()
            self.fail('Subdivision containing another subdivision allowed.')
        LOG.debug(context_manager.exception)

    def test_city_containing_zip(self):
        """ Assert Newburgh cannot be added to an instance with 12550. """
        self.example_flyer_placement()
        self.example_zip_subdivision()
        with self.assertRaises(ValidationError) as context_manager:
            self.example_city_subdivision()
            self.fail('Subdivision containing another subdivision allowed.')
        LOG.debug(context_manager.exception)


class TestFlyerSubjectModel(TestCase):
    """ Tests for FlyerSubject, that do not require a transaction. """
    
    def test_save_flyer_subject(self):
        """ Tests save method of flyer subject. Assert defaults used. """
        flyer_subject = FlyerSubject()
        flyer_subject.title = "Test"
        flyer_subject.save()
        self.assertTrue(flyer_subject.week != None)
