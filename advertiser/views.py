""" Views for advertiser app. """
#pylint: disable=W0613
import datetime
import logging

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (HttpResponseRedirect, HttpResponse,
    HttpResponsePermanentRedirect)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

from advertiser.business.decorators import business_required
from advertiser.forms import (AdvertiserRegistrationForm,
    get_advertiser_reg_init_data)
from advertiser.models import Advertiser, Business
from advertiser.service import (process_update_advertiser,
    process_create_advertiser, clean_adv_acct_post_data, get_adv_acct_business,
    get_adv_acct_context, get_adv_acct_json_data, registration_parent_redirect)
from common.context_processors import current_site
from common.decorators import password_required
from common.session import (parse_curr_session_keys,
    check_if_i_own_this_business, check_for_unpublished_offer,
    delete_key_from_session)
from common.utils import (get_object_or_redirect, format_date_for_dsp)
from coupon.config import TEN_COUPON_RESTRICTIONS
from coupon.models import Coupon, Slot
from coupon.service.expiration_date_service import get_default_expiration_date
from coupon.service.flyer_service import next_flyer_date
from coupon.service.coupon_performance import CouponPerformance
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.locking_service import (get_locked_data,
    get_unlocked_data, get_incremented_pricing)
from firestorm.models import AdRepAdvertiser
from market.decorators import market_required
from market.models import Site
from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)


class ProxyObject(object):
    """ A proxy object for passing to other functions, for create or update. """
    pass

def redirect_advertiser_sign_in(request):
    """ Redirect from an old url path. """
    return HttpResponsePermanentRedirect(reverse('sign-in'))

def redirect_advertiser_reg(request):
    """ Redirect from an old url path. """
    return HttpResponsePermanentRedirect(reverse('advertiser-registration'))

def redirect_adv_password_help(request):
    """ Redirect from an old url path. """
    return HttpResponsePermanentRedirect(reverse('forgot-password'))

def show_advertiser_faq(request):
    """ Display advertiser FAQ """
    site = get_current_site(request)
    neighbor_sites = site.get_or_set_close_sites()
    consumer_count = get_unlocked_data(site)[2]
    try:
        municipality_division = site.get_state_division_type(plural_form=True)
    except AttributeError:
        municipality_division = 'counties'
    context_instance_dict = {
            'js_advertiser_faq':1,
            'site':site,
            'consumer_count':consumer_count,
            'site_count': Site.objects.get_or_set_cache().count(),
            'municipality_division': municipality_division
            }
    if neighbor_sites:
        context_instance_dict['neighbor_sites'] = neighbor_sites
    try:
        session_dict = parse_curr_session_keys(request.session, ['business_id'])
        context_instance_dict.update({'parent_slot_count': 
            Slot.objects.filter(
                business__id=session_dict['business_id']).count()})
    except KeyError:
        pass
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response('advertiser/display_advertiser_faq.html', 
        context_instance=context_instance)

