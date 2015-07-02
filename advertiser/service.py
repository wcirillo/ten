""" Service functions of advertiser app. """

import datetime
from esapi.core import ESAPI
from esapi.validation_error_list import ValidationErrorList
import logging

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect

from advertiser.models import Advertiser, Business
from common.session import (check_if_i_own_this_coupon, get_this_coupon_data,
    check_if_i_own_this_business, create_consumer_from_adv,
    add_update_business_session, build_advertiser_session,
    check_advertiser_owns_business, check_for_unpublished_offer)
from consumer.models import Consumer
from coupon.models import Coupon, Slot
from coupon.service.expiration_date_service import (
    frmt_expiration_date_for_dsp, default_expiration_date)
from coupon.service.slot_service import (check_available_family_slot, 
    publish_business_coupon)
from coupon.service.valid_days_service import VALID_DAYS
from coupon.tasks import send_coupon_published_email
from ecommerce.models import OrderItem
from ecommerce.service.product_list import set_selected_product

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def process_update_advertiser(request, advertiser, proxy_advertiser):
    """ Update the advertiser, if there is something filled into the fields.
    Since this advertiser already exists, don't want to update certain values
    unless they exist on the form to avoid wiping out valid information that the
    advertiser might have filled out another time.
    """
    save_advertiser = False
    if proxy_advertiser.advertiser_name:
        save_advertiser = True
    advertiser.advertiser_name = proxy_advertiser.advertiser_name
    # Only update the phone number if exchange and number are fully
    # filled out.
    if len(proxy_advertiser.advertiser_exchange) == 3 \
    and len(proxy_advertiser.advertiser_number) == 4:
        for field in ['advertiser_area_code', 'advertiser_exhange',
                'advertiser_number']:
            setattr(advertiser, field, getattr(proxy_advertiser, field))
        save_advertiser = True
    if save_advertiser:
        advertiser.save()
    # Advertiser exists in database but not in current session!
    build_advertiser_session(request, advertiser)
    business_exists_for_advertiser = check_advertiser_owns_business(
        request, proxy_advertiser.business_name)
    if business_exists_for_advertiser:
        # Check if this business has an unpublished offer. If
        # unpublished offer is found, set the current_offer
        # position pointer to that offer, otherwise set it to the next
        # offer in line starting at the current_coupon = 0
        # An unpublished offer is defined as an offer that was created
        # and a published coupon is not associated with it.
        business = advertiser.businesses.filter(
            business_name=proxy_advertiser.business_name)[0]
        (business_has_offer, business_has_unpublished_offer,
                offer_has_coupon_association) = check_for_unpublished_offer(
                    request, delete_keys=False)
        if (business_has_offer and business_has_unpublished_offer
            and offer_has_coupon_association
        ) or (business_has_offer and not business_has_unpublished_offer
            and not offer_has_coupon_association):
            # Before we jump to preview edit, check if the slogan for
            # this business has been filled out. If so, update it. If
            # if wasn't filled out, don't overwrite a possible good
            # slogan for this business.
            if proxy_advertiser.slogan != '':
                business.slogan = proxy_advertiser.slogan
                business.save()
                add_update_business_session(request, business)
            redirect_path = registration_parent_redirect(request, business.id)
            if not redirect_path:
                redirect_path = reverse('preview-coupon')
            return HttpResponseRedirect(redirect_path)
        else:
            # Since we didn't jump to preview edit, check if the slogan
            # has changed. Update it accordingly.
            if business.slogan != proxy_advertiser.slogan:
                business.slogan = proxy_advertiser.slogan
                business.save()
                add_update_business_session(request, business)
    else:
        business = Business.objects.create(advertiser_id=advertiser.id,
            business_name=proxy_advertiser.business_name,
            short_business_name=proxy_advertiser.business_name[:25],
            slogan=proxy_advertiser.slogan)
        add_update_business_session(request, business)
        # Check for any other businesses with unpaid coupons

