"""
Tests of sms_gateway tasks specific to receiving text messages that are an
email address, or the word 'email'.
"""

from django.conf import settings

from consumer.models import Consumer
from sms_gateway.models import SMSMessageReceived, SMSMessageSent
from sms_gateway.tests.sms_gateway_test_case import SMSGatewayTestCase
from subscriber.models import Subscriber, MobilePhone

settings.EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'
settings.CELERY_ALWAYS_EAGER = True

class TestTasksWordEmail(SMSGatewayTestCase):
    """ Tests for receiving an sms that is the word 'email'. It happens! """
    # Loading the sms_gateway itself will cause post_save signal to fire,
    # if there are any SMSMessagesReceived in fixtures.
    
    def test_word_email_no_subscriber(self):
        """Assert for the word 'email' from someone who is not a subscriber:
        we create a subscriber and respond with a request for zipcode.
        """
        sms_message_received = SMSMessageReceived(smsid='700', 
            smsfrom='8455553000', smsmsg='email', network='ATTUS',
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        try:
            Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455553000')
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553000')
        except SMSMessageSent.DoesNotExist:
            self.fail('We did not respond to a valid message received.')
        self.assertEqual(sms_message_sent.smsto, '8455553000')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        
    def test_word_email_from_sub(self):
        """ Assert for the word 'email' from  a subscriber with zip '00000':
        we send a response requesting a zip.
        """
        subscriber = Subscriber(subscriber_zip_postal='00000')
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553001', 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='701', 
            smsfrom='8455553001', smsmsg='email', network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        try:
            sms_message_sent = SMSMessageSent.objects.get(smsto='8455553001')
        except SMSMessageSent.MultipleObjectsReturned:
            self.fail("We sent more than one response.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not respond to a valid message received.")
        self.assertEqual(sms_message_sent.smsto, '8455553001')
        self.assertEqual(sms_message_sent.smsmsg[15:65],
            self.good_sms['reply_zip'])
        
class TestTasksEmailAddress(SMSGatewayTestCase):
    """ Tests for receiving an sms that is an email address. """
    fixtures = ['test_uszip_buffalo', 'test_advertiser', 
        'test_coupon', 'test_subscriber', 'test_sms_gateway']
      
    def test_email_address_new(self):
        """ Assert for a new email address from a new phone: subscriber is
        created with a zipcode 00000, a phone is created, and an sms response
        requesting zip is sent.
        """
        sms_message_received = SMSMessageReceived(smsid='719', 
            smsfrom='8455553019', smsmsg='test_email_address_new@example.com',
            network='ATTUS', smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(
            smsto='8455553019').order_by('id')
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['reply_zip'])
        try:
            subscriber = Subscriber.objects.get(
                mobile_phones__mobile_phone_number='8455553019')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(subscriber.subscriber_zip_postal, '00000')
        self.assertEqual(subscriber.site.id, 1)
        self.assertEqual(subscriber.sms_subscription.count(), 0)
    
    def test_email_address_sub(self):
        """ Assert for an email address from subscriber w/o sms subscription.
        """
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553009',
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='709', 
            smsfrom='8455553009', smsmsg='test-email_address_sub@example.com',
            network='ATTUS', smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(
            smsto='8455553009').order_by('id')
        self.assertEqual(sms_messages_sent.count(), 2)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['hv_email'])
        self.assertEqual(sms_messages_sent[1].smsmsg[15:65],
            self.good_sms['double'])
        try:
            subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455553009')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        try:
            consumer = Consumer.objects.get(
                email='test-email_address_sub@example.com')
        except Consumer.MultipleObjectsReturned:
            self.fail("We created more than one consumer.")
        except Consumer.DoesNotExist:
            self.fail("We did create not a consumer.")
        self.assertEqual(consumer.subscriber, subscriber)
        self.assertEqual(subscriber.sms_subscription.count(), 0)
    
    def test_email_address_con(self):
        """ Assert for an email address from a subscriber and we have a consumer
        by this email, but the two are not related.
        """
        email = 'test-email_address_con@example.com'
        consumer = Consumer(username=email, email=email)
        consumer.save()
        subscriber = Subscriber(subscriber_zip_postal = '12550', site_id=2)
        subscriber.save()
        subscriber = Subscriber.objects.latest('id')
        mobile_phone = MobilePhone(mobile_phone_number='8455553010', 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='710', 
            smsfrom='8455553010', smsmsg=email, network='ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto='8455553010')
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['double'])
        try:
            consumer = Consumer.objects.get(email=email)
        except Consumer.DoesNotExist:
            self.fail("We did create not a consumer.")
        except Consumer.MultipleObjectsReturned:
            self.fail("We created more than one consumer.")
        self.assertEqual(consumer.subscriber, subscriber)
        print('sms_subscription.count(): %s' % 
            subscriber.sms_subscription.count())
        self.assertEqual(subscriber.sms_subscription.count(), 0)
    
    def test_sub_new_email_address(self):
        """ Assert a subscriber who is a consumer sends us a text containing a
        new email address, we update the consumer and respond.
        """
        email = 'test-sub_new_email_address@example.com'
        consumer = Consumer(username='8455553018', email=email, site_id=2)
        consumer.save()
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        subscriber.sms_subscription.add(1)
        consumer.subscriber = subscriber
        consumer.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553018', 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='711',  
            smsfrom='8455553018', network='ATTUS', smsdate='2000-01-01',
            smsmsg='test-sub_new_email_different@example.com')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto='8455553018')
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['hv_email'])
        self.assertEqual(sms_messages_sent[1].smsmsg[15:65],
            self.good_sms['hv_success'])
        # Get fresh object:
        consumer = Consumer.objects.get(id=consumer.id)
        self.assertEqual(consumer.email, 
            'test-sub_new_email_different@example.com') 
        
    def test_email_address_con_sub(self):
        """ Assert an email address from someone who is a subscriber, and we
        have a consumer by this email, and they are related, and subscribed to
        sms.
        """
        email = 'test-address_con_sub@example.com'
        consumer = Consumer(username='8455553011', email=email)
        consumer.save()
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        subscriber = Subscriber.objects.latest('id')
        subscriber.sms_subscription.add(1)
        consumer.subscriber = subscriber
        consumer.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553011', 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='711', 
            smsfrom='8455553011', smsmsg=email, network='ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto='8455553011')
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['success'])
        
    def test_email_con_sub_diff(self):
        """ Assert an email address from someone who is a subscriber, and we
        have a consumer by this email whom we don't have a subscriber for.
        """
        phone_number = '8455553012'
        email = 'test-con_sub_diff@example.com'
        # The pre-existing consumer:
        consumer = Consumer(username=phone_number, email=email)
        consumer.save()
        # The guy whose phone sends this text:
        diff_consumer = Consumer(username=phone_number * 2, 
            email="%s%s" % (phone_number, email))
        diff_consumer.save()
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        subscriber.sms_subscription.add(1)
        diff_consumer.subscriber = subscriber
        diff_consumer.save()
        mobile_phone = MobilePhone(mobile_phone_number=phone_number, 
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='712', 
            smsfrom=phone_number, smsmsg=email, network='ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto=phone_number)
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['check'])
        # Test we haven't changed relationships
        consumer = Consumer.objects.get(email=email)
        self.assertFalse(consumer.subscriber)
        diff_consumer = Consumer.objects.get(
            email="%s%s" % (phone_number, email))
        self.assertEqual(diff_consumer.subscriber, subscriber)
        
    def test_email_consumers_mismatch(self):
        """ Assert for most complex mismatch. Message from a subscriber who is a
        consumer. Email address in the message is a consumer who has a
        subscriber. But the two do not match!
        """
        # Setup complete consumer, subscriber, mobile_phone for Guy A.
        phone_number = '8455553013'
        email = 'test-consumers_mismatch@example.com'
        consumer = Consumer(username=phone_number, email=email)
        consumer.save()
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        subscriber.sms_subscription.add(1)
        consumer.subscriber = subscriber
        consumer.save()
        mobile_phone = MobilePhone(mobile_phone_number=phone_number,
            carrier_id=2, subscriber=subscriber)
        mobile_phone.save()
        subscriber.mobile_phone = mobile_phone
        subscriber.save()
        # Setup complete consumer, subscriber, mobile_phone for Guy B.
        diff_phone_number = '9145550000'
        diff_consumer = Consumer(username=diff_phone_number, 
            email=diff_phone_number)
        diff_consumer.save()
        diff_subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        diff_subscriber.save()
        diff_subscriber = Subscriber.objects.all().order_by('-id')[0]
        diff_subscriber.sms_subscription.add(1)
        diff_consumer.subscriber = diff_subscriber
        diff_consumer.save()
        diff_mobile_phone = MobilePhone(mobile_phone_number=diff_phone_number, 
            carrier_id=2, subscriber=diff_subscriber)
        diff_mobile_phone.save()
        diff_subscriber.mobile_phone = diff_mobile_phone
        diff_subscriber.save()
        sms_message_received = SMSMessageReceived(smsid='713', 
            smsfrom=diff_phone_number, smsmsg=email, network='ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(
            smsto=diff_phone_number)
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['check'])
        # Test we haven't changed relationships
        consumer = Consumer.objects.get(email=email)
        self.assertEqual(consumer.subscriber, subscriber)
        diff_consumer = Consumer.objects.get(email=diff_phone_number)
        self.assertEqual(diff_consumer.subscriber, diff_subscriber)
        
    def test_email_subscriber_sms(self):
        """ Assert for an email from someone a subscriber and a consumer with an
        sms subscription.
        """
        email = 'test-subscriber_sms@example.com'
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        subscriber.sms_subscription.add(1)
        consumer = Consumer(username=email, email=email, subscriber=subscriber)
        consumer.save()
        mobile_phone = MobilePhone(mobile_phone_number='8455553014', 
            carrier_id=2, subscriber = subscriber)
        mobile_phone.save()
        sms_message_received = SMSMessageReceived(smsid='714', 
            smsfrom='8455553014', smsmsg=email, network = 'ATTUS', 
            smsdate= '2000-01-01')
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto='8455553014')
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['success'])
        
    def test_email_consumer_only(self):
        """ Assert for an email address from someone who isn't a subscriber, but
        is already a consumer.
        """
        email = 'test-email_consumer_only@example.com'
        consumer = Consumer(username=email, email=email)
        consumer.save()
        sms_message_received = SMSMessageReceived(smsid='715', 
            smsfrom='8455553015', smsmsg=email, network='ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto='8455553015')
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['double'])
        try:
            subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455553015')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        try:
            consumer = Consumer.objects.get(subscriber=subscriber)
        except Consumer.MultipleObjectsReturned:
            self.fail("We created more than one consumer.")
        except Consumer.DoesNotExist:
            self.fail("We did not relate the consumer to a subscriber.")
        self.assertEqual(Consumer.objects.get(email=email), consumer)
        
    def test_email_consumer_sub(self):
        """ Assert for an email from a phone we don't know, but the email is for
        a consumer with a different phone we do know.
        """
        email = 'test-email_consumer_sub@example.com'
        subscriber = Subscriber(subscriber_zip_postal='12550', site_id=2)
        subscriber.save()
        diff_mobile_phone = MobilePhone(mobile_phone_number='9145553016',
            carrier_id=2, subscriber=subscriber)
        diff_mobile_phone.save()
        consumer = Consumer(username=email, email=email, subscriber=subscriber,
            consumer_zip_postal='12550', site_id=2)
        consumer.save()
        sms_message_received = SMSMessageReceived(smsid='716', 
            smsfrom='8455553016', smsmsg=email, network='ATTUS', 
            smsdate='2000-01-01')
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto='8455553016')
        self.assertEqual(sms_messages_sent.count(), 1)
        self.assertEqual(sms_messages_sent[0].smsmsg[15:65],
            self.good_sms['hv_email'])
        try:
            new_subscriber = Subscriber.objects.get(
                    mobile_phones__mobile_phone_number='8455553016')
        except Subscriber.MultipleObjectsReturned:
            self.fail("We created more than one subscriber.")
        except Subscriber.DoesNotExist:
            self.fail("We did create not a subscriber.")
        self.assertEqual(new_subscriber.subscriber_zip_postal, '12550')
        self.assertEqual(new_subscriber.site_id, 2)
        try:
            Consumer.objects.get(subscriber=subscriber)
        except Consumer.MultipleObjectsReturned:
            self.fail("We created another consumer.")
        except Consumer.DoesNotExist:
            self.fail("We deleted a consumer subscriber relationship.")
        
    def test_email_address_malformed(self):
        """ Assert a malformed email address is ignored. """
        email = 'test-email@aol'
        sms_message_received = SMSMessageReceived(smsid='717', 
            smsfrom='8455553017', smsmsg=email, network='ATTUS', 
            smsdate='2000-01-01')
        # Saving this fires the task:
        sms_message_received.save()
        sms_messages_sent = SMSMessageSent.objects.filter(smsto='8455553017')
        self.assertEqual(sms_messages_sent.count(), 0)
