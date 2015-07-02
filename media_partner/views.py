""" Views of the media_partner app of project ten. """
import logging

from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from pyflot import Flot

from market.service import get_current_site
from media_partner.decorators import media_partner_required
from media_partner.models import MediaPieShare
from media_partner.service import (filter_report_payments, get_user_type,
    can_view_this_report, get_json_data, get_report_list)
from media_partner.stats import SiteConsumerStats

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

@media_partner_required()
@login_required
def show_transaction_report(request,
    template_name='media_partner/display_transaction_report.html'):
    """ Display the transaction report to qualified users, for a given period.

    In the Transaction Report, a Media Partner can view the Transaction payments
    within a selected group of time.  Either all transactions since the launch
    of the market, or individual quarters, or even an individual month.
    """
    LOG.debug('Logged in.')
    user_type, media_partner = get_user_type(request)
    site = get_current_site(request)
    can_view_this_report_, media_group, affiliate = can_view_this_report(
        user_type, media_partner, site.id)
    if not can_view_this_report_:
        return HttpResponseRedirect(reverse('media-partner-sign-in'))
    all_create_dates = filter_report_payments(site).values('create_datetime')
    media_pie_shares = MediaPieShare.objects.filter(
        affiliate=affiliate).order_by('-start_date')
    if request.POST:
        data = get_json_data(request, site, all_create_dates, media_pie_shares)
        return HttpResponse(data, mimetype='application/json')
    report_list = get_report_list(site, all_create_dates, media_pie_shares)
    return render_to_response(template_name,
        {
            'affiliate':affiliate,
            'media_group':media_group,
            'report_list':report_list,
            'js_transaction_report': 1,
        }, context_instance=RequestContext(request))

@media_partner_required()
@login_required
def consumer_acquisition_report(request, stype):
    """
    Generates a report showing monthly consumer sign-ups for the MediaPartner
    """
    site = get_current_site(request)
    partner_site = SiteConsumerStats(site=site)

    graph = Flot()
    graph.add_time_series(partner_site.get_series(stype)['series'],
            "My Site",
            lines={'show': True})
    return render_to_response('media_partner/consumer_acquisition.html',
            {'graph': graph,
             'graph_title': stype.replace('-', ' ').capitalize(),
             'js_flot': True},
            context_instance=RequestContext(request))
