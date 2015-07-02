""" Views for  default and custom restrictions for the coupon app. """

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from advertiser.business.tasks import take_web_snap
from common.session import delete_key_from_session, parse_curr_session_keys
from coupon.forms import (RestrictionsForm, get_restrictions_initial_data,
    ValidDaysForm, get_valid_days_initial_data)
from coupon.models import Coupon
from coupon.service.single_coupon_service import SINGLE_COUPON
from coupon.service.restrictions_service import COUPON_RESTRICTIONS
from coupon.service.valid_days_service import VALID_DAYS
from ecommerce.service.locking_service import (get_locked_data,
    get_incremented_pricing)
from ecommerce.service.product_list import set_selected_product
from ecommerce.service.calculate_current_price import get_product_price

from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)
    
def show_create_restrictions(request):
    """ Allows advertiser to specify coupon restrictions. """
    try:
        session_dict = parse_curr_session_keys(request.session, 
            ['this_business', 'this_offer'])
        business = session_dict['this_business']
        offer = session_dict['this_offer']
        site = get_current_site(request)
        slot_price, locked_flyer_price, locked_consumer_count = \
            get_locked_data(request, site)
    except KeyError:
        return HttpResponseRedirect(reverse('advertiser-registration'))
    annual_slot_price = get_product_price(3, site)
    context_dict = {}
    context_instance_dict = {'js_create_restrictions':1,
                'business_name':business['business_name'],
                'slogan':business['slogan'],
                'headline':offer['headline'],
                'qualifier':offer['qualifier'],
                'slot_price':slot_price,
                'locked_flyer_price':locked_flyer_price,
                'locked_consumer_count':locked_consumer_count,
                'annual_slot_price':annual_slot_price}
    context_instance_dict.update(get_incremented_pricing(locked_consumer_count))
    if request.method == 'POST':
        return process_create_restrictions(request, 
            created_redirect=reverse('checkout-coupon-purchase'), 
            required_fields_not_filled_out='coupon/display_create_restrictions.html', 
            context_instance=RequestContext(request, context_instance_dict))  
    else:
        try:
            session_dict = parse_curr_session_keys(request.session, 
                ['coupon_id', 'this_coupon'])
            coupon = Coupon.objects.get(id=session_dict['coupon_id'])
            # Remove 'add_locations' key from session. No longer needed.
            delete_key_from_session(request, 'add_location')
            context_dict.update(SINGLE_COUPON.set_single_coupon_dict(
                request, coupon))
            # Display the Offer Creation restrictions_form.
            restrictions_intial_dict = \
                get_restrictions_initial_data(session_dict['this_coupon'])
            restrictions_form = \
                RestrictionsForm(initial=restrictions_intial_dict)
            valid_days_initial_dict = \
                get_valid_days_initial_data(session_dict['this_coupon'])
            valid_days_form = ValidDaysForm(initial=valid_days_initial_dict) 
            context_dict.update({'restrictions_form':restrictions_form,
                        'valid_days_form':valid_days_form})
            return render_to_response('coupon/display_create_restrictions.html', 
                context_dict, 
                context_instance=RequestContext(request, context_instance_dict))
        except KeyError:
            return HttpResponseRedirect(reverse('advertiser-registration')) 

def process_create_restrictions(request, created_redirect, 
        required_fields_not_filled_out, context_instance):
    """ Save configured coupon restrictions. """
    # Populate the RestrictionsForm.
    restrictions_form = RestrictionsForm(request.POST)
    valid_days_form = ValidDaysForm(request.POST)  
    # Check all required fields are filled out.
    if restrictions_form.is_valid() and valid_days_form.is_valid():
        try:
            session_dict = parse_curr_session_keys(request.session, 
            ['this_business', 'this_offer', 'this_coupon', 'coupon_id'])
            # Use cleaned_data
            restrictions_cleaned_data = restrictions_form.cleaned_data 
            valid_days_cleaned_data = valid_days_form.cleaned_data
            # Get coupon_id from session.
            # Check coupon exists.
            coupon = Coupon.objects.get(
                id=session_dict['this_coupon']['coupon_id'])
            COUPON_RESTRICTIONS.check_redeemed_by_sms_changes(
                restrictions_cleaned_data, coupon, session_dict['this_coupon'])
            COUPON_RESTRICTIONS.check_for_restriction_changes(
                restrictions_cleaned_data, coupon, session_dict['this_coupon'])    
            VALID_DAYS.check_for_valid_days_changes(valid_days_cleaned_data, coupon, 
                session_dict['this_coupon'])
            # Web Snap.
            if coupon.offer.business.web_url: 
                if settings.CELERY_ALWAYS_EAGER is False:
                    take_web_snap.delay(coupon.offer.business)
            #add_slot_choice of 0 will only add a slot to the products list 
            #calculations and create list of products in session.
            if request.session.get('ad_rep_id', False):
                # Set default product selection for ad rep in session.
                set_selected_product(request, 2)
            else:
                set_selected_product(request, 2)
            # Session has been modified, save the session.
            request.session.modified = True
            coupon.save()
        except Coupon.DoesNotExist:
            return HttpResponseRedirect(reverse('all-coupons'))
        return HttpResponseRedirect(created_redirect)   
    else:
        context_dict = {'restrictions_form':restrictions_form,
                        'valid_days_form':valid_days_form}
        # All required fields are not filled out. Return to page with form data.
        return render_to_response(required_fields_not_filled_out, 
            context_dict, 
            context_instance=context_instance)