""" Test common contest services. """

from django.test import TestCase

from common.contest import select_eligible_consumers
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from subscriber.models import Subscriber

class TestContestEligibility(TestCase):
    """ Test case for eligibility of contest candidacy."""
    fixtures = ['test_subscriber', 'test_media_partner']
    
    def prep_test(self, only_subscriber=False):
        """ Get consumer and subscriber for tests. """
        self.subscriber = Subscriber.objects.get(id=6)
        if not only_subscriber:
            self.consumer = CONSUMER_FACTORY.create_consumer()
            CONSUMER_FACTORY.qualify_consumer(self.consumer)
        
    def test_eligible_consumer(self):
        """ Assert eligible consumer is deemed eligible. """
        self.prep_test()
        result = select_eligible_consumers()
        self.assertEqual(result.filter(id=self.consumer.id).count(), 1)

    def test_staff_member(self):
        """ Assert staff is not eligible. """
        self.prep_test()
        self.consumer.is_staff = True
        self.consumer.save()
        result = select_eligible_consumers()
        self.assertEqual(result.filter(id=self.consumer.id).count(), 0)

    def test_media_partner(self):
        """ Assert media partner is not eligible. """
        consumer = Consumer.objects.get(id=406)
        self.prep_test(only_subscriber=True)
        consumer.subscriber = self.subscriber
        consumer.save()
        result = select_eligible_consumers()
        self.assertEqual(result.filter(id=consumer.id).count(), 0)
