""" These views are used for operations that take place before a user is logged 
in with an 'authenticated' session.
"""
#pylint: disable=W0613, W0104

import datetime
import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (HttpResponseRedirect, HttpResponse,
    HttpResponsePermanentRedirect, HttpResponseForbidden)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

from advertiser.models import Advertiser
from common.custom_format_for_display import list_as_text
from common.forms import (SignInForm, get_sign_in_form_initial_data,
    OptInOptOutForm, SetPasswordForm, ForgotPasswordForm)
from common.service.common_service import disjoin_sticky_session
from common.service.login_service import (process_login_from_form,
    redirect_local_to_market_site, build_sign_in_form_context)
from common.service.payload_signing import PAYLOAD_SIGNING
from common.session import delete_key_from_session, process_sign_out
from common.utils import check_spot_path_fs, is_datetime_recent
from consumer.email_subscription.service import check_for_email_subscription
from consumer.forms import (ConsumerRegistrationForm, MarketSearchForm,
    get_consumer_reg_initial_data)
from consumer.models import Consumer, UniqueUserToken, EmailSubscription
from consumer.service import (build_consumer_count_list,
    process_consumer_opt_out)
from consumer.views import process_consumer_registration
from coupon.forms import AddFlyerByMapForm
from coupon.service.flyer_service import (next_flyer_date, get_recent_flyer,
    get_subdivision_consumer_count)
from coupon.models import Coupon
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.locking_service import get_unlocked_data
from geolocation.service import build_county_geometries
from email_gateway.send import send_email
from market.decorators import market_required
from market.models import Site
from market.service import (append_geoms_to_close_sites, get_current_site, 
    check_for_cross_site_redirect, get_close_sites, get_markets_in_state, 
    get_or_set_market_state_list, build_site_directory)
from media_partner.service import has_medium_partnered
from subscriber.forms import (SubscriberRegistrationForm,
    get_subscriber_reg_init_data)
from subscriber.views import process_subscriber_registration

def show_csrf_error(request, reason=''):
    """ Show the nice error page for CSRF failure. """
    context_instance = RequestContext(request, {'reason': reason})
    return HttpResponseForbidden(render_to_response(
        'csrf_error.html', context_instance=context_instance
        ))

def show_contact_us(request):
    """ Show the contact us page. """
    context_instance_dict = {'nav_contact_us': "on", 'js_contact_us':1}
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'display_contact_us.html', context_instance=context_instance
        )

def show_contest_rules(request):
    """ Show the contest rules page. """
    context_instance_dict = {'nav_contest_rules': "on"}
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'display_contest_rules.html', context_instance=context_instance
        )

def show_help(request):
    """ FAQs """
    context_instance_dict = {'js_help':1, 'nav_help': 'on'}
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'display_help.html', context_instance=context_instance
        )

@market_required('how-it-works')
def show_how_it_works(request):
    """ Display the Learn More page. """
    site = get_current_site(request)
    slot_price, flyer_price, consumer_count = get_unlocked_data(site)
    county_list = site.get_or_set_counties()
    municipality_division = site.get_state_division_type(plural_form=True)       
    context_instance_dict = {
            'js_how_it_works':1,
            'nav_how_it_works':'on',
            'next_flyer_date':next_flyer_date(),
            'site':site,
            'annual_slot_price': get_product_price(3, site),
            'slot_price':slot_price,
            'flyer_price':flyer_price,
            'consumer_count':consumer_count,
            'site_count':Site.objects.get_or_set_cache().count(),
            'county_list': list_as_text(county_list),
            'municipality_division': municipality_division,
            'has_newspaper': has_medium_partnered(['newspaper'], site)
            }
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response('display_how_it_works.html', 
        context_instance=context_instance)

