""" Service functions for email_subscription of a consumer. """

from consumer.models import EmailSubscription

def check_for_email_subscription(request, subscription_type=1):
    """ Does the consumer has an email subscription of 'Email'? """
    try:
        # Check if consumer is in session.
        email = request.session['consumer']['email']
        try:
            EmailSubscription.objects.get(id=subscription_type, 
                consumers__email=email)
            return True
        except EmailSubscription.DoesNotExist:
            # Not subscribed.
            return False
    except KeyError:
        # No consumer currently in session.
        return False
