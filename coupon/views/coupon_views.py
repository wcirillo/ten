""" Views for coupon app. """
#pylint: disable=W0613
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import (HttpResponseRedirect, HttpResponsePermanentRedirect,
    HttpResponse)
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

from advertiser.business.location.service import (get_location_coords_list,
    get_locations_for_coupons)
from advertiser.models import Business
from advertiser.service import get_meta_for_business
from common.contest import check_contest_is_running, check_if_eligible_to_win
from common.context_processors import products
from common.service.common_service import get_home_data
from common.service.payload_signing import PAYLOAD_SIGNING
from common.service.registration_service import (post_common_registration,
    get_common_registration)
from common.session import (build_session_from_user, create_consumer_in_session,
    get_consumer_id_in_session)
from common.utils import build_fb_like_meta, list_as_text
from consumer.email_subscription.service import check_for_email_subscription
from consumer.forms import (ConsumerRegistrationForm,
    get_consumer_reg_initial_data)
from consumer.models import Consumer
from consumer.views import process_consumer_registration
from coupon.config import TEN_COUPON_RESTRICTIONS
from coupon.forms import SearchCouponForm
from coupon.models import Coupon
from coupon.service.coupon_code_service import (check_coupon_code, 
    create_coupon_code)
from coupon.service.coupons_service import ALL_COUPONS
from coupon.service.expiration_date_service import frmt_expiration_date_for_dsp
from coupon.service.single_coupon_service import SINGLE_COUPON
from coupon.service.twitter_service import TWITTER_SERVICE
from coupon.service.valid_days_service import VALID_DAYS
from coupon.tasks import (RecordAction, record_action_multiple_coupons,
    update_facebook_share_coupon)
from email_gateway.process import email_hash_decypher
from firestorm.service import build_adv_url_with_ad_rep
from market.decorators import market_required
from market.service import get_current_site
from sms_gateway.service import save_phone_by_carrier_lookup, send_sms
from subscriber.forms import (SubscriberRegistrationForm,
    get_subscriber_reg_init_data)
from subscriber.models import MobilePhone
from subscriber.views import process_subscriber_registration
from subscriber.service import check_if_user_is_a_subscriber
from ecommerce.service.locking_service import (get_unlocked_data,
    get_incremented_pricing)


LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)
    
def redirect_view_single_coupon(request, slug, coupon_id):
    """ Redirect old url to new. """
    return HttpResponsePermanentRedirect(reverse('view-single-coupon', 
        kwargs={'slug': slug, 'coupon_id':coupon_id}))

def redirect_show_all_offers(request):
    """ Show all offers by redirecting to home page. """
    return HttpResponsePermanentRedirect(reverse('all-coupons'))

