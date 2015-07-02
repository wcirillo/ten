""" Tests for tasks of email_gateway app. """
from datetime import datetime, timedelta
import logging

from django.core import mail

from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import ConsumerHistoryEvent, EmailSubscription
from email_gateway.tasks.ad_rep_mtg_reminder_email import AdRepMtgReminderEmail
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRepLead

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestAdRepMtgReminder(EnhancedTestCase):
    """ This class has the tests for the AdRepMtgReminderEmail Task. """
    
    def setUp(self):
        """ Create test users: ad rep and ad rep lead. """
        self.email_task = AdRepMtgReminderEmail()
        self.create_ad_rep_lead(32)
        self.ad_rep_lead = self.create_ad_rep_lead(2)
        self.ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.ad_rep.email_subscription.add(self.email_task.list_id)
        
    def create_ad_rep_lead(self, days_ago):
        """ Create ad rep lead test user. """
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.consumer_create_datetime = \
            datetime.now() - timedelta(days=days_ago)
        consumer.save()
        ad_rep_lead = AdRepLead.objects.create_ad_rep_lead_from_con(
            consumer.id, {'first_name': '', 'last_name': '', 
                'primary_phone_number': '', 'email': consumer.email})
        ad_rep_lead.email_subscription.add(self.email_task.list_id)
        return ad_rep_lead
    
    def test_send_email_success(self):
        """ Assert an email is sent to all ad reps and all ad rep leads with 
        meeting reminder email subscription. """
        mail.outbox = []
        self.email_task.run()
        self.assertEquals(len(mail.outbox), 3) # 2 ad rep leads, 1 ad rep
        for num in [0, 1, 2]:
            for text in ['Conference', '10LocalCoupons.com', 'opt-out', 
                'Participant Access Code']:
                LOG.debug(text)
                self.assertTrue(text in mail.outbox[num].alternatives[0][0])
                self.assertTrue(text in mail.outbox[num].body)
            self.assertTrue('10LocalCoupons.com' in mail.outbox[num].subject)
            self.assertTrue('Coupons.com <Coupons@10Coupons.com>' in 
                mail.outbox[num].extra_headers['From'])
        # one last check for content in ad rep lead email
        text = 'rush up on basic'
        self.assertFalse(text in mail.outbox[2].alternatives[0][0])
        self.assertTrue(self.verify_email_sub_list(
            mail.outbox[2].alternatives[0][0], 6))
        self.assertFalse(text in mail.outbox[2].body)
        history = self.ad_rep_lead.history.all()[0]
        self.assertTrue(history.event_type, 10)
        self.assertTrue(history.data, 6)
   
    def test_qry_ad_reps(self):
        """ Test query ad reps returns ad_reps and not referring consumers."""
        self.assertEqual(self.email_task.qry_ad_reps().count(), 1)

    def test_qry_ad_rep_leads(self):
        """ Test query ad_rep_leads returns ad_rep_leads only."""
        self.assertEqual(self.email_task.qry_ad_rep_leads().count(), 2)

    def test_qry_ad_rep_leads_new(self):
        """ Assert new ad rep lead will get email, not existing ad reps or 
        ad rep leads. Also verify if an ad rep lead was sent the email when the
        last time they got the email was more than a month ago. """
        self.email_task.run()
        self.assertEquals(len(mail.outbox), 4)
        # create ad rep, 2 emails sent, 2 ad rep leads, 1 ad rep
        ad_rep_lead = self.create_ad_rep_lead(0)
        self.email_task.run(rerun=True)
        self.assertEquals(len(mail.outbox), 6) # 1 new ad rep lead, 1 ad rep
        email_subscription = EmailSubscription.objects.get(
            id=self.email_task.list_id)
        email_subscription_name = email_subscription.email_subscription_name
        consumer_history = ConsumerHistoryEvent.objects.filter(
            consumer=ad_rep_lead, event_type='10', 
            data__contains={'email_subscription_name': email_subscription_name}
            ).order_by('-event_datetime')[0]
        consumer_history.event_datetime = datetime.now() - timedelta(days=32)
        consumer_history.save()
        self.email_task.run(rerun=True)
        self.assertEquals(len(mail.outbox), 8) 
        # 1 ad rep, 1 ad rep lead which got the email more than 30 days ago 
        self.assertEquals(len(ConsumerHistoryEvent.objects.filter(
            consumer=ad_rep_lead, event_type='10', 
            data__contains={'email_subscription_name': email_subscription_name}
            )), 1)
        
    def test_mtg_reminder_test_mode(self):
        """ Test mtg reminder test_mode."""
        mail.outbox = []
        self.email_task.run(test_mode=self.ad_rep_lead.email)
        self.assertEquals(len(mail.outbox), 1) # ad rep lead is emailed
