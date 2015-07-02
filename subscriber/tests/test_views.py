""" Tests for views of subscriber app. """

from django.core.urlresolvers import reverse
from django.conf import settings

from common.session import create_consumer_in_session
from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from sms_gateway.models import SMSMessageSent
from subscriber.models import Subscriber
from subscriber.factories.subscriber_factory import SUBSCRIBER_FACTORY


class TestViews(EnhancedTestCase):
    """ Test case for subscriber views. """
    urls = 'urls_local.urls_3'
    
    post_data = {'mobile_phone_number': '9145550000', 
            'subscriber_zip_postal': '12550', 'carrier': '2'}

    def assert_phone_number(self, response, mobile_phone_number):
        """ Assert the response contains the properly formatted phone number.
        """
        self.assertContains(response,
            'sent to <strong>(%s) %s-%s' % (mobile_phone_number[:3],
                mobile_phone_number[3:6], mobile_phone_number[6:]))
    
    def test_show_subscriber_reg(self):
        """ Assert that form is displayed. """
        response = self.client.get(reverse('subscriber-registration'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 
            'form id="id_form_subscriber" name="frm_subscriber_registration"')
        self.assertContains(response, 
            "input type='hidden' name='csrfmiddlewaretoken'")
        self.assertContains(response, 'input name="mobile_phone_number"')
        self.assertContains(response, 'input name="subscriber_zip_postal"')
        self.assertContains(response,
            'select id="id_carrier" class="fulltext" name="carrier"')
        self.assertNotContains(response, 'Win $10,000!*') # Suppressed.
        
    def test_post_subscriber_reg(self):
        """ Assert post to registration form without data redraws form. """
        response = self.client.post(reverse('subscriber-registration'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 
            'Please enter the 10 digit number of your cell phone')
        self.assertContains(response, 
            'Please enter a 5 digit zip')
        self.assertContains(response, 
            'Select your cell phone service provider')
        self.assertContains(response, 
            'form id="id_form_subscriber" name="frm_subscriber_registration"')
        self.assertContains(response, 
            "input type='hidden' name='csrfmiddlewaretoken'")
        self.assertContains(response, 'input name="mobile_phone_number"')
        self.assertContains(response, 'input name="subscriber_zip_postal"')
        self.assertContains(response,
            'select id="id_carrier" class="fulltext" name="carrier"')
        
    def test_valid_subscriber_reg(self):
        """ Assert Post to registration form with valid data. """
        response = self.client.post(reverse('subscriber-registration'), 
            self.post_data, follow=True)
        # Redirects to local site.
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('subscriber-registration-confirmation', 
                urlconf='urls_local.urls_2')
            ))
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 
            'A text message was sent to <strong>(914) 555-0000</strong>')
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='9145550000')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.site_id, 2)
        sms_message_sent = SMSMessageSent.objects.latest('id')
        self.assertEqual(sms_message_sent.smsto, '9145550000')
        self.assertEqual(sms_message_sent.smsmsg[:50], 
            "10Coupons Alrts: Reply YES to get text coupons (4m")
    
    def test_update_subscriber_reg(self):
        """ Assert Post to registration form with valid data for existing 
        subscriber updates the carrier. """
        subscriber = SUBSCRIBER_FACTORY.create_subscriber()
        mobile_phone_number = subscriber.mobile_phones.all(
            )[0].mobile_phone_number
        post_data = {'mobile_phone_number': mobile_phone_number,
            'subscriber_zip_postal': '12601', 'carrier': '4'}
        response = self.client.post(reverse('subscriber-registration'), 
            post_data, follow=True)
        self.assert_phone_number(response, mobile_phone_number)
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number=mobile_phone_number)
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        self.assertEqual(subscriber.mobile_phones.all()[0].carrier.id, 4)

    def test_consumer_new_subscriber(self):
        """ Assert existing consumer updated with new subscriber. """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.post(reverse('subscriber-registration'), 
            self.post_data, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        updated_consumer = Consumer.objects.get(id=consumer.id)
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='9145550000')
        except Subscriber.DoesNotExist:
            self.fail('Subscriber was not created for consumer.')
        self.assertEqual(updated_consumer.subscriber, subscriber)
        self.assertEqual(subscriber.subscriber_zip_postal, '12550')
           
    def test_subscriber_reg_with_con(self):
        """ Post to registration form with valid data, with a consumer already
        in session. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        post_data = {'mobile_phone_number': '9145550001', 
            'subscriber_zip_postal': '12550', 'carrier': '2'}
        response = self.client.post(reverse('subscriber-registration'), 
            post_data, follow=True)
        # Redirects to local site.
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('subscriber-registration-confirmation', 
                urlconf='urls_local.urls_2')
            ))
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 
            'A text message was sent to <strong>(914) 555-0001</strong>')
        consumer = Consumer.objects.get(id=consumer.id)
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='9145550001')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.site_id, 2)
        self.assertEqual(consumer.subscriber, subscriber)
        sms_message_sent = SMSMessageSent.objects.latest('id')
        self.assertEqual(sms_message_sent.smsto, '9145550001')
        self.assertEqual(sms_message_sent.smsmsg[:50], 
            "10Coupons Alrts: Reply YES to get text coupons (4m")

    def test_repeat_sub_reg_with_con(self):
        """ Post a phone number already in the database to registration form
        with valid data, with a consumer already in session.
        """
        subscriber = SUBSCRIBER_FACTORY.create_subscriber()
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        mobile_phone_number = subscriber.mobile_phones.all(
            )[0].mobile_phone_number
        post_data = {'mobile_phone_number': mobile_phone_number,
            'subscriber_zip_postal': '12550', 'carrier': '2'}
        response = self.client.post(reverse('subscriber-registration'), 
            post_data, follow=True)
        # Redirects to local site.
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('subscriber-registration-confirmation', 
                urlconf='urls_local.urls_2')
            ))         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assert_phone_number(response, mobile_phone_number)
        consumer = Consumer.objects.get(id=consumer.id)
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number=mobile_phone_number)
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.site_id, 2)
        self.assertEqual(consumer.subscriber, subscriber)
        sms_message_sent = SMSMessageSent.objects.latest('id')
        self.assertEqual(sms_message_sent.smsto, mobile_phone_number)
        self.assertEqual(sms_message_sent.smsmsg[:50], 
            "10Coupons Alrts: Reply YES to get text coupons (4m")
    
    def test_get_coupons_sub_form(self):
        """ Assert all coupons with consumer in session loads subscriber form
        and contest text is not suppressed.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('all-coupons'))
        self.assertTemplateUsed(response, 'coupon/display_all_coupons.html')
        self.assertContains(response, 'Win $10,000!*')

    def test_reenter_off_site_zip(self):
        """ Assert a consumer in session posts a phone number registered to
        another consumer on the all coupons page.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        subscriber = SUBSCRIBER_FACTORY.create_subscriber()
        consumer_2 = CONSUMER_FACTORY.create_consumer()
        consumer_2.subscriber = subscriber
        consumer_2.save()
        mobile_phone_number = subscriber.mobile_phones.all(
            )[0].mobile_phone_number
        self.assemble_session(self.session)
        post_data = {'mobile_phone_number': mobile_phone_number,
            'subscriber_zip_postal': '12550', 'carrier': '5'}
        response = self.client.post(reverse('all-coupons'), post_data)
        self.assertTemplateUsed(response, 'coupon/display_all_coupons.html')
        self.assertTemplateUsed(response, 
            'include/dsp/dsp_pricing_unlocked.html')
        
    def test_con_sub_reg_confirmation(self):
        """ Assert consumer + subscriber registration success confirmation page
        displays correctly if is_email_verified is not set in session.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        CONSUMER_FACTORY.qualify_consumer(consumer)
        create_consumer_in_session(self, consumer)
        # Remove is_email_verified from session.
        del self.session['consumer']['is_email_verified']
        self.assemble_session(self.session)
        response = self.client.post(reverse('con-sub-reg-confirmation'))
        self.assertTemplateUsed(response,
            'registration/display_con_sub_reg_confirmation.html')
        self.assertTemplateUsed(response,
            'include/dsp/dsp_subscriber_registration_confirmation.html')
        self.assertTemplateUsed(response,
            'include/dsp/dsp_con_sub_reg_confirmation.html')

    def test_log_out_subscriber_reg(self):
        """ Assert a consumer is removed from session on logout. """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('log-out-subscriber-registration'),
            follow=True)
        self.assertEqual(response.status_code, 200)
        # Asserting that it does not say "...@10coupons.com | My Account"
        self.assertNotContains(response, consumer.email)
        self.assertContains(response, 'sign in</a>')
 
    def test_update_solo_subscriber(self):
        """ Assert Post to registration form with valid data for existing 
        subscriber that has no consumer updates the zip and carrier. """
        subscriber = SUBSCRIBER_FACTORY.create_subscriber()
        mobile_phone_number = subscriber.mobile_phones.all(
            )[0].mobile_phone_number
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        post_data = {'mobile_phone_number': mobile_phone_number,
            'subscriber_zip_postal': '12550', 'carrier': '3'}
        response = self.client.post(reverse('subscriber-registration'), 
            post_data, follow=True)       
        self.assert_phone_number(response, mobile_phone_number)
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number=mobile_phone_number)
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        self.assertEqual(subscriber.mobile_phones.all()[0].carrier.id, 3)
        self.assertEqual(subscriber.subscriber_zip_postal, '12550')
