""" Subscriber Views """

import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from common.context_processors import current_site, products
from common.custom_format_for_display import format_phone
from consumer.email_subscription.service import check_for_email_subscription
from consumer.models import Consumer
from consumer.service import (create_subscriber_for_consumer,
    update_subscriber_of_consumer)
from common.contest import check_if_eligible_to_win
from common.service.common_service import get_home_data
from common.utils import get_core_path_info
from coupon.service.single_coupon_service import SINGLE_COUPON
from market.service import check_for_cross_site_redirect, get_current_site
from common.session import clear_session, create_subscriber_in_session
from sms_gateway.service import send_sms
from subscriber.forms import (SubscriberRegistrationForm,
    get_subscriber_reg_init_data)
from subscriber.models import Subscriber, MobilePhone, SMSSubscription
from subscriber.service import (add_update_subscriber,
    check_if_user_is_a_subscriber)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

def show_subscriber_registration(request):
    """ Display the subscriber registration form. """
    sample_phone_text = SINGLE_COUPON.set_sample_phone_display_text(request)
    is_eligible_to_win = check_if_eligible_to_win(request)
    context_dict = {}
    context_instance_dict = {'is_eligible_to_win': is_eligible_to_win,
        'sample_phone_text': sample_phone_text, 'button_text':'Text Me!',
        'suppress_contest_reward': True} 
    if request.method == 'POST':
        return process_subscriber_registration(request, 
            created_redirect=reverse(subscriber_reg_confirmation), 
            required_fields_not_filled_out=
                'registration/display_subscriber_registration.html',
            context_instance = RequestContext(request, context_instance_dict, 
                processors=[current_site, products])
            )
    else:
        try:
            email = request.session['consumer']['email']
        except KeyError:
            email = ''
        initial_data = get_subscriber_reg_init_data(request.session)
        # Display the subscriber registration form.
        subscriber_reg_form = SubscriberRegistrationForm(initial=initial_data)    
        context_dict['email'] = email
        context_dict['subscriber_reg_form'] = subscriber_reg_form
        return render_to_response(
            'registration/display_subscriber_registration.html', 
            context_dict, 
            context_instance = RequestContext(request, context_instance_dict, 
                processors=[current_site, products]))

def process_subscriber_registration(request, required_fields_not_filled_out, 
        context_instance, created_redirect=None, coupon_id=None, 
        do_not_redirect=False):
    """ Do the work of subscriber registration. """
    # Populate the SubscriberRegistrationForm.
    subscriber_reg_form = SubscriberRegistrationForm(request.POST)    
    context_dict = {'subscriber_reg_form': subscriber_reg_form}
    # Check all required fields are filled out.
    if subscriber_reg_form.is_valid():
        # Use Cleaned subscriber_reg_form data        
        mobile_phone_number = subscriber_reg_form.cleaned_data[
            'mobile_phone_number']
        try:
            consumer_id = request.session['consumer']['consumer_id']
        except KeyError:
            consumer_id = False
        carrier = subscriber_reg_form.cleaned_data['carrier']
        subscriber_zip_postal = subscriber_reg_form.cleaned_data[
            'subscriber_zip_postal']
        site, created_redirect, curr_site = check_for_cross_site_redirect(
            request, subscriber_zip_postal, created_redirect)
        # If we supposedly have a registered consumer in session.
        if consumer_id:
            LOG.debug('consumer_id: %s' % consumer_id)
            try:
                # Make sure consumer exists already.
                consumer = Consumer.objects.get(pk=consumer_id)
                if consumer.subscriber_id:
                    # If this consumer is associated with a subscriber.
                    phone_number_already_in_use = update_subscriber_of_consumer(
                        consumer=consumer, carrier_id=carrier.id, 
                        mobile_phone_number=mobile_phone_number, 
                        subscriber_zip_postal=subscriber_zip_postal, site=site)
                else:
                    # Create and relate subscriber.
                    phone_number_already_in_use = create_subscriber_for_consumer(
                        consumer=consumer, carrier_id=carrier.id, 
                        mobile_phone_number=mobile_phone_number, 
                        subscriber_zip_postal=subscriber_zip_postal, site=site)
                if phone_number_already_in_use:
                    context_dict.update({
                        'msg_mobile_phone_number_already_exists': True})
                    # If on all-coupons page ('/coupons/' or '/1/'), the 
                    # latter is home w/ msg of invalid coupon, then load home_data.
                    core_path_info = get_core_path_info(request, curr_site)
                    if core_path_info in ('/coupons/', '/1/'):
                        context_dict.update(get_home_data(request)) 
                    return render_to_response(
                        required_fields_not_filled_out, context_dict, 
                        context_instance=context_instance)
            except Consumer.DoesNotExist:
                add_update_subscriber(carrier_id=carrier.id, 
                    mobile_phone_number=mobile_phone_number, 
                    subscriber_zip_postal=subscriber_zip_postal, site=site)
        else:
            # No Consumer found in session.
            LOG.debug('No consumer')
            add_update_subscriber(carrier_id=carrier.id, 
                mobile_phone_number=mobile_phone_number, 
                subscriber_zip_postal=subscriber_zip_postal, site=site)
        mobile_phone = MobilePhone.objects.get(
            mobile_phone_number=mobile_phone_number)
        subscriber = Subscriber.objects.get(mobile_phones=mobile_phone)
        create_subscriber_in_session(request, subscriber)
        request.session.modified = True
        try:
            subscriber.sms_subscription.get(id=1)
        except SMSSubscription.DoesNotExist:
            if int(carrier.id)  > 1:
                send_sms(template='sms/request_double_opt_in.html', 
                    smsto=mobile_phone_number)
        # Send to phone or do_not_redirect for home page ajax processing.
        if coupon_id or do_not_redirect:
            return True
        else:
            return HttpResponseRedirect(created_redirect)   
    else:
        site = get_current_site(request)
        core_path_info = get_core_path_info(request, site)
        # If on all-coupons page ('/coupons/' or '/1/'), the latter is home 
        # w/ msg of invalid coupon, then load home_data.
        if core_path_info in ('/coupons/', '/1/'):
            context_dict.update(get_home_data(request))
            # Check if this user is a consumer that is subscribed to "Flyer".
            is_email_subscription = check_for_email_subscription(request)
            is_a_subscriber = check_if_user_is_a_subscriber(request)
            if is_email_subscription and not is_a_subscriber:
                sample_phone_text = \
                    SINGLE_COUPON.set_sample_phone_display_text(request)
                context_dict.update({
                    'sample_phone_text': sample_phone_text, 
                    'button_text': 'Text Me!'})
            elif is_email_subscription:
                context_dict.update({
                    'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
                    'js_home': 1})        
            is_eligible_to_win = check_if_eligible_to_win(request)
            context_dict.update({
                'is_eligible_to_win': is_eligible_to_win,
                'is_email_subscription': is_email_subscription,
                'is_a_subscriber': is_a_subscriber})