@market_required('advertiser-registration')
def show_advertiser_registration(request):
    """ Show the advertiser registration form. """
    site = get_current_site(request)
    context_dict = {}
    context_instance_dict = {'next_flyer_date': next_flyer_date(), 
        'js_advertiser_registration':1, 
        'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS,
        'annual_slot_price': get_product_price(3, site)}
    if request.method == 'POST':
        slot_price, locked_flyer_price, locked_consumer_count = get_locked_data(
            request, site)
        context_instance_dict.update(
            get_incremented_pricing(locked_consumer_count))
        context_instance_dict.update({'slot_price': slot_price,
            'locked_flyer_price': locked_flyer_price,
            'locked_consumer_count': locked_consumer_count})
        return process_advertiser_registration(request, 
            created_redirect=reverse("add-offer"), 
            required_fields_not_filled_out=
                'registration/display_advertiser_registration.html',
            context_instance=RequestContext(request, context_instance_dict, 
                processors=[current_site]))  
    else:
        # Delete 'coupon_mode' key out of session. Since we are creating a 
        # new coupon, we don't what a different coupon_mode such as 'EDIT'
        # to exist and run the wrong code.
        delete_key_from_session(request, 'coupon_mode')
        delete_key_from_session(request, 'current_slot_id')
        delete_key_from_session(request, 'flyer_dates_list')
        slot_price, locked_flyer_price, locked_consumer_count = get_locked_data(
            request, site, lock_it_now=True)
        context_instance_dict.update(
            get_incremented_pricing(locked_consumer_count))
        context_instance_dict.update({'slot_price': slot_price,       
            'locked_flyer_price': locked_flyer_price,
            'locked_consumer_count': locked_consumer_count})
        try:
            # Check for coupon in session either paid or unpaid.
            session_dict = parse_curr_session_keys(request.session, 
                ['this_advertiser', 'this_business', 'this_offer'])
            context_dict.update({'business_name':
                session_dict['this_business']['business_name'],
                'slogan':session_dict['this_business']['slogan'],
                'advertiser_name':
                    session_dict['this_advertiser']['advertiser_name']})
            context_dict.update({'headline':
                session_dict['this_offer']['headline'],
                'qualifier':session_dict['this_offer']['qualifier']})
            redirect_path = registration_parent_redirect(
                request, session_dict['this_business']['business_id'])
            if redirect_path:
                return HttpResponseRedirect(redirect_path)
            # Although it looks like these variables aren't being used.  They
            # actually need to be set in order to figure out if we have a 
            # KeyError. If a KeyError exists it will not jump to preview-coupon!
            session_dict.update(parse_curr_session_keys(
                request.session, ['coupon_id']))
            # Get all coupons by this business.
            coupons = Coupon.objects.select_related().filter(
                offer__business=session_dict['this_business']['business_id'])
            if coupons.count > 0:
                return HttpResponseRedirect(reverse('preview-coupon'))          
        except KeyError:
            pass
        try:
            (business_has_offer, business_has_unpublished_offer,
            offer_has_coupon_association) = check_for_unpublished_offer(
                request, delete_keys=False)
            if (business_has_offer and business_has_unpublished_offer
                and offer_has_coupon_association
            ) or (business_has_offer and not business_has_unpublished_offer
                and not offer_has_coupon_association):
                return HttpResponseRedirect(reverse('preview-coupon'))
        except KeyError:
            pass
        # Display the Advertiser registration form.
        initial_data = get_advertiser_reg_init_data(request)
        advertiser_reg_form = AdvertiserRegistrationForm(initial=initial_data)    
        context_instance_dict.update({
            'advertiser_reg_form': advertiser_reg_form,
            'expiration_date': get_default_expiration_date()})
        return render_to_response(
            'registration/display_advertiser_registration.html', 
            context_dict, context_instance=RequestContext(request, 
                context_instance_dict, processors=[current_site]))

def process_advertiser_registration(request, created_redirect, 
        required_fields_not_filled_out, context_instance):
    """ Process the advertiser registration form on POST """
    site = get_current_site(request)
    # Populate the AdvertiserRegistrationForm.
    advertiser_reg_form = AdvertiserRegistrationForm(request.POST)    
    # Check all required fields are filled out.
    if advertiser_reg_form.is_valid():
        # Create User in database.  If user exists, update consumer_zip_postal 
        # if different from zip_postal already stored.
        cleaned_data = advertiser_reg_form.cleaned_data
        proxy_advertiser = ProxyObject()
        for field in ['business_name', 'slogan', 'email', 'advertiser_name',
                'advertiser_area_code', 'advertiser_exchange',
                'advertiser_number']:
            setattr(proxy_advertiser, field, cleaned_data.get(field, None))
        try:
            # Check if advertiser exists already.
            # pylint: disable=E1101
            advertiser = Advertiser.objects.select_related(
                'offer', 'offer__business').get(
                email__iexact=proxy_advertiser.email)
            process_update_advertiser(request, advertiser, proxy_advertiser)
        except Advertiser.DoesNotExist:
            advertiser = process_create_advertiser(request, site,
                proxy_advertiser)
        # Add the AdRepAdvertiser
        AdRepAdvertiser.objects.create_update_rep(request, advertiser)
        return HttpResponseRedirect(created_redirect)   
    else:
        context_dict = {'advertiser_reg_form': advertiser_reg_form,
            'expiration_date': get_default_expiration_date()}
        try:
            # Check for coupon in session either paid or unpaid.
            session_dict = parse_curr_session_keys(request.session,
                ['this_advertiser', 'this_business', 'this_offer'])
            context_dict.update({
                'business_name':session_dict['this_business']['business_name'],
                'slogan':session_dict['this_business']['slogan'],
                'advertiser_name':
                    session_dict['this_advertiser']['advertiser_name']})
            context_dict.update({
                'headline':session_dict['this_offer']['headline'],
                'qualifier':session_dict['this_offer']['qualifier']})
        except KeyError:
            pass
        # All required fields are not filled out. Return to page with form data.
        return render_to_response(required_fields_not_filled_out, context_dict, 
            context_instance=context_instance)

