""" Views for the Ad Rep Account app. """

import logging
import operator

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import Http404, HttpResponse
from django.shortcuts import render_to_response
from django.template.defaultfilters import date as date_filter
from django.template import RequestContext
from django.utils import simplejson
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from gargoyle.decorators import switch_is_active

from advertiser.models import Advertiser
from coupon.service.coupon_performance import CouponPerformance
from firestorm.decorators import ad_rep_required_md, ad_rep_required
from firestorm.models import (AdRep, AdRepCompensation,
    get_current_pay_period_dates)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)
LOG.info('Logging Started')

class AdRepAccount(TemplateResponseMixin, View):
    """ Class based view for an ad reps account. """
    template_name = 'firestorm/display_ad_rep_account.html'
    context = {}

    @method_decorator(ad_rep_required_md())
    def dispatch(self, *args, **kwargs):
        return super(AdRepAccount, self).dispatch(*args, **kwargs)

    def get(self, request):
        """ Handle a GET request of this view. """
        self.prepare(request)
        return self.render_to_response(RequestContext(request, self.context))

    def prepare(self, request):
        """ Prepare the context dict for this request. """
        ad_rep = AdRep.objects.get(email=request.session['consumer']['email'])
        # Note: the resultant string itself has an embedded %s.
        link_base = '%s%s' % (ad_rep.site.domain, reverse('redirect-for-ad-rep',
            kwargs={'redirect_string': '%s' + ad_rep.url}, 
            urlconf='urls_local.urls_1'))
        # Remove / before redirect_string.
        link_base = link_base.replace('/%s', '%s')
        LOG.debug('link_base: %s' % link_base)
        my_commisions = AdRepCompensation.current_pay_period.filter(
                ad_rep=ad_rep, child_ad_rep=None).aggregate(
                    Sum('amount'))['amount__sum']
        if not my_commisions:
            my_commisions = 0
        my_teams_commisions = AdRepCompensation.current_pay_period.filter(
                ad_rep=ad_rep).exclude(child_ad_rep=None).aggregate(
                    Sum('amount'))['amount__sum']
        if not my_teams_commisions:
            my_teams_commisions = 0
        total_commisions_ever = ad_rep.ad_rep_compensations.aggregate(
                    Sum('amount'))['amount__sum']
        (start_of_pay_period, end_of_pay_period) = get_current_pay_period_dates()
        pay_period = '%s %s - %s %s' % (date_filter(start_of_pay_period, 'F'),
                                   date_filter(start_of_pay_period, 'd'),
                                   date_filter(end_of_pay_period, 'F'),
                                   date_filter(end_of_pay_period, 'd'),)
        if not total_commisions_ever:
            total_commisions_ever = 0
        self.context.update({'ad_rep':ad_rep,
            'is_ad_rep_account': 1,
            'pay_period': pay_period, 
            'my_commisions': '$' '%.2f' % my_commisions,
            'my_teams_commisions': '$' '%.2f' % my_teams_commisions,
            'total_earnings_this_pay_period': '$' '%.2f' % (
                my_commisions + my_teams_commisions),
            'total_commisions_ever': '$' '%.2f' % total_commisions_ever,
            'how_it_works_link': link_base % reverse('how-it-works', 
                urlconf='urls_local.urls_1'),
            'recommend_enrollment_link':
                link_base % reverse('recommend-enroll',
                    urlconf='urls_local.urls_1'),
            'personal_website_link': '%s/%s/' % (ad_rep.site.domain,
                ad_rep.url) })
        return ad_rep

@staff_member_required
def admin_ad_rep_consumers(request, ad_rep_id):
    """ A view for use in admin. """
    ad_rep = AdRep.objects.get(id=ad_rep_id)
    return base_ad_rep_consumers(request, ad_rep)

@switch_is_active('firestorm-feeds')
def ad_rep_consumers(request, ad_rep=None):
    """ A view for use in firestorm back office. """
    return base_ad_rep_consumers(request, ad_rep)