def show_single_coupon(request, slug, coupon_id):
    """ The details view of a coupon. """
    site = get_current_site(request)
    coupon_or_redirect = SINGLE_COUPON.check_single_coupon_redirect(
        coupon_id, site, slug)
    if isinstance(coupon_or_redirect, Coupon):
        coupon = coupon_or_redirect
    else:
        return coupon_or_redirect
    coupon.expiration_date = frmt_expiration_date_for_dsp(
        coupon.expiration_date)
    all_locations = coupon.location.all().order_by('id')
    # Create coordinates list for map.
    location_coords = coupon.get_location_coords_list()  
    location_list, display_city = coupon.get_location_string()
    display_location = list_as_text(location_list)
    title, meta_description = SINGLE_COUPON.get_coupon_title_meta_desc(site,
        coupon, display_city, display_location)
    # Check if this user is a consumer subscribed to "Email" Subscription.
    is_email_subscription = check_for_email_subscription(request)
    is_a_subscriber = check_if_user_is_a_subscriber(request)
    context_instance_dict = {'coupon': coupon, 'title': title,
        'business_active_coupon_count': len(ALL_COUPONS.get_business_coupons(
            business_id=coupon.offer.business.id, site=site)[0]),
        'meta_description': meta_description, 
        'canonical': SINGLE_COUPON.get_coupon_canonical(site, coupon,
            'view-single-coupon', {'slug': slug, 'coupon_id':coupon_id}),
        'all_locations': all_locations,
        'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS, 
        'valid_days': VALID_DAYS.create_valid_days_string(coupon), 
        'js_single_coupon': 1,
        'onload_single_coupon': 1,
        'is_email_subscription':is_email_subscription, 
        'is_a_subscriber':is_a_subscriber, 
        'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
        'fb_dict': build_fb_like_meta(site, coupon)}
    if location_coords:
        context_instance_dict.update({'location_coords' : location_coords})
    if is_email_subscription and not is_a_subscriber:
        sample_phone_text = SINGLE_COUPON.set_sample_phone_display_text(request)
        context_instance_dict.update({'sample_phone_text': sample_phone_text, 
            'button_text': 'Text Me!'})         
    is_eligible_to_win = check_if_eligible_to_win(request)
    slot_price, flyer_price, consumer_count = get_unlocked_data(site)
    context_instance_dict.update(get_incremented_pricing(consumer_count))
    context_instance_dict.update({'is_eligible_to_win': is_eligible_to_win,
        'slot_price': slot_price, 
        'flyer_price': flyer_price,
        'consumer_count': consumer_count})
    if request.method == 'POST':
        return post_common_registration(request, is_email_subscription,
            is_a_subscriber, 'coupon/display_single_coupon.html',
            context_instance_dict)
    else:
        RecordAction().delay(action_id=2, coupon_id=coupon_id,
            consumer_id=get_consumer_id_in_session(request))
        return get_common_registration(request, is_email_subscription,
            is_a_subscriber, 'coupon/display_single_coupon.html',
            context_instance_dict)

def show_all_coupons_this_business(request, slug, business_id):
    """ Display current coupons of a given business. """
    site = get_current_site(request)
    try:
        business = Business.objects.select_related(
                'business_profile_description', 'advertiser__site__id'
            ).defer('advertiser__site__envelope',
                'advertiser__site__geom', 'advertiser__site__point'
            ).get(id=business_id)
    except Business.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    if slug != business.slug():
        return HttpResponsePermanentRedirect(reverse(
            'view-all-businesses-coupons',
            kwargs={'slug': business.slug(), 'business_id': business_id}))
    all_coupons, coupon_ids = ALL_COUPONS.get_business_coupons(business_id, site)
    if not coupon_ids:
        # No coupons returned for this business_id, redirect to view-all-offers
        # 302 redirect because this page might be valid in the future.
        return HttpResponseRedirect(reverse('all-coupons-msg',
            kwargs={'msg': 1}))
    all_locations = get_locations_for_coupons(all_coupons)
    # Create coordinates list for map.
    location_coords = get_location_coords_list(all_locations)
    record_action_multiple_coupons.delay(action_id=1,
        coupon_ids=tuple(coupon_ids),
        consumer_id=get_consumer_id_in_session(request))
    meta_dict = get_meta_for_business(business, all_locations)
    title = meta_dict['title']
    meta_description = meta_dict['desc']
    canonical = ''
    if site.id != business.advertiser.site_id:
        url_conf_id = business.advertiser.site_id
        if url_conf_id == 1: # National, Bulk should use site 2.
            url_conf_id = 2
        canonical = "%s%s" % (settings.HTTP_PROTOCOL_HOST, reverse(
            'view-all-businesses-coupons', 
            kwargs={'slug':business.slug(), 'business_id':business_id},
            urlconf='urls_local.urls_%s' % url_conf_id))
    for coupon in all_coupons:
        valid_days = VALID_DAYS.create_valid_days_string(coupon)
        coupon.expiration_date = frmt_expiration_date_for_dsp(
                                                        coupon.expiration_date)
    # Check if this user is a consumer that is subscribed to "Flyer".
    is_email_subscription = check_for_email_subscription(request)
    is_a_subscriber = check_if_user_is_a_subscriber(request)
    context_instance_dict = {
        'title': title,
        'meta_description': meta_description,
        'canonical': canonical,
        'all_coupons': all_coupons,
        'coupon_id': all_coupons[0].id,
        'coupon': all_coupons[0], # dsp_single_location expects a coupon.
        'all_locations': all_locations, 
        'business': business, 
        'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS,
        'js_all_coupons_this_business': 1,
        'onload_all_coupons_this_business': 1,
        'is_email_subscription':is_email_subscription,
        'is_a_subscriber':is_a_subscriber, 
        'valid_days': valid_days, 
        'http_protocol_host': settings.HTTP_PROTOCOL_HOST}
    if location_coords:
        context_instance_dict.update({'location_coords' : location_coords})
    if is_email_subscription and not is_a_subscriber:
        sample_phone_text = SINGLE_COUPON.set_sample_phone_display_text(
            request)
        context_instance_dict.update({'sample_phone_text': sample_phone_text, 
            'button_text': 'Text Me!'})         
    slot_price, flyer_price, consumer_count = get_unlocked_data(site)
    context_instance_dict.update(
        get_incremented_pricing(consumer_count))
    context_instance_dict.update({
        'is_eligible_to_win': check_if_eligible_to_win(request),
        'slot_price': slot_price,
        'flyer_price': flyer_price,
        'consumer_count': consumer_count})
    if request.method == 'POST':
        return post_common_registration(request, is_email_subscription,
            is_a_subscriber,
            'coupon/display_all_coupons_for_this_business.html',
            context_instance_dict)
    else:
        return get_common_registration(request, is_email_subscription,
            is_a_subscriber, 
            'coupon/display_all_coupons_for_this_business.html',
            context_instance_dict)

