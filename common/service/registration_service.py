""" Service functions for common registration processes for project ten. """
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext

from common.context_processors import current_site, products
from consumer.forms import (ConsumerRegistrationForm,
    get_consumer_reg_initial_data)
from consumer.views import process_consumer_registration
from subscriber.forms import (SubscriberRegistrationForm,
    get_subscriber_reg_init_data)
from subscriber.views import process_subscriber_registration

def post_common_registration(request, is_email_subscription, is_a_subscriber,
        template, context_instance_dict):
    """ Check for subscriber_zip_postal in the POST data to ensure we are not
    submitting the consumer registration form again.  CASE:  User hits
    the back button after reaching the consumer registration success page.
    Then resubmits the consumer registration form... is_email_subscription
    and not is_a_subscriber will be true on the POST, therefore we need
    to verify exactly which form we are submitting by accessing the
    appropriate form key.
    """
    if is_email_subscription and not is_a_subscriber \
    and ('subscriber_zip_postal' in request.POST):
        return process_subscriber_registration(request,
        created_redirect=reverse('subscriber-registration-confirmation'),
        required_fields_not_filled_out=template,
        context_instance = RequestContext(request, context_instance_dict,
            [products]))
    else:
        return process_consumer_registration(request,
        created_redirect=reverse('consumer-registration-confirmation'),
        required_fields_not_filled_out=template,
        context_instance=RequestContext(request, context_instance_dict,
            [products]))

def get_common_registration(request, is_email_subscription, is_a_subscriber,
        template, context_instance_dict):
    """ Display the correct registration form with the given template. """
    context_dict = {}
    processors = [products]
    if is_email_subscription and not is_a_subscriber:
        initial_data = get_subscriber_reg_init_data(request.session)
        subscriber_reg_form = SubscriberRegistrationForm(
            initial=initial_data)
        context_dict.update({'subscriber_reg_form': subscriber_reg_form})
        processors.append(current_site)
    elif not is_email_subscription:
        initial_data = get_consumer_reg_initial_data(request)
        consumer_reg_form = ConsumerRegistrationForm(
            initial=initial_data)
        context_dict['consumer_reg_form'] = consumer_reg_form
    return render_to_response(template, context_dict,
        context_instance=RequestContext(request, context_instance_dict,
            processors=processors))