def base_ad_rep_consumers(request, ad_rep):
    """ An HTML page used as an include within the Firestorm system, for
    displaying all the consumers of an ad rep and the eligibility state of each.
    """
    # Decorator passes along verified ad_rep.
    context_dict = RequestContext(request, {
        'js_consumer_bonus': 1,
        'ad_rep': ad_rep,
        'consumer_points': ad_rep.qualified_consumer_points(),
        'consumer_count': ad_rep.consumers().count(),
        'consumers': ad_rep.consumers().extra(select={
            'is_email_subscription': '''SELECT COUNT(id)
                FROM consumer_consumer_email_subscription
                WHERE emailsubscription_id = 1
                AND consumer_id = consumer_consumer.user_ptr_id''',
                }
            ).order_by('email'),
        })
    return render_to_response(
        "firestorm/display_ad_rep_consumers.html", context_dict)

@staff_member_required
def admin_downline_consumers(request, ad_rep_id, downline_ad_rep_id=None):
    """ A view for use in admin. """
    ad_rep = AdRep.objects.get(id=ad_rep_id)
    return base_downline_consumers(request, ad_rep, downline_ad_rep_id,
        is_admin=True)

@switch_is_active('firestorm-feeds')
def downline_consumers(request, ad_rep=None, downline_ad_rep_id=None):
    """ A view for use in firestorm back office. """
    return base_downline_consumers(request, ad_rep, downline_ad_rep_id)

def base_downline_consumers(request, ad_rep, downline_ad_rep_id,
        is_admin=False):
    """ Given an ad_rep and the id of an ad_rep who is in his downline, report
    the number of consumers, verified consumers, and annual sales for the
    ad_reps in the immediate downline of the downline ad_rep, and how many days
    left until each has reached 30 days if any. Provide drill-down links.
    """
    if downline_ad_rep_id:
        try:
            downline_ad_rep = AdRep.objects.get(id=downline_ad_rep_id)
            if downline_ad_rep.is_ad_rep_in_upline(ad_rep):
                report_ad_rep = downline_ad_rep
            else:
                raise Http404
        except AdRep.DoesNotExist:
            raise Http404
    else:
        report_ad_rep = ad_rep
    child_ad_reps_list = list(report_ad_rep.child_ad_reps())
    consumer_count_list = []
    annual_order_count_list = []
    has_downline_list = []
    for child_ad_rep in child_ad_reps_list:
        consumer_count_list.append(child_ad_rep.consumers().count())
        annual_order_count_list.append(child_ad_rep.annual_orders().count())
        has_downline_list.append(child_ad_rep.has_child_ad_reps())
    data_set = zip(child_ad_reps_list, consumer_count_list,
        annual_order_count_list, has_downline_list)
    LOG.debug('data_set: %s' % data_set)
    # Sort list by consumer count descending
    data_set = sorted(data_set, key=operator.itemgetter(1), reverse=True)
    context_dict = RequestContext(request, {
        'ad_rep': ad_rep,
        'report_ad_rep': report_ad_rep,
        'data_set': data_set,
        'is_admin': is_admin
    })
    return render_to_response("firestorm/display_downline_consumers.html",
        context_dict)

@staff_member_required
def admin_recruitment_assistance(request, ad_rep_id):
    """ A view for use in admin. """
    ad_rep = AdRep.objects.get(id=ad_rep_id)
    return base_recruitment_assistance(request, ad_rep)

def recruitment_assistance(request, ad_rep=None):
    """ A view for use in firestorm back office. """
    return base_recruitment_assistance(request, ad_rep)

def base_recruitment_assistance(request, ad_rep):
    """ Provide ApReps with Copy and Links to be used for recruitment of other 
    Reps through sites like Craig's List.
    """
    context = {
        'ad_rep': ad_rep,
        'http_protocol_host' : settings.HTTP_PROTOCOL_HOST,}
    return render_to_response("firestorm/display_recruitment_ad.html",
        RequestContext(request, context))