def show_opt_in_opt_out(request):
    """ Display the opt out form. """
    is_email_subscription = check_for_email_subscription(request)
    context_instance_dict = {'nav_opt_in_opt_out':'on', 
                             'is_email_subscription':is_email_subscription}
    context_instance = RequestContext(request, context_instance_dict)
    if request.method == 'POST':
        return process_opt_out(request, 
            redirect_path=reverse('opt-out-confirmation'), 
            required_fields_not_filled_out='display_opt_in_opt_out.html')  
    else:
        try:
            email = request.session['consumer']['email']
        except KeyError:
            return render_to_response(
                'display_opt_in_opt_out.html',
                context_instance=context_instance)
        form = OptInOptOutForm(data={'email':email})
        context_dict = {'form': form}
        return render_to_response(
            'display_opt_in_opt_out.html',
            context_dict,
            context_instance=context_instance)

def process_opt_out(request, redirect_path, required_fields_not_filled_out):
    """ Process the opt out request. """
    context_instance = RequestContext(request)
    # Populate the OptInOptOutForm.
    form = OptInOptOutForm(request.POST)
    # Check all required fields are filled out.
    if form.is_valid():
        try:
            email = form.cleaned_data.get('email', None)
            # Check if user exists in database.
            consumer = Consumer.objects.get(email=email)
            # Website optout page should unsubscribe you from everything.
            process_consumer_opt_out(request, consumer, ['ALL'])
        except (Consumer.DoesNotExist, ValueError):
            # If user doesn't exist, reload form.
            return render_to_response(required_fields_not_filled_out,
                {'form': form,
                 'nav_opt_in_opt_out': 'on',
                 'email': email},
                 context_instance=context_instance)
        return HttpResponseRedirect(redirect_path)
    else:
        # All required fields are not filled out. Return to page with form data.
        return render_to_response(required_fields_not_filled_out,
            {'form': form, 'nav_opt_in_opt_out': 'on'},
            context_instance=context_instance)

def opt_out_confirmation(request, payload=None):
    """ Display opt out success confirmation. list_id is only needed for 
    email subscription list ids > 1. """
    if payload:
        payload_dict = PAYLOAD_SIGNING.parse_payload(payload)
        subscription_list = payload_dict.get('subscription_list')
    else:
        subscription_list = None
    context_instance = RequestContext(request)
    try:
        email = request.session['consumer']['email']
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons'))
    opt_out_list = False
    live_help_banner = True
    response_template = 'display_opt_out_confirmation.html'
    if subscription_list:
        email_subscriptions = EmailSubscription.objects.filter(
            id__in=subscription_list).values_list('email_subscription_name')
        opt_out_list = []
        for email_ in email_subscriptions:
            if email_[0] in ('External', 'Ad Rep Meeting Reminder'):
                live_help_banner = False
            opt_out_list.append(email_[0])
        opt_out_list = list_as_text(opt_out_list)
        response_template = 'display_variable_opt_out_confirmation.html'
    try:
        advertiser = Advertiser.objects.get(email=email)
        is_advertiser = True 
        consumer_create_datetime = advertiser.consumer_create_datetime
    except Advertiser.DoesNotExist:
        consumer = Consumer.objects.get(email=email)
        consumer_create_datetime = consumer.consumer_create_datetime
        is_advertiser = False
    # Garbage cleanup in the session from the previous method.
    delete_key_from_session(request, 'opt_out_email')
    return render_to_response(response_template,
        {'nav_opt_in_opt_out': 'on', 
        'email': email, 
        'optout_type': opt_out_list,
        'live_help_banner': live_help_banner,
        'is_advertiser': is_advertiser,
        'is_consumer_recent': is_datetime_recent(consumer_create_datetime, 5)},
        context_instance=context_instance)

def show_privacy_policy(request):
    """ Show the static privacy policy page. """
    context_instance_dict = {'nav_privacy_policy': "on"}
    return render_to_response('display_privacy_policy.html', 
        context_instance=RequestContext(request, context_instance_dict))

