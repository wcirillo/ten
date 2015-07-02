""" Views for adding slots to a business/advertiser. """

import datetime

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from common.session import (delete_key_from_session, parse_curr_session_keys,
    check_required_session_keys)
from coupon.decorators import i_own_this_coupon
from coupon.models import Coupon
from coupon.service.single_coupon_service import SINGLE_COUPON
from ecommerce.forms import AddSlotForm
from ecommerce.service.locking_service import (get_incremented_pricing, 
    set_flyers_context)
from ecommerce.service.product_list import set_selected_product
from market.service import get_current_site

def show_add_slot(request):
    """Displays the add_slot form. """
    delete_key_from_session(request, 'add_flyer_choice')
    if not check_required_session_keys(request, 
        ['locked_flyer_price', 'locked_consumer_count']):
        return HttpResponseRedirect(reverse('all-coupons'))
    context_instance_dict = {}
    if request.method == 'POST':
        return process_add_slot(request, 
            created_redirect=reverse('checkout-coupon-purchase'), 
            required_fields_not_filled_out='ecommerce/display_add_slot.html', 
            context_instance=RequestContext(request, context_instance_dict))  
    else:
        session_dict = parse_curr_session_keys(request.session, 
            ['business_id', 'coupon_id'])
        site = get_current_site(request)
        coupon = Coupon.objects.select_related(
            'offer', 'offer__business').get(id=session_dict['coupon_id'])
        today = datetime.date.today()
        business_active_slot_count = site.slots.filter(
            business__id=session_dict['business_id'],
            start_date__lte=today, end_date__gte=today).count()
        slot_coupons_count = Coupon.current_coupons. \
            get_current_coupons_by_site(site).filter(
                offer__business=session_dict['business_id']).count()
        if slot_coupons_count != business_active_slot_count \
        and request.user.is_authenticated():
            return HttpResponseRedirect(reverse('advertiser-account'))
        if business_active_slot_count > 0:
            # Give this user a way to create this coupon as a draft only!
            show_save_coupon_link = True
        else:
            # This advertiser must purchase a slot!
            show_save_coupon_link = False
        try:
            add_slot_choice = request.session['add_slot_choice']
            initial_data = {'add_slot_choices': add_slot_choice} 
        except KeyError:
            initial_data = {}
        add_slot_form = AddSlotForm(initial=initial_data)
        context_dict = {'add_slot_form': add_slot_form, 'site': site}
        context_instance_dict = {'js_add_slot': 1,
            'show_save_coupon_link': show_save_coupon_link}
        context_instance_dict.update(set_flyers_context(request, site))
        context_instance_dict.update(get_incremented_pricing( 
            request.session['locked_consumer_count']))
        context_instance_dict.update(SINGLE_COUPON.set_single_coupon_dict(
            request, coupon))
        return render_to_response(
            'ecommerce/display_add_slot.html', 
            context_dict, 
            context_instance=RequestContext(request, context_instance_dict))
        
def process_add_slot(request, created_redirect, 
        required_fields_not_filled_out, context_instance):
    """ Processes add slot form. """
    add_slot_form = AddSlotForm(request.POST) 
    # Check all required fields are filled out.
    if add_slot_form.is_valid():
        add_slot_choice = add_slot_form.cleaned_data.get(
            'add_slot_choices', None)       
        # Create the list of products that will be purchased with the associated
        # prices.      
        set_selected_product(request, 2, add_slot_choice)
        return HttpResponseRedirect(created_redirect)   
    else:
        context_dict = {'add_slot_form':add_slot_form}
        return render_to_response(required_fields_not_filled_out, 
            context_dict, 
            context_instance=context_instance)

@i_own_this_coupon()
def show_add_a_new_display(request, coupon_id):
    """ Add a display when coming from the advertiser account. This occurs when you 
    Drag & Drop a coupon into the add display. 
    """
    return show_add_slot(request)
