""" Test for the advertiser business app service functions. """
#pylint: disable=C0103
import logging

from advertiser.models import (BusinessProfileDescription, Location)
from advertiser.service import get_meta_for_business
from advertiser.business.location.service import get_locations_for_coupons
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import Coupon
from coupon.service.coupons_service import ALL_COUPONS

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestBusinessService(EnhancedTestCase):
    """ Test case for service functions of business package of advertiser app.
    """
    def setUp(self):
        """ Set a coupon in a slot. """
        super(TestBusinessService, self).setUp()
        self.coupon = COUPON_FACTORY.create_coupon(create_location=False)
        SLOT_FACTORY.create_slot(coupon=self.coupon,
            create_slot_time_frame=True)
        self.business = self.coupon.offer.business
        BusinessProfileDescription.objects.create(business=self.business,
            business_description='The best profile description evah.')
        self.advertiser = self.business.advertiser

    def get_meta_for_location(self, location):
        """ Get meta contents for a test. """
        location.coupons.add(self.coupon)
        _coupon_ids = ALL_COUPONS.get_coupons_this_business(self.business.id,
            self.advertiser.site)
        _all_coupons = Coupon.objects.filter(id__in=_coupon_ids).select_related(
            'offer', 'offer__business')
        _all_locations = get_locations_for_coupons(_all_coupons)
        meta = get_meta_for_business(self.business, _all_locations)
        LOG.debug(meta)
        return meta

    def test_business_meta(self):
        """ Assert business meta title and desc tags are populated correctly
        when coupon has location.
        """
        location = Location(business=self.coupon.offer.business,
            location_address1='1 Road',
            location_city='City 1',
            location_area_code='111',
            location_exchange='111',
            location_number='1111',
            location_state_province='AL')
        location.save()
        meta = self.get_meta_for_location(location)
        self.assertTrue(len(meta['desc']) <= 160)
        self.assertEqual(meta['title'],
            '%s, City 1' % self.business.business_name)
        self.assertTrue(self.business.business_name in meta['title'])
        self.assertTrue(self.business.business_name in meta['desc'])
        self.assertTrue('coupons in City 1, AL. The best profile description'
            in meta['desc'])

    def test_business_meta_blank_city(self):
        """ Assert meta contents when city location is blank. """
        location = Location(
            business=self.coupon.offer.business,
            location_city="",
            location_state_province="AL",
            location_exchange="111",
            location_area_code="111",
            location_description="Across from 1",
            location_zip_postal="11111",
            location_address1="1 Road",
            location_address2="Apartment 1",
            location_number="1111")
        location.save()
        meta = self.get_meta_for_location(location)
        self.assertEqual(meta['title'],
            '%s, Hudson Valley Area' % self.business.business_name)
        self.assertTrue(self.business.business_name in meta['desc'])
        self.assertTrue('coupons in the Hudson Valley Area.' in meta['desc'])

    def test_business_meta_buffalo(self):
        """ Assert meta contents when city is Buffalo and state is blank. """
        location = Location(
            business=self.coupon.offer.business,
            location_address1='1 Road',
            location_city='Buffalo',
            location_area_code='111',
            location_exchange='111',
            location_number='1111',
            location_state_province='')
        location.save()
        meta = self.get_meta_for_location(location)
        self.assertTrue('coupons in Buffalo.' in meta['desc'])
        self.assertEqual(meta['title'],
            '%s, Buffalo' % self.business.business_name)

    def test_business_meta_no_location(self):
        """ Test meta tags in business all-coupons view when no location. """
        coupon_ids = ALL_COUPONS.get_coupons_this_business(self.business.id,
            self.advertiser.site)
        all_coupons = Coupon.objects.filter(id__in=coupon_ids).select_related(
            'offer', 'offer__business')
        all_locations = get_locations_for_coupons(all_coupons)
        meta = get_meta_for_business(self.business, all_locations)
        self.assertEqual('%s coupons in the Hudson Valley Area. %s' %
            (self.business.business_name,
            self.business.business_profile_description.business_description),
            meta['desc'])
        self.assertEqual('%s, Hudson Valley Area' %
            self.business.business_name, meta['title'])