def show_sample_flyer(request):
    """ Example flyer view, show most recent if one exists. """
    context_instance_dict = {
        'nav_sample_flyer': "on",
        'js_sample_flyer': 1}
    site = get_current_site(request)
    flyer = get_recent_flyer(site)
    flyer_coupons = None
    if flyer:
        flyer_coupons = Coupon.objects.select_related(
            'offer', 'offer__business').filter(
            id__in=flyer.flyer_coupons.values_list('coupon__id', flat=True))
    context_instance_dict.update({
        'flyer': flyer,
        'flyer_coupons': flyer_coupons,
        'payload': 0,
        'site': site})
    # Payload = 0 spoofs payload and allows url // (empty payload) to work.
    return render_to_response('display_sample_flyer.html',
        context_instance=RequestContext(request, context_instance_dict))

def show_home(request, msg=None):
    """ Show home page with a consumer registration & subscriber registration 
    form. If site.id is 1 (generic non-market), prompt for zip entry before
    allowing links to navigate away.
    """
    site = get_current_site(request)
    context_instance_dict = {'is_home':True, 'nav_home':True}
    if not request.is_ajax():
        if msg not in ['e', 'f']:
            redirect_path = redirect_local_to_market_site(request,
                default_view='home')[0]
            if redirect_path:
                return HttpResponseRedirect(redirect_path)
            # If on site 1 and have consumer session with unknown market show
            # proper map to select market.
            if site.id == 1:
                try:
                    request.session['consumer']['consumer_zip_postal']
                    return HttpResponseRedirect("%s?next=/" %
                        reverse('locate-market-map'))
                except KeyError:
                    pass
    # Check if this user is a consumer that is subscribed to "Flyer".
    context_instance_dict = {'js_home': 1, 'nav_home':True, 'is_home':True,
        'button_text': 'Finish '}
    if request.method == 'POST':
        # Check for subscriber_zip_postal in the POST data to ensure we are not
        # submitting the consumer registration form again.  CASE:  User hits 
        # the back button after reaching the consumer registration success page.
        # Then resubmits the consumer registration form... is_email_subscription
        # and not is_a_subscriber will be true on the POST, therefore we need
        # to verify exactly which form we are submitting by accessing the 
        # appropriate form key.
        ajax_mode = request.POST.get('ajax_mode', None)
        if ajax_mode == 'consumer_reg':
            
            consumer_reg_form = ConsumerRegistrationForm(request.POST)
            if consumer_reg_form.is_valid():
                is_already_registered, url_to_change_market = \
                    process_consumer_registration(request, 
                    created_redirect=
                        reverse('consumer-registration-confirmation'),
                    required_fields_not_filled_out=
                        'coupon/display_email_coupon.html',
                    context_instance=
                        RequestContext(request, context_instance_dict),
                    do_not_redirect=True)
                json_data = {"is_already_registered": is_already_registered,
                    'url_to_change_market': url_to_change_market}
                json = simplejson.dumps(json_data)
                return HttpResponse(json, mimetype='application/json')
            json_data = {"errors": consumer_reg_form.errors}
        else:
            subscriber_reg_form = SubscriberRegistrationForm(request.POST)
            if subscriber_reg_form.is_valid():
                process_subscriber_registration(request,
                    created_redirect=reverse(
                        'con-sub-reg-confirmation'),
                    required_fields_not_filled_out="display_home.html",
                    context_instance = RequestContext(request),
                    do_not_redirect=True)
                json_data = {"is_already_registered": True}
            else:
                json_data = {"errors": subscriber_reg_form.errors}
        json = simplejson.dumps(json_data)
        return HttpResponse(json, mimetype='application/json')
    else:
        context_dict = {}
        if request.GET.get('cross_site', False):
            # Slide subscriber form over on page load, we just changed markets.
            context_dict.update({'cross_site': 1})
        if site.id == 1:
            context_dict.update({'js_local_home': 1, 
                'http_protocol_host' : settings.HTTP_PROTOCOL_HOST,
                'site_count': Site.objects.get_or_set_cache().count()})
        initial_data = get_consumer_reg_initial_data(request)
        consumer_reg_form = ConsumerRegistrationForm(
            initial=initial_data)
        initial_data = get_subscriber_reg_init_data(request.session)
        subscriber_reg_form = SubscriberRegistrationForm(
                initial=initial_data)
        context_dict.update({'consumer_reg_form':consumer_reg_form,
                        'subscriber_reg_form':subscriber_reg_form})
        return render_to_response("display_home.html", context_dict,
            context_instance=RequestContext(request, context_instance_dict))

