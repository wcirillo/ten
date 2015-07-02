""" Task to send ad rep meeting reminder emails. """
from datetime import datetime, timedelta
import logging

from consumer.models import ConsumerHistoryEvent, EmailSubscription
from email_gateway.send import send_email
from email_gateway.tasks.email_task import EmailTask
from firestorm.models import AdRep, AdRepLead
from logger.service import log_db_entry

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class AdRepMtgReminderEmail(EmailTask):
    """ Class to define task that sends a weekly email to consumers (ad reps 
    and ad rep leads) with 'ad rep meeting reminder' email subscription.
    """
    list_id = 6 # ad rep meeting reminder

    @classmethod
    def get_task_name(cls):
        """ Return custom task name. """
        return cls.__name__

    def qry_ad_reps(self):
        """ Query ad reps with email subscription: mtg reminder and are not 
        referring consumers. 
        """
        return AdRep.objects.filter(
            email_subscription__id=self.list_id,
            is_active=True, 
            is_emailable=True
            ).exclude(rank='CUSTOMER')

    def qry_ad_rep_leads(self):
        """ Query ad rep leads with email subscription: mtg reminder. """
        return AdRepLead.objects.filter(
            email_subscription__id=self.list_id,
            is_active=True, 
            is_emailable=True
            )

    def prepare_and_send_email(self, consumer, is_ad_rep):
        """ Prepare to send email to this ad_rep or ad_read_lead. """
        email_context = {'to_email': str(consumer.email),
            'bouncing_checked': True,
            'subject': 'Invitation: 10LocalCoupons.com Company Overview',
            'is_ad_rep': is_ad_rep,
            'show_unsubscribe': False,
            'mailing_list': [self.list_id]
            }
        LOG.debug('send_email: %s' % consumer.email)
        send_email(template='firestorm_meeting_reminder',
            site=consumer.site, context=email_context)

    def send_email_to_ad_rep_leads(self, ad_rep_leads):
        """ Send email to ad rep leads """
        ad_rep_lead_count = 0
        email_subscription = EmailSubscription.objects.get(id=self.list_id)
        email_subscription_name = email_subscription.email_subscription_name
        for ad_rep_lead in ad_rep_leads:
            # Send to ad rep leads if they do not have a history record or
            # have a last email send datetime > 30 days ago. 
            consumer_history_event = ConsumerHistoryEvent.objects.filter(
                consumer=ad_rep_lead.consumer, 
                event_type='10', 
                data={'email_subscription_name': email_subscription_name}
                ).order_by('-event_datetime')
            if consumer_history_event: 
                if (consumer_history_event[0].event_datetime > 
                    datetime.now() - timedelta(days=30)):
                    continue
                else:
                    consumer_history_event[0].event_datetime = datetime.now()
                    consumer_history_event[0].save()
            else:
                consumer_history_event = ConsumerHistoryEvent.objects.create(
                    consumer=ad_rep_lead.consumer, 
                    ip='127.0.0.1',
                    event_type='10',
                    data={'email_subscription_name': email_subscription_name}
                    )
                consumer_history_event.save()
            self.prepare_and_send_email(ad_rep_lead.consumer, is_ad_rep=False)
            ad_rep_lead_count += 1
        return ad_rep_lead_count

    def run(self, rerun=False, test_mode=False):
        """ Send weekly email to consumers (ad reps and ad rep leads) with 
        'ad rep meeting reminder' email subscription. 
        """
        task_status = 'EMAIL'
        if self.has_task_run_today(rerun=rerun):
            return "Already ran today"
        if test_mode:
            task_status = 'TEST_MODE'
            try:
                ad_reps = [AdRep.objects.get(email=test_mode)]
            except AdRep.DoesNotExist:
                ad_reps = []
            try:
                ad_rep_leads = [AdRepLead.objects.get(email=test_mode)]
            except AdRepLead.DoesNotExist:
                ad_rep_leads = []
        else:
            ad_reps = self.qry_ad_reps()
            ad_rep_leads = self.qry_ad_rep_leads()
            LOG.debug('ad_reps: %s' % ad_reps)
            LOG.debug('ad_rep_leads: %s' % ad_rep_leads)
        for ad_rep in ad_reps:
            self.prepare_and_send_email(ad_rep.consumer, is_ad_rep=True)
        ad_rep_lead_count = self.send_email_to_ad_rep_leads(ad_rep_leads)
        log_db_entry(self.get_task_name(), task_status,
            {'last_run': datetime.today().date(), 
            'ad_rep emails_sent': len(ad_reps), 
            'ad_rep_lead emails sent': ad_rep_lead_count})
