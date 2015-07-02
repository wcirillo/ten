""" A once-off promotion email to ad_rep_leads. """
import datetime
import logging

from email_gateway.context_processors import get_rep_context
from email_gateway.send import send_email
from email_gateway.tasks.email_task import EmailTask
from firestorm.models import AdRepLead

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)


class AdRepLeadPromoTask(EmailTask):
    """ Once-out email to ad rep leads informing them of dropped enrollment fee.
    First once out sent included a promotion to leads created before December.
    Current once out doesnt include tracking code cuz all enrollments are free
    and will send to anyone signed up between 11/30/11 and 1/19/12.
    """
    @classmethod
    def get_task_name(cls):
        """ Return custom task name. """
        return cls.__name__

    @staticmethod
    def get_ad_rep_leads():
        """ Return ad_rep_leads created before December who have not opt-ed out
        of these emails.
        """
        return AdRepLead.objects.filter(
            create_datetime__range=(
                datetime.date(2011, 12, 1), datetime.date(2012, 1, 19)),
            email_subscription__id=5)

    def run(self):
        """ Send email to ad_rep_leads. """
        ad_rep_leads = self.get_ad_rep_leads()
        LOG.debug('Will send to %s ad_rep_leads.' % ad_rep_leads.count())
        for ad_rep_lead in ad_rep_leads:
            try:
                firestorm_id = ad_rep_lead.ad_rep.firestorm_id
                friendly_from = "%s at %s" % (
                    ad_rep_lead.ad_rep.first_name, ad_rep_lead.site.domain)
            except AttributeError:
                firestorm_id = 43096
                friendly_from = 'President at %s' % ad_rep_lead.site.domain
            context = {
                'to_email': ad_rep_lead.email,
                'subject': "%s%s" % (
                    'Start today as an Advertising Representative for ',
                    ad_rep_lead.site.domain),
                'ad_rep_lead': ad_rep_lead,
                'firestorm_id': firestorm_id,
                'friendly_from': friendly_from,
                'mailing_list': [5]
            }
            context.update(get_rep_context(
                ad_rep_lead.site, ad_rep_lead.email, cc_rep=False))
            send_email(template='firestorm_ad_rep_lead_promo',
                site=ad_rep_lead.site, context=context)

AD_REP_LEAD_PROMO_TASK = AdRepLeadPromoTask()