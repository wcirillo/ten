""" Sms_subscription model service functions for the subscriber app. """

from subscriber.models import SMSSubscription

def check_for_sms_subscription(request):
    """ Is subscriber in session opted in to receive sms messages? """
    flag = False
    try:
        # Check if subscriber is in session.
        subscriber_id = request.session['consumer']['subscriber']['subscriber_id']
        # Check if this subscriber has an sms subscription of 'SMS'.
        if subscriber_id:
            try:
                SMSSubscription.objects.get(pk=1, subscribers__id=subscriber_id)
                flag = True # SMS subscription found.
            except SMSSubscription.DoesNotExist:
                pass
    except KeyError:
        pass # No subscriber currently in session.
    return flag