def process_create_advertiser(request, site, proxy_advertiser):
    """ Process registration for a new advertiser. """
    try:
        # Check if consumer exists already
        consumer = Consumer.objects.get(email__iexact=proxy_advertiser.email)
        # Associate this consumer with advertiser
        advertiser = Advertiser.objects.create_advertiser_from_consumer(
            consumer, advertiser_name=proxy_advertiser.advertiser_name,
            advertiser_area_code=proxy_advertiser.advertiser_area_code,
            advertiser_exchange=proxy_advertiser.advertiser_exchange,
            advertiser_number=proxy_advertiser.advertiser_number)
    except Consumer.DoesNotExist:
        advertiser = Advertiser.objects.create(username=proxy_advertiser.email,
           email=proxy_advertiser.email.strip().lower(),
           advertiser_name=proxy_advertiser.advertiser_name,
           advertiser_area_code=proxy_advertiser.advertiser_area_code,
           advertiser_exchange=proxy_advertiser.advertiser_exchange,
           advertiser_number=proxy_advertiser.advertiser_number,
           last_login=datetime.datetime.now(),
           date_joined=datetime.datetime.now(),
           site=site)
        advertiser.email_subscription.add(2)
        advertiser.email_subscription.add(4)
        advertiser.set_unusable_password()
        advertiser.save()
    # Subscribe this advertiser to EmailSubscription 'Email'
    # Note: this is being done in this spot to handle the case of
    # whether or not a consumer existed already.  Even if a consumer
    # existed and we created the advertiser from consumer, there is a
    # chance that advertiser may have opted out in the past.  So, we
    # want to make sure they get opted back in!
    advertiser.email_subscription.add(1)
    business = Business.objects.create(advertiser_id=advertiser.id,
        business_name=proxy_advertiser.business_name,
        short_business_name=proxy_advertiser.business_name[:25],
        slogan=proxy_advertiser.slogan)
    # If advertiser doesn't exist, create a new advertiser.
    create_consumer_from_adv(request, advertiser)
    add_update_business_session(request, business)
    return advertiser

def clean_adv_acct_post_data(request):
    """
    Clean the data posted to the advertiser account view.    
    
    business_id = The business we are working with.
    ajax_mode = The flavor of what we are doing.    
    coupon_id = The coupon we are turning on or off for a slot.
    headline = The headline of the coupon.
    """
    instance = ESAPI.validator()
    error_list = ValidationErrorList()
    temp_headline = request.POST.get('headline', None)
    if temp_headline:
        for char in temp_headline:
            if ord(char) > 127:
                temp_headline = 'Your coupon'
                break
    clean_data = {
        'business_id': instance.get_valid_number('business_id', int, 
            request.POST.get('business_id', None), 1, 999999, True, error_list),
        'ajax_mode': instance.get_valid_input('ajax_mode',
            request.POST.get('ajax_mode', None), 'SafeDisplay', 24,
            True, error_list),
        'coupon_id': instance.get_valid_number('coupon_id', int, 
            request.POST.get('coupon_id', None), 1, 999999, True, 
            error_list),
        'display_id': instance.get_valid_number('display_id', int, 
            request.POST.get('display_id', None), 1, 999999, True, 
            error_list),
        'headline': instance.get_valid_input('headline', 
            temp_headline, 'SafeDisplay', 100, True,
            error_list),
         }
    if len(error_list):
        LOG.error(error_list)
    return clean_data, error_list

def get_adv_acct_business(clean_data, all_slot_coupons, this_advertiser):
    """
    Select a business for display on the advertiser account view.
    """
    business_id = clean_data['business_id']
    if business_id:
        business = Business.objects.get(id=business_id)
    elif all_slot_coupons:
        # Select the business with the most recently added slot_time_frame.
        business = Business.objects.filter(
            slots__slot_time_frames__coupon=all_slot_coupons.latest(
                'slot_time_frames'))[0]
    else:
        # No slots for this advertiser.
        # Select the last business in session.
        these_businesses = this_advertiser['business'] 
        business_count = len(these_businesses)
        business_id = these_businesses[business_count-1]['business_id']
        business = Business.objects.get(id=business_id)
    return business

def get_slot_time_frame(slot, slot_coupon):
    """ Return the first slot_time_frame for this slot and this coupon in a
    slot_time_frame of the slot.

    Raises an IndexError if there are no matching slot_time_frames.

    Fuzz 'now' to this hour to allow for query caching, else this query will
    *always* be unique.

    Assumes all slot time frames have already started.
    """
    hour_future = datetime.datetime.now() + datetime.timedelta(0, 0, 0, 0, 0, 1)
    return slot.slot_time_frames.filter(
        Q(end_datetime__gt=hour_future) | Q(end_datetime=None),
        coupon=slot_coupon)[0]

