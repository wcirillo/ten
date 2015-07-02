""" Views for a business of an advertiser. """

import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from advertiser.business.decorators import i_own_this_business
from advertiser.business.forms import (WebURLForm, EditBusinessProfileForm,
    get_edit_profile_form_init_data)
from advertiser.business.tasks import take_web_snap
from advertiser.models import Business, BusinessProfileDescription
from common.session import (add_update_business_session,
    get_consumer_id_in_session)
from coupon.models import Coupon
from coupon.tasks import RecordAction
from ecommerce.models import OrderItem
from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

@i_own_this_business()
def show_edit_business_profile(request, business_id):
    """ Update this business profile. """
    site = get_current_site(request)
    context_dict = {} 
    try:
        coupon = Coupon.current_coupons.get_current_coupons_by_site(
            site).filter(offer__business__id=business_id)[0]
        all_locations = coupon.location.all().order_by('id')
        location_coords = coupon.get_location_coords_list() 
        business = coupon.offer.business
        created_redirect = reverse("view-single-coupon",
            kwargs={'slug':coupon.slug(), 'coupon_id':coupon.id})
    except IndexError:
        try:
            coupon = None
            business = Business.objects.get(id=business_id)
            created_redirect = reverse("advertiser-account")
            location_coords = None
            all_locations = None
        except Business.DoesNotExist:
            return HttpResponseRedirect(reverse('all-coupons'))
    context_instance_dict = {
        'js_edit_business_profile': 1,
        'coupon': coupon,
        'business': business,
        'all_locations': all_locations}
    if location_coords:
        context_instance_dict.update({
            'location_coords': location_coords})
    context_instance = RequestContext(request, context_instance_dict)
    this_display_path = 'advertiser/business/display_edit_business_profile.html'
    if request.method == 'POST':
        return process_business_profile(request, 
            created_redirect=created_redirect, 
            required_fields_not_filled_out=this_display_path, 
            context_instance = context_instance)
    else:
        initial_data = get_edit_profile_form_init_data(business)
        edit_business_profile_form = EditBusinessProfileForm(
            initial=initial_data)
        web_url_form = WebURLForm(initial={'web_url': business.web_url})
        context_dict['edit_business_profile_form'] = edit_business_profile_form
        context_dict['web_url_form'] = web_url_form
        return render_to_response(this_display_path, context_dict, 
            context_instance=context_instance)

def process_business_profile(request, created_redirect, 
        required_fields_not_filled_out, context_instance):
    """ Process the advertiser registration form on POST. """
    # Populate the EditBusinessProfileForm
    edit_business_profile_form = EditBusinessProfileForm(request.POST)
    web_url_form = WebURLForm(request.POST)
    # Check all required fields are filled out
    if edit_business_profile_form.is_valid() and web_url_form.is_valid():
        # Create User in database.  If user exists, update consumer_zip_postal 
        # if different from zip_postal already stored.
        business = context_instance['business']
        slogan = edit_business_profile_form.cleaned_data['slogan']
        business_description = \
            edit_business_profile_form.cleaned_data['business_description']
        category = [edit_business_profile_form.cleaned_data['category']]
        web_url = web_url_form.cleaned_data.get('web_url', None)
        if web_url:
            business.web_url = web_url
            take_web_snap.delay(business)
        show_web_snap = edit_business_profile_form.cleaned_data['show_web_snap']
        show_map = edit_business_profile_form.cleaned_data['show_map']
        business.slogan = slogan
        business.show_web_snap = show_web_snap
        business.show_map = show_map
        business.categories = category
        business.save()
        try:
            business_profile_description = \
                BusinessProfileDescription.objects.get(business=business)
        except BusinessProfileDescription.DoesNotExist:
            business_profile_description = BusinessProfileDescription(
                business_id=business.id)
        business_profile_description.business_description = business_description
        business_profile_description.save() 
        add_update_business_session(request, business)
        return HttpResponseRedirect(created_redirect)
    else:
        context_dict = {
            'edit_business_profile_form': edit_business_profile_form,
            'web_url_form': web_url_form}
        # All required fields are not filled out. Return to page with form data.
        return render_to_response(required_fields_not_filled_out, context_dict, 
            context_instance=context_instance)

def hit_web_snap(request, business_id):
    """ Take this businesses web_snap. """
    try:
        business = Business.objects.get(id=business_id)
        if business.web_url != '':
            take_web_snap(business)
            LOG.info('BUSINESS_ID = %s , SNAPPING = %s ' % (
                    str(business.id), business.web_url)) 
            return HttpResponseRedirect(reverse('view-all-businesses-coupons',
                    args=[business.slug(), business.id]))
    except Business.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))

def snap_all_businesses(request):
    """ Perform a web snap for all businesses. """
    ordered_items = OrderItem.objects.values_list('item_id', flat=True)
    all_businesses = Business.objects.distinct().select_related(
        'offers__coupons').filter(
            offers__coupons__coupon_type__coupon_type_name='Paid',
            offers__coupons__id__in=ordered_items
        ).exclude(web_url = None).exclude(web_url = '').order_by('id')
    for business in all_businesses:
        LOG.debug('No good BUSINESS = ' + str(business.id) + " " + str(
                all_businesses.count()))
        take_web_snap.delay(business)
        LOG.info('BUSINESS_ID = %s , SNAPPING = %s' % (
                str(business.id), business.web_url)) 
                #LOG.debug('Snapped ' + business.web_url)
        #LOG.debug('Snapped Path ' + str(web_snap_path))
    return HttpResponseRedirect(reverse('all-coupons'))

def click_business_web_url(request, coupon_id):
    """ Records an off-site click action, then redirects. """
    if request.GET:
        # Not preferable to fall into this code since there is a possibility of 
        # losing all argument data hooked to a url after ampersands.
        # Pull the redirect_path from the GET data that was passed in 
        # from the url in the template. If this key isn't in the GET data,
        # redirect home. This will handle the case of having a location_url
        # instead of coupon.offer.business.web_url.
        redirect_path = request.GET.get('url', None)
    else:
        try:
            # Preferable to drop into this code as primary function for the
            # site. No url in the request.GET; use the businesses web_url
            # instead.
            coupon = Coupon.objects.get(id=coupon_id)
            RecordAction().delay(action_id=8, coupon_id=coupon.id,
                consumer_id=get_consumer_id_in_session(request))
            redirect_path = coupon.offer.business.web_url
        except Coupon.DoesNotExist:
            # No url path in the request.GET and no coupon exists with 
            # this coupon_id.   
            redirect_path = reverse('all-coupons')
    return HttpResponseRedirect(redirect_path)
