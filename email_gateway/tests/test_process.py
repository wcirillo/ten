""" Unit tests for process functions of email_gateway app. """

from django.test import TestCase

from consumer.models import Consumer
from email_gateway.process import flag_bouncing_email

class TestProcess(TestCase):
    """ Test case for process functions of email_gateway app. """
    
    fixtures = ['test_consumer']
    
    def test_flag_bouncing_email(self):
        """ 
        Assert consumers are not emailable after this function is called.
        """
        consumer1 = Consumer.objects.get(email='bounce-report3@example.com')
        self.assertTrue(consumer1.is_emailable)
        flag_bouncing_email(consumer1.email, 1)
        consumer2 = Consumer.objects.get(email='bounce-report3@example.com')
        self.assertTrue(not consumer2.is_emailable)