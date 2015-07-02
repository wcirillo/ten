""" Service functions and a context processor for 10coupons sweepstakes. """
#pylint: disable=W0613
import datetime
import random
import logging

from django.conf import settings
from django.db.models import Q

from consumer.email_subscription.service import check_for_email_subscription
from consumer.service import qry_qualified_consumers
from subscriber.service import check_if_subscriber_is_verified

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

def check_contest_is_running():
    """ Return boolean: is now during the contest? """
    now = datetime.datetime.now()
    start = datetime.datetime.strptime(settings.CONTEST_START_DATE, '%Y-%m-%d')
    end = datetime.datetime.strptime(settings.CONTEST_END_DATE, '%Y-%m-%d')
    return start < now < end
    
def contest_is_running(request):
    """ Context processor returning the value of check_contest_is_running. """
    return {
        'contest_is_running': check_contest_is_running()
    }

def check_if_eligible_to_win(request):
    """Single function that checks all criteria to validate if a user is
    eligible to win. Returns True if all criteria validates.
    """
    is_eligible_to_win = False
    try:
        this_consumer = request.session['consumer']
        if this_consumer['is_email_verified']:
            if check_for_email_subscription(request):
                if check_if_subscriber_is_verified(request):
                    is_eligible_to_win = True
    except KeyError:
        pass        
    return is_eligible_to_win
    
def select_eligible_consumers():
    """ Return a QuerySet of fully qualified consumers eligible to win the 
    sweepstakes (excludes staff and media partners). 
    """
    return qry_qualified_consumers().exclude(
            is_staff=True).exclude(
                Q(mediapartner__affiliates__isnull=False)
                | Q(mediapartner__media_groups__isnull=False))
   
def select_random_winner():
    """ Returns a random Consumer from eligible consumers. """
    eligible_consumers = select_eligible_consumers()
    eligible_count = eligible_consumers.count()
    if eligible_count == 0:
        raise Exception('No eligible consumers')
    random_index = random.randint(0, eligible_consumers.count() - 1)
    random_consumer = eligible_consumers[random_index]
    LOG.info('Out of %s eligible consumers, random consumer is %s!' % (
        eligible_count, random_consumer))
    LOG.info('Random consumer id is %s!' % random_consumer.id)
    return random_consumer