def force_generic_home(request, msg='e'):
    """ Force local home page to display. """
    # Dont let force-generic-home URL catch the response that clears the cookie.
    if msg == 'e/':
        msg = 'f/'
    response = HttpResponseRedirect('/%s' % msg)
    disjoin_sticky_session(request, response)
    return response

def show_map_market_counties(request):
    """ Display all the counties for this market. """
    display_template = "display_counties_in_market_map.html"
    site = get_current_site(request)
    try:
        municipality_division = [site.get_state_division_type(plural_form=False),
            site.get_state_division_type(plural_form=True)]          
    except AttributeError:
        municipality_division = None
    context_dict = {}
    county_list, context_dict['market_coverage'] = build_county_geometries(site)
    if context_dict['market_coverage']:
        context_dict['onload_county_map'] = 1
    close_sites = append_geoms_to_close_sites(site.get_or_set_close_sites())
    context_dict.update({
        'http_protocol_host' : settings.HTTP_PROTOCOL_HOST,
        'js_market_counties' : 1, 
        'municipality_division': municipality_division,
        'close_sites' : close_sites,
        'map_height': 400,
        'map_width': 630,
        'close_sites_caption': 'These markets are nearby',
        'county_list': list_as_text(county_list)})
    return render_to_response(display_template, context_dict,
        context_instance=RequestContext(request))

def show_market_search(request):
    """ Show market search form in iframe for site 1. """
    if request.method == "POST":
        market_search_form = MarketSearchForm(request.POST)
        if market_search_form.is_valid():
            # Send to correct site.
            zip_postal = market_search_form.cleaned_data['consumer_zip_postal']
            request.session['consumer'] = request.session.get('consumer', {})
            request.session['consumer']['consumer_zip_postal'] = zip_postal
            json_data = {"successful_submit": True}
        else:
            json_data = {"errors": market_search_form.errors}
        json = simplejson.dumps(json_data)
        return HttpResponse(json, mimetype='application/json')
    else:
        market_search_form = MarketSearchForm(initial={
            'consumer_zip_postal': request.session.get('consumer_zip_postal')})
    context_dict = {'market_search_form': market_search_form,
        'js_market_search_form' : 1,
        'onload_market_search_form': 1}
    return render_to_response('consumer/display_market_search_form.html',
         context_dict, context_instance=RequestContext(request))

def show_close_markets(request):
    """ Show map of five closest markets to zip in session. (User is likely 
    coming from local site 1 after entering a zip that does not exist in a 
    market.
    """
    _next = request.GET.get('next', None)
    if not _next:
        return HttpResponseRedirect(reverse('home'))
    try:
        zip_postal = request.session['consumer']['consumer_zip_postal']
    except KeyError:
        zip_postal = None
    site, created_redirect, curr_site = \
        check_for_cross_site_redirect(request, zip_postal, redirect_path=_next)
    if created_redirect and site != curr_site:
        return HttpResponseRedirect(created_redirect)
    neighbor_sites = append_geoms_to_close_sites(get_close_sites(zip_postal))
    if neighbor_sites:
        # Set defaults for site_directory map around submitted zip.
        context_dict = { 'js_site_directory': 1}
        context_dict['state_site_list'], \
            context_dict['market_coverage'] = \
                build_site_directory(neighbor_sites)
        return render_to_response("display_select_markets_map.html",
            context_instance=RequestContext(request, context_dict))
    else:
        # If neighbor_sites returns None, display all markets.
        return show_site_directory(request)

