""" Test cases for email tasks of firestorm app of project ten. """
import datetime
import logging
import time

from django.core import mail
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from common.custom_format_for_display import format_phone
from common.service.payload_signing import PAYLOAD_SIGNING
from common.test_utils import EnhancedTestCase
from email_gateway.tests.test_email_task import TestEmailTask
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.factories.ad_rep_lead_factory import AD_REP_LEAD_FACTORY
from firestorm.models import AdRepConsumer
from firestorm.tasks import (SEND_ENROLLMENT_EMAIL, AD_REP_INVITE_TASK,
    AD_REP_LEAD_PROMO_TASK)
from firestorm.tasks.email_tasks import (NOTIFY_NEW_RECRUIT, 
    SendMarketManagerPitch)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def get_mail_index_to_email(email):
    """ Loop through the mail.inbox and get the piece of mail to this email. """
    index = 0
    for idx, box in enumerate(mail.outbox):
        if box.to[0] == email:
            index = idx
            break
    return index


class TestCeleryTaskDelay(EnhancedTestCase):
    """ Test a celery task defined as a class (not a decorator) will run
    with delay.
    """
    def test_task_delay(self):
        """ Test simple notify ad rep lead task will execute with delay. """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        AD_REP_INVITE_TASK.delay(test_mode=[ad_rep_lead])
        time.sleep(2) # Give it 2 full seconds to execute before we check.
        self.assertTrue(len(mail.outbox))