def print_single_coupon(request, coupon_id):
    """ The 'print this coupon' page. """
    try:
        coupon = Coupon.objects.select_related('offer','offer__business').get(
            id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    coupon_code = create_coupon_code(coupon)
    business = coupon.offer.business
    coupon.__dict__['business'] = business
    coupon.expiration_date = frmt_expiration_date_for_dsp(
        coupon.expiration_date)
    location_coords = coupon.get_location_coords_list()
    valid_days = VALID_DAYS.create_valid_days_string(coupon)
    RecordAction().delay(action_id=3, coupon_id=coupon_id,
        consumer_id=get_consumer_id_in_session(request))
    
    # Ensure coupon (qr_code and logo link) are branded to slot's site.
    site = coupon.get_site()
    url_conf = 'urls_local.urls_%s' % site.id
    context_dict = {'coupon':coupon, 
        'all_locations':coupon.location.all(),
        'coupon_code':coupon_code, 
        'ten_coupon_restrictions':TEN_COUPON_RESTRICTIONS, 
        'valid_days':valid_days,
        'js_print_single_coupon': 1,
        'onload_print_single_coupon': 1,
        'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
        'site': site,
        'single_coupon_qr_code_link': reverse('view-single-coupon', url_conf, 
            kwargs={'slug': coupon.slug(), 'coupon_id': coupon.id}),
        'all_coupons_link': reverse('all-coupons', url_conf)
        }
    if location_coords:
        context_dict.update({'location_coords': location_coords})
    return render_to_response('coupon/display_print_single_coupon.html', 
        context_dict,
        context_instance=RequestContext(request))

def window_display(request, coupon_id):
    """ Advertiser Window Display """
    try:
        coupon = Coupon.objects.select_related('offer','offer__business').get(
            id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    business = coupon.offer.business
    coupon.__dict__['business'] = business
    coupon.expiration_date = frmt_expiration_date_for_dsp(
        coupon.expiration_date)
    RecordAction().delay(action_id=3, coupon_id=coupon_id,
        consumer_id=get_consumer_id_in_session(request))
    referer = request.META.get('HTTP_REFERER', None)
    return render_to_response('coupon/display_window_display.html', 
        {'coupon':coupon, 
        'ten_coupon_restrictions':TEN_COUPON_RESTRICTIONS, 
        'js_print_single_coupon': 1,
        'onload_print_single_coupon': 1,
        'http_protocol_host' : settings.HTTP_PROTOCOL_HOST,
        'qr_image_path': build_adv_url_with_ad_rep(business.advertiser, 
            reverse('view-all-businesses-coupons', 
            kwargs={'slug': business.slug(), 'business_id': business.id})),
        'referer':referer}, context_instance=RequestContext(request))

def show_email_coupon(request, coupon_id):
    """ Display the 'email this coupon' page.
    When a user does not have a consumer in session, this view requires that
    user to enter in their email and zipcode in order to print coupons. The
    first coupon will be sent to their email account and they will be able to
    print coupons forever as long as that consumer remains in session.
    """
    try:
        coupon = Coupon.objects.select_related(
            'offer', 'offer__business').get(id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    # Google sees this as a page so it should get a unique title. 
    context_instance_dict = {'title': '%s %s print coupon' % 
            (coupon.offer.business.business_name, coupon.offer.headline),
        'business_name': coupon.offer.business.business_name,
        'button_text': 'Hello', 
        'js_email_coupon': 1,
        'coupon_id': coupon.id,
        'email_coupon':True}
    
    if request.method == 'POST':        
        try:
            # Check if user exists already.
            email = request.POST.get('email', None)
            if email:
                consumer = Consumer.objects.get(email__iexact=email)
                build_session_from_user(request, consumer)
                json_data = {'is_already_registered':True}
                json = simplejson.dumps(json_data)
                return HttpResponse(json, mimetype='application/json')                
            else:
                is_already_registered = False
        except Consumer.DoesNotExist:
            is_already_registered = False        
        consumer_reg_form = ConsumerRegistrationForm(request.POST)
        if consumer_reg_form.is_valid():
            email = consumer_reg_form.cleaned_data.get('email', None)
            process_consumer_registration(request, 
            created_redirect=reverse('consumer-registration-confirmation'), 
            required_fields_not_filled_out='coupon/display_email_coupon.html', 
            context_instance=RequestContext(request, context_instance_dict),
            coupon_id=coupon_id)
            email = consumer_reg_form.cleaned_data.get('email', None)
            consumer = Consumer.objects.get(email__iexact=email)
            json_data = {'is_already_registered':is_already_registered}
        else:
            json_data = {'errors': consumer_reg_form.errors}
        json = simplejson.dumps(json_data)
        return HttpResponse(json, mimetype='application/json')
    else:
        # Display the consumer registration form.
        initial_data = get_consumer_reg_initial_data(request)
        consumer_reg_form = ConsumerRegistrationForm(initial=initial_data)  
        return render_to_response('coupon/display_email_coupon.html', 
            {'consumer_reg_form': consumer_reg_form,
             'coupon_id':coupon_id}, 
            context_instance=RequestContext(request, context_instance_dict))
        
def show_send_sms_single_coupon(request, coupon_id):
    """ Display the 'send this coupon to a mobile phone' functionality. """
    try:
        coupon = Coupon.objects.select_related(
            'offer', 'offer__business').get(id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    sample_phone_text = """<p><strong>71010:</strong><br />
        10Coupon Alrts: %s Details on Website.</p>""" % coupon.sms
    # Google sees this as a page so it should get a unique title. 
    context_instance_dict = {'title': '%s %s mobile coupon' % 
            (coupon.offer.business.business_name, coupon.offer.headline),
        'business_name': coupon.offer.business.business_name, 
        'sample_phone_text': sample_phone_text, 
        'button_text': 'Send To My Cell Phone', 
        'js_send_to_phone': 1}
    if request.method == 'POST':
        subscriber_reg_form = SubscriberRegistrationForm(request.POST)  
        is_registered = process_subscriber_registration(request, 
            required_fields_not_filled_out=\
                'coupon/display_send_sms_single_coupon.html', 
            context_instance=RequestContext(request, context_instance_dict), 
            coupon_id=coupon_id) 
        if is_registered:
            subscriber_reg_form.get_cleaned_data_for_sms() 
            mobile_phone_number = \
                subscriber_reg_form.cleaned_data['mobile_phone_number']
            mobile_phone = MobilePhone.objects.get(
                mobile_phone_number=mobile_phone_number)
            if mobile_phone.carrier.id == 1:
                try:
                    mobile_phone = save_phone_by_carrier_lookup(
                        mobile_phone.mobile_phone_number)
                except ValidationError:
                    context_dict = {'subscriber_reg_form': subscriber_reg_form}
                    return render_to_response(
                        'coupon/display_send_sms_single_coupon.html', 
                        context_dict, context_instance=RequestContext(request, 
                            context_instance_dict))
            return send_sms_single_coupon(request, coupon_id, mobile_phone, 
                coupon.offer.business.business_name, sample_phone_text)
        else:
            context_dict = {'subscriber_reg_form': subscriber_reg_form}
            return render_to_response(
                'coupon/display_send_sms_single_coupon.html', 
                context_dict, context_instance=RequestContext(request, 
                    context_instance_dict))
    else:
        initial_data = get_subscriber_reg_init_data(request.session)
        # Display the subscriber registration form.
        subscriber_reg_form = SubscriberRegistrationForm(initial=initial_data)  
        return render_to_response('coupon/display_send_sms_single_coupon.html', 
            {'subscriber_reg_form': subscriber_reg_form}, 
            context_instance=RequestContext(request, context_instance_dict))

def send_sms_single_coupon(request, coupon_id, mobile_phone, business_name, 
        sample_phone_text):
    """ Send a coupon to a mobile phone. """
    try:
        coupon = Coupon.objects.select_related(
            'offer', 'offer__business').get(id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    coupon_code = ''
    if coupon.is_coupon_code_displayed:
        coupon_code = create_coupon_code(coupon, 4)
    business = coupon.offer.business
    if mobile_phone.carrier.id != 1:
        context = { 'coupon': coupon, 'coupon_code': coupon_code }
        try:
            send_sms(template='sms/coupon.html', 
                smsto=mobile_phone.mobile_phone_number, context=context)
        except ValidationError:
            pass
    coupon.__dict__['business'] = business
    coupon.expiration_date = frmt_expiration_date_for_dsp(
        coupon.expiration_date)
    RecordAction().delay(action_id=4, coupon_id=coupon_id,
        consumer_id=get_consumer_id_in_session(request))
    return render_to_response(
        'coupon/display_send_sms_single_coupon_confirmation.html', 
        {'coupon':coupon, 
         'coupon_code':coupon_code,
         'business_name':business_name, 
         'sample_phone_text':sample_phone_text}, 
        context_instance=RequestContext(request))

def external_click_coupon(request, coupon_id):
    """ Record that a person clicked a 'precise url' link for a coupon, and
    redirects to that url.
    """
    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('home'))
    if not coupon.precise_url:
        return HttpResponseRedirect(reverse('home'))
    RecordAction().delay(action_id=8, coupon_id=coupon_id,
        consumer_id=get_consumer_id_in_session(request))
    return HttpResponsePermanentRedirect(coupon.precise_url)

def flyer_click_coupon(request, coupon_id, payload=None):
    """ Record that a person click a flyer link for a coupon, and redirects to
    the coupon.
    """
    try:
        coupon = Coupon.objects.select_related().get(id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    if payload and payload != '0': # 0 is spoofed payload for sample flyer.
        PAYLOAD_SIGNING.handle_payload(request, payload)
        RecordAction().delay(action_id=9, coupon_id=coupon_id,
            consumer_id=get_consumer_id_in_session(request))
    slug = coupon.slug()
    # Redirect to the regular coupon view page, w/o flyer/tracking stuff.
    return HttpResponsePermanentRedirect(reverse('view-single-coupon',
        args=(slug, coupon_id)))

def flyer_click_show_single_coupon(request, slug, coupon_id,
        consumer_email_hash):
    """ Pending deprectation 1/1/2012. New version is flyer_click_coupon.
    Records that a person click a flyer link for a coupon, and redirects to
    the coupon.
    """
    try:
        coupon = Coupon.objects.select_related().get(id=coupon_id)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    try: 
        email_hash = email_hash_decypher(consumer_email_hash)
        consumer = Consumer.objects.get(email_hash=email_hash)
        LOG.debug("Got consumer id %d, email %s for  %s" % 
            (consumer.id, consumer.email, consumer_email_hash))
        RecordAction().delay(action_id=9, coupon_id=coupon_id,
            consumer_id=consumer.id)
        create_consumer_in_session(request, consumer)
    except Consumer.DoesNotExist:
        LOG.debug("no consumer found for %s" % consumer_email_hash)    
        RecordAction().delay(action_id=9, coupon_id=coupon_id,
            consumer_id=get_consumer_id_in_session(request))
    if slug != coupon.slug():
        slug = coupon.slug()
    # Redirect to the regular coupon view page, w/o flyer/tracking stuff.
    return HttpResponsePermanentRedirect(reverse('view-single-coupon',
        args=(slug, coupon_id)))

def scan_coupon_qr_code(request, slug, coupon_id, code):
    """  Record scan of coupon qr code, then redirects to the coupon. """
    try:
        coupon = Coupon.objects.get(id=coupon_id) 
        if check_coupon_code(coupon, code) != -1: 
            RecordAction().delay(action_id=12, coupon_id=coupon_id,
                consumer_id=get_consumer_id_in_session(request))
        else: 
            return HttpResponseRedirect(reverse('all-coupons'))
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    return HttpResponsePermanentRedirect(reverse('view-single-coupon',
        args=(slug, coupon_id)))

def tweet_coupon(request, coupon_id, textflag=None): 
    """ Record click of Tweet (to Twitter) then redirects to the coupon. """
    try:
        coupon = Coupon.objects.get(id=coupon_id) 
        RecordAction().delay(action_id=13, coupon_id=coupon_id,
            consumer_id=get_consumer_id_in_session(request))
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    twitter_url = "http://twitter.com/share?text="
    if textflag:
        twitter_url += TWITTER_SERVICE.build_tweet_message(coupon)
        twitter_url = twitter_url.replace('%', '%25')
        twitter_url = twitter_url.replace('&', '%26')
    else:
        twitter_url += get_current_site(request).domain
        if check_contest_is_running(): 
            if check_if_eligible_to_win(request):
                twitter_url += " I'm in the Drawing for $10,000! Sign up for\
                 Coupons, Qualify to Win! Rules Online"
            else:
                twitter_url += " Sign up for coupons. Qualify to Win $10,000!\
                 See rules &amp; details on website"
        else:
            twitter_url += " - coupons and deals that save you money weekly:"
    twitter_url += "&url=http://%s%s" % (request.META['HTTP_HOST'], 
        reverse('view-single-coupon', 
        kwargs={'slug':coupon.slug(), 'coupon_id':coupon.id}))
    return HttpResponseRedirect(twitter_url)

def facebook_coupon(request, coupon_id): 
    """ Record Facebook share of coupon with delay of 3 minutes (180 secs) """
    try:
        coupon = Coupon.objects.get(id=coupon_id)
        LOG.debug('clicked facebook coupon')
        update_facebook_share_coupon.apply_async(kwargs={'coupon' : coupon}, 
            countdown=180)
    except Coupon.DoesNotExist:
        return HttpResponseRedirect(reverse('all-coupons'))
    if request.is_ajax():
        json = simplejson.dumps({})
        return HttpResponse(json, mimetype='application/json')
    else:
        return HttpResponseRedirect(reverse('all-coupons'))

@market_required('all-coupons')
def show_all_coupons(request, msg=None):
    """ Show market home page (not site 1) with lots of coupons and maybe a 
    consumer registration form. 
    """
    # Check if this user is a consumer that is subscribed to "Flyer".
    context_instance_dict = {}
    is_eligible_to_win = check_if_eligible_to_win(request)
    if is_eligible_to_win:
        is_email_subscription = True
        is_a_subscriber = True
    else:
        is_email_subscription = check_for_email_subscription(request)
        is_a_subscriber = check_if_user_is_a_subscriber(request)
    if is_email_subscription and not is_a_subscriber:
        sample_phone_text = SINGLE_COUPON.set_sample_phone_display_text(
            request)
        context_instance_dict.update({
            'sample_phone_text': sample_phone_text, 
            'button_text': 'Text Me!'})
    else:
        if is_email_subscription:
            context_instance_dict.update({
                'http_protocol_host': settings.HTTP_PROTOCOL_HOST})        
    context_instance_dict.update({
        'is_eligible_to_win': is_eligible_to_win,
        'is_email_subscription': is_email_subscription,
        'is_a_subscriber': is_a_subscriber})
    if request.method == 'POST':
        search_coupons_form = SearchCouponForm(request.POST)    
    else:
        search_coupons_form = SearchCouponForm(request.GET)
    context_instance_dict.update({
        'search_coupons_form': search_coupons_form,
        'js_all_coupons': 1, 'js_search_coupons': 1})    
    if search_coupons_form.is_valid():
        coupons, suggestion = search_coupons_form.process_search(request)
        context_instance_dict.update({
    #            'page': page,
    #            'paginator': paginator,
    #            'query': query,
            'suggestion': suggestion,
            'all_coupons': coupons})
    if getattr(settings, 'HAYSTACK_INCLUDE_SPELLING', False):
        context_instance_dict['suggestion'] = \
            search_coupons_form.get_suggestion()
    if request.method == 'POST' and 'process_search_btn' not in request.POST:
        return post_common_registration(request, is_email_subscription,
            is_a_subscriber, "coupon/display_all_coupons.html",
            context_instance_dict)
    category = request.GET.get('cat', None)
    if request.method == 'GET' and category is None and \
       request.GET.get('q', None) is None:
#        if search_coupons_form.is_valid():
#        #if 'process_search_btn' in request.POST:
#            coupons = search_coupons_form.process_search(request)
##            paginator = Paginator(coupons, 5)
##            try:
##                page = paginator.page(int(request.POST.get('page', 1)))
##            except InvalidPage:
##                page = paginator.page(1)
#            context_instance_dict.update({
#                'search_coupons_form': search_coupons_form,
##                'page': page,
##                'paginator': paginator,
##                'query': query,
#                'suggestion': None,
#                'all_coupons': coupons})
#            if getattr(settings, 'HAYSTACK_INCLUDE_SPELLING', False):
#                context_instance_dict['suggestion'] = search_coupons_form.get_suggestion()
#        else:
#            return post_common_registration(request, is_email_subscription,
#                is_a_subscriber, "coupon/display_all_coupons.html",
#                context_instance_dict)
#    else:
        context_instance_dict.update(get_home_data(request))
        #search_coupons_form = SearchCouponForm()
    context_dict = {}
    if is_email_subscription and not is_a_subscriber:
        subscriber_reg_form = SubscriberRegistrationForm(
            initial=get_subscriber_reg_init_data(request.session))
        context_dict['subscriber_reg_form'] = subscriber_reg_form
    else:
        if not is_email_subscription:
            consumer_reg_form = ConsumerRegistrationForm(
                initial=get_consumer_reg_initial_data(request))
            context_dict['consumer_reg_form'] = consumer_reg_form
    site = get_current_site(request)
    # Context var msg checks if we were redirected from invalid coupon.
    context_dict.update({'msg' : msg, 
        'close_sites' : site.get_or_set_close_sites(),
        'municipality_division': site.get_state_division_type(plural_form=True),
        'county_list' : list_as_text(site.get_or_set_counties())})
    return render_to_response("coupon/display_all_coupons.html",
        context_dict,
        context_instance=RequestContext(request, context_instance_dict,
            [products]))

def show_all_coupons_facebook(request):
    """ Display coupons similar to show_all_coupons in a narrow template, minus
    the registration forms for use as a Facebook app.
    """
    context_instance_dict = {'is_iframe': True}
    context_instance_dict.update(get_home_data(request))
    return render_to_response("coupon/display_all_coupons_facebook.html",
        context_instance=RequestContext(request, context_instance_dict))
