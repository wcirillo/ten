""" Context processors for the firestorm app of project ten."""
import logging

from common.session import get_consumer_id_in_session
from firestorm.models import AdRep, AdRepWebGreeting

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def referring_ad_rep(request):
    """
    Context processor used to display 'replicated website' info.

    Pulls id from the session if it exists. If not, but there is a user in
    session, checks to see if this is an advertiser of an ad_rep (preferred),
    then a consumer of an ad_rep.
    """
    context = {}
    ad_rep_id = request.session.get('ad_rep_id', None)
    LOG.debug('ad_rep_id: %s' % ad_rep_id)
    if ad_rep_id:
        LOG.debug('quit!')
        context.update({'ad_rep': AdRep.objects.get(id=ad_rep_id)})
        return context
    consumer_id = get_consumer_id_in_session(request)
    if consumer_id and not request.session.get('ad_rep_checked', False):
        # Is this an advertiser of an ad_rep.
        ad_rep = None
        try:
            ad_rep = AdRep.objects.get(
                ad_rep_advertisers__advertiser__id=consumer_id)
        except AdRep.DoesNotExist:
            # Is this a consumer of an ad_rep
            try:
                ad_rep = AdRep.objects.get(
                    ad_rep_consumers__consumer__id=consumer_id)
            except AdRep.DoesNotExist:
                pass
        if ad_rep:
            try:
                web_greeting = AdRepWebGreeting.objects.values_list(
                    'web_greeting', flat=True).get(ad_rep=ad_rep)
                LOG.debug('web_greeting: %s' % web_greeting)
                ad_rep.web_greeting = web_greeting
            except AdRepWebGreeting.DoesNotExist:
                pass
            context.update({'ad_rep': ad_rep})
        else:
            # Do not go through that for every request.
            request.session['ad_rep_checked'] = True
    return context
