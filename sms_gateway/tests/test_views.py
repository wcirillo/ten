"""
Tests for sms_gateway app views.
"""
import datetime

from django.conf import settings
from django.test.client import RequestFactory

from geolocation.models import USZip
from subscriber.models import MobilePhone, Subscriber

from sms_gateway.models import SMSMessageReceived, SMSMessageSent, SMSReport
from sms_gateway.views import receive_sms, receive_report
from sms_gateway.tests.sms_gateway_test_case import SMSGatewayTestCase

class TestReceiveSMS(SMSGatewayTestCase):
    """ Test case for views of sms_gateway. """
    # Loading the sms_gateway itself will cause post_save signal to fire,
    # if there are any SMSMessagesReceived.
    fixtures = ['test_advertiser', 'test_coupon', 'test_subscriber', 
        'test_sms_gateway']
    
    def setUp(self):
        """
        Tests need eager queue. Tests needs access to the request factory.
        """
        super(TestReceiveSMS, self).setUp()
        settings.CELERY_ALWAYS_EAGER = True
        self.factory = RequestFactory()    
    
    def test_post_receive_sms(self):
        """ This view disallows requests POST method. """
        data = {'foo': 'bar'}
        request = self.factory.post('/sms-gateway/receive-sms/', data)
        response = receive_sms(request)
        self.assertEquals(response.status_code, 400)
    
    def test_get_receive_sms(self):
        """ Assert gateway requests is good and new phone number is stored.
        Some versions of this will also send a response.
        """
        request = self.factory.get('/sms-gateway/receive-sms/?user=foo&pass=bar&smsto=71010&smsfrom=8455551234&note=test&smsid=100&smsmsg=stop&bits=7&smsdate=2010-03-13+21%3A58%3A00&network=ATTUS')
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(response.content, 'OK')
        try:
            MobilePhone.objects.get(mobile_phone_number='8455551234')
        except MobilePhone.DoesNotExist:
            self.fail("We didn't save a new phone.")
        except MobilePhone.MultipleObjectsReturned:
            self.fail("We saved duplicate new phones.")

    def test_missing_params(self):
        """ Assert receiving an sms with required params missing fails. """
        request = self.factory.get('/sms-gateway/receive-sms/?smsto=71010&smsfrom=8455550000')
        response = receive_sms(request)
        self.assertEquals(response.status_code, 400)
        
    def test_missing_bits(self):
        """ Assert a received message with required param bits missing fails. """
        request = self.factory.get('/sms-gateway/receive-sms/?smsto=71010&smsfrom=8455550001&smsid=102&smsmsg=12550&smsdate=2010-10-10+21%3A58%3A00&network=ATTUS')
        response = receive_sms(request)
        self.assertEquals(response.status_code, 400)
        
    def test_blank_smsmsg(self):
        """ Assert when a text is received with an blank body, it is expanded to
        a single space. 
        """
        phone_number = '8455550002'
        request = self.factory.get(
            '/sms-gateway/receive-sms/?smsto=71010&smsfrom=%s&smsid=103&smsmsg=&smsdate=%s&network=ATTUS&bits=7' % 
            (phone_number, '2010-10-10+21%3A58'))
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)
        try:
            sms_message_received = SMSMessageReceived.objects.get(
                    smsfrom=phone_number
                )
        except SMSMessageReceived.MultipleObjectsReturned:
            self.fail("We saved more than one message received.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not store a valid message received.")
        self.assertEquals(sms_message_received.smsmsg, ' ')
        
    def test_incoming_sms_messages_view(self):
        """ Assert normal functional flow of subscriber via radio. """
        # Test json loaded a zip code to use
        us_zip = USZip.objects.get(code='12550')
        self.assertEquals(us_zip.code, '12550')
        received_count = 0
        sent_count = 0
        # Create subscriber. Mimics someone responding to radio commercial.
        request = self.factory.get('/sms-gateway/receive-sms/?smsto=71010&smsfrom=8455550003&smsid=300&smsmsg=12550&smsdate=2010-10-10+21%3A58%3A00&network=ATTUS&bits=7')
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)
        # Check to see if subscriber was created.
        try:
            mobile_phone = MobilePhone.objects.get(
                    mobile_phone_number='8455550003'
                )
        except MobilePhone.DoesNotExist:
            self.fail('Mobile phone was not created.')
        try:
            subscriber = Subscriber.objects.get(mobile_phones=mobile_phone)
        except Subscriber.DoesNotExist:
            self.fail('Subscriber was not created.')
        received_count += 1
        sent_count += 1
        # Check to see if message was received
        self.assertEquals(
            SMSMessageReceived.objects.filter(
                    smsfrom=mobile_phone.mobile_phone_number
                ).count(), received_count)
        # Check to see if response was sent
        self.assertEquals(
            SMSMessageSent.objects.filter(
                    smsto=mobile_phone.mobile_phone_number
                ).count(), sent_count)
        # Check not double opted in yet.
        self.assertEquals(subscriber.sms_subscription.count(), 0)
        # Do double opt in.
        request = self.factory.get('/sms-gateway/receive-sms/?smsto=71010&smsfrom=8455550003&smsid=301&smsmsg=YES&smsdate=2010-10-10+21%3A58%3A00&network=ATTUS&bits=7')
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)
        # Check double opted in.
        self.assertEquals(subscriber.sms_subscription.count(), 1)
        received_count += 1
        sent_count += 1
        self.assertEquals(
            SMSMessageReceived.objects.filter(
                    smsfrom=mobile_phone.mobile_phone_number
                ).count(), received_count)
        self.assertEquals(
            SMSMessageSent.objects.filter(
                    smsto=mobile_phone.mobile_phone_number
                ).count(), sent_count)
        # Create consumer for this subscriber.
        request = self.factory.get('/sms-gateway/receive-sms/?smsto=71010&smsfrom=8455550003&smsid=302&smsmsg=steve-unittester@example.com&smsdate=2010-10-10+21%3A58%3A00&network=ATTUS&bits=7')
        response = receive_sms(request)
        received_count += 1
        sent_count += 2 # We send two test messages in this case.
        self.assertEquals(
            SMSMessageReceived.objects.filter(
                    smsfrom=mobile_phone.mobile_phone_number
                ).count(), received_count)
        self.assertEquals(
            SMSMessageSent.objects.filter(
                    smsto=mobile_phone.mobile_phone_number
                ).count(), sent_count)
        self.assertEquals(response.status_code, 200)
        # Do opt out.
        request = self.factory.get('/sms-gateway/receive-sms/?smsto=71010&smsfrom=8455550003&smsid=303&smsmsg=STOP&smsdate=2010-10-10+21%3A58%3A00&network=ATTUS&bits=7')
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(subscriber.sms_subscription.count(), 0)
        received_count += 1
        sent_count += 1
        self.assertEquals(
            SMSMessageReceived.objects.filter(
                    smsfrom=mobile_phone.mobile_phone_number
                ).count(), received_count)
        self.assertEquals(
            SMSMessageSent.objects.filter(
                    smsto=mobile_phone.mobile_phone_number
                ).count(), sent_count)

    def test_unknown_carrier(self):
        """ Assert when a text is received with an unknown carrier, we save the
        message received.
        """
        phone_number = '8455550004'
        request = self.factory.get(
            '/sms-gateway/receive-sms/?smsto=71010&smsfrom=%s&smsid=104&smsmsg=12550&smsdate=%s&network=FOO&bits=7' %
            (phone_number, '2010-10-10+21%3A58'))
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)
        try:
            sms_message_received = SMSMessageReceived.objects.get(
                    smsfrom=phone_number
                )
        except SMSMessageReceived.MultipleObjectsReturned:
            self.fail("We saved more than one message received.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not store a valid message received.")
        self.assertEquals(sms_message_received.smsmsg, '12550')
        self.assertEquals(sms_message_received.network, 'FOO')

    def test_cingular(self):
        """  Assert an sms from carrier CINGULARUS, we translate it to ATTUS.
        """
        phone_number = '8455550005'
        request = self.factory.get(
            '/sms-gateway/receive-sms/?smsto=71010&smsfrom=%s&smsid=105&smsmsg=12550&smsdate=%s&network=CINGULARUS&bits=7' %
            (phone_number, '2010-10-10+21%3A58'))
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)
        try:
            sms_message_received = SMSMessageReceived.objects.get(
                    smsfrom=phone_number
                )
        except SMSMessageReceived.MultipleObjectsReturned:
            self.fail("We saved more than one message received.")
        except SMSMessageSent.DoesNotExist:
            self.fail("We did not store a valid message received.")
        self.assertEquals(sms_message_received.smsmsg, '12550')
        self.assertEquals(sms_message_received.network, 'ATTUS')

    def test_smsmsg_too_long(self):
        """ Assert when a text is received with a message that is too long, we
        return a 400 error.
        """
        phone_number = '8455550006'
        request = self.factory.get(
            '/sms-gateway/receive-sms/?smsto=71010&smsfrom=%s&smsid=106&smsmsg=%s&smsdate=%s&network=ATTUS&bits=7' %
            (phone_number, 'toolong' * 100, '2010-10-10+21%3A58'))
        response = receive_sms(request)
        self.assertEquals(response.status_code, 400)

    def test_hex_smsucs2(self):
        """ Assert a hexidecimal value is converted and stored. """
        phone_number = '8455550006'
        request = self.factory.get(
            '/sms-gateway/receive-sms/?smsto=71010&smsfrom=%s&smsid=107&smsmsg=%s&smsdate=%s&network=ATTUS&bits=7&smsucs2=%s' %
            (phone_number, 'like my hex?', '2010-10-10+21%3A58',
            '005900650073000A00B00056004900490049002D0056002D004D004D0058004900B0'))
        response = receive_sms(request)
        self.assertEquals(response.status_code, 200)