@password_required
@login_required
@business_required()
def show_advertiser_account(request):
    """ Show the advertiser account when advertiser is authenticated. """
    try:
        this_advertiser = request.session['consumer']['advertiser']
        advertiser_id = this_advertiser['advertiser_id']
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons'))
    # Get clean data. Won't fail if this is a GET, but we need it for finding
    # out what businesses this is for.
    clean_data = clean_adv_acct_post_data(request)[0]
    site = get_current_site(request)
    # Advertiser coupons and slots.
    all_coupons = Coupon.objects.select_related('offer').filter(
        offer__business__advertiser=advertiser_id)
    all_slot_coupons = Coupon.current_coupons.get_current_coupons_by_site(site).filter(
            offer__business__advertiser=advertiser_id
        ).order_by('offer__business__id')
    # Set the current_business position to the business we are working on.
    business = get_adv_acct_business(clean_data, all_slot_coupons, 
        this_advertiser)
    if not check_if_i_own_this_business(request, business.id):
        # This user can't change this business.
        return HttpResponseRedirect(reverse('all-coupons'))
    if request.is_ajax():
        json = simplejson.dumps(get_adv_acct_json_data(request,
            clean_data, business))
        return HttpResponse(json, mimetype='application/json')
    next_send_date = next_flyer_date()
    context_dict = get_adv_acct_context(business, all_coupons, all_slot_coupons)
    # Only need first and last item of this 3 tuple:
    slot_price, locked_consumer_count = list(
        get_locked_data(request, site, lock_it_now=True))[::2]
    try:
        business_category = business.categories.all()[0].name
    except IndexError:
        business_category = ''
    context_instance_dict = {
        'js_advertiser_account': 1,
        'is_advertiser_account': 1, 
        'businesses': Business.objects.filter(advertiser=advertiser_id), 
        'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS,
        'business_id': business.id,
        'business_name': business.business_name,
        'business_category': business_category,
        'business_profile_description':business.get_business_description(),
        'slot_price': slot_price,
        'locked_consumer_count': locked_consumer_count,
        'first_flyer_date': format_date_for_dsp(next_send_date),
        'second_flyer_date': format_date_for_dsp(
                                next_send_date + datetime.timedelta(days=7)),
        'third_flyer_date': format_date_for_dsp(
                                next_send_date + datetime.timedelta(days=14)),
        'fourth_flyer_date': format_date_for_dsp(
                                next_send_date + datetime.timedelta(days=21))}
    context_instance_dict.update(
        get_incremented_pricing(locked_consumer_count))
    return render_to_response('advertiser/display_advertiser_account.html', 
        context_dict, context_instance=RequestContext(request, 
            context_instance_dict))

@password_required
@login_required
def show_coupon_stats(request, **kwargs):
    """ Show the stats for all coupons associated with this advertiser. """
    template_name = kwargs.get(
        'template_name', 'advertiser/display_coupon_stats.html')
    advertiser = get_object_or_redirect(Advertiser, reverse('sign-out'),
        id=request.user.id)
    # A POST could be a login or a JSON request.
    businesses = advertiser.businesses.all()
    try:
        business_id = businesses[0].id
    except IndexError:
        business_id = None
    size_limit = 20
    context_dict = {
        'js_coupon_stats': 1,
        'businesses': businesses,
        'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS,
        'business_id': business_id,
        'size_limit': size_limit,
        'show_edit': True}
    if request.POST:
        coupon_performance = CouponPerformance(
            size_limit=size_limit, render_preview=True)
        
        coupon_list = coupon_performance.get_coupon_list(
            advertiser_ids=[advertiser.id],  **request.POST)
        json = simplejson.dumps(coupon_list)
        return HttpResponse(json, content_type='application/json')
    else:
        return render_to_response(template_name, context_dict, 
            context_instance=RequestContext(request))
