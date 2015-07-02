""" Views for coupon offers. """

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from coupon.config import TEN_COUPON_RESTRICTIONS
from coupon.offer.forms import CreateOfferForm
from coupon.models import Coupon, Offer
from coupon.service.expiration_date_service import  get_default_expiration_date
from coupon.service.single_coupon_service import SINGLE_COUPON
from common.session import add_update_business_offer, parse_curr_session_keys
from ecommerce.service.locking_service import (get_locked_data,
    get_incremented_pricing)
from ecommerce.service.calculate_current_price import get_product_price
from market.service import get_current_site

def show_create_offer(request):
    """ Display the create offer form. """
    try:
        session_dict = parse_curr_session_keys(
            request.session, ['this_business'])
        business_name = session_dict['this_business']['business_name']
        category = (session_dict['this_business'].get('categories', [7]) or [7])[0]
        site = get_current_site(request)
        #Get the expiration date out of session that the user set. If it doesn't
        #exist in session, set it to 90 days ahead.
        expiration_date = request.session.get(
            'expiration_date', get_default_expiration_date())
        slot_price, locked_flyer_price, locked_consumer_count = \
                                                get_locked_data(request, site)
        context_dict = {}        
        context_instance_dict = {
            'js_create_offer':1,
            'css_date_picker':1, 
            'business_name':business_name, 
            'slogan':session_dict['this_business']['slogan'],
            'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS,
            'slot_price':slot_price,
            'locked_flyer_price':locked_flyer_price,
            'locked_consumer_count':locked_consumer_count,
            'annual_slot_price': get_product_price(3, site)
            } 
        context_instance_dict.update(
            get_incremented_pricing(locked_consumer_count))
    except KeyError:
        # No business be operated on at this time from session, redirect!
        return HttpResponseRedirect(reverse('advertiser-registration'))
    except IndexError: # Session has invalid data in it, redirect to coupons.
        return HttpResponseRedirect(reverse('all-coupons'))
    if request.method == 'POST':
        return process_create_offer(
            request, 
            created_redirect=reverse('add-location'), 
            required_fields_not_filled_out=
                'coupon/offer/display_create_offer.html', 
            context_instance=RequestContext(request, context_instance_dict)
            )  
    else: 
        try:
            session_dict = parse_curr_session_keys(
                request.session, ['this_offer'])
            headline = session_dict['this_offer']['headline']
            qualifier = session_dict['this_offer']['qualifier']
            form = CreateOfferForm(initial={
                'headline': headline, 
                'qualifier': qualifier,
                'expiration_date': expiration_date,
                'category': category})
            try:
                session_dict = parse_curr_session_keys(
                    request.session, ['coupon_id'])
                coupon = Coupon.objects.get(id=session_dict['coupon_id'])
                context_dict.update(SINGLE_COUPON.set_single_coupon_dict(
                    request, coupon))  
            except KeyError:
                # No coupon being worked on in session yet.
                pass
        except KeyError:
            # No offer being worked on in session yet.
            headline = ''
            qualifier = ''
            # Display the Offer Creation form. 
            form = CreateOfferForm(
                initial={'expiration_date': expiration_date,
                'category': category})  
        context_dict['form'] = form    
        context_dict['headline'] = headline
        context_dict['qualifier'] = qualifier
        context_dict['expiration_date'] = expiration_date
        return render_to_response(
            'coupon/offer/display_create_offer.html',
            context_dict,
            context_instance = RequestContext(request, context_instance_dict))

def process_create_offer(request, created_redirect, 
        required_fields_not_filled_out, context_instance):
    """ Process the create offer form. """
    # Populate the CreateOfferForm.
    form = CreateOfferForm(request.POST)    
    # Check all required fields are filled out.)
    if form.is_valid():
        # Use cleaned form data.      
        headline = form.cleaned_data.get('headline', None)
        qualifier = form.cleaned_data.get('qualifier', None)
        expiration_date = form.cleaned_data.get('expiration_date', None)
        category_id = form.cleaned_data.get('category', None)
        try:
            # Get current business we are working on out of session.
            this_business = request.session['consumer']['advertiser']\
                ['business'][request.session['current_business']]
            business_id = this_business['business_id']
            try:
                # Are we updating an offer that already exists in session.
                current_offer = request.session['current_offer']
                offer_id = this_business['offer'][current_offer]['offer_id']
                offer = Offer.objects.get(id=offer_id)
                offer.headline = headline
                offer.qualifier = qualifier
                offer.save()
            except KeyError:
                # This is a new offer.
                offer = Offer.save(Offer(business_id=business_id,
                                          headline=headline, 
                                          qualifier=qualifier))
            business = offer.business
            business.categories = [category_id]
            business.save()
            add_update_business_offer(request, offer, category_id)
            request.session['expiration_date'] = expiration_date
            return HttpResponseRedirect(created_redirect)
        except KeyError:
            # No business be operated on at this time from session, redirect home!
            return HttpResponseRedirect(reverse('all-coupons')) 
    else:            
        # All required fields are not filled out. Return to page with form data.
        return render_to_response(required_fields_not_filled_out, 
                                  {'form':form,
                                   'expiration_date':
                                        request.POST.get('expiration_date')}, 
                                  context_instance=context_instance)