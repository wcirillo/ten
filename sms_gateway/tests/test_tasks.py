"""
Tests of sms_gateway app tasks. Also see test_tasks_email.py.
"""

from django.conf import settings

from consumer.models import Consumer
from sms_gateway.models import SMSMessageSent, SMSMessageReceived, SMSResponse
from sms_gateway.tests.sms_gateway_test_case import SMSGatewayTestCase
from subscriber.models import Subscriber, MobilePhone, SMSSubscription

settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
settings.CELERY_ALWAYS_EAGER = True


class TestTasks(SMSGatewayTestCase):
    """ Some tests of sms_gateway for EzTexting API. """
    # Loading the sms_gateway itself will cause post_save signal to fire,
    # if there are any SMSMessagesReceived.
    
    def test_program_brief(self):
        """
        Here we test the full function flow of someone following the program
        brief we filed with EZTexting and, through them, the phone carriers.
        """
        mobile_phone_number = '8455551000'
        sms_message_received = SMSMessageReceived(smsid='100', 
            smsfrom=mobile_phone_number, smsmsg='save', network='ATTUS',
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(
                smsto=mobile_phone_number)
        except SMSMessageSent.DoesNotExist:
            self.fail('We did not respond to a valid message received.')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number=mobile_phone_number)
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        try:
            mobile_phone = MobilePhone.objects.get(
                mobile_phone_number=mobile_phone_number)
        except MobilePhone.DoesNotExist as error:
            self.fail(error)
        self.assertTrue(mobile_phone.is_verified)
        sms_message_received = SMSMessageReceived(smsid='101', 
            smsfrom='8455551000', smsmsg='12550', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        sms_message_sent = SMSMessageSent.objects.latest('id')
        self.assertEqual(sms_message_sent.smsto, '8455551000')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['hv_consumer'])
        self.assertEqual(subscriber.sms_subscription.count(), 1)
        sms_message_received = SMSMessageReceived(smsid='102', 
            smsfrom='8455551000', smsmsg='STOP', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        sms_message_sent = SMSMessageSent.objects.latest('id')
        self.assertEqual(sms_message_sent.smsto, '8455551000')
        self.assertEqual(sms_message_sent.smsmsg[15:65], self.good_sms['opt_out'])
        self.assertEqual(subscriber.sms_subscription.count(), 0)
            
    def test_save_subscriber(self):
        """
        Here we get the word "save" from someone who is already a subscriber.
        """
        subscriber = Subscriber(subscriber_zip_postal='00000')
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455550000', 
            carrier_id=3)
        mobile_phone.subscriber = subscriber
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='10', 
            smsfrom='8455550000', smsmsg = 'save', network = 'ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455550000')
        except SMSMessageSent.DoesNotExist:
            self.fail('We did not respond to a valid message received.')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        
    def test_save_subscriber_12550(self):
        """
        Here we get the word "save" from someone who is already a subscriber
        with a real zipcode.
        """
        subscriber = Subscriber(subscriber_zip_postal='12550')
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455550001', 
            carrier_id=3)
        mobile_phone.subscriber = subscriber
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='10', 
            smsfrom='8455550001', smsmsg='save', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455550001')
        except SMSMessageSent.DoesNotExist:
            self.fail('We did not respond to a valid message received.')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['double'])
        
    def test_unknown_carrier(self):
        """ Assert an sms from an unknown carrier raises an error. """
        subscriber = Subscriber(subscriber_zip_postal='00000')
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455551001', 
            carrier_id=3, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='106', 
            smsfrom='8455551001', smsmsg='stop', network='fake', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            SMSMessageSent.objects.get(smsto='8455551001')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            pass
        phone = MobilePhone.objects.get(mobile_phone_number='8455551001')
        # Phone not updated.
        self.assertEqual(phone.carrier_id, 3)
        
    def test_carrier_change(self):
        """ Assert for sms from a subscriber of a carrier that's not on record.
        """
        subscriber = Subscriber(subscriber_zip_postal='00000')
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455551001', 
            carrier_id=3, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='103', 
            smsfrom='8455551001', smsmsg='stop', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455551001')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455551001')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['opt_out'])
        phone = MobilePhone.objects.get(mobile_phone_number='8455551001')
        self.assertEqual(phone.carrier_id, 2)
        
    def test_stop_advertiser(self):
        """ Assert opt out for someone who has multiple sms subscriptions."""
        subscriber = Subscriber(subscriber_zip_postal='00000')
        subscriber.save()
        subscriber.sms_subscription.add(1, 2)
        mobile_phone = MobilePhone(mobile_phone_number='8455551002', 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='104', 
            smsfrom='8455551002', smsmsg='stop', network='ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455551002')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455551002')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['opt_out'])
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        
    def test_stop_not_subscriber(self):
        """ Assert that when someone who has never texted us sends "Stop", we
        sent the opt out confirmation
        """
        sms_message_received = SMSMessageReceived(smsid='105', 
            smsfrom='8455551003', smsmsg='Stop', network='CRICKETUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455551003')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455551003')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did not create a subscriber for valid message.")
        self.assertEqual(sms_message_sent.smsto, '8455551003')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['opt_out'])
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        try:
            sms_response = SMSResponse.objects.get(received__smsid=105)
        except SMSResponse.DoesNotExist:
            self.fail("We did not create an sms response for valid response.")
        except SMSResponse.MultipleObjectsReturned:
            self.fail("We created more than one sms response.")
        self.assertTrue(sms_response.is_opt_out)
        
    def test_word_coupon_sub_zip_12550(self):
        """ Asserts for the word 'coupon' from someone who is a subscriber with
        the zipcode 12550.
        """
        subscriber = Subscriber(subscriber_zip_postal='12550')
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553002', 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='702', 
            smsfrom='8455553002', smsmsg='coupon', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553002')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553002')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_email'])
      
    def test_word_help(self):
        """ Assert good response to request for 'help' from someone. """
        sms_message_received = SMSMessageReceived(smsid='703', 
            smsfrom='8455553003', smsmsg='help', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553003')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553003')
        self.assertEqual(sms_message_sent.smsmsg[:60], 
            "Problems w/10Coupons Alrts (4msg/mo)? Call 18005813380 or vi")
        
    def test_word_ad(self):
        """ Asserts for the word 'ad' from someone new. """
        sms_message_received = SMSMessageReceived(smsid='704', 
            smsfrom='8455553004', smsmsg='ad', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553004')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553004')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455553004')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(
            subscriber.sms_subscription.all()[0],
            SMSSubscription.objects.get(id=2)
            )
        
    def test_word_ad_consumer(self):
        """ Asserts for the word 'advertise' from someone who is a consumer. """
        consumer = Consumer()
        consumer.email = 'test-word_ad_consumer@example.com'
        consumer.username = consumer.email
        consumer.save()
        subscriber = Subscriber()
        subscriber.subscriber_zip_postal = '12550'
        subscriber.site_id = 2
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number ='8455553005', 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        consumer.subscriber = subscriber
        consumer.save()
        sms_message_received = SMSMessageReceived(smsid='705', 
            smsfrom='8455553005', smsmsg='advertise', network='ATTUS',
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553005')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553005')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['hv_success'])
        self.assertEqual(subscriber.sms_subscription.filter(id=2).count(), 1)
        
    def test_blank_smsmsg(self):
        """ Assert that when we receive a text that is a single space, ' ', we
        do not send a response, and do not create a subscriber.
        """
        sms_message_received = SMSMessageReceived(smsid='704', 
            smsfrom='8455553009', smsmsg=' ', network='VERIZONUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            SMSMessageSent.objects.get(smsto='8455553009')
            self.fail("We responded to an invalid message received.")
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            pass
        try:
            Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455553009')
            self.fail("We created a subscriber for invalid message.")
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            pass

    def test_smsid_received_twice(self):
        """ Assert that when an sms is received multiple times the response
        relationship is only created once. 
        """
        sms_message_received = SMSMessageReceived(smsid='706', 
            smsfrom='8455553010', smsmsg='yes', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        sms_message_received = SMSMessageReceived(smsid='706', 
            smsfrom='8455553010', smsmsg='yes', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        self.assertTrue(SMSMessageSent.objects.filter(
            smsto='8455553010').count(), 2)
        self.assertTrue(SMSResponse.objects.filter(received__smsid=706).count(),
            1)

    
class TestTasksZip(SMSGatewayTestCase):
    """ Tests for when we receive an SMS message that is a zip code. """
    fixtures = ['test_uszip_buffalo']
        
    def test_12550(self):
        """ Assert that when we receive the text the word '12550', a valid zip
        for site 2, from someone who is not a subscriber, that we:
        - create a subscriber on site 2 with this mobile phone.
        - send them a double opt in request.
        """
        sms_message_received = SMSMessageReceived(smsid = '706', 
            smsfrom='8455553006', smsmsg='12550', network='ATTUS',
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553006')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553006')
        self.assertEqual(sms_message_sent.smsmsg[15:65], self.good_sms['double'])
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455553006')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        self.assertEqual(subscriber.subscriber_zip_postal, '12550')
        self.assertEqual(subscriber.site_id, 2)
        
    def test_12550_no_subscription(self):
        """ Asserts for the word '12550' from someone who is a subscriber and a
        consumer, but who doesn't have an sms_subscription.
        """
        phone_number = '8455553007'
        consumer = Consumer()
        consumer.username = phone_number
        consumer.email = 'test-12550_no_sub@example.com'
        consumer.save()
        subscriber = Subscriber()
        subscriber.subscriber_zip_postal = '12550'
        subscriber.site_id = 2
        subscriber.save()
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        mobile_phone = MobilePhone()
        mobile_phone.mobile_phone_number = phone_number
        mobile_phone.carrier_id = 2
        mobile_phone.subscriber = subscriber
        mobile_phone.save()
        consumer.subscriber = subscriber
        consumer.save()
        sms_message_received = SMSMessageReceived()
        sms_message_received.smsid = '707'
        sms_message_received.smsfrom = phone_number
        sms_message_received.smsmsg = '12550'
        sms_message_received.network = 'ATTUS'
        sms_message_received.smsdate = '2000-01-01'
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto=phone_number)
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, phone_number)
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['hv_success'])
        self.assertEqual(subscriber.sms_subscription.count(), 1)
        self.assertEqual(subscriber.subscriber_zip_postal, '12550')
        self.assertEqual(subscriber.site_id, 2)
    
    def test_99999(self):
        """ Asserts for the word '99999' from someone. Not a valid zipcode. """
        sms_message_received = SMSMessageReceived()
        sms_message_received.smsid = '102'
        sms_message_received.smsfrom = '8455551002'
        sms_message_received.smsmsg = '99999'
        sms_message_received.network = 'ATTUS'
        sms_message_received.smsdate = '2000-01-01'
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455551002')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455551002')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['double'])
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455551002')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        self.assertEqual(subscriber.subscriber_zip_postal, '00000')
        self.assertEqual(subscriber.site_id, 1)
    
    def test_zipcode_14201(self):
        """ Assert for the word '14201' from someone. It is valid zipcode (for
        Buffalo) but doesn't belong to a test site.
        """
        sms_message_received = SMSMessageReceived()
        sms_message_received.smsid = '103'
        sms_message_received.smsfrom = '8455551003'
        sms_message_received.smsmsg = '14201'
        sms_message_received.network = 'ATTUS'
        sms_message_received.smsdate = '2000-01-01'
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455551003')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455551003')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['double'])
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455551003')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        self.assertEqual(subscriber.subscriber_zip_postal, '14201')
        self.assertEqual(subscriber.site_id, 1)
    
    def test_12550_sub(self):
        """ Asserts the word '12550' from someone who is a subscriber. """
        zip_postal = '12550'
        subscriber = Subscriber()
        subscriber.subscriber_zip_postal = zip_postal
        subscriber.save()
        subscriber = Subscriber.objects.all().order_by('-id')[0]
        sms_message_received = SMSMessageReceived()
        sms_message_received.smsid = '707'
        sms_message_received.smsfrom = '8455553007'
        sms_message_received.smsmsg = zip_postal
        sms_message_received.network = 'ATTUS'
        sms_message_received.smsdate = '2000-01-01'
        # Saving this fires the task:
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553007')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553007')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['double'])
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455553007')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        self.assertEqual(subscriber.subscriber_zip_postal, zip_postal)
        self.assertEqual(subscriber.site_id, 2)
    

