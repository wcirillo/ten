""" Task to send emails to advertisers that abandoned create coupon process
without buying a coupon and have never made a purchase with us.
"""
import logging
from datetime import datetime, timedelta

from advertiser.models import Business
from coupon.models import Coupon
from email_gateway.config import ABANDONED_COUPON_SCHED_DICT
from email_gateway.context_processors import get_rep_context
from email_gateway.send import send_email
from email_gateway.service.task_service import check_email_schedule
from email_gateway.tasks.email_task import EmailTask
from logger.service import log_db_entry

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class AbandonedCouponEmailTask(EmailTask):
    """ Send an email to advertisers who have abandoned the create-coupon 
    process and never completed a transaction.
    """
    @classmethod
    def get_task_name(cls):
        """ Return a custom name. Uses the historical function name to preserve
        correct history.
        """
        return 'email_gateway.tasks.send_abandoned_coupon_followup'

    @classmethod
    def qry_abandoned_coupon_email(cls, mod_filter, cut_off,
            advertiser_id=None):
        """ Return most recent business belonging to this advertiser who have
        never made a qualifying purchase and has registered at least 10 days ago,
        respect excluded auth_groups and email subscriptions. THis is a
        perpetual email, so space out the emails from sending too frequently by
        only sending to businesses with an odd or even business id per query (as
        indicated by mod_filter passed in.
        """
        return Business.objects.raw("""
            SELECT biz.*
            FROM advertiser_business biz
                INNER JOIN (
                    SELECT id, inner_biz.advertiser_id
                    FROM advertiser_business inner_biz
                        INNER JOIN
                            (
                            SELECT advertiser_id,
                            MAX(business_modified_datetime) last_modified_date
                            FROM advertiser_business
                            GROUP BY advertiser_id
                            ) recent
                            ON inner_biz.advertiser_id = recent.advertiser_id
                                AND inner_biz.business_modified_datetime =
                                recent.last_modified_date
                    ) recent_biz
                ON biz.advertiser_id = recent_biz.advertiser_id
                    AND biz.id = recent_biz.id
                    AND biz.business_modified_datetime <=
                        COALESCE(%(cut_off)s, biz.business_modified_datetime)
                INNER JOIN consumer_consumer_email_subscription con_sub_xref
                    ON biz.advertiser_id = con_sub_xref.consumer_id
                INNER JOIN consumer_emailsubscription sub
                    ON con_sub_xref.emailsubscription_id = sub.id
                    AND sub.email_subscription_name in ('Advertiser_Marketing')
                LEFT JOIN auth_user_groups groups
                    ON biz.advertiser_id = groups.user_id
                LEFT JOIN auth_group
                    ON groups.group_id = auth_group.id
                        AND name in ('advertisers__do_not_market')
            WHERE biz.advertiser_id = COALESCE(%(advertiser_id)s,
                    biz.advertiser_id)
                and MOD(biz.id, 2) = COALESCE(%(mod_filter)s, MOD(biz.id, 2))
                and auth_group IS NULL
                and biz.advertiser_id NOT IN (
                    Select consumer_ptr_id From advertiser_advertiser a2
                    Inner Join advertiser_business b2
                        On b2.advertiser_id = a2.consumer_ptr_id
                    Inner join ecommerce_orderitem
                        On business_id = b2.id)
            ORDER BY biz.business_create_datetime DESC""",
            {'cut_off': cut_off, 'advertiser_id': advertiser_id,
             'mod_filter': mod_filter})

    def run(self, business=None):
        """ Send an email to advertisers who have abandoned the create-coupon 
        process and never completed a transaction. Setting optional parameter 
        test_mode to an email address sends the email to said address. Optional 
        parameter business only runs the task for this business).
        """
        state, business_filter = check_email_schedule(self.get_task_name(),
            ABANDONED_COUPON_SCHED_DICT, 'EMAIL', self.test_mode)[1:]
        log_db_entry(self.get_task_name(), state,
            "{'business_filter': %s}" % business_filter)
        if state == 'ABORT':
            return
        if business:
            # Ensure business passed in is appropriate to receive this email.
            businesses = self.qry_abandoned_coupon_email(
                advertiser_id=business.advertiser_id, mod_filter=None,
                cut_off=None)
        else:
            # Business_filter processes only businesses with odd or even ids.
            businesses = self.qry_abandoned_coupon_email(
                mod_filter=business_filter,
                cut_off=datetime.now() - timedelta(10))
        LOG.debug("%s looping through abandoned coupons from %s" %
            (self.get_task_name(), list(businesses)))
        for business in businesses:
            site = business.advertiser.site
            try:
                coupon = Coupon.objects.filter(
                        offer__business__id=business.id
                    ).exclude(coupon_type=3).latest()
            except Coupon.DoesNotExist:
                # Coupon has been published, Abort!
                coupon = None
            to_email = self.get_to_email(business)
            context = {
                'to_email': to_email,
                'business': business,
                'mailing_list': [4],
                'coupon': coupon
                }
            # Get sales rep info and add it into the context.
            context.update(get_rep_context(site, to_email[0], cc_rep=True))
            context.update({'friendly_from': '%s at %s' %
                (context['rep_first_name'], site.domain)})
            if business.advertiser.groups.filter(name='Coldcall-Leads'):
                subject_prefix = 'Publish a'
            else:
                subject_prefix = 'Complete your'
            context.update({'subject': '%s coupon for %s' % (subject_prefix,
                business.business_name)})
            LOG.debug("   sending email to %s at %s from %s on site %s" % (
                business.business_name, to_email, context['rep_first_name'], 
                site.domain))
            send_email(template='advertiser_follow_abandoned_coupon', site=site,
                context=context)
