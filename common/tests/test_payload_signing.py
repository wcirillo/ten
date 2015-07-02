""" Tests for payload encryption service. """
from django.test.client import RequestFactory

from common.service.payload_signing import PAYLOAD_SIGNING
from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer


class TestPayloadSigning(EnhancedTestCase):
    """ Tests case for generating and parsing payloads. """
    
    def build_request(self, email):
        """ Build request for test. """
        factory = RequestFactory()
        self.request = factory.get('/')
        self.request.session = self.session
        self.payload = PAYLOAD_SIGNING.create_payload(email=email)

    def test_payload_email(self):
        """ Assert payload with email is encrypted and parsed successfully. """
        email = 'name1@testdomain.com'
        payload = PAYLOAD_SIGNING.create_payload(email=email)
        payload_dict = PAYLOAD_SIGNING.parse_payload(payload) 
        self.assertEqual(payload_dict['email'], email)
    
    def test_payload_extra_keys(self):
        """ Assert payload with email and additional keys encrypts and parses
        correctly.
        """
        email = 'name2@testdomain.com'
        test1 = 'mountain'
        subscription_list = [1]
        payload = PAYLOAD_SIGNING.create_payload(email=email, test1=test1,
            subscription_list=subscription_list)
        payload_dict = PAYLOAD_SIGNING.parse_payload(payload) 
        self.assertEqual(payload_dict['email'], email)
        self.assertEqual(payload_dict['test1'], test1)
        self.assertEqual(payload_dict['subscription_list'], subscription_list)
    
    def test_parse_payload(self):
        """ Assert existing payload parses. """
        payload = "%s%s%s" % ('eyJ0ZXN0MSI6Im1vdW50YWluIiwic3Vic2',
            'NyaXB0aW9uX2xpc3QiOlsxXSwiZW1haWwiOiJuYW1lMkB',
            '0ZXN0ZG9tYWluLmNvbSJ9:1RZ0IN:EUurnc9capXl0deg-LLuhFRW2fM')
        payload_dict = PAYLOAD_SIGNING.parse_payload(payload)
        self.assertEqual(payload_dict['email'], 'name2@testdomain.com')
        self.assertEqual(payload_dict['test1'], 'mountain')
        self.assertEqual(payload_dict['subscription_list'], [1])
        
    def test_verify_payload_w_consumer(self):
        """ Assert payload is read, and consumer is verified, and added to
        session.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assertEqual(consumer.is_email_verified, False)
        self.build_request(consumer.email)
        PAYLOAD_SIGNING.handle_payload(self.request, self.payload)
        consumer = Consumer.objects.get(email=consumer.email)
        self.assertTrue(consumer.is_email_verified)
        self.assertEqual(self.request.session['consumer']['consumer_id'],
            consumer.id)
        
    def test_verify_payload_no_match(self):
        """ Assert payload is read, and returns gracefully when email not 
        found.
        """
        email = 'nosuchconsumer1@example.com'
        self.build_request('nosuchconsumer1@example.com')
        value_dict = \
            PAYLOAD_SIGNING.handle_payload(self.request, self.payload)
        with self.assertRaises(Consumer.DoesNotExist):
            consumer = Consumer.objects.get(email=email)
            self.assertFalse(consumer)
        self.assertEqual(self.request.session.get('consumer', None), None)
        self.assertEqual(value_dict['email'], email)
        
    def test_verify_payload_opting(self):
        """ Assert that payload built with valid consumer email and 
        opting flag True, adds subscription.
        """
        consumer = CONSUMER_FACTORY.create_consumer(subscription_list=False)
        self.assertEqual(consumer.email_subscription.count(), 0)
        self.build_request(consumer.email)
        PAYLOAD_SIGNING.handle_payload(self.request, self.payload,
            opting=True)
        self.assertEqual(consumer.email_subscription.count(), 1)
