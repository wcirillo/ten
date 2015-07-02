""" Views of the consumer app of the ten project. """
#pylint: disable=W0613
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

from consumer.email_subscription.service import check_for_email_subscription
from consumer.forms import ConsumerRegistrationForm
from common.contest import check_if_eligible_to_win, check_contest_is_running
from common.session import build_session_from_user
from common.utils import get_core_path_info
from coupon.models import Coupon
from coupon.service.single_coupon_service import SINGLE_COUPON
from email_gateway.send import send_email
from firestorm.models import AdRepConsumer
from market.service import get_current_site
from subscriber.service import check_if_user_is_a_subscriber

def redirect_consumer_registration(request):
    """ Permanent redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('home'))

def process_consumer_registration(request, created_redirect, 
        required_fields_not_filled_out, context_instance, coupon_id=None,
        **kwargs):
    """ Processes consumer registration form. """
    do_not_redirect = kwargs.get('do_not_redirect', False)
    if do_not_redirect:
        # If we do a redirect it will be to home page (ajax request) because
        # they are not in the correct market for the zip they enter.
        created_redirect = '/'
    if coupon_id:
        try:
            coupon = Coupon.objects.select_related(
                'offer', 'offer__business').get(id=coupon_id)
        except Coupon.DoesNotExist:
            coupon_id = None
    consumer_reg_form = ConsumerRegistrationForm(request.POST)
    # Check all required fields are filled out.
    if consumer_reg_form.is_valid():
        # Add the AdRepConsumer before the create_consumer_session wipes out
        # the session keys.
        consumer = consumer_reg_form.save(request, created_redirect)
        AdRepConsumer.objects.create_update_rep(request, consumer)
        # Defining this here because build_session_from_user munges the
        # consumer object.
        try:
            if consumer.email != request.session['consumer']['email'] or \
            consumer.consumer_zip_postal \
            != request.session['consumer']['consumer_zip_postal']:
                build_session_from_user(request, consumer)
        except KeyError:
            build_session_from_user(request, consumer)
        if not consumer.is_email_verified:
            context = {'to_email': request.session['consumer']['email'],
                       'subject': 'IMPORTANT - Get your Coupons',
                       'from_address': 'Coupons', 
                       'ref_num': consumer.id,
                       'contest_is_running': check_contest_is_running()}
            if coupon_id:
                context.update({'subject':'Get your Coupon',
                                'coupon':coupon
                                })
            send_email(template='consumer_welcome', site=consumer.site,
                context=context)
        if coupon_id:
            return True
        elif do_not_redirect:
            return True, consumer_reg_form.url_to_change_market
        else:
            return HttpResponseRedirect(consumer_reg_form.redirect_path)   
    else: 
        site = get_current_site(request)
        context = {'consumer_reg_form': consumer_reg_form}
        # If on all-coupons page ('/coupons/' or '/1/'), the latter is home 
        # w/ msg of invalid coupon, then load home_data.
        if get_core_path_info(request, site) in ('/coupons/', '/1/'):
            # Check if this user is a consumer that is subscribed to "Flyer".
            is_email_subscription = check_for_email_subscription(request)
            is_a_subscriber = check_if_user_is_a_subscriber(request)
            if is_email_subscription and not is_a_subscriber:
                context.update({
                    'sample_phone_text': \
                        SINGLE_COUPON.set_sample_phone_display_text(request),
                    'button_text': 'Text Me!'})
            else:
                if is_email_subscription:
                    context.update({
                        'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
                        'js_home': 1})
            context.update({
                'is_eligible_to_win': check_if_eligible_to_win(request),
                'is_email_subscription': is_email_subscription,
                'is_a_subscriber': is_a_subscriber})
        if coupon_id or do_not_redirect:
            return False
        else:
            # All required fields are not filled out. Return to page with form 
            # data.
            return render_to_response(required_fields_not_filled_out, 
                context, context_instance=context_instance)

def consumer_reg_confirmation(request, coupon_id=None):
    """ Display success confirmation after consumer registration. """
    if coupon_id:
        try:
            coupon = Coupon.objects.select_related(
                'offer','offer__business').get(id=coupon_id)
        except Coupon.DoesNotExist:
            coupon = None
    else:
        coupon = None
    try:
        email = request.session['consumer']['email']     
        is_email_verified = request.session['consumer']['is_email_verified']
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons'))
    is_eligible_to_win = check_if_eligible_to_win(request)
    context_instance_dict = {'is_eligible_to_win':is_eligible_to_win}
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'registration/display_consumer_registration_confirmation.html', 
        {'email':email, 'is_email_verified':is_email_verified, 
        'coupon':coupon}, 
        context_instance=context_instance)
