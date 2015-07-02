""" Tests for tasks of email_gateway app. """
from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core import mail

from advertiser.models import Advertiser
from common.test_utils import EnhancedTestCase
from consumer.models import Consumer
from consumer.service import get_site_rep
from email_gateway.tasks.unqualified_consumer_emails import (
    UnqualifiedConsumerEmailTask)
from firestorm.models import AdRep, AdRepAdvertiser
from logger.service import get_last_db_log
from subscriber.models import Subscriber

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class TestUnqualifiedEmail(EnhancedTestCase):
    """ Test case for send_unqualified_email X+3 task. """
    fixtures = ['test_consumer', 'test_advertiser', 'test_sales_rep', 
        'test_subscriber', 'test_ad_rep']

    def prep_consumer(self):
        """ Prep consumer for test. """
        self.consumer = Consumer.objects.get(id=101)
        if self.consumer.subscriber:
            self.fail('It is assumed that this consumer has no subscriber.')
        self.three_days_ago = datetime.today().date() - timedelta(days=3)
        self.consumer.consumer_create_datetime = self.three_days_ago
        self.consumer.email_subscription.add(1)
        self.consumer.is_emailable = True
        self.rep = get_site_rep(self.consumer.site)
        self.consumer.save()
    
    def prep_advertiser(self):
        """ Prep advertiser for test. """
        self.prep_consumer()
        self.advertiser = Advertiser.objects.get(id=113)
        self.consumer = Consumer.objects.get(id=113)
        self.consumer.consumer_create_datetime = self.three_days_ago
        self.consumer.email_subscription.add(1)
        self.consumer.save()
    
    def prep_ad_rep(self, ad_rep):
        """ Prep advertiser with ad rep for test. """
        self.prep_advertiser()
        AdRepAdvertiser.objects.create(
            ad_rep=ad_rep, advertiser=self.advertiser)

    def common_asserts(self, ad_rep=False):
        """ Test common assertions. """
        self.assertEqual(mail.outbox[0].subject,
            'Are you ready to win $10,000?')
        self.assertEqual(mail.outbox[0].to, [self.consumer.email])
        self.assertEqual(mail.outbox[0].extra_headers['Reply-To'],
                '%s@10Coupons.com' % (self.rep.consumer.first_name))
        if not ad_rep:
            self.assertTrue('%s %s' % (self.rep.consumer.first_name,
                self.rep.consumer.last_name) in mail.outbox[0].body)
            self.assertTrue('%s %s' % (self.rep.consumer.first_name,
                self.rep.consumer.last_name)
                in mail.outbox[0].alternatives[0][0])
            self.assertTrue( '%s at %s' % (self.rep.consumer.first_name, 
                self.consumer.site.domain) 
                in mail.outbox[0].extra_headers['From'])
    
    def test_qry_unqualified_eligible(self):
        """ Assert that there are no qualified, eligible consumers in this 
        query. """
        from_date = datetime.strptime('2008-01-01', '%Y-%m-%d')
        to_date = datetime.today().date()
        consumer = Consumer.objects.get(id=106)
        subscriber = Subscriber.objects.get(id=6)
        consumer.subscriber = subscriber
        consumer.save()
        result = UnqualifiedConsumerEmailTask().qry_unqualified_consumers(
            from_date, to_date)
        self.assertEqual(result.filter(id=106).count(), 0)
        
    def test_unqualified_by_date(self):
        """ Assert that unqualified, eligible consumers were selected in the 
        confines of the dates specified. """
        to_date = datetime.today() - timedelta(days=2)
        from_date = to_date.date() - timedelta(days=2)
        consumer = Consumer.objects.get(id=103)
        consumer.is_emailable = True
        consumer.consumer_create_datetime = to_date - timedelta(days=1)
        consumer.save()
        result = UnqualifiedConsumerEmailTask().qry_unqualified_consumers(
            from_date, to_date.date())
        self.assertEqual(result.filter(id=103).count(), 1) 

    def test_emailable(self):
        """ Assert that unqualified, eligible consumers are emailable. """
        to_date = datetime.today() - timedelta(days=2)
        consumer = Consumer.objects.get(id=103)
        consumer.consumer_create_datetime = to_date - timedelta(days=1)
        consumer.is_emailable = False
        consumer.save()
        from_date = to_date.date() - timedelta(days=2)
        result = UnqualifiedConsumerEmailTask().qry_unqualified_consumers(
            from_date, to_date.date())
        self.assertEqual(result.filter(id=103).count(), 0)

    def test_verified_consumer(self):
        """ Assert email for a consumer that is verified. """
        self.prep_consumer()
        self.consumer.is_email_verified = True
        self.consumer.save()
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        self.common_asserts()
        self.assertTrue('Use this link to confirm your email address.' not in
            mail.outbox[0].body)
        self.assertTrue('Confirm your email address with a single click.' not in
            mail.outbox[0].alternatives[0][0])
        self.assertEqual(mail.outbox[0].cc, [])
        self.assertTrue('Provide your cell phone number' 
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue('Provide your cell phone number. Follow this link:' 
            in mail.outbox[0].body)

    def test_unverified_consumer(self):
        """ Assert email to unqualified consumer that is not yet verified. """
        self.prep_consumer()
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        self.common_asserts()
        self.assertTrue('Confirm your email address with a single click.' in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue('Use this link to confirm your email address' in
            mail.outbox[0].body)
        
    def test_consumer_w_subscriber(self):
        """ Assert consumer with subcriber with phone does not prompt to 
        subscribe.
        """
        self.prep_consumer()
        subscriber = Subscriber.objects.get(id=6)
        self.consumer.subscriber = subscriber
        self.consumer.save()
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        self.common_asserts()
        self.assertTrue('Provide your cell phone number' 
            not in mail.outbox[0].alternatives[0][0])
        self.assertTrue('Provide your cell phone number. Follow this link:' 
            not in mail.outbox[0].body)

    def test_unverified_subscriber(self):
        """ Assert consumer with subcriber with an unverified phone is not
        prompted to subscribe but does get a message about verifying their 
        phone number.
        """
        self.prep_consumer()
        subscriber = Subscriber.objects.get(id=7)
        self.consumer.subscriber = subscriber
        self.consumer.save()
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        self.common_asserts()
        self.assertTrue('71010' in mail.outbox[0].alternatives[0][0])
        self.assertTrue('71010' in mail.outbox[0].body)
    
    def test_email_after_contest_end(self):
        """ Assert task will abort if contest is no longer running. """
        self.prep_consumer()
        temp_date = settings.CONTEST_END_DATE
        settings.CONTEST_END_DATE = str(
            datetime.today().date() - timedelta(days=1))
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        log = get_last_db_log(
            'email_gateway.tasks.send_unqualified_emails', 'EMAIL')
        if log:
            self.fail('Performed task even though contest ended.')
        settings.CONTEST_END_DATE = temp_date
    
    def test_advertiser_recipient(self):
        """ Assert advertiser recipient email success. """
        self.prep_advertiser()
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        self.common_asserts()
    
    def test_advertiser_w_ad_rep(self):
        """ Assert advertiser with ad rep, gets ad rep's signature and friendly
        from display.
        """
        ad_rep = AdRep.objects.get(id=1000)
        self.prep_ad_rep(ad_rep)
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        self.common_asserts(ad_rep=True)
        self.assertTrue('%s %s' % (ad_rep.first_name,
                ad_rep.last_name) in mail.outbox[0].body)
        self.assertTrue('%s %s' % (ad_rep.first_name, 
            ad_rep.last_name) in mail.outbox[0].alternatives[0][0])
        self.assertTrue( '%s at %s' % (ad_rep.first_name, 
            self.consumer.site.domain) in mail.outbox[0].extra_headers['From'])
        self.assertEqual(len(mail.outbox),  # ad rep, consumer, admin report.
            2 + len(settings.NOTIFY_CONSUMER_UNQUALIFIED_REPORT))
        for email in mail.outbox:
            if email.to == self.consumer.email or ad_rep.email:
                self.assertEqual(mail.outbox[0].extra_headers['Cc'],
                ad_rep.email)
    
    def test_adv_w_customer_ad_rep(self):
        """ Assert advertiser with ad_rep of rank CUSTOMER ignores ad rep. """
        ad_rep = AdRep.objects.get(id=1000)
        ad_rep.rank = 'CUSTOMER'
        ad_rep.save()
        self.prep_ad_rep(ad_rep)
        UnqualifiedConsumerEmailTask().run(test_mode=self.consumer)
        self.common_asserts()
        
    def test_double_run_same_day(self):
        """ Assert when task runs twice on the same day, the 2nd run is aborted.
        """
        self.prep_consumer()
        UnqualifiedConsumerEmailTask().run()
        first_log = get_last_db_log(
            'email_gateway.tasks.send_unqualified_emails', 'EMAIL')
        UnqualifiedConsumerEmailTask().run()
        second_log = get_last_db_log(
            'email_gateway.tasks.send_unqualified_emails', 'EMAIL')
        self.assertEqual(first_log, second_log)
