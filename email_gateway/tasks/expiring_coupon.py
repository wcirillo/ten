""" Task for sending email to advertisers with expiring coupons. """
import datetime
import logging

from django.conf import settings
from django.template.defaultfilters import date as date_filter

from coupon.models import Coupon
from email_gateway.context_processors import get_rep_context
from email_gateway.send import send_email
from email_gateway.tasks.email_task import EmailTask
from logger.service import log_db_entry

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class ExpiringCouponTask(EmailTask):
    """ Celery tasks for alerting advertisers about expiring coupons. """
    from_date = None
    to_date = None

    @classmethod
    def get_task_name(cls):
        """ Return custom task name. """
        return cls.__name__

    @staticmethod
    def get_bcc_list():
        """ Return a list of emails to BCC: on the email to the advertiser. """
        ad_rep_bcc_list = []
        if settings.ENVIRONMENT['environment'] == 'prod':
            ad_rep_bcc_list = ['alana@10coupons.com', 'scott@10coupons.com',
                'steve@10coupons.com']
        elif settings.ENVIRONMENT['is_test']:
            ad_rep_bcc_list = ['test_expiring_coupon_bcc@example.com']
        return ad_rep_bcc_list

    def get_expiring_coupons(self):
        """ Return coupons expiring during the correct window of time, whose
        advertisers have not opted-out of this list.
        """
        return list(Coupon.current_coupons
            .filter(
                expiration_date__range=(self.from_date, self.to_date),
                offer__business__advertiser__email_subscription__id=2)
            .order_by('offer__business'))

    def email_this_business(self, business, coupons):
        """ Send an email to the advertiser of this business. """
        advertiser = business.advertiser
        to_email = advertiser.email
        context = {
            'to_email': to_email,
            'business': business,
            'mailing_list': [2],
        }
        if len(coupons) == 1:
            context['coupon'] = coupons[0]
        else:
            context['coupons'] = coupons
        rep_context = get_rep_context(advertiser.site, advertiser.email)
        context.update(rep_context)
        context.update({
            'friendly_from': '%s at %s' % (context['company'] or
                context['rep_first_name'], advertiser.site.domain),
        })
        if len(coupons) == 1:
            context['subject'] = 'Your coupon - %s - expires %s' % (
                coupons[0].offer.headline,
                date_filter(coupons[0].expiration_date, 'F j'))
            subject_for_rep = 'A coupon for %s expires %s' % (
                business.business_name,
                date_filter(coupons[0].expiration_date, 'F j'))
        else:
            context['subject'] = '%s - your coupons expire soon' % (
                business.business_name)
            subject_for_rep = 'Coupons for %s expire soon!' % (
                business.business_name)
        send_email(template='advertiser_expiring_coupon', site=advertiser.site,
            context=context)
        if context.get('firestorm_id', False):
            to_email = context['signature_email']
            try:
                location = coupons[0].location.all()[0]
            except IndexError:
                location = None
            context.update({
                'to_email': to_email,
                'subject': subject_for_rep,
                'location': location})
            self.update_context_for_sales_rep(context, advertiser.site)
            context.update({
                'friendly_from': '%s at %s' % (context['sales_rep_first_name'],
                    advertiser.site.domain),
            })
            send_email(template='advertiser_expiring_coupon',
                site=advertiser.site, context=context)
        bcc_list = self.get_bcc_list()
        if bcc_list:
            context.update({
                'to_email': bcc_list,
                'bcc': True,
                'original_to': to_email,
                })
            LOG.warning("Sending BCC to  %s" % bcc_list)
            send_email(template='advertiser_expiring_coupon',
                site=advertiser.site, context=context)

    def run(self, rerun=False, coupons=None):
        """ Send email to advertisers with expiring coupons.

        For testing purposes only, coupons can be given as a argument, and email
        will be generated for those coupons without regard to expiration date.
        """
        task_status = 'EMAIL'
        if self.has_task_run_today(rerun=rerun):
            return "Already ran today"
        self.from_date, self.to_date = self.get_task_date_range(-10)
        if not coupons:
            coupons = self.get_expiring_coupons()
        this_business = None
        coupons_this_business = []
        business_counter = 0
        for coupon in coupons:
            if coupon.offer.business == this_business:
                coupons_this_business.append(coupon)
            else:
                # Make sure this is not first iteration.
                if this_business:
                    self.email_this_business(this_business,
                        coupons_this_business)
                business_counter += 1
                coupons_this_business = [coupon]
                this_business = coupon.offer.business
        # Last business:
        if this_business:
            self.email_this_business(this_business, coupons_this_business)
        log_db_entry(self.get_task_name(), task_status,
            {'last_run': datetime.datetime.today().date(),
            'expiring coupon emails sent': business_counter,
            'from_date': self.from_date, 'to_date': self.to_date})