class TestTasksYes(SMSGatewayTestCase):
    """ Tests for when we receive an SMS that is the word 'yes'. """
        
    def test_yes_subscriber(self):
        """ Assert that when we get the word 're:|yes' from someone who is a
        subscriber, the 're:|' is trimmed and we respond with the locally
        branded message.
        """
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553008', 
            carrier_id = 2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='708', 
            smsfrom='8455553008', smsmsg='re:|yes', network='ATTUS',
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553008')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553008')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['hv_consumer'])
        try:
            subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455553008'
                )
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did not create a subscriber.")
        self.assertEqual(subscriber.sms_subscription.count(), 1)
    
    def test_yes_not_subscriber(self):
        """ Here we get the word 'yes' from someone who is NOT a subscriber. """
        sms_message_received = SMSMessageReceived(smsid='608', 
            smsfrom='8455551005', smsmsg='yes', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455551005')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455551005')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        try:
            subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455551005'
                )
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did not create a subscriber.")
        self.assertEqual(subscriber.sms_subscription.count(), 0)


class TestTasksNo(SMSGatewayTestCase):
    """ Tests for when we receive an SMS that is the word 'no'. """

    def test_no_from_subscriber(self):
        """ Assert that we get the word 'no' from someone who is a subscriber we
        send the correct response, the mobile_phone is verified, and no
        sms_subscriptions survive.
        """
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553010',
            carrier_id = 2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='709',
            smsfrom='8455553010', smsmsg='no', network='ATTUS',
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553010')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553010')
        self.assertEqual(sms_message_sent.smsmsg[15:65], self.good_sms['no'])
        subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455553010'
                )
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        self.assertTrue(MobilePhone.objects.get(
            mobile_phone_number='8455553010').is_verified)

    def test_no_from_not_subscriber(self):
        """ Assert that when we get the word 'no' from someone who is NOT a
        subscriber, we respond with the request for zip sms, and the
        mobile_phone is verified anyway. """
        sms_message_received = SMSMessageReceived(smsid='710',
            smsfrom='8455553011', smsmsg='no', network='ATTUS',
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553011')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553011')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        try:
            subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455553011'
                )
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did not create a subscriber.")
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        self.assertTrue(MobilePhone.objects.get(
            mobile_phone_number='8455553011').is_verified)

    def test_subscriber_00000(self):
        """ Assert that we get the word 'no' from someone who is a subscriber
        with the zip code 00000 we send the 'request zip' response and the
        mobile_phone is verified.
        """
        subscriber = Subscriber(subscriber_zip_postal='00000', site_id=2)
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553012',
            carrier_id = 2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='711',
            smsfrom='8455553012', smsmsg='no', network='ATTUS',
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553012')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553012')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        self.assertTrue(MobilePhone.objects.get(
            mobile_phone_number='8455553012').is_verified)

    def test_subscriber_subscription(self):
        """ Assert that we get the word 'no' from someone who is a subscriber
        with an sms subscription and a good zip we send the 'opt out success'
        response and the mobile_phone is verified, and the subscription is
        deleted.
        """
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        subscriber.sms_subscription.add(1)
        mobile_phone = MobilePhone(mobile_phone_number='8455553013',
            carrier_id = 2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='712',
            smsfrom='8455553013', smsmsg='no', network='ATTUS',
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553013')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553013')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['opt_out'])
        subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455553013'
                )
        self.assertEqual(subscriber.sms_subscription.count(), 0)
        self.assertTrue(MobilePhone.objects.get(
            mobile_phone_number='8455553013').is_verified)