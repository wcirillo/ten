""" Classes to send emails to ad reps and ad rep leads in firestorm app. """
from datetime import datetime, timedelta
import logging

from celery.task import Task
from django.conf import settings

from common.custom_format_for_display import format_phone
from email_gateway.context_processors import get_rep_context
from email_gateway.send import send_email
from email_gateway.tasks.email_task import EmailTask
from firestorm.models import AdRep, AdRepLead
from logger.service import get_last_db_log, log_db_entry
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)


class SendEnrollmentNotification(Task):
    """ Notify staff of new ad rep enrollments. """
    @staticmethod
    def run(ad_reps=None, test_mode=False):
        """ Sends an email to all staff including all ad reps enrolled. The 
        criteria is all ad reps enrolled yesterday. """
        if test_mode:
            to_email = [test_mode]
        else:
            to_email = settings.NOTIFY_EVERYONE
        LOG.debug("Sending Ad Rep Enrolled email to everyone.")
        if not ad_reps: # ad reps enrolled yesterday
            from_date = datetime.now().date() - timedelta(days=1)
            to_date = from_date + timedelta(days=1)
            LOG.debug('Admin enroll email: from_date: %s to_date = %s' % (
                from_date, to_date))
            ad_reps = AdRep.objects.filter(ad_rep_create_datetime__range=(
                from_date, to_date)).exclude(rank='CUSTOMER')
        if ad_reps and len(ad_reps) > 0:
            for ad_rep in ad_reps:
                ad_rep.primary_phone_number = format_phone(
                    ad_rep.primary_phone_number)
            send_email(template='admin_ad_rep_enrolled', 
                site=Site.objects.get(id=1), 
                context={'to_email': to_email, 
                    'subject': 'Advertising Representatives Enrolled', 
                    'ad_reps': ad_reps, 
                    'show_unsubscribe': False})
            LOG.debug('Admin ad rep enroll email sent')


class SendEnrollmentEmail(Task):
    """ Task that sends an email to this newly enrolled ad rep. """
    accept_magic_kwargs = False

    @staticmethod
    def run(ad_rep_id, referred=False):
        """ Send an email to this newly enrolled ad rep, including promotional 
        codes for annual placement product.
        """
        ad_rep = AdRep.objects.get(id=ad_rep_id)
        ad_rep.email_subscription.add(6)
        internal_cc = []
       
        if not settings.ENVIRONMENT['is_test']:
            internal_cc = settings.NOTIFY_AD_REP_ENROLLED
        if not settings.DEMO:
            send_email(template='firestorm_welcome_ad_rep', site=ad_rep.site, 
                context={'to_email': ad_rep.email, 
                    'internal_cc': internal_cc,
                    'subject':
                        "Welcome Aboard! Here's some help getting started.",
                    'ad_rep': ad_rep,
                    'friendly_from': 'Sales Support at %s' % ad_rep.site.domain,
                    'mailing_list': [4],
                    'ad_rep_referred': referred
                    })

class NotifyNewRecruit(Task):
    """ Task that sends an email to the sponsoring ad rep that they have a new
    recruit.
    """
    @staticmethod
    def run(child_ad_rep_id):
        """ Send an email to the sponsoring ad rep of this newly enrolled ad
        rep.
        """
        child_ad_rep = AdRep.objects.get(id=child_ad_rep_id)
        parent_ad_rep = child_ad_rep.parent_ad_rep
        if not settings.DEMO and parent_ad_rep:
            context={
            'to_email': parent_ad_rep.email, 
            'subject': "A New Team Member may help you Earn More",
            'parent_ad_rep': parent_ad_rep,
            'child_ad_rep': child_ad_rep,
            'friendly_from': 
                "Ad Rep Support at %s" % parent_ad_rep.site.domain,
            'mailing_list': [6]
            }
            context.update(get_rep_context(
                parent_ad_rep.site,
                parent_ad_rep.email,
                instance_filter='ad_rep'))
            send_email(template='firestorm_notify_new_recruit',
                site=parent_ad_rep.site,
                context=context)

class SendMarketManagerPitch(EmailTask):
    """ Send an email to ad rep leads (that signed up between yesterday and
    the last run) pitching them to become market managers and explaining the 
    perks of the compensation plan.
    """
    from_date = None
    to_date = None

    @classmethod
    def get_task_name(cls):
        """ Return custom task name. """
        return cls.__name__

    def qry_recipients(self, **kwargs):
        """ Return query of ad rep leads to receive this email. """
        test_mode = kwargs.get('test_mode', False)
        days_past = kwargs.get('days_past', 1)
        self.from_date, self.to_date = self.get_task_date_range(
            days_past=days_past, max_days=180)
        recipients = AdRepLead.objects.filter(
            create_datetime__range=(self.from_date, self.to_date),
            email_subscription__email_subscription_name__in=['AdRepLead'],
            is_emailable=True)
        if test_mode:
            recipients = recipients.filter(email=test_mode)
        return recipients

    def run(self, days_past=1, test_mode=False, rerun=False):
        """ Send all ad rep leads that were created since this process last run
        and were created at least one day ago (so we do not have to track 
        date/time). If test_mode param supplied (for testing) only send to 
        respective value (will be an email).
        """
        task_ = {'status': 'EMAIL'}
        if self.has_task_run_today(status=task_['status'], rerun=rerun):
            return 'Aborted:: %s already ran today' % self.get_task_name()
        recipients = self.qry_recipients(test_mode=test_mode, 
                days_past=days_past)
        last_log = get_last_db_log(self.get_task_name(), task_['status'])
        if not last_log:
            task_['last_run'] = 'NEVER'
        else:
            task_['last_run'] = last_log.execution_date_time
        log_db_entry(self.get_task_name(), task_['status'], {
            'last_run': task_['last_run'],
            'ad_rep_lead_recipients': 'Total: %s' % recipients.count(),
            'ad_rep_leads_created': 'between: %s and %s' %
                (self.from_date, self.to_date)})
        email_context = {
            'subject': 'Market Manager Opportunity - Exclusive Territory',
            'signature_name': 'Eric Straus',
            'rep_first_name': 'Eric',
            'signature_title': 'CEO',
            'signature_email': 'Eric@10LocalCoupons.com',
            'signature_phone': '914-920-3059',
            'Reply-To': 'Coupons@10coupons.com',
            'display_all_recipients': False,
            'bouncing_checked': True,
            'show_unsubscribe': True,
            'mailing_list':[5],
            }
        for ad_rep_lead in recipients:
            context = email_context.copy()
            context.update({
                'to_email': str(ad_rep_lead.email),
                'friendly_from': '%s at %s' %
                    (context['rep_first_name'], ad_rep_lead.site.domain),
                'ref_num': ad_rep_lead.email,
                'ad_rep_lead_first_name': ad_rep_lead.first_name
                })
            send_email(template='firestorm_market_manager_pitch',
                site=ad_rep_lead.site, context=context)


NOTIFY_NEW_RECRUIT = NotifyNewRecruit()
SEND_ENROLLMENT_NOTIFICATION = SendEnrollmentNotification()
SEND_ENROLLMENT_EMAIL = SendEnrollmentEmail()
