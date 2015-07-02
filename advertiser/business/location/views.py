""" Views for locations of a business of an advertiser. """

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from advertiser.models import Business
from advertiser.business.forms import WebURLForm
from advertiser.business.location.forms import (CreateLocationForm,
    get_location_initial_dict)
from advertiser.business.location.service import create_location_ids_list
from coupon.config import TEN_COUPON_RESTRICTIONS
from coupon.models import Coupon, CouponType, Offer
from coupon.service.single_coupon_service import SINGLE_COUPON
from common.session import (add_coupon_to_offer_in_session,
    add_update_business_session, parse_curr_session_keys)
from ecommerce.service.locking_service import (get_locked_data,
    get_incremented_pricing)
from ecommerce.service.calculate_current_price import get_product_price

from market.service import get_current_site

def show_create_location(request):
    """ This displays the create_location_form for the 1st Location. """
    try:
        session_dict = parse_curr_session_keys(request.session, 
            ['this_business', 'this_offer'])
        business_name = session_dict['this_business']['business_name']
        slogan = session_dict['this_business']['slogan']
        headline = session_dict['this_offer']['headline']
        qualifier = session_dict['this_offer']['qualifier']
        expiration_date = request.session.get('expiration_date', None)
        site = get_current_site(request)
        annual_slot_price = get_product_price(3, site)
        slot_price, locked_flyer_price, locked_consumer_count = \
                                                get_locked_data(request, site)
        # context_instance_dict holds the values that will be passed in the get 
        # and post. They will be passed into the context_instance.
        context_instance_dict = {'js_create_location':1,
                'business_name':business_name,
                'slogan':slogan,
                'headline':headline,
                'qualifier':qualifier,
                'expiration_date':expiration_date,
                'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS,
                'slot_price':slot_price,
                'locked_flyer_price':locked_flyer_price,
                'locked_consumer_count':locked_consumer_count,
                'annual_slot_price': annual_slot_price}
        context_instance_dict.update(
            get_incremented_pricing(locked_consumer_count))
        if request.method == 'POST':
            return process_create_location(request, 
                created_redirect=reverse('create-restrictions'), 
                required_fields_not_filled_out= \
                    'advertiser/business/location/display_create_location.html', 
                context_instance = RequestContext(request, 
                                                  context_instance_dict))  
        else:
            try:
                # If we already created the coupon object that means this is 
                # at least the second time in this process so we can display 
                # the location on the coupon.
                session_dict = parse_curr_session_keys(request.session, 
                    ['coupon_id'])
                coupon = Coupon.objects.get(id=session_dict['coupon_id'])
                # Concatenate the 2 dictionaries.
                context_dict = SINGLE_COUPON.set_single_coupon_dict(request, coupon)
            except KeyError:
                context_dict = {}
            try:
                web_url_initial_dict = {'web_url':
                    session_dict['this_business']['web_url']}
                location_initial_dict = get_location_initial_dict(request)
                web_url_form = WebURLForm(initial=web_url_initial_dict)
                create_location_form = CreateLocationForm(
                    initial=location_initial_dict, site=site)
            except KeyError:
                # Display the Location Creation form.
                web_url_form = WebURLForm()
                create_location_form = CreateLocationForm(site=site) 
            context_dict.update({'web_url_form': web_url_form,
                'create_location_form': create_location_form,})   
            return render_to_response(
                'advertiser/business/location/display_create_location.html', 
                context_dict, 
                context_instance=RequestContext(request, 
                                                context_instance_dict))
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons'))  

def process_create_location(request, created_redirect, 
        required_fields_not_filled_out, context_instance):
    """ Process for frm_create_location.html """
    # Populate the Forms.
    site = get_current_site(request)
    web_url_form = WebURLForm(request.POST) 
    create_location_form = CreateLocationForm(data=request.POST, site=site)
    context_dict = {}
    try:
        # Get business_id from session.
        session_dict = parse_curr_session_keys(request.session, 
            ['business_id', 'offer_id'])
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons')) 
    try:
        business = Business.objects.get(id=session_dict['business_id'])
    except Business.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons')) 
    try:    
        offer = Offer.objects.get(id=session_dict['offer_id'])
        # Set coupon_type = 1 is set for "In Progress"
        coupon_type = CouponType.objects.get(id=1)
        sms = offer.headline + ' ' + offer.business.get_short_business_name()
    except Offer.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons')) 

    # Check all required fields are filled out.
    if create_location_form.is_valid() and web_url_form.is_valid():
        # Clean all form data.
        web_url = web_url_form.cleaned_data.get('web_url', None)
        if web_url:
            business.web_url = web_url
            business.save()
            add_update_business_session(request, business)
        try:
            session_dict = parse_curr_session_keys(
                request.session, ['coupon_id'])
            coupon = Coupon.objects.get(id=session_dict['coupon_id']) 
            business_loc_ids = [id_dict['id'] for id_dict in 
                                coupon.offer.business.locations.values(
                                                        'id').order_by('id')]
            business_loc_count = len(business_loc_ids)
            
            if business_loc_count == 0:
                # This business has no locations yet.  If locations got posted,
                # add them to the business and the coupon in the db and 
                # session.
                create_location_form.add_business_coupon_locations(request, 
                                                                   coupon)
                add_coupon_to_offer_in_session(request, coupon)
            else:
                location_count, location_number_list = \
                                        create_location_form.locations_posted()
                if location_count == business_loc_count:
                    location_ids_list = create_location_ids_list(business_loc_ids, 
                                                        location_number_list)
                    create_location_form.update_all_business_locations(request, 
                                                                location_ids_list)
                else:
                    if location_count > business_loc_count:
                        # More locations got POSTed compared to how many is 
                        # associated with this business already.
                        # Update all existing locations and add a few new ones.
                        update_loc_number_list = \
                                        location_number_list[:business_loc_count]
                        location_ids_list = create_location_ids_list(
                                        business_loc_ids, update_loc_number_list)
                        create_location_form.update_all_business_locations(
                                                    request, location_ids_list)
                        add_loc_number_list = \
                                        location_number_list[business_loc_count:]
                        create_location_form.create_business_locations(request, 
                                                    coupon, add_loc_number_list)
                    else:
                        # Update the first x amount of locations and make sure 
                        # only those locations get added to the coupon.
                        business_loc_ids_list = business_loc_ids[:location_count]
                        location_ids_list = create_location_ids_list(
                                    business_loc_ids_list, location_number_list)
                        create_location_form.update_all_business_locations(
                                                    request, location_ids_list)
                        coupon.location = business_loc_ids_list
                        add_coupon_to_offer_in_session(request, coupon)
            return HttpResponseRedirect(created_redirect) 
        except KeyError:
            # First time this form was submitted.  This is where we 
            # create the coupon in the database for the 1st time!
            coupon = Coupon(
                offer_id=offer.id, coupon_type=coupon_type, sms=sms,
                expiration_date= \
                    request.session.get('expiration_date')
                )
            coupon.save()          
            add_coupon_to_offer_in_session(request, coupon) 
            create_location_form.add_business_coupon_locations(request, coupon)
            add_coupon_to_offer_in_session(request, coupon) 
            return HttpResponseRedirect(created_redirect) 
    else:          
        context_dict.update({'web_url_form': web_url_form,
            'create_location_form': create_location_form})
        # All required fields are not filled out. Return to page with form data.
        return render_to_response(required_fields_not_filled_out, 
            context_dict, context_instance=context_instance)