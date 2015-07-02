""" Celery task emailing ad rep leads from yesterday. """
from datetime import datetime
import logging

from email_gateway.context_processors import get_ad_rep_context
from email_gateway.send import send_email
from email_gateway.tasks.email_task import EmailTask
from firestorm.models import AdRepLead
from logger.service import log_db_entry

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class AdRepInviteTask(EmailTask):
    """ Send an email to ad rep leads created yesterday inviting them to enroll
    as an ad rep.
    """
    from_date = None
    to_date = None

    @classmethod
    def get_task_name(cls):
        """ Return task name. """
        return cls.__name__
    
    def get_ad_rep_leads(self, days_past):
        """ Return ad_rep_leads create days_past days ago. """
        self.from_date, self.to_date = self.get_task_date_range(
            days_past=days_past)
        ad_rep_leads = AdRepLead.objects.filter(
            create_datetime__range=(self.from_date, self.to_date),
            email_subscription__id=5)
        LOG.debug(ad_rep_leads)
        return ad_rep_leads

    def run(self, days_past=1, rerun=False, test_mode=False):
        """ Send email.

        test_mode: allows False or an iterable of ad_rep_leads.
        """
        status = 'EMAIL'
        if self.has_task_run_today(status=status, rerun=rerun):
            return 'Aborted:: %s already ran today' % self.get_task_name()
        if test_mode:
            ad_rep_leads = test_mode
        else:
            ad_rep_leads = self.get_ad_rep_leads(days_past)
        for ad_rep_lead in ad_rep_leads:
            len_right_person_text = 0
            if ad_rep_lead.right_person_text:
                len_right_person_text = len(ad_rep_lead.right_person_text)
            context = {
                'to_email': ad_rep_lead.email,
                'subject':
                    'Start today as an Advertising Representative for %s' %
                        ad_rep_lead.site.domain,
                'friendly_from': 'Sales Support at %s' %
                    ad_rep_lead.site.domain,
                'mailing_list': [5],
                'ad_rep_lead': ad_rep_lead,
                'len_right_person_text': len_right_person_text
            }
            if ad_rep_lead.ad_rep:
                context.update(get_ad_rep_context(ad_rep_lead.ad_rep))
            send_email(template='firestorm_ad_rep_invite',
                site=ad_rep_lead.site, context=context)
        log_db_entry(self.get_task_name(), status,
            {'last_run': datetime.today().date(), 
            'emails_sent': len(ad_rep_leads), 
            'from_date': self.from_date, 'to_date': self.to_date})

AD_REP_INVITE_TASK = AdRepInviteTask()
