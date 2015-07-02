""" Views for adding slots to a business/advertiser """

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from common.custom_format_for_display import list_as_text
from common.session import (delete_key_from_session,
    check_required_session_keys, check_if_i_own_this_coupon,
    delete_all_session_keys_in_list)
from consumer.service import build_consumer_count_list
from coupon.decorators import i_own_this_active_coupon_slot
from coupon.forms import (AddFlyerDatesForm, AddFlyerByMapForm,
    AddFlyerByListForm)
from coupon.models import Slot
from coupon.service.flyer_service import (set_subdivision_dict,
    get_subdivision_consumer_count, get_available_flyer_dates,
    get_subdivision_dict)
from coupon.service.single_coupon_service import SINGLE_COUPON
from ecommerce.service.locking_service import set_locked_data
from ecommerce.service.product_list import create_products_list
from geolocation.service import build_county_geometries
from market.service import get_current_site

@i_own_this_active_coupon_slot() 
def show_add_flyer_by_map(request, slot_id):
    """ Show market map of counties and zips to select flyer placement. """
    delete_key_from_session(request, 'subdivision_dict')
    site = get_current_site(request)
    context_dict = {'slot_id':slot_id}
    try:
        municipality_division = site.get_state_division_type(plural_form=True)
    except AttributeError:
        municipality_division = 'counties'
    county_list, context_dict['market_coverage'] = build_county_geometries(site)
    county_dict = build_consumer_count_list(site.id)
    add_flyer_by_map_form = AddFlyerByMapForm(county_dict=county_dict)
    context_dict.update({
        'add_flyer_by_map_form':add_flyer_by_map_form,
        'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
        'js_consumers_map': 1,
        'map_height': 535,
        'map_width': 620,
        'market_consumer_count':site.get_or_set_consumer_count(),
        'municipality_division': municipality_division,
        'subdivision_consumer_count':get_subdivision_consumer_count(request),
        'county_list': list_as_text(county_list),
        'county_dict':county_dict,
        'geom_zip_url_arg': '%s-zip-geoms.txt' % site.directory_name
    })
    if request.method == 'POST':  
        return process_add_flyer_by_map(request, 
            created_redirect=reverse('add-flyer-dates',
                kwargs={'slot_id':slot_id}),
            county_dict=county_dict, 
            required_fields_not_filled_out=
            'ecommerce/display_add_flyer_by_map.html', 
            context_instance=RequestContext(request))
    return render_to_response("ecommerce/display_add_flyer_by_map.html",
            context_dict, context_instance=RequestContext(request))

def process_add_flyer_by_map(request, created_redirect, county_dict,
        required_fields_not_filled_out, context_instance):
    """ Processes add flyers form. """
    add_flyer_by_map_form = AddFlyerByMapForm(county_dict=county_dict)
    # Check all required fields are filled out.
    if add_flyer_by_map_form.custom_is_valid(post_data=request.POST):
        zip_array = add_flyer_by_map_form.cleaned_data.get(
            'zip_array', None)
        county_array = add_flyer_by_map_form.cleaned_data.get(
            'county_array', None)
        subdivision_consumer_count = add_flyer_by_map_form.cleaned_data.get(
            'subdivision_consumer_count', None)
        set_subdivision_dict(request, 
            subdivision_consumer_count, 
            county_array=county_array, 
            zip_array=zip_array)
        set_locked_data(request, 
            get_current_site(request), 
            subdivision_consumer_count=subdivision_consumer_count)
        return HttpResponseRedirect(created_redirect)   
    else:
        context_dict = {'add_flyer_by_map_form': add_flyer_by_map_form}
        return render_to_response(required_fields_not_filled_out, 
            context_dict, 
            context_instance=context_instance)

def show_add_flyer_by_list(request, slot_id):
    """ Show zips and counties to select flyer placement. """
    site = get_current_site(request)
    context_dict = {'slot_id':slot_id}    
    county_list, context_dict['market_coverage'] = build_county_geometries(site)
    county_dict = build_consumer_count_list(site.id)
    add_flyer_by_list_form = AddFlyerByListForm(county_dict=county_dict)
    context_dict.update({'add_flyer_by_list_form':add_flyer_by_list_form,
        'js_add_flyer_by_list': 1,
        'map_height': 535,
        'map_width': 620,
        'county_list': county_list,
        'market_consumer_count':site.get_or_set_consumer_count(),
        'subdivision_consumer_count':get_subdivision_consumer_count(request),
        'county_dict':county_dict,
        'geom_zip_url_arg': '%s-zip-geoms.txt' % site.directory_name,
        'geom_city_url_arg': '%s-city-geoms.txt' % site.directory_name,
        'municipality_division': site.get_state_division_type(plural_form=False) 
    })
    return render_to_response("ecommerce/display_add_flyer_by_list.html", 
            context_dict, context_instance=RequestContext(request))

