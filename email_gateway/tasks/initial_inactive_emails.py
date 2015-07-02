""" Task to send email to advertisers that recently became inactive (first
email).
"""
from datetime import datetime, timedelta
import logging

from coupon.models import Coupon
from email_gateway.send import send_email
from email_gateway.service.task_service import qry_inactive_email
from email_gateway.tasks.email_task import EmailTask
from logger.service import log_db_entry
from media_partner.service import get_site_active_media_mediums

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class InitialInactiveEmail(EmailTask):
    """ Send an email to advertisers who have abandoned the create-coupon 
    process and never completed a transaction.
    """
    @classmethod
    def get_task_name(cls):
        """ Return custom task name. """
        return cls.__name__

    def run(self, business=None):
        """ Task to send initial email task to invite recently inactive  
        businesses to rerun their coupons on the site. 
            - Business must have had an active coupon on the site historically.
            - Business have no current active slots.
            - Business' latest slot must have expired yesterday.
        Setting optional parameter test_mode sends an email to said address. 
        Optional parameter business only runs the task for this business.
        """
        yesterday = datetime.now().date()- timedelta(days=1)
        if not business:
            businesses = qry_inactive_email(end_date=yesterday) 
        else:
            if self.test_mode: # Allow overriding query filters.
                businesses = [business]
            else:
                businesses = qry_inactive_email(
                    advertiser_id=business.advertiser.id,
                    end_date=yesterday)
        LOG.debug("sending initial_inactive_email to: %s" % list(businesses))
        log_db_entry('email_gateway.tasks.send_initial_inactive_email', 'RUN', 
            "{'business_count': %s}" % sum(1 for result in businesses))
        for business in businesses:
            site = business.advertiser.site
            try:
                coupon = Coupon.objects.filter(offer__business__id=business.id,
                    offer__business__slots__end_date=yesterday).latest()
            except Coupon.DoesNotExist:
                coupon = None
            to_email = self.get_to_email(business)
            context = {
                'to_email': to_email,
                'subject': 'Potential Customers are looking for %s' % 
                    business.business_name,
                'business': business,
                'coupon': coupon,
                'mailing_list': [4],
                'market_medium_list': get_site_active_media_mediums(site.id)
                }
            self.update_context_for_ad_rep(context, site, to_email,
                cc_rep=True)
            LOG.debug("   sending email to %s at %s from %s on site %s" % (
                business, to_email, context['rep_first_name'], site.domain))
            send_email(template='advertiser_initial_inactive', site=site,
                context=context)
        LOG.info("Initial_inactive task sent a total of %s email(s)" %
            len(list(businesses)))
