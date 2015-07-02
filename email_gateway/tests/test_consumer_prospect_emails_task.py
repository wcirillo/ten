""" Tests for tasks of email_gateway app. """
from datetime import datetime, timedelta
import logging

from django.core import mail, validators
from django.core.exceptions import ValidationError

from common.test_utils import EnhancedTestCase
from consumer.models import Consumer
from email_gateway.tasks.consumer_prospect_emails import (
    ConsumerProspectEmailTask)
from firestorm.models import AdRep, AdRepConsumer, AdRepLead

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class TestSendConsumerProspectEmails(EnhancedTestCase):
    """ Test cases for X+1 email from the Pres. process. """

    fixtures = ['test_consumer', 'test_ad_rep']
    
    def setUp(self):
        """ Prepare consumer, today and yesterday vars for tests. """
        self.today = datetime.today().date()
        self.yesterday = datetime.today() - timedelta(1)
        self.consumer = Consumer.objects.get(id=111)
        self.consumer.consumer_create_datetime = self.yesterday
        self.consumer.email_subscription.add(1)
        self.consumer.save()

    def test_good_send(self):
        """  Assert emails are sent to users who registered yesterday.
        Assert bounce headers are set correctly.
        """
        ConsumerProspectEmailTask().run()
        x = 0
        while x < len(mail.outbox):
            LOG.debug('subject: %s' % mail.outbox[x].subject) 
            LOG.debug('to: %s' % mail.outbox[x].to[0])
            x += 1
        # Above method, send_consumer_prospect_emails send out one email per
        # consumer, plus one summary report email when completed.
        # Using date here to be earlier than datetime.today() above:
        for _mail in mail.outbox:
            consumer_emails_sent = Consumer.objects.filter(
                consumer_create_datetime__gt=self.today - timedelta(1),
                consumer_create_datetime__lt=self.today,
                is_active=True,
                email_subscription=1,
                advertiser=None,
                adrep=None,
                adreplead=None,
                is_emailable=True).count()
        self.assertEqual(len(mail.outbox), consumer_emails_sent + 1)
        self.assertEqual(mail.outbox[0].subject,
            'A message from the president of 10HudsonValleyCoupons.com')
        # Assert the from_email is valid. This is generated from email_hash,
        # and is used for bounce tracking.
        try:
            validators.validate_email(mail.outbox[0].from_email)
        except ValidationError as error:
            self.fail(error)
        self.assertTrue(mail.outbox[-1].subject[:20], 'X+1 send results for')
        self.assertTrue(
            '10HudsonValleyCoupons.com -- Sending to %s recipients' % 
            consumer_emails_sent in mail.outbox[-1].body)

    def test_send_w_ad_rep_consumer(self):
        """  Assert emails render properly when recipient has ad_rep_consumer.
        """
        ad_rep = AdRep.objects.latest('id')
        AdRepConsumer.objects.create(ad_rep=ad_rep, consumer=self.consumer)
        ConsumerProspectEmailTask().run()
        found_consumer = False
        for _mail in mail.outbox:
            if _mail.to[0] == self.consumer.email:
                found_consumer = True
                self.assertTrue('Message from the president' in _mail.subject)
                self.assertTrue(ad_rep.url in _mail.alternatives[0][0])
                self.assertTrue('Maybe you know' \
                    not in _mail.alternatives[0][0])
                self.assertTrue("looking for local Advertising Representative" \
                    not in _mail.alternatives[0][0])
                self.assertTrue("looking for local Advertising Representative" \
                    not in _mail.body)
                self.assertTrue('P.S. Know any local business' in _mail.body)
        if not found_consumer:
            self.fail('X+1 email never sent consumer with ad rep consumer')

    def test_send_w_ad_rep_lead(self):
        """  Assert emails are not sent to ad rep leads. """
        AdRepLead.objects.create_ad_rep_lead_from_con(self.consumer.id, {
            'first_name': '', 'last_name': '', 'primary_phone_number': '', 
            'email': self.consumer.email})
        ConsumerProspectEmailTask().run()
        for _mail in mail.outbox:
            if _mail.to[0] == self.consumer.email:
                self.fail('AdRepLeads cannot receive x+1 emails')
    
    def test_send_no_subscription(self):
        """  Assert emails are not sent to consumers without subscriptions. """
        self.consumer.email_subscription = []
        self.consumer.save()
        ConsumerProspectEmailTask().run()
        for _mail in mail.outbox:
            if _mail.to[0] == self.consumer.email:
                self.fail('Need an email subscription to receive x+1 emails')
                
    def test_send_not_emailable(self):
        """  Assert emails are not sent to consumers that are not emailable. """
        self.consumer.is_emailable = False
        self.consumer.save()
        ConsumerProspectEmailTask().run()
        for _mail in mail.outbox:
            if _mail.to[0] == self.consumer.email:
                self.fail('Need an email subscription to receive x+1 emails')
                
    def test_send_not_active(self):
        """  Assert emails are not sent to consumers that are not active. """
        self.consumer.is_active = False
        self.consumer.save()
        ConsumerProspectEmailTask().run()
        for _mail in mail.outbox:
            if _mail.to[0] == self.consumer.email:
                self.fail('Consumer must be active to receive x+1 emails')