def show_state_markets(request, state_name):
    """ Display all markets in this state. """
    display_template = "display_select_markets_map.html"
    context_dict = {}
    markets = get_markets_in_state(state_name)
    if markets:
        context_dict['state_site_list'], context_dict['market_coverage'] = \
                build_site_directory(markets)
    if context_dict['market_coverage']:
        context_dict['onload_state_markets'] = 1
    context_dict.update({ 'http_protocol_host' : settings.HTTP_PROTOCOL_HOST,
                         'js_state_markets' : 1,
                         'state_name' : state_name.replace('-', ' ')})
    return render_to_response(display_template, context_dict,
            context_instance=RequestContext(request))

def redirect_site_directory(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('site-directory'))

def show_site_directory(request):
    """ Display a list of links to local market sites. """
    state_site_list = get_or_set_market_state_list()
    context_instance = RequestContext(request, 
        {'state_site_list': state_site_list, 
        'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
        'js_site_directory': 1,
        'onload_site_directory': 1})
    return render_to_response('display_site_directory.html', 
        context_instance=context_instance)

def show_terms_of_use(request):
    """ Displays terms of use. """
    context_instance = RequestContext(request)
    return render_to_response('display_terms_of_use.html', 
        {'nav_terms_of_use': "on"}, context_instance=context_instance)

def show_who_we_are(request):
    """ Show who we are static page. """
    context_instance = RequestContext(request)
    return render_to_response('display_who_we_are.html', 
        {'nav_who_we_are': "on"}, context_instance=context_instance)

def show_widgets(request):
    """ Show widget page. """
    site = get_current_site(request)
    if site.id > 1:
        context_instance = RequestContext(request)
        return render_to_response('display_widgets.html', 
            {'nav_widget': "on", 
            'http_protocol_host': settings.HTTP_PROTOCOL_HOST}, 
            context_instance=context_instance)
    else:
        return HttpResponseRedirect(reverse('all-coupons'))

def loader(request, page_to_load):
    """ Loader helps load the modal window. Called in templates. """
    page_to_load = 'loader/' + page_to_load.replace('%5f', '_') + '.html'
    context_instance = RequestContext(request)
    return render_to_response(page_to_load, 
        context_instance=context_instance)

def sign_out(request):
    """ Sign out and clear session! If ad_rep_id in session, save it
    and put it back.
    """
    process_sign_out(request)
    redirect_to = request.GET.get('next', reverse('home'))
    return HttpResponseRedirect(redirect_to)

def show_sign_in(request):
    """ Display the sign in form or process it. """
    context_dict = {'js_sign_in':1}
    if request.method == 'POST':
        return process_sign_in(request,  
            required_fields_not_filled_out='display_sign_in.html', 
            context_instance = RequestContext(request, context_dict))  
    else:
        context_dict, redirect_to = \
            build_sign_in_form_context(request, context_dict)
        if redirect_to:
            return HttpResponseRedirect(reverse(redirect_to))
        return render_to_response('display_sign_in.html', context_dict, 
            context_instance = RequestContext(request, context_dict))

def process_sign_in(request, required_fields_not_filled_out, context_instance):
    """ Processes the sign in form on POST. """
    # Populate the SignInForm.
    form = SignInForm(request.POST,
        test_mode=request.session.get('tlc_sandbox_testing', False))
    # Check all required fields are filled out.
    if form.is_valid():
        redirect_path = process_login_from_form(request, form=form)
        if redirect_path:
            return HttpResponseRedirect(redirect_path)
    return render_to_response(required_fields_not_filled_out, {'form': form},
        context_instance=context_instance)
     