@i_own_this_active_coupon_slot()
def show_buy_market_flyer(request, slot_id):
    """ Clean session to buy the flyer for the entire market """
    delete_all_session_keys_in_list(request, ['subdivision_dict',
        'locked_flyer_price', 'locked_consumer_count', 'add_slot_choice', 
        'add_flyer_choice', 'flyer_dates_list'])
    set_locked_data(request, get_current_site(request))
    return HttpResponseRedirect(reverse('add-flyer-dates', kwargs={'slot_id':slot_id}))

@i_own_this_active_coupon_slot()
def show_add_flyer_dates(request, slot_id):
    """ Show available flyer purchase dates of a selected subdivision. """
    delete_key_from_session(request, 'add_slot_choice')
    if not check_required_session_keys(request, 
        ['locked_flyer_price', 'locked_consumer_count']):
        return HttpResponseRedirect(reverse('all-coupons'))
    site = get_current_site(request)
    coupon = Slot.objects.get(id=slot_id).get_active_coupon()
    # check_if_i_own_this_coupon() will reset the current_coupon in 
    # session to ensure that the correct coupon shows up on the page when 
    # SINGLE_COUPON.set_single_coupon_dict() gets called.
    check_if_i_own_this_coupon(request, coupon.id)
    subdivision_consumer_count = get_subdivision_consumer_count(request)
    subdivision_dict = get_subdivision_dict(request, subdivision_consumer_count)
    available_flyer_dates_list = get_available_flyer_dates(
        site, subdivision_dict=subdivision_dict, slot_id=slot_id)
    add_flyer_dates_form = AddFlyerDatesForm(
        available_flyer_dates_list=available_flyer_dates_list,
        subdivision_consumer_count=subdivision_consumer_count)
    context_instance_dict = {'js_add_flyer_dates': 1,
                    'available_flyer_dates_list':available_flyer_dates_list,
                    'subdivision_consumer_count':subdivision_consumer_count}
    context_instance_dict.update(SINGLE_COUPON.set_single_coupon_dict(request, coupon))
    if request.method == 'POST':
        request.session['current_slot_id'] = slot_id  
        return process_add_flyers(request, 
            created_redirect=reverse('checkout-coupon-purchase'),
            available_flyer_dates_list=available_flyer_dates_list, 
            required_fields_not_filled_out=
            'ecommerce/display_add_flyer_dates.html', 
            context_instance=RequestContext(request, context_instance_dict))
    else:
        context_dict = {'add_flyer_dates_form':add_flyer_dates_form}
        return render_to_response("ecommerce/display_add_flyer_dates.html", 
              context_dict, context_instance=RequestContext(
                request, context_instance_dict))

def process_add_flyers(request, created_redirect, available_flyer_dates_list,
        required_fields_not_filled_out, context_instance):
    """ Processes add flyers form. """
    add_flyer_dates_form = AddFlyerDatesForm(
        available_flyer_dates_list=available_flyer_dates_list, 
        checked_data=request.POST)
    # Check all required fields are filled out.
    try:
        if add_flyer_dates_form.custom_is_valid(post_data=request.POST):
            flyer_dates_list = add_flyer_dates_form.cleaned_data.get(
                'flyer_dates_list', None)
            request.session['flyer_dates_list'] = flyer_dates_list
            product_list = create_products_list(request)
            request.session['product_list'] = product_list
            return HttpResponseRedirect(created_redirect)   
        else:
            context_dict = {'add_flyer_dates_form': add_flyer_dates_form}
            return render_to_response(required_fields_not_filled_out, 
                context_dict, 
                context_instance=context_instance)
    except ValidationError:
        # Abnormal form values, invalid consumer count.
        return HttpResponseRedirect(reverse('advertiser-account'))
