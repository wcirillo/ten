""" Test for the coupon app models. """

import datetime
import logging

from django.core.exceptions import ValidationError
from django.test import TestCase

from advertiser.factories.business_factory import BUSINESS_FACTORY
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import FlyerPlacement, Slot, SlotTimeFrame
from coupon.service.flyer_service import next_flyer_date
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestSlotModels(TestCase):
    """ Tests for coupon slot models. """

    def test_save_slot(self):
        """ Assert a slot can be saved with default values. """
        business = BUSINESS_FACTORY.create_business()
        slot = Slot.objects.create(site_id=2, business_id=business.id,
            start_date = datetime.date.today(),
            end_date = datetime.date.today() + datetime.timedelta(1))
        LOG.debug(slot)
        self.assertTrue(slot.id)
        self.assertEqual(slot.renewal_rate, 10)
        self.assertEqual(slot.is_autorenew, False)
        
    def test_modify_slot_site(self):
        """ Assert a slot site cannot be modified if there is a flyer placement.
        """
        slot = SLOT_FACTORY.create_slot()
        FlyerPlacement.objects.create(site_id=2, slot=slot,
            send_date=next_flyer_date())
        slot.site = Site.objects.get(id=3)
        with self.assertRaises(ValidationError) as context_manager:
            slot.save()
            self.fail('Slot with flyer placements allowed site update.')
        LOG.debug(context_manager.exception)
        
    def test_save_slot_site_1(self):
        """ Assert a slot cannot be saved on site 1. """
        business = BUSINESS_FACTORY.create_business()
        with self.assertRaises(ValidationError) as context_manager:
            Slot.objects.create(site_id=1, business_id=business.id,
                start_date = datetime.date.today(),
                end_date = datetime.date.today() + datetime.timedelta(1))
            self.fail('Invalid slot saved.')
        LOG.debug(context_manager.exception)
        
    def test_save_slot_same_start_end(self):
        """ Assert a slot cannot be saved with same start and end date values.
        """
        business = BUSINESS_FACTORY.create_business()
        with self.assertRaises(ValidationError) as context_manager:
            Slot.objects.create(site_id=2, business_id=business.id,
                start_date=datetime.date.today(),
                end_date=datetime.date.today())
            self.fail('Invalid slot saved.')
        LOG.debug(context_manager.exception)
        
    def test_slot_end_before_start(self):
        """ Assert a slot cannot be saved with end date before start date. """
        business = BUSINESS_FACTORY.create_business()
        with self.assertRaises(ValidationError) as context_manager:
            Slot.objects.create(site_id=2, business_id=business.id,
                start_date=datetime.date.today() + datetime.timedelta(3),
                end_date=datetime.date.today() + datetime.timedelta(2))
            self.fail('Invalid slot saved.')
        LOG.debug(context_manager.exception)
            
    def test_modify_slot_start_late(self):
        """ Assert a slot cannot be modified such that its start date is after
        the start_datetime of one of its slot_time_frames.
        """
        coupon = COUPON_FACTORY.create_coupon()
        slot = Slot.objects.create(site_id=2,
            business_id=coupon.offer.business.id,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(2))
        SlotTimeFrame.objects.create(slot=slot, coupon_id=coupon.id,
            start_datetime=datetime.datetime.today(),
            end_datetime=datetime.datetime.today() + datetime.timedelta(1))
        slot.start_date = datetime.date.today() + datetime.timedelta(1)
        with self.assertRaises(ValidationError) as context_manager:
            slot.save()
            self.fail('Invalid slot saved.')
        LOG.debug(context_manager.exception)
            
    def test_modify_slot_end_early(self):
        """ Assert a slot cannot be modified such that its end date is before
        the end_datetime of one of its slot_time_frames.
        """
        coupon = COUPON_FACTORY.create_coupon()
        slot = Slot.objects.create(site_id=2,
            business_id=coupon.offer.business.id,
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(2))
        SlotTimeFrame.objects.create(slot=slot, coupon_id=coupon.id,
            start_datetime=datetime.datetime.today(),
            end_datetime=datetime.datetime.today() + datetime.timedelta(1))
        slot.end_date = datetime.date.today() + datetime.timedelta(1)
        with self.assertRaises(ValidationError) as context_manager:
            slot.save()
            self.fail('Invalid slot saved.')
        LOG.debug(context_manager.exception)
            
    def test_valid_not_modified(self):
        """ Assert time frames that do not overlap are not modified by the
        justify process.
        """
        coupon = COUPON_FACTORY.create_coupon()
        past_date = datetime.datetime.now() - datetime.timedelta(60)
        slot = Slot.objects.create(site_id=2,
            business_id=coupon.offer.business.id,
            start_date=past_date,
            end_date=past_date + datetime.timedelta(30))
        slot_time_frame_y = SlotTimeFrame.objects.create(slot=slot,
            coupon_id=coupon.id,
            start_datetime=past_date + datetime.timedelta(20))
        slot_time_frame_x = SlotTimeFrame.objects.create(slot=slot,
            coupon_id=coupon.id,
            start_datetime=past_date + datetime.timedelta(1),
            end_datetime=past_date + datetime.timedelta(2))
        try:
            slot_time_frame_x.justify_time_frames(slot_time_frame_y)
        except ValidationError as error:
            LOG.debug(error)
            self.fail('Valid slot time frames failed justification.')
            
    def test_save_slot_time_frames(self):
        """ Assert time frames of slots cannot overlap. """
        coupon = COUPON_FACTORY.create_coupon()
        slot = Slot.objects.create(site_id=2,
            business_id=coupon.offer.business.id,
            start_date=datetime.datetime.today(),
            end_date = datetime.datetime.today() + datetime.timedelta(1))
        now = datetime.datetime.now()
        datetime_list = [
            # test iteration 1: Cannot start time frame before the slot starts.
            (now - datetime.timedelta(1), now, False),
            # 2. Cannot end time frame before starting it.
            (now + datetime.timedelta(1), now, False), 
            # 3. Cannot start and end at the same time.
            (now, now, False), 
            (now, now + datetime.timedelta(1), True), # Becomes slot id = 1.
            # 5. Cannot begin at same time.
            (now, now + datetime.timedelta(1), False), 
            (now + datetime.timedelta(1), now + datetime.timedelta(2), True), #2
            (now + datetime.timedelta(2), now + datetime.timedelta(3), True), #3
            (now + datetime.timedelta(5), now + datetime.timedelta(8), True), #4
            # 9. Cannot be a subset of a timeframe.
            (now + datetime.timedelta(6), now + datetime.timedelta(7), False),
            # 10. Cannot wholly include a timeframe.
            (now + datetime.timedelta(4), now + datetime.timedelta(9), False),
            # 11. Cannot straddle a start datetime.
            (now + datetime.timedelta(4), now + datetime.timedelta(6), False),
            # 12. Cannot straddle an end datetime.
            (now + datetime.timedelta(7), now + datetime.timedelta(9), False),
            # 13. Cannot end at the same time.
            (now + datetime.timedelta(6), now + datetime.timedelta(8), False),
            (now + datetime.timedelta(10), None, True), # Becomes slot id = 5.
            (now + datetime.timedelta(9), None, True), # Becomes slot id = 6
            (now + datetime.timedelta(11), None, True), # Becomes slot id = 7
            (now + datetime.timedelta(12), now + datetime.timedelta(15), True),
            ]
        counter = 0
        for start_datetime, end_datetime, is_valid in datetime_list:
            counter += 1
            LOG.debug('test iteration: %s' % counter)
            LOG.debug('test start_datetime: %s' % start_datetime)
            LOG.debug('test end_datetime: %s' % end_datetime)
            slot_time_frame = SlotTimeFrame(slot=slot, coupon_id=coupon.id,
                start_datetime=start_datetime, end_datetime=end_datetime)
            if is_valid:
                slot_time_frame.save()
                self.assertTrue(slot_time_frame.id)
            else:
                with self.assertRaises(ValidationError) as context_manager:
                    slot_time_frame.save()
                    self.fail('Invalid time frame saved.')
                LOG.debug(context_manager.exception)

    def test_parent_update_child(self):
        """ Assert updating the end_date of a parent also updates its children.
        """
        today = datetime.date.today()
        business = BUSINESS_FACTORY.create_business()
        slot = Slot.objects.create(site_id=2, business_id=business.id,
            start_date=today, end_date=today + datetime.timedelta(1))
        child_slot = Slot.objects.create(site_id=2, business_id=business.id,
            start_date=today, end_date=today + datetime.timedelta(1),
            parent_slot=slot)
        slot.end_date = today + datetime.timedelta(2)
        slot.save()
        child_slot = Slot.objects.get(id=child_slot.id)
        self.assertEqual(slot.end_date, child_slot.end_date)

    def test_get_active_coupon(self):
        """ Assert the current coupon of a slot is selected. """
        coupon = COUPON_FACTORY.create_coupon()
        slot = SLOT_FACTORY.create_slot(coupon=coupon)
        future_date = datetime.date.today() + datetime.timedelta(weeks=1)
        coupon.expiration_date = future_date
        coupon.save()
        self.assertEqual(slot.get_active_coupon(), coupon)

    def test_get_active_coupon_bad(self):
        """ Assert a slot with an expired coupon returns None. """
        coupon = COUPON_FACTORY.create_coupon()
        slot = SLOT_FACTORY.create_slot(coupon=coupon)
        coupon.expiration_date = (datetime.date.today() -
            datetime.timedelta(weeks=1))
        coupon.save()
        self.assertEqual(slot.get_active_coupon(), None)


