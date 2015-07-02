""" Slot Factory used to help create quick Slot/Coupon instances for tests. """
import datetime

from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.offer_factory import OFFER_FACTORY
from coupon.models import Slot, SlotTimeFrame

class SlotFactory(object):
    """ Slot Factory Class """
    
    @staticmethod
    def _create(business, parent_slot=None):
        """ Create a single slot instance. If no parent_slot is passed in,
        this slot will be created as a parent.  If a parent_slot is passed in,
        the slot will become a child of the parent. """
        slot = Slot.objects.create(business_id=business.id, 
            site_id=business.advertiser.site.id, 
            start_date=datetime.date(2011, 1, 1), 
            end_date=datetime.date(2099, 1, 1))
        if parent_slot:
            slot.parent_slot_id = parent_slot.id
        else:
            slot.parent_slot_id = slot.id
        slot.save()
        return slot
    
    def create_slot(self, slot=None, coupon=None, create_slot_time_frame=True):
        """ Create a ONE basic slot instance with a business and 
        advertiser association. """
        if not coupon:
            coupon = COUPON_FACTORY.create_coupon()
        if not slot:
            slot = self._create(business=coupon.offer.business)
        if create_slot_time_frame:
            SLOT_TIME_FRAME_FACTORY.create_slot_time_frame(
            slot, coupon)
        return slot
        
    def create_slots(self, create_count=1):
        """
        Create 1 or more slots and associate them with 
        different coupons -> businesses -> advertisers. 
            Ex: slot -> coupon -> offer -> business -> advertiser
                slot1 -> coupon1 -> offer1 -> business1 -> advertiser1
                slot2 -> coupon2 -> offer2 -> business2 -> advertiser2
                slot3 -> coupon3 -> offer3 -> business3 -> advertiser3
        """
        slot_list = []
        current_create_count = 0
        while current_create_count < create_count:
            slot = self.create_slot()
            current_create_count += 1
            slot_list.append(slot)
        return slot_list
    
    @staticmethod
    def get_active_coupons(slot_list):
        """ Create a list of running coupons from this slot_list. """
        coupon_list = []
        for slot in slot_list:
            coupon_list.append(slot.get_active_coupon())
        return coupon_list

    def create_slot_family(self, create_count=10):
        """ Create a parent with 1 to 9 children to ensure a full slot family
        has been established.
        """
        children_list = []
        offer_list = OFFER_FACTORY.create_offers(
            create_business=True,
            create_count=create_count)
        for index, offer in enumerate(offer_list):
            coupon = COUPON_FACTORY.create_coupons(offer=offer)[0]
            if index == 0:
                slot = self._create(business=coupon.offer.business)
                parent_slot = slot
                SLOT_TIME_FRAME_FACTORY.create_slot_time_frame(
                    slot=parent_slot,
                    coupon=coupon)
            else:
                child_slot = self._create(business=coupon.offer.business,
                    parent_slot=parent_slot)
                SLOT_TIME_FRAME_FACTORY.create_slot_time_frame(
                    slot=child_slot, coupon=coupon)
                children_list.append(child_slot)
        family_dict =  {'parent':parent_slot, 'children':children_list}
        children_list.append(parent_slot)
        slot_list = children_list
        return family_dict, slot_list

    @staticmethod
    def prepare_slot_coupons_for_flyer(slot_list, send_date=None):
        """ Approves the coupons in the slot time frame of these slots. """
        coupon_list = []
        for slot in slot_list:
            slot_time_frame = slot.slot_time_frames.latest('id')
            coupon = slot_time_frame.coupon
            coupon.is_approved = True
            coupon.save()
            coupon_list.append(coupon)
            if send_date:
                slot.start_date = send_date - datetime.timedelta(weeks=1)
                slot.save()
                slot_time_frame.start_datetime = datetime.datetime.combine(
                    slot.start_date, datetime.time())
                slot_time_frame.save()
        return coupon_list


class SlotTimeFrameFactory(object):
    """ SlotTimeFrame Factory Class """
    
    @staticmethod
    def _create(slot, coupon, 
            start_datetime=datetime.datetime.now(), 
            end_datetime=None):
        """ Create a single slot_time_frame instance for this slot and coupon.
        """
        SlotTimeFrame.objects.create(slot_id=slot.id,
            coupon_id=coupon.id,
            start_datetime = start_datetime,
            end_datetime=end_datetime)
        return slot
    
    def create_slot_time_frame(self, slot, coupon):
        """ Create a ONE basic running slot_time_frame instance with a 
        for a slot coupon. """
        slot_time_frame = self._create(slot, coupon)
        return slot_time_frame

    def create_expired_time_frame(self, slot, coupon, 
            start_datetime=datetime.datetime.now() - datetime.timedelta(
                days=25),
            end_datetime=datetime.datetime.now() - datetime.timedelta(
                days=1)):
        """ Create an expired slot_time_frame for a slot coupon. """
        slot_time_frame = self._create(slot, coupon,
            start_datetime, end_datetime)
        return slot_time_frame
    
    def create_future_time_frame(self, slot, coupon, 
            start_datetime=datetime.datetime.now() + datetime.timedelta(
                days=10),
            end_datetime=None):
        """ Create a future slot_time_frame for a slot coupon. """
        slot_time_frame = self._create(slot, coupon,
            start_datetime=start_datetime, 
            end_datetime=end_datetime)
        return slot_time_frame

SLOT_FACTORY = SlotFactory()
SLOT_TIME_FRAME_FACTORY = SlotTimeFrameFactory()