#            context_instance = RequestContext(request, context_instance_dict,
#                [products])
        try:
            email = request.session['consumer']['email']
        except KeyError:
            email = ''
        # Send to phone or do_not_redirect for home page ajax processing.
        if coupon_id or do_not_redirect:
            return False
        else:
            context_dict['email'] = email
            # Required fields not filled out. Return to page with 
            # subscriber_reg_form data.
            return render_to_response(required_fields_not_filled_out, 
                context_dict, context_instance=context_instance)

def subscriber_reg_confirmation(request):
    """ Success confirmation page after subscriber registration. """
    is_email_subscription = check_for_email_subscription(request)
    is_eligible_to_win = check_if_eligible_to_win(request)
    context_instance_dict = {'is_eligible_to_win':is_eligible_to_win,
                             'is_email_subscription':is_email_subscription}
    context_instance = RequestContext(request, context_instance_dict)
    try:
        this_consumer = request.session['consumer']
        this_subscriber = this_consumer['subscriber']
        mobile_phone_number = this_subscriber['mobile_phone_number']
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons'))
    context_dict = {
            'mobile_phone_number': format_phone(phone=mobile_phone_number)
            }
    return render_to_response(
        'registration/display_subscriber_registration_confirmation.html', 
        context_dict, 
        context_instance=context_instance)

def con_sub_reg_confirmation(request):
    """ Success confirmation page after a user successfully registers as a 
    consumer and a subscriber. """
    is_email_subscription = check_for_email_subscription(request)
    is_eligible_to_win = check_if_eligible_to_win(request)
    context_instance_dict = {'is_eligible_to_win':is_eligible_to_win,
                             'is_email_subscription':is_email_subscription}
    context_instance = RequestContext(request, context_instance_dict)
    try:
        this_consumer = request.session['consumer']
        this_subscriber = this_consumer['subscriber']
        mobile_phone_number = this_subscriber['mobile_phone_number']
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons'))
    context_dict = {
            'is_email_verified': this_consumer.get('is_email_verified', False),
            'mobile_phone_number': format_phone(phone=mobile_phone_number)
            }
    return render_to_response(
        'registration/display_con_sub_reg_confirmation.html', 
        context_dict, 
        context_instance=context_instance)

def log_out_subscriber(request):
    """ Show logout form for subscriber. """ 
    if request.method == 'POST':
        return process_subscriber_registration(
            request, 
            created_redirect=reverse(subscriber_reg_confirmation), 
            required_fields_not_filled_out=
                'registration/display_subscriber_registration.html',
            context_instance=RequestContext(request))
    else:
        # Display the subscriber registration form.
        clear_session(request)
        return HttpResponseRedirect(reverse(show_subscriber_registration))