class TestSlotModelFlyerPlacement(TestCase):
    """ Test case for cleaning of slots with flyer placements. """

    def test_slot_flyer_placem_good(self):
        """ Assert a slot with flyer placements passes clean. """
        slot = SLOT_FACTORY.create_slot()
        FlyerPlacement.objects.create(site_id=2, slot=slot,
            send_date=next_flyer_date())
        try:
            slot.clean()
        except ValidationError:
            self.fail('Slot with a flyer placement failed cleaning.')

    def test_slot_flyer_placem_bad(self):
        """ Assert a slot with flyer placements cannot change sites. """
        slot = SLOT_FACTORY.create_slot()
        FlyerPlacement.objects.create(site_id=2, slot=slot,
            send_date=next_flyer_date())
        slot.site_id = 3
        with self.assertRaises(ValidationError) as context_manager:
            slot.clean()
            self.fail('Slot with a flyer placement changed site.')
        LOG.debug(context_manager.exception)


class TestCalculateNextEndDate(TestCase):
    """ Tests for slot.calculate_end_date(). """
    
    def test_calculate_next_end_date(self):
        """ Assert slot end date calculated correctly. """
        site = Site.objects.get(id=2)
        business = BUSINESS_FACTORY.create_business()
        slot = Slot(site=site, business=business)
        slot.start_date = datetime.date(2010, 12, 31)
        slot.end_date = datetime.date(2011, 01, 31)
        slot.save()
        slot.end_date = slot.calculate_next_end_date()
        self.assertEqual(slot.end_date, datetime.date(2011, 02, 28))
        slot = slot.save()
        slot.end_date = slot.calculate_next_end_date()
        self.assertEqual(slot.end_date, datetime.date(2011, 03, 31))
        slot = slot.save()
        slot.end_date = slot.calculate_next_end_date()
        self.assertEqual(slot.end_date, datetime.date(2011, 04, 30))
