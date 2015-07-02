""" Service functions for slot models of coupon app. """

import datetime
import logging

from django.db.models import Q

from coupon.models import Slot, SlotTimeFrame

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def close_slot_open_time_frame(slot):
    """ Given a slot, close the open time frame of it. A slot has at most one
    open time frame.
    """
    now = datetime.datetime.now()
    slot_time_frames = SlotTimeFrame.objects.filter(
        Q(end_datetime__gt=now) | Q(end_datetime=None),
        start_datetime__lt=now, slot=slot)
    if slot_time_frames:
        slot_time_frames[0].close_this_frame_now()

def create_business_families_list(business_id):
    """ Create a list of dictionaries each holding a slot family for all
    current families this business owns. A parent has from 0 to 9 children.
    Example:
    [{'parent':<Slot: Slot 357 on Hudson Valley>, 
      'children':[<Slot: Slot 358 on Hudson Valley>,
                <Slot: Slot 359 on Hudson Valley>,
                <Slot: Slot 360 on Hudson Valley>,
                <Slot: Slot 361 on Hudson Valley>,
                <Slot: Slot 362 on Hudson Valley>,
                <Slot: Slot 363 on Hudson Valley>,
                <Slot: Slot 364 on Hudson Valley>,
                <Slot: Slot 365 on Hudson Valley>,
                <Slot: Slot 366 on Hudson Valley>]},
     {'parent':<Slot: Slot 370 on Hudson Valley>,
      'children':[<Slot: Slot 375 on Hudson Valley>,
                <Slot: Slot 381 on Hudson Valley>,
                <Slot: Slot 398 on Hudson Valley>]},
     {'parent':<Slot: Slot 410 on Hudson Valley>, 
      'children':[]}
    ]
    """
    all_families_list = []
    current_parent_slots, current_children_slots = \
            Slot.current_slots.get_current_family_slots(business_id=business_id)
    for parent_slot in current_parent_slots:
        children_list = []
        for child_slot in current_children_slots:
            if parent_slot == child_slot.parent_slot:
                children_list.append(child_slot)
        family_dict =  {'parent':parent_slot, 'children':children_list}
        all_families_list.append(family_dict)
    LOG.debug('all_families_list: %s' % all_families_list)
    return all_families_list

def check_available_family_slot(business_id):
    """ Check if any family slot member does not have a current time frame.
    If all parents and children have current time frames, check if a new child
    needs to get created for a parent who has less than 9 children in their
    family. If none of these are true, a new parent will have to get created.
    - A family can have a max of 10 members
    - 1 parent + (9 children max)/(0 children min)
    - 1 business can have multiple families
    We should always max out the number of children in the oldest family before
    we create/update another younger family.
    """
    publish_to_parent = False
    publish_to_child = False
    available_parent_slot = None
    available_child_slot = None
    for family in create_business_families_list(business_id=business_id):
        LOG.debug('family: %s' % family)
        if not family['parent'].has_active_time_frame():
            publish_to_parent = True
            available_parent_slot = family['parent']
            break
        for child in family['children']:
            if not child.has_active_time_frame():
                publish_to_child = True
                available_parent_slot = family['parent']
                available_child_slot = child
                break
        # Prefer early family children over later family parents.
        if publish_to_child:
            break
        if len(family['children']) < 9:
            available_parent_slot = family['parent']
            break
    family_availability_dict = {
        'available_parent_slot':available_parent_slot,
        'available_child_slot':available_child_slot,
        'publish_to_parent':publish_to_parent,
        'publish_to_child':publish_to_child}
    return family_availability_dict

def publish_business_coupon(family_availability_dict, coupon):
    """
    Do 1 of 3 things here.
    1.) Use existing parent_slot to put this coupon live.
    2.) Use existing child_slot to put this coupon live.
    3.) Create a new child_slot to put this coupon live because no other
        slot is empty/available for this business.
    We never should be calling this function if a new parent needs to 
    be created.
    """
    available_parent_slot = family_availability_dict['available_parent_slot']
    available_child_slot = family_availability_dict['available_child_slot']
    publish_to_parent = family_availability_dict['publish_to_parent']
    publish_to_child = family_availability_dict['publish_to_child']
    if available_child_slot:
        # Unused child slot exists already for this business that has an 
        #slot.end_date that hasn't closed yet.
        available_child_slot.site_id = available_parent_slot.site_id
        available_child_slot.end_date = available_parent_slot.end_date
        slot = available_child_slot
    if publish_to_parent:
        # Unused Parent slot exists already.
        slot = available_parent_slot
    if not publish_to_parent and not publish_to_child:
        # Create new child
        slot = Slot(site_id=available_parent_slot.site_id, 
            business_id=available_parent_slot.business_id,
            renewal_rate=None, 
            is_autorenew=False,
            parent_slot=available_parent_slot,
            end_date=available_parent_slot.end_date)
    slot.save()
    slot_time_frame = SlotTimeFrame(slot_id=slot.id, 
        coupon_id=coupon.id)
    slot_time_frame.save()
    return slot