class TestReceiveReport(SMSGatewayTestCase):
    """ Test case for receive_report view. """
    fixtures = ['test_subscriber', 'test_sms_gateway', ]

    def setUp(self):
        """
        Tests need eager queue. Tests needs access to the request factory.
        """
        super(TestReceiveReport, self).setUp()
        settings.CELERY_ALWAYS_EAGER = True
        self.factory = RequestFactory()

    def test_get_receive_report_good(self):
        """ Assert a received report for a message id we know is saved. """
        sms_message_sent = SMSMessageSent.objects.get(id=2)
        phone_number = sms_message_sent.smsto
        path = '/sms-gateway/receive-report/?smsfrom=%s' % phone_number, \
            '&smsmsg=REPORT+%s' % sms_message_sent.smsid, \
            '+DELIVERED&smsto=913&shortcode=913&', \
            'smsid=%s' % sms_message_sent.smsid, \
            '&smsdate=2010-04-30+21%3A58%3A00&reason=1359151616'
        path = ''.join(path)
        request = self.factory.get(path)
        response = receive_report(request)
        self.assertEquals(response.status_code, 200)
        # Test report was saved.
        try:
            SMSReport.objects.get(smsfrom=phone_number)
        except SMSReport.MultipleObjectsReturned:
            self.fail("We saved multiple reports.")
        except SMSReport.DoesNotExist:
            self.fail("We did not save report.")

    def test_get_receive_report(self):
        """ Assert a received report for a message id we don't know fails. """
        request = self.factory.get('/sms-gateway/receive-report/?smsfrom=8455551234&smsmsg=REPORT+1000+DELIVERED&smsto=913&shortcode=913&smsid=101&smsdate=2010-04-30+21%3A58%3A00&reason=1359151616')
        response = receive_report(request)
        self.assertEquals(response.status_code, 400)
        # Test no report was saved.
        try:
            SMSReport.objects.get(smsid=201)
            self.fail("We saved a report for a missing smsid.")
        except SMSReport.MultipleObjectsReturned:
            self.fail("We saved more than one report.")
        except SMSReport.DoesNotExist:
            pass
    
    def test_post_receive_report(self):
        """ Assert report received disallows requests POST method. """
        request = self.factory.post('/sms-gateway/receive-report/?smsfrom=8455551234&smsmsg=REPORT+1000+DELIVERED&smsto=913&shortcode=913&smsid=401&smsdate=2010-04-30+21%3A58%3A00&reason=1359151616')
        response = receive_report(request)
        self.assertEquals(response.status_code, 400)

    def test_bad_date(self):
        """ Assert a bad report datetime string degrades to a date string. """
        sms_message_sent = SMSMessageSent.objects.get(id=2)
        phone_number = sms_message_sent.smsto
        path = '/sms-gateway/receive-report/?smsfrom=%s' % phone_number, \
            '&smsto=913&shortcode=913', \
            '&smsid=%s' % sms_message_sent.smsid, \
            '&smsmsg=REPORT+%s+DELIVERED' % sms_message_sent.smsid, \
            '&smsdate=2011-08-31+11%3A61%3A25&reason=1359151616'
        path = ''.join(path)
        request = self.factory.get(path)
        response = receive_report(request)
        self.assertEquals(response.status_code, 200)
        sms_report = SMSReport.objects.latest('id')
        self.assertEqual(sms_report.smsdate, datetime.datetime(2011, 8, 31))