class TestSendEnrollmentEmail(EnhancedTestCase):
    """ Test case for the SendEnrollmentEmail task. """
    
    def common_asserts(self, ad_rep):
        """ Make common assertions on email content. """
        self.assertEqual(ad_rep.email_subscription.values_list('id')[0][0], 6)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], ad_rep.email)
        self.assertTrue('Welcome Aboard!' in mail.outbox[0].subject)
        self.assertTrue(ad_rep.first_name in mail.outbox[0].alternatives[0][0])
        self.assertTrue(ad_rep.url in mail.outbox[0].alternatives[0][0])
        self.assertTrue(ad_rep.first_name in mail.outbox[0].body)
        self.assertTrue(ad_rep.url in mail.outbox[0].body)

    def test_send_email_good(self):
        """ Assert the enrollment email is sent. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        mail.outbox = []
        SEND_ENROLLMENT_EMAIL.run(ad_rep.id)
        self.common_asserts(ad_rep)
        self.assertTrue('To Activate your Virtual Office' 
            not in mail.outbox[0].alternatives[0][0])
        
    def test_send_referred_email(self):
        """ Assert the enrollment email is sent with text for a referred ad rep.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        mail.outbox = []
        SEND_ENROLLMENT_EMAIL.run(ad_rep.id, referred=True)
        self.common_asserts(ad_rep)
        self.assertTrue('Activate your '
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue('Virtual Office</a>'
            in mail.outbox[0].alternatives[0][0])
        # Ad reps in initial version create their password at sign up.
        self.assertTrue('Create Password Now'
            not in mail.outbox[0].alternatives[0][0])
        self.assertTrue('your Password with this link'
            not in mail.outbox[0].body)
        self.assertTrue('Go to your Virtual Office'
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue('Activate your Virtual Office using this link'
            in mail.outbox[0].body)
        

class TestNotifyNewRecruit(EnhancedTestCase):
    """ Test cases for firestorm email task NotifyNewRecruit. """
    fixtures = ['test_sales_rep']

    def test_send_good(self):
        """ Assert sending email when good. """
        child_ad_rep = AD_REP_FACTORY.create_ad_rep()
        parent_ad_rep = AD_REP_FACTORY.create_ad_rep()
        child_ad_rep.parent_ad_rep = parent_ad_rep
        child_ad_rep.save()
        mail.outbox = []
        NOTIFY_NEW_RECRUIT.run(child_ad_rep.id)
        self.assertEqual(mail.outbox[0].subject, 
            'A New Team Member may help you Earn More')
        self.assertTrue("%s %s" % 
            (parent_ad_rep.first_name, parent_ad_rep.last_name)
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("%s %s" % 
            (parent_ad_rep.first_name, parent_ad_rep.last_name)
            in mail.outbox[0].body)
        self.assertTrue("%s %s" % 
            (child_ad_rep.first_name, child_ad_rep.last_name)
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("%s %s" % 
            (child_ad_rep.first_name, child_ad_rep.last_name)
            in mail.outbox[0].body)
        self.assertTrue(child_ad_rep.email in mail.outbox[0].alternatives[0][0])
        self.assertTrue(child_ad_rep.email in mail.outbox[0].body)
        self.assertTrue(format_phone(child_ad_rep.primary_phone_number)
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue(format_phone(child_ad_rep.primary_phone_number)
            in mail.outbox[0].body)
        self.assertTrue(reverse('compensation-plan')
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue(reverse('compensation-plan') in mail.outbox[0].body)
        self.assertTrue("There's a new member of your team"
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("There's a new member of your team" 
            in mail.outbox[0].body)
        self.verify_email_sub_list(mail.outbox[0].alternatives[0][0], [6])
        self.assertTrue('Reputable@10Coupons.com' 
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue('Reputable@10Coupons.com' in mail.outbox[0].body)
        
        
    def test_send_no_parent(self):
        """ Assert that when new ad rep has no parent, no email is sent. """
        child_ad_rep = AD_REP_FACTORY.create_ad_rep()
        mail.outbox = []
        NOTIFY_NEW_RECRUIT.run(child_ad_rep.id)
        self.assertEqual(len(mail.outbox), 0)


class TestAdRepLeadPromoTask(EnhancedTestCase):
    """ Test cases once-out email task AdRepLeadPromoTask that will send to
    leads created in a specific time frame to notify of changes to our
    enrollment process.
    """
    fixtures = ['test_sales_rep']
    @staticmethod
    def create_sendable_lead():
        """ Create a lead that will receive an email by this task for testing."""
        ad_rep_lead_sendable = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        ad_rep_lead_sendable.create_datetime = datetime.date(2011, 12, 16)
        ad_rep_lead_sendable.save()
        mail.outbox = []
        return ad_rep_lead_sendable

    @staticmethod
    def get_sample_email(lead_email):
        """ Return email to make assertions against. """
        email = None
        for email in mail.outbox:
            if email.to == lead_email:
                break
        return email

    def common_email_assertions(self, email, ):
        """ Assert basic text is used in the email. """
        self.assertEqual(email.subject, "%s%s" % (
            'Start today as an Advertising Representative',
            ' for 10HudsonValleyCoupons.com'))
        self.assertTrue("interest you've shown in joining" 
            in email.alternatives[0][0])
        self.assertTrue("Here's some important news" in email.body)
        self.assertTrue("/hudson-valley/enrollment-offer/" 
            in email.alternatives[0][0])
        self.assertTrue("/hudson-valley/enrollment-offer/" in email.body)
        self.assertTrue("marketing-resources/terms-of-agreement/" 
            in email.alternatives[0][0])
        self.assertTrue("marketing-resources/terms-of-agreement/" in email.body)
        self.assertTrue("you <strong>won't</strong>" 
            in email.alternatives[0][0])
        self.assertTrue("You WON'T be asked" in email.body)
        self.assertTrue("to cancel these email messages"
            in email.alternatives[0][0])
        self.assertTrue("to cancel these email messages" in email.body)

    def test_created_time_span(self):
        """ Assert only leads within time span are selected. """
        ad_rep_lead_too_old = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        AD_REP_LEAD_FACTORY.create_ad_rep_lead() # Too new.
        ad_rep_lead_sendable = self.create_sendable_lead()
        ad_rep_lead_too_old.create_datetime = datetime.date(2011, 11, 30)
        ad_rep_lead_too_old.save()
        leads = AD_REP_LEAD_PROMO_TASK.get_ad_rep_leads()
        self.assertEqual(leads.count(), 1)
        self.assertEqual(leads[0].email, ad_rep_lead_sendable.email)
    
    def test_email_with_first_name(self):
        """ Assert email greeting with first name of lead present. """
        ad_rep_lead = self.create_sendable_lead()
        AD_REP_LEAD_PROMO_TASK.run()
        self.assertTrue(len(mail.outbox) > 0)
        email = self.get_sample_email(ad_rep_lead.email)
        self.assertTrue(email.to, ad_rep_lead.email)
        self.assertTrue('Hi %s' % ad_rep_lead.first_name
            in email.alternatives[0][0])
        self.assertTrue('Hi %s' % ad_rep_lead.first_name
            in email.body)
        self.common_email_assertions(email)
    
    def test_ad_rep_signature(self):
        """ Assert ad rep signature present when lead is related. """
        ad_rep_lead = self.create_sendable_lead()
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        ad_rep_lead.ad_rep = ad_rep
        ad_rep_lead.save()
        request = RequestFactory().get(reverse('contact-us'))
        request.session = {}
        AdRepConsumer.objects.create_update_rep(
            request, ad_rep_lead.consumer, ad_rep)
        AD_REP_LEAD_PROMO_TASK.run()
        self.assertTrue(len(mail.outbox) > 0)
        email = self.get_sample_email(ad_rep_lead.email)
        self.assertTrue(email.to, ad_rep_lead.email)
        self.common_email_assertions(email)
        self.assertTrue(ad_rep.first_name in email.alternatives[0][0])
        self.assertTrue(ad_rep.first_name in email.body)
        self.assertTrue(ad_rep.url in email.alternatives[0][0])
        self.assertTrue(ad_rep.url in email.body)
    
    def test_generic_signature(self):
        """ Assert generic signatures when no ad rep related to lead. """
        ad_rep_lead = self.create_sendable_lead()
        AD_REP_LEAD_PROMO_TASK.run()
        self.assertTrue(len(mail.outbox) > 0)
        email = self.get_sample_email(ad_rep_lead.email)
        self.assertTrue(email.to, ad_rep_lead.email)
        self.assertTrue('Eric Straus, Pres' in email.alternatives[0][0])
        self.assertTrue('Eric Straus, Pres' in email.body)
        self.assertTrue('David Sage, Chie' in email.alternatives[0][0])
        self.assertTrue('David Sage, Chie' in email.body)
        self.assertTrue('Alana Lenec, Cus' in email.alternatives[0][0])
        self.assertTrue('Alana Lenec, Cus' in email.body)

    
class TestAdRepLeadEmails(EnhancedTestCase):
    """ Test cases for email sent to ad rep or sales rep for ad rep lead and
    welcome email sent to lead.
    """
    fixtures = ['test_sales_rep']

    def common_notify_asserts(self, index, site, ad_rep, ad_rep_lead):
        """ Assert common notification email conditions are met. """
        formatted_phone = '(%s) %s-%s' % (ad_rep_lead.primary_phone_number[:3],
            ad_rep_lead.primary_phone_number[3:6], 
            ad_rep_lead.primary_phone_number[6:])
        self.assertTrue("answered these questions." in mail.outbox[index].body)
        self.assertTrue(ad_rep_lead.email in mail.outbox[index].body)
        self.assertTrue(formatted_phone in mail.outbox[index].body)
        self.assertTrue('Reputable Salesperon' in mail.outbox[index].body)
        self.assertTrue("Here\'s some information about:" in
            mail.outbox[index].alternatives[0][0])
        self.assertTrue(ad_rep_lead.email in
            mail.outbox[index].alternatives[0][0])
        self.assertTrue(formatted_phone in
            mail.outbox[index].alternatives[0][0])
        self.assertTrue('Reputable Salesperon' in
            mail.outbox[index].alternatives[0][0])
        if site.id == 1:
            self.assertEqual(mail.outbox[index].extra_headers['From'],
                'Reputable at 10LocalCoupons.com <Coupons@10Coupons.com>')
        else:
            self.assertEqual(mail.outbox[index].extra_headers['From'],
                'Reputable at 10HudsonValleyCoupons.com <Coupons@10Coupons.com>')
        if ad_rep:
            self.assertEqual(mail.outbox[index].subject,
                'New Lead - Advertising Representative')
        else:
            self.assertEqual(mail.outbox[index].subject,
                'New Lead - Advertising Representative')
        # Test if email list ID in payload
        self.assertTrue(self.verify_email_sub_list(
            mail.outbox[index].alternatives[0][0], 4))


class TestAdRepLeadMarketMgrPitch(EnhancedTestCase):
    """ Test cases for email sent to ad rep leads promoting market manager
    position.
    """
    def create_ad_rep_lead(self, **kwargs):
        """ Create an ad rep lead for testing. """
        if kwargs.get('add_subscriptions', 'use_default') == 'use_default':
            ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        else:
            ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead(
                add_subscriptions=False)
        created_days_past = kwargs.get('created_days_past', 7)
        ad_rep_lead.create_datetime = (
            datetime.datetime.today() - datetime.timedelta(created_days_past))
        ad_rep_lead.save()
        self.ad_rep_lead = ad_rep_lead

    def test_honor_subscription(self):
        """ Assert the recipient ad rep lead has not opted out of the adreplead
        email subscription.
        """
        self.assertEqual(len(mail.outbox), 0)
        self.create_ad_rep_lead(add_subscriptions=False)
        SendMarketManagerPitch().run(test_mode=self.ad_rep_lead.email)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_is_emailable(self):
        """ Assert the recipient ad rep lead is_emailable = True. """
        self.assertEqual(len(mail.outbox), 0)
        self.create_ad_rep_lead()
        self.ad_rep_lead.is_emailable = False
        self.ad_rep_lead.save()
        SendMarketManagerPitch().run(test_mode=self.ad_rep_lead.email)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_created_outside_range(self):
        """ Assert the recipient ad rep lead has a created date in the time
        frame specified between last_run (max 90 days) and yesterday.
        """
        self.assertEqual(len(mail.outbox), 0)
        self.create_ad_rep_lead(created_days_past=200)
        SendMarketManagerPitch().run(test_mode=self.ad_rep_lead.email)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_created_today(self):
        """ Assert recipient signed up today does not get email on task run. """
        self.assertEqual(len(mail.outbox), 0)
        self.create_ad_rep_lead(created_days_past=0)
        SendMarketManagerPitch().run(test_mode=self.ad_rep_lead.email)
        self.assertEqual(len(mail.outbox), 0)
   
    def test_email_task_already_ran(self):
        """ Assert task will not run twice on the same day (without rerun flag)
        """
        self.assertEqual(len(mail.outbox), 0)
        self.create_ad_rep_lead(created_days_past=0)
        SendMarketManagerPitch().run(test_mode=self.ad_rep_lead.email)
        self.assertEqual(len(mail.outbox), 0)
        # Run again.
        result = SendMarketManagerPitch().run(test_mode=self.ad_rep_lead.email)
        self.assertEqual(result, 
            'Aborted:: SendMarketManagerPitch already ran today')

    def test_email_content(self):
        """ Assert email content on successful send. """
        self.assertEqual(len(mail.outbox), 0)
        self.create_ad_rep_lead()
        SendMarketManagerPitch().run(days_past=7, test_mode=self.ad_rep_lead.email)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 
            'Market Manager Opportunity - Exclusive Territory')
        self.assertTrue(self.ad_rep_lead.first_name in mail.outbox[0].body)
        self.assertTrue(self.ad_rep_lead.first_name
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue('ONE great Market Manager' in mail.outbox[0].body)
        self.assertTrue('ONE great Market Manager' 
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue('Eric Straus' in mail.outbox[0].body)
        self.assertTrue('Eric Straus' in mail.outbox[0].alternatives[0][0])
        self.assertTrue('cancel these email messages' in mail.outbox[0].body)
        self.assertTrue('unsubscribe' in mail.outbox[0].alternatives[0][0])

    def test_unsubscribe_payload(self):
        """ Assert when user unsubscribes from AdRepLead subscription they also
        get unsubscribed from ad rep meeting reminder subscription. 
        """
        self.create_ad_rep_lead()
        subscription_list = self.ad_rep_lead.email_subscription.all(
            ).order_by('id').values_list('id')
        self.assertEqual(subscription_list[0][0], 1)
        self.assertEqual(subscription_list[1][0], 5)
        self.assertEqual(subscription_list[2][0], 6)
        list_id_list = [5]
        response = self.client.get(reverse('opt_out',
            args=[PAYLOAD_SIGNING.create_payload(
                email=self.ad_rep_lead.email, subscription_list=list_id_list)]),
                follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(self.ad_rep_lead.email_subscription.count(), 1)
        # Email flyer subscription should still exist.
        self.assertEqual(
            self.ad_rep_lead.email_subscription.values_list('id')[0][0], 1)