def get_adv_acct_context(business, all_coupons, all_slot_coupons):
    """
    Build and return the context dictionary for the advertiser account view.
    """
    context_dict = {}
    # Business Coupons and slots
    all_coupons_this_biz = all_coupons.filter(offer__business=business)
    slot_items_list = []
    # All Open Slots for this business
    for slot in Slot.objects.filter(business=business,
            start_date__lte=datetime.date.today(),
            end_date__gte=datetime.date.today()).order_by('id'):
        no_coupon_for_slot = True
        is_parent_slot = False
        if slot == slot.parent_slot:
            is_parent_slot = True
        purchased_flyers_count = OrderItem.objects.filter(
            item_id=slot.id, product=1, content_type__model='slot').count()
        slot_items_dict = {'is_parent_slot':is_parent_slot,
            'purchased_flyers_count':purchased_flyers_count}
        try: # Do this only if slot is purchased coupon
            slot_items_dict['product_id'] = OrderItem.objects.filter(
                item_id=slot.id, content_type__model='slot')[0].product.id
        except IndexError:
            pass
        for slot_coupon in all_slot_coupons.filter(offer__business=business):
            try:
                get_slot_time_frame(slot, slot_coupon)
                # Found a slot for this coupon
                slot_coupon.valid_days = \
                    VALID_DAYS.create_valid_days_string(slot_coupon)
                slot_coupon.expiration_date = frmt_expiration_date_for_dsp(
                    slot_coupon.expiration_date)
                slot_items_dict.update({'slot':slot, 'coupon':slot_coupon})
                slot_items_list.append(slot_items_dict)
                all_coupons_this_biz = all_coupons_this_biz.exclude(
                    id=slot_coupon.id)
                no_coupon_for_slot = False
            except IndexError:
                # This coupon has no time frame associated with it.
                pass
        if no_coupon_for_slot and is_parent_slot:
            # This Slot has no coupon associated with it.
            if is_parent_slot:
                slot_items_dict.update({'slot':slot})
                slot_items_list.append(slot_items_dict)
    no_slot_coupons = all_coupons_this_biz
    for coupon in no_slot_coupons:
        coupon.valid_days = VALID_DAYS.create_valid_days_string(coupon)
        coupon.expiration_date = frmt_expiration_date_for_dsp(
            coupon.expiration_date)
    context_dict.update({'slot_items_list': slot_items_list,
        'no_slot_coupons': no_slot_coupons})
    return context_dict

def get_meta_for_business(business, all_locations):
    """
    Get meta page title and description for this business to display on
    all-coupons-this-business page. If no locations, use market-region. If
    multiple locations use first one.
    """
    meta_dict = {'title':'', 'desc': ''}
    loc_flag = False
    for location in all_locations:
        if location.get_coords():
            meta_dict['title'] = location.location_city.strip()
        if meta_dict['title'] != '':
            loc_flag = True
            meta_dict['desc'] = ('%s coupons in %s, %s.' % (
                business.business_name, location.location_city.strip(),
                location.location_state_province)).replace(' ,', '').replace(
                ', .', '.').strip()
            break
    meta_dict['title'] = ('%s, %s' % (business.business_name,
        meta_dict['title'])).strip()
    if not loc_flag:
        # Default location to market region.
        meta_dict['title'] += ' %s' % business.advertiser.site.region
        meta_dict['desc'] = '%s coupons in the %s.' % (
            business.business_name, business.advertiser.site.region)
    meta_dict['desc'] = ('%s %s' % (meta_dict['desc'].strip(),
        business.get_business_description()[:159-len(
        meta_dict['desc'])])).strip()
    return meta_dict