def redirect_media_partner_sign_in(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('media-partner-sign-in')) 

def show_advertiser_sign_in(request):
    """ Sign in form for advertisers. """
    context_dict = {'js_sign_in':1}      
    if request.method == 'POST':
        return process_sign_in(request,  
            required_fields_not_filled_out=
                'advertiser/display_advertiser_sign_in.html', 
            context_instance=RequestContext(request, context_dict))  
    else:
        context_dict, redirect_to = \
            build_sign_in_form_context(request, context_dict)
        if redirect_to: 
            return HttpResponseRedirect(reverse(redirect_to))
        # Display the sign in form.
        return render_to_response('advertiser/display_advertiser_sign_in.html', 
            context_dict, 
            context_instance=RequestContext(request, context_dict))

def show_media_partner_sign_in(request):
    """ Sign in form for media partners. """
    site = Site.objects.get(id=request.META['site_id'])
    context_dict = {'js_sign_in':1, 'has_spots': check_spot_path_fs(site)}      
    if request.method == 'POST':
        return process_sign_in(request,  
        required_fields_not_filled_out=
        'media_partner/display_media_partner_sign_in.html', 
        context_instance=RequestContext(request, context_dict))  
    else:
        initial_data = get_sign_in_form_initial_data(request)
        form = SignInForm(initial=initial_data)
        context_dict['form'] = form
        # Display the sign in form.
        return render_to_response(
            'media_partner/display_media_partner_sign_in.html', 
            context_dict, 
            context_instance=RequestContext(request, context_dict))   

