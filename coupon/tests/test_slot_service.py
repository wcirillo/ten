""" Tests of service functions of coupon slots. """
import logging

from django.test import TestCase

from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import Coupon
from coupon.service.slot_service import (check_available_family_slot,
    publish_business_coupon)
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestGetSlotCoupons(TestCase):
    """ Test cases for selecting coupons in slots. """

    urls = 'urls_local.urls_2'
        
    def setUp(self):
        super(TestGetSlotCoupons, self).setUp()
        self.site = Site.objects.get(id=2)
        self.initial_coupon_count = \
            Coupon.current_coupons.get_current_coupons_by_site(
                self.site).count()
        self.slot_list = SLOT_FACTORY.create_slots(5) 
    
    def test_slot_coupons_by_site_1(self):
        """ Assert no coupons are selected for site 1. """
        site = Site.objects.get(id=1)
        self.assertEqual(Coupon.current_coupons.get_current_coupons_by_site(
            site).count(), 0)
        
    def test_slot_coupons_by_site_hv(self):
        """ Assert a coupon is selected for site hudson-valley. """
        self.assertEqual(Coupon.current_coupons.get_current_coupons_by_site(
            self.site).count(), self.initial_coupon_count + len(self.slot_list))


class TestPublishBusinessCoupon(TestCase):
    """ Test case for the slot service function publish_business_coupon. """

    def test_family_first(self):
        """ Assert a business related to two slot families, the first having an
        available child and the second having an available parent slot,
        the first family is filled first.
        """
        slot_family_1 = SLOT_FACTORY.create_slot_family(create_count=2)
        LOG.debug('slot_family_1: %s' % str(slot_family_1))
        # New slot for that same business:
        slot = SLOT_FACTORY.create_slot(create_slot_time_frame=False)
        slot.business = slot_family_1[0]['parent'].business
        slot.save()
        family_availability_dict = check_available_family_slot(slot.business.id)
        coupon = COUPON_FACTORY.create_coupon()
        new_slot = publish_business_coupon(family_availability_dict, coupon)
        LOG.debug('family_availability_dict: %s' % family_availability_dict)
        self.assertEqual(new_slot.parent_slot, slot_family_1[0]['parent'])
        
    def test_reuse_old_child(self):
        """ Assert that when a parent needs a child and a non expired child slot
        for this business already exists we utilize this child slot. The child
        start_date will remain the same. The child end_date will match the
        parents end_date and the child's parent slot will be the parent slot.
        """
        slot_family = SLOT_FACTORY.create_slot_family(create_count=2)
        # End the slot_time_frame of the child slot.
        child_slot = slot_family[0]['children'][0]
        slot_time_frame = child_slot.slot_time_frames.latest('id')
        slot_time_frame.close_this_frame_now()
        coupon = COUPON_FACTORY.create_coupon()
        family_availability_dict = check_available_family_slot(
            slot_family[0]['parent'].business.id)
        new_slot = publish_business_coupon(family_availability_dict, coupon)
        LOG.debug(family_availability_dict)
        self.assertEqual(new_slot.parent_slot, slot_family[0]['parent'])
        self.assertEqual(new_slot.start_date, child_slot.start_date)
        self.assertEqual(new_slot.end_date, child_slot.end_date)