def json_turn_display_on_handler(request, clean_data):
    """
    Return json data for 'json-off' mode. No longer display this coupon.
    Close the time frame for this slot/coupon.
    """
    if clean_data['coupon_id'] and clean_data['business_id'] \
    and check_if_i_own_this_business(request, clean_data['business_id']) \
    and check_if_i_own_this_coupon(request, clean_data['coupon_id']):
        family_availability_dict = check_available_family_slot(
                                    business_id=clean_data['business_id'])
        if family_availability_dict['available_parent_slot']:
            coupon = Coupon.objects.get(id=clean_data['coupon_id'])
            this_coupon, expiration_date = get_this_coupon_data(request)[1:3]
            coupon.coupon_type_id = 3
            coupon.save()
            this_coupon['coupon_type_id'] = 3
            request.session.modified = True
            today = datetime.date.today()
            if expiration_date < today:
                # This coupon is expired... Bump the expiration_date up
                # 90 days from today.
                expiration_date = default_expiration_date()
                coupon.expiration_date = expiration_date
                coupon.save()
                this_coupon['expiration_date'] = expiration_date
            slot = publish_business_coupon(family_availability_dict, coupon)
            # Send email to staff that someone just published a coupon.
            send_coupon_published_email.delay(coupon=coupon, just_created=False)
            json_data = {'msg': '%s is now displayed.' % clean_data['headline'],
                'new_display_id': slot.id,
                'expiration_date':frmt_expiration_date_for_dsp(expiration_date)}
        else:
            # add_slot_choice of 0 will only add a slot to the products list
            # calculations and create list of products to be purchased.
            set_selected_product(request, 2)
            json_data = {'has_full_family':True}
    else:
        json_data = {'msg': 'You are restricted to do anything with this coupon!'}
    return json_data

def json_turn_display_off_handler(request, clean_data):
    """
    Return json data for 'json-off' mode. No longer display this coupon.
    Close the time frame for this slot/coupon.
    """
    now = datetime.datetime.now()
    if clean_data['coupon_id'] and clean_data['display_id'] \
    and check_if_i_own_this_coupon(request, clean_data['coupon_id']):
        coupon = Coupon.objects.get(id=clean_data['coupon_id'])
        slot_time_frames = coupon.slot_time_frames.filter(
            Q(end_datetime__gt=now) | Q(end_datetime=None),
            start_datetime__lt=now, slot=clean_data['display_id'])
        # Business Rules state that only one time_frame can be open at
        # a time for this slot. Close it.
        try:
            slot_time_frames[0].close_this_frame_now()
            msg = '%s has been removed.' % (clean_data['headline'])
        except IndexError:
            msg = ''
    else:
        msg = 'You are restricted to do anything with this coupon!'
    return {'msg':msg}

def get_adv_acct_json_data(request, clean_data, business):
    """
    Produce json for advertiser account view.

    'msg' in json is the message displayed in the "growler."
    """
    if clean_data['ajax_mode'] == 'turn-display-on':
        #json_data = json_bucket_handler(request, clean_data)
        json_data = json_turn_display_on_handler(request, clean_data)
    elif clean_data['ajax_mode'] == 'turn-display-off':
        json_data = json_turn_display_off_handler(request, clean_data)
    elif clean_data['ajax_mode'] in ('turn-autorenew-on', 'turn-autorenew-off'):
        slot_id = clean_data['display_id']
#    elif clean_data['ajax_mode'] == 'available':
#        json_data = json_available_handler(request, clean_data, business)
        # Cannot modify a slot of a different business.
        try:
            slot = business.slots.get(id=slot_id)
            if clean_data['ajax_mode'] == 'turn-autorenew-on':
                is_autorenew = True
                msg = 'Auto Renew is now ON'
            else:
                is_autorenew = False
                msg = 'Auto Renew is now OFF'
            slot.is_autorenew = is_autorenew
            slot.save()
            json_data = {'msg': msg}
        except Slot.DoesNotExist:
            json_data = {'msg': ''}
    else:
        json_data = {'msg': ''}
    return json_data

def registration_parent_redirect(request, business_id):
    """
    Check if this advertiser has current slots running and redirect to the
    appropriate places so child slots can get created for Free!
    """
    redirect_path = None
    if not request.user.is_authenticated():
        current_business_slots = Slot.current_slots.get_current_business_slots(
            business_id=business_id)
        if current_business_slots:
            try:
                advertiser = Advertiser.objects.get(
                    id=current_business_slots[0].business.advertiser.id)
                if advertiser.has_usable_password():
                    redirect_path = '%s?next=%s' % (reverse('sign-in'),
                        reverse('advertiser-registration'))
                else:
                    redirect_path = '%s?next=%s' % (reverse('forgot-password'),
                         reverse('advertiser-registration'))
            except Advertiser.DoesNotExist:
                redirect_path = reverse('contact-us')
    return redirect_path