def redirect_media_explanation(request):
    """ Permanent redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('media-partner-home'))

def show_media_partner_home(request):
    """ Media Partner Home-Landing page. """
    site_count = Site.objects.get_or_set_cache().count()
    context_dict = {"site_count" : site_count}
    return render_to_response('media_partner/display_media_partner_home.html',
        context_dict, context_instance=RequestContext(request, context_dict))

def show_media_partner_half_off(request):
    """ Media Partner Half Off Page. """
    context_instance_dict = {'nav_media_partner_explanation': 'on'}
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'media_partner/display_media_partner_half_off.html', 
        context_instance=context_instance)

def show_inside_radio(request):
    """ Show Inside Radio article. """
    context_instance_dict = {'nav_media_partner_explanation': 'on'}
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response('media_partner/display_inside_radio.html', 
        context_instance=context_instance)

def show_radio_ink(request):
    """ Show Radio Ink article. """
    context_instance_dict = {'nav_media_partner_explanation': 'on'}
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response('media_partner/display_radio_ink.html', 
        context_instance=context_instance)
        
def show_press_release(request):
    """ Show the press release static page. """
    context_instance = RequestContext(request)
    return render_to_response('media_partner/display_press_release.html', 
        {'nav_media_partner_explanation': 'on'}, 
        context_instance=context_instance)

@login_required
def set_password(request):
    """ Form for setting a user password. """
    form = SetPasswordForm()
    _next = request.GET.get('next', None)
    if request.POST:
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            form.save(request)
            return HttpResponseRedirect(_next)
    context_dict = {'form':form, 'next':_next}
    return render_to_response('login/display_reset_password.html', context_dict, 
        context_instance=RequestContext(request))

def show_forgot_password(request):
    """ Handle Forgot Password requests for all user types. """
    context_instance = RequestContext(request)
    _next = request.GET.get('next', None)
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email', None)
            try:
                consumer = Consumer.objects.get(email__iexact=email)
                if consumer.is_active:
                    # Number of days the password reset request should be 
                    # valid:
                    change_request_lifetime = 3
                    password_token = UniqueUserToken(user=consumer, 
                        lifetime = change_request_lifetime * 86400)
                    password_token.save()
                    context = {
                        'to_email': consumer.email,
                        'subject': 'Password reset request from %s' % (
                            consumer.site.domain),
                        'password_token': password_token.hashstamp,
                        'password_change_request_lifetime_days': 
                                change_request_lifetime,
                        'ref_num': consumer.id,
                        'next':_next
                        }
                    send_email(template='consumer_forgot_password',
                        site=consumer.site, context=context)
            except Consumer.DoesNotExist:
                pass    
            # No matter what: 
            context = {'email': email}
            return render_to_response(
                'login/display_reset_password_confirmation.html', context, 
                context_instance=context_instance)
        else:
            # Display email form with any errors
            return render_to_response('login/display_forgot_password.html', 
                {'form':form, 'next':_next}, context_instance=context_instance)
    else:
        # Display the forgot password form.
        try:
            email = request.session['consumer']['email']
        except KeyError:
            email = None
        form = ForgotPasswordForm(initial={'email':email})  
        return render_to_response('login/display_forgot_password.html', 
            {'form': form, 'next':_next, 'js_advertiser_forgot_password':1}, 
            context_instance=context_instance)

def show_spots(request):
    """ Locates, sorts, displays the spots for site """
    site = get_current_site(request)
    media_types = ['mp3', 'mpeg', 'mov', 'mpg', 'mp4', 'm4v']
    spot_titles = { 
        'LsnUp': "Listen Up!",
        'GvAwy': '$10,000 Givaway',
        'bs': 'Smart Business People',
        'if': "It's Free!",
        'jeff': 'Jeff phones home',
        'biz': '10,000 Reasons',
        'gad': 'Is a deal really a deal...',
        'jgb': 'Just got better',
        'nsm': 'Not so Much',
        'po': 'George told Rachel...',
        'pob': 'Purpose of a Business',
        'sot': 'Story of 2 coupons',
        }
    spot_path = os.path.join("media", "spots", site.spot_name())    
    abs_spot_path = check_spot_path_fs(site)
    spots = []
    if abs_spot_path:
        for spot_file in sorted(os.listdir(abs_spot_path), reverse=True):
            ext = spot_file.split('.')[-1].lower()
            if ext in media_types:
                spot_data_list = spot_file.split('_')
                date = datetime.date(int(spot_data_list[1]), 
                        int(spot_data_list[2]), 1)
                try:
                    spot = {
                        'date': date,
                        'name': spot_data_list[3],
                        'length': spot_data_list[5],
                        'path': spot_path,
                        'filename': spot_file,
                        'title': spot_titles.get(spot_data_list[3],
                                spot_data_list[3]),
                        'target': spot_data_list[6].split('.')[0],
                        'file_extension': ext,
                        }
                    spots.append(spot)
                except IndexError:
                    pass
        context = {'spots': spots }
        
        return render_to_response('display_site_spots.html', context, 
            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('all-coupons'))

def show_consumer_map(request):
    """ Show market map of consumers for counties and zips. """
    site = get_current_site(request)
    county_list, market_coverage = \
        build_county_geometries(site)
    county_dict = build_consumer_count_list(site.id)
    add_flyer_by_map_form = AddFlyerByMapForm(county_dict=county_dict)
    try:
        municipality_division = site.get_state_division_type(plural_form=True)
    except AttributeError:
        municipality_division = 'counties'
    context_dict = {
        'add_flyer_by_map_form':add_flyer_by_map_form,
        'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
        'js_consumers_map': 1,
        'map_height': 535,
        'map_width': 620,
        'market_coverage': market_coverage,
        'market_consumer_count':site.get_or_set_consumer_count(),
        'subdivision_consumer_count':get_subdivision_consumer_count(request),
        'county_list': list_as_text(county_list),
        'county_dict':county_dict,
        'geom_zip_url_arg': '%s-zip-geoms.txt' % site.directory_name,
        'municipality_division': municipality_division
    }
    context_dict.update({'is_consumer_map':True})
    return render_to_response("display_consumer_map.html",
            context_dict, context_instance=RequestContext(request))