@staff_member_required
def admin_web_addresses(request, ad_rep_id):
    """ A view for use in admin. """
    ad_rep = AdRep.objects.get(id=ad_rep_id)
    return base_web_address(request, ad_rep)

def web_addresses(request, ad_rep=None):
    """ A view for use in the firestorm back office. """
    return base_web_address(request, ad_rep)

def base_web_address(request, ad_rep):
    """ Display urls ad reps can send to prospects. """
    # Note: the resultant string itself has an embedded %s.
    link_base = '%s%s' % (ad_rep.site.domain, reverse('redirect-for-ad-rep',
        kwargs={'redirect_string': '%s' + ad_rep.url}, 
        urlconf='urls_local.urls_1'))
    # Remove / before redirect_string.
    link_base = link_base.replace('/%s', '%s')
    LOG.debug('link_base: %s' % link_base)
    context = {
        'ad_rep': ad_rep,
        'how_it_works_link': link_base % reverse('how-it-works',
            urlconf='urls_local.urls_1'),
        'recommend_enrollment_link':
            link_base % reverse('recommend-enroll',
            urlconf='urls_local.urls_1'),
        'personal_website_link': '%s/%s/' % (ad_rep.site.domain,
            ad_rep.url)
        }
    return render_to_response("firestorm/display_web_addresses.html",
        RequestContext(request, context))

@staff_member_required
def admin_advertiser_stats(request, ad_rep_id):
    """ A view for use in admin. """
    ad_rep = AdRep.objects.get(id=ad_rep_id)
    return base_advertiser_stats(request, ad_rep)

@ad_rep_required
def advertiser_stats(request, ad_rep=None):
    """ A view for use in admin. """
    return base_advertiser_stats(request, ad_rep)

def base_advertiser_stats(request, ad_rep):
    """ Display advertisers of this ad_rep, and stats for current coupons for
    each.
    """
    advertiser_ids = Advertiser.objects.filter(
        ad_rep_advertiser__ad_rep=ad_rep).values_list('id', flat=True)
    size_limit = 20
    context = {
        'ad_rep': ad_rep,
        'size_limit': 20,
        'js_advertiser_stats': 1
    }
    LOG.debug('advertiser ids: %s' % advertiser_ids)
    if request.POST:
        coupon_performance = CouponPerformance(
            size_limit=size_limit, 
            render_preview=False, 
            exclude_unpublished=True)
        coupon_list = coupon_performance.get_coupon_list(
            advertiser_ids=advertiser_ids,  order_by='advertiser',
            **request.POST)
        LOG.debug('coupon_list: %s' % coupon_list)
        json = simplejson.dumps(coupon_list)
        LOG.debug('json: %s' % json)
        return HttpResponse(json, content_type='application/json')
    return render_to_response("firestorm/display_advertiser_stats.html",
        RequestContext(request, context))
    
def show_share_links(request):
    """ Show pre-created links for an ad-rep to share their site. """
    try:
        ad_rep = AdRep.objects.get(
            id=request.session['consumer']['consumer_id'])
    except (AdRep.DoesNotExist, KeyError):
        return HttpResponseRedirect(reverse('sign-in'))
    # Note: the resultant string itself has an embedded %s.
    link_base = '%s%s' % (ad_rep.site.domain, reverse('redirect-for-ad-rep',
        kwargs={'redirect_string': '%s' + ad_rep.url}, 
        urlconf='urls_local.urls_1'))
    # Remove / before redirect_string.
    link_base = link_base.replace('/%s', '%s')
    LOG.debug('link_base: %s' % link_base)
    context = {
        'ad_rep': ad_rep,
        'how_it_works_link': link_base % reverse('how-it-works',
            urlconf='urls_local.urls_1'),
        'recommend_enrollment_link':
            link_base % reverse('recommend-enroll',
            urlconf='urls_local.urls_1'),
        'personal_website_link': '%s/%s/' % (ad_rep.site.domain,
            ad_rep.url)
        }
    return render_to_response("firestorm/display_links_for_sharing.html",
        RequestContext(request, context))


