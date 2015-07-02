""" Task to send warm lead emails. """
import datetime
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import date as date_filter

from advertiser.models import Advertiser, Business
from consumer.models import SalesRep
from coupon.models import Coupon, Offer
from coupon.service.valid_days_service import VALID_DAYS
from ecommerce.service.calculate_current_price import calculate_current_price
from ecommerce.models import OrderItem, PromotionCode
from email_gateway.context_processors import get_rep_context
from email_gateway.send import send_email
from email_gateway.service.task_service import check_email_schedule
from email_gateway.tasks.email_task import EmailTask
from feed.tasks.tasks import sync_business_to_sugar
from firestorm.models import AdRep
from logger.service import log_db_entry
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class WarmLeadEmailTask(EmailTask):
    """ Task to send emails to advertisers who have begun to sign up but 
    abandoned before purchasing.
    """
    test_mode = False
    start_datetime = None
    end_datetime = None
    # We will send versions of this email today to advertisers who abandoned
    # coupons these n days ago, which will include y custom message:
    schedule = [1, 10, 40, 70, 100, 130]

    @classmethod
    def get_task_name(cls):
        """ Return custom task name. """
        return cls.__name__

    @staticmethod
    def get_ad_rep_bcc_list():
        """ Return a list of emails to BCC: on the email to the ad rep. """
        ad_rep_bcc_list = []
        if settings.ENVIRONMENT['environment'] == 'prod':
            ad_rep_bcc_list = ['alana@10coupons.com', 'scott@10coupons.com',
                'eric@10coupons.com']
        elif settings.ENVIRONMENT['is_test']:
            ad_rep_bcc_list = ['test_ad_rep_bcc@example.com']
        return ad_rep_bcc_list

    @staticmethod
    def get_report_list():
        """ Return a list of email a report to. """
        report_list = []
        if settings.ENVIRONMENT['environment'] == 'prod':
            report_list = ['jeremy@10coupons.com', 'dennis@10coupons.com',
                'scott@10coupons.com', 'steve@10coupons.com']
        elif settings.ENVIRONMENT['is_test']:
            report_list = ['test_report@example.com']
        return report_list

    def qry_warm_businesses_since(self):
        """ Return a QuerySet of business who entered an email and business name
        but never got so far as entering an offer. 
        """
        return Business.objects.filter(
            advertiser__is_emailable=True,
            advertiser__email_subscription=4,
            advertiser__is_active=True,
            advertiser__advertiser_create_datetime__gt=self.start_datetime,
            advertiser__advertiser_create_datetime__lte=self.end_datetime,
            offers=None,
        ).exclude(advertiser__groups__name__in=['Coldcall-Leads',
            'advertisers__do_not_market']).exclude(
            # Make sure 
            advertiser__id__in=OrderItem.objects.values_list(
                'business__advertiser__id', flat=True)
        )

    def qry_warm_offers_since(self):
        """ Return the abandoned coupons for businesses w/o a paid coupon since
        the last_run datetime.
        """
        LOG.debug("%s %s" % (self.start_datetime, self.end_datetime))
        return Offer.objects.filter(
            business__advertiser__is_emailable=True,
            business__advertiser__email_subscription=4,
            business__advertiser__is_active=True,
            business__advertiser__advertiser_create_datetime__gt=
                self.start_datetime,
            business__advertiser__advertiser_create_datetime__lte=
                self.end_datetime,
        ).exclude(business__advertiser__groups__name__in=['Coldcall-Leads',
                'advertisers__do_not_market']).exclude(
            # Make sure we don't send to folk who have paid for something
            business__advertiser__id__in=OrderItem.objects.values_list(
                'business__advertiser__id', flat=True)
        )

    def qry_warm_offers_and_businesses(self):
        """  Return offers and businesses to send warm lead emails to since the
        last time this process was run.
        """
        advertisers, businesses, offers = [], [], []
        pre_offers = self.qry_warm_offers_since()
        pre_businesses = self.qry_warm_businesses_since()
        # Remove additional offers from the same advertiser.
        if pre_offers:
            for offer in list(pre_offers):
                advertiser = offer.business.advertiser
                if advertiser not in advertisers:
                    offers.append(offer)
                    advertisers.append(advertiser)
        # Remove additional businesses from the same advertiser.
        if pre_businesses:
            for business in list(pre_businesses):
                advertiser = business.advertiser
                if advertiser not in advertisers:
                    advertisers.append(advertiser)
                    businesses.append(business)
        LOG.debug('businesses: %s' % businesses)
        LOG.debug('offers: %s' % offers)
        return businesses, offers

    @staticmethod
    def get_recent_coupon(offer):
        """ Return a recent coupon for the same site that is for a business that
        is related to a different category than this offer.
        """
        coupons = (Coupon.current_coupons
            .get_current_coupons_by_site(offer.business.advertiser.site)
            .filter(
                coupon_create_datetime__gt=
                    datetime.date.today() - datetime.timedelta(10))
            .order_by('-coupon_create_datetime'))
        category_ids = offer.business.categories.values_list('id', flat=True)
        if category_ids and not 7 in category_ids:
            coupons = coupons.exclude(offer__business__categories__in=
                offer.business.categories.all())
        try:
            return coupons[0]
        except IndexError:
            return None

    @staticmethod
    def put_rep_in_context(context, site, to_email):
        """ Get ad_rep or sales_rep info and add it into the context. """
        rep_context = get_rep_context(site, to_email[0], cc_rep=True,
            is_lead=True)
        context.update(rep_context)
        context['cc_signature_flag'] = False
        if context.get('firestorm_id', False):
            context.update({
                'dynamic_url': '%s%s' % (settings.HTTP_PROTOCOL_HOST,
                    reverse('redirect-for-ad-rep',
                        urlconf='urls_local.urls_%s' % site.id,
                        kwargs={
                            'redirect_string': '%s%s' % (
                                AdRep.objects.get(
                                    firestorm_id=context['firestorm_id']).url,
                                reverse('advertiser-registration')[:-1])}))})
        else:
            context.update({'dynamic_url': '%s%s' % (
                settings.HTTP_PROTOCOL_HOST,
                reverse('advertiser-registration',
                    urlconf='urls_local.urls_%s' % site.id))})

    def process_offer(self, offer, schedule_item):
        """ Send an email for an offer. """
        site = offer.business.advertiser.site
        try:
            coupon = offer.coupons.latest()
            offer.valid_days = VALID_DAYS.create_valid_days_string(coupon)
            offer.expiration_date = date_filter(
                coupon.expiration_date, 'n/j/y')
        except Coupon.DoesNotExist:
            coupon = False
        if self.test_mode:
            to_email = [self.test_mode]
        else:
            to_email = [offer.business.advertiser.email]
        context = {
            'to_email': to_email,
            'offer': offer,
            'business': offer.business,
            'mailing_list': [4],
            'coupon': coupon,
            'schedule_item': schedule_item,
            'promo_code': PromotionCode.objects.get(id=98).code,
            'discounted_annual_coupon_display':
                calculate_current_price(3) - 100,
            'recent_coupon': self.get_recent_coupon(offer)
        }
        self.put_rep_in_context(context, site, to_email)
        if context.get('firestorm_id', False) and schedule_item == 130:
            subject = 'Publish up to 10 coupons and save $100'
        elif coupon:
            subject = "Publish this Coupon today"
        else:
            subject = "Publish your first coupon today"
        LOG.debug(context['headers'])
        context.update({
            'friendly_from': '%s at %s' % (context['company'] or
                context['rep_first_name'], site.domain),
            'subject': subject,
            })
        context['headers'].update({'Cc': "%s <%s>" % (
            context['rep_first_name'], context['signature_email'])})
        if settings.SUGAR_SYNC_MODE:
            # Sync this coupon business to SugarCRM.
            sync_business_to_sugar.delay(offer=offer)
        LOG.debug("found offer from: %s -- %s" % (offer.business, offer))
        LOG.debug("   sending email to %s from %s on site %s" % (
            to_email, context['rep_first_name'], site.domain))
        send_email(template='advertiser_warm_leads', site=site, context=context)
        # Send to ad_rep or sales_rep.
        context.update({'to_email': context['signature_email'],
            'subject': "WARM LEAD: %s" % context['subject']})
        if context.get('firestorm_id', False):
            self.update_context_for_sales_rep(context, site)
            context.update({
                'friendly_from': '%s at %s' % (context['sales_rep_first_name'],
                    site.domain),
            })
        send_email(template='advertiser_warm_leads', site=site,
            context=context)
        bcc_list = self.get_ad_rep_bcc_list()
        if bcc_list:
            phone = ''
            # Grabs the phone # of the first location, if entered.
            try:
                location = offer.business.locations.exclude(
                    location_number='').order_by('id')[0]
                phone = "(%s) %s-%s" % (location.location_area_code,
                    location.location_exchange,
                    location.location_number)
            except IndexError:
                pass
            context.update({
                'to_email': bcc_list,
                'bcc': True,
                'original_to': to_email[0],
                'phone': phone,
                })
            LOG.warning("Sending BCC to  %s" % bcc_list)
            send_email(template='advertiser_warm_leads', site=site,
                context=context)
    
    def run_for_time_period(self, query_obj=None, schedule_item=None):
        """ Loop warm leads for a given time period.

        query_obj is dict which may have keys coupon, offer, or business.
        """
        offers, businesses = [], []
        if query_obj and query_obj.get('offer', False):
            offers = [query_obj['offer']]
        elif query_obj and query_obj['coupon']:
            offers = [query_obj['coupon'].offer]
        if query_obj and query_obj.get('business', False):
            # Businesses passed in cannot belong to Coldcall-Leads user group.
            businesses = Business.objects.filter(id=query_obj['business'].id,
                    business_create_datetime__gt=self.start_datetime,
                    business_create_datetime__lt=self.end_datetime,
                ).exclude(advertiser__id__in=
                    Advertiser.objects.filter(groups__name__in=[
                        'advertisers__do_not_market',
                        'Coldcall-Leads']))
        if not query_obj:
            businesses, offers = self.qry_warm_offers_and_businesses()
        log_db_entry(self.get_task_name(), 'EMAIL', {
            'end_datetime': self.end_datetime,
            'start_datetime': self.start_datetime,
            'num_offers': len(offers),
            'num_businesses':len(businesses)})
        # Cycle through 'warm' offers.
        for offer in offers:
            self.process_offer(offer, schedule_item)
        # Cycle through 'warm' businesses with no offers.
        for business in businesses:
            site = business.advertiser.site
            if self.test_mode:
                to_email = [self.test_mode]
            else:
                to_email = [business.advertiser.email] 
            context = {
                'to_email': to_email,
                'business': business,
                'mailing_list': [4],
                'schedule_item': schedule_item,
                'promo_code': PromotionCode.objects.get(id=98).code,
            }
            self.put_rep_in_context(context, site, to_email)
            LOG.debug(context)
            context.update({
                'friendly_from': '%s at %s' % (context['company'] or 
                    context['rep_first_name'], site.domain), 
                'subject': 'Finish your first Coupon today',
                })
            context['headers'].update({'Cc': "%s <%s>" % (
                context['rep_first_name'], context['signature_email'])})
            if settings.SUGAR_SYNC_MODE:
                # Sync this coupon business to SugarCRM
                sync_business_to_sugar.delay(business=business)
            # Get sales rep info and add it into the context.
            LOG.debug("found warm business %s" % business)
            # Send to advertiser.
            send_email(template='advertiser_warm_leads', 
                site=site, context=context)
            context.update({'to_email': context['signature_email'],
                'subject': "WARM LEAD: %s" % context['subject']})
            # Send it to ad_rep or sales rep.
            send_email(template='advertiser_warm_leads',
                site=site, context=context)
            ad_rep_bcc_list = self.get_ad_rep_bcc_list()
            if ad_rep_bcc_list:
                # Bcc the email that went to the ad_rep.
                context.update({
                    'to_email': ad_rep_bcc_list,
                    'bcc': True,
                    'original_to': to_email[0],
                    })
                LOG.warning("Sending BCC to  %s" % ad_rep_bcc_list)
                send_email(template='advertiser_warm_leads', site=site,
                    context=context)
        LOG.debug("Offers: %s" % offers)
        LOG.debug("Businesses: %s" % businesses)
        return businesses, offers

    def run(self, query_obj=None, last_run_days=None, schedule_item=None):
        """ Send an email to advertisers who have begun to sign up but abandoned
        the coupon creating process before purchasing, OR to the owner of the
        supplied coupon, offer or business as query_obj.

        schedule_item: in item in self.schedule. If this exists, just send to
        advertisers for this iteration, else send email for every schedule in
        self.schedule.

        Setting self.test_mode to an email address sends the warm lead to said
        address.
        """
        if schedule_item:
            if not schedule_item in self.schedule:
                LOG.error('Invalid schedule_item: %s' % schedule_item)
                return
        if last_run_days:
            last_run = (
                datetime.date.today() - datetime.timedelta(days=last_run_days))
        else:
            last_run = check_email_schedule(
                self.get_task_name(), None, 'EMAIL', self.test_mode, 1)[0]
        LOG.info("Last run at %s, currently %s" % (last_run,
            datetime.datetime.now()))
        results_dict = dict()
        if query_obj:
            schedule = [1]
        else:
            schedule = self.schedule
        for schedule_item in schedule:
            LOG.debug('Now working on %s day(s) ago.' % schedule_item)
            self.start_datetime = (
                last_run - datetime.timedelta(days=schedule_item))
            self.end_datetime = (
                datetime.date.today() - datetime.timedelta(days=schedule_item))
            LOG.debug('start_datetime: %s' % self.start_datetime)
            LOG.debug('end_datetime: %s' % self.end_datetime)
            # Set business, offers tuple to results dict.
            businesses, offers = self.run_for_time_period(query_obj,
                schedule_item)
            results_dict[schedule_item] = dict()
            results_dict[schedule_item]['businesses'] = businesses
            results_dict[schedule_item]['offers'] = offers
        # Send report.
        if self.test_mode:
            to_email = [self.test_mode]
        else:
            to_email = list(SalesRep.objects.values_list('consumer__email',
                flat=True)) + self.get_report_list()
            LOG.info("sending report to: %s" % to_email)
        LOG.debug('results_dict:')
        LOG.debug([(key, item) for key, item in results_dict.iteritems()])
        context = {
            'to_email': to_email,
            'subject': "Warm leads since %s" % last_run,
            'friendly_from': 'Warm leads Genie',
            'show_unsubscribe': False,
            'results_dict': results_dict,
            'last_run': last_run,
            }
        send_email(template='admin_warm_leads_report', 
            site=Site.objects.get(id=1), context=context)
