""" Consumer Factory used to help create quick Consumer instances for tests. """

from consumer.models import Consumer
from common.utils import random_string_generator
from subscriber.factories.subscriber_factory import SUBSCRIBER_FACTORY


class ConsumerFactory(object):
    """ Consumer Factory Class """

    @staticmethod
    def _get_email():
        """ Create random email. """
        return '%s@example.com' % random_string_generator(
            lower_alpha_only=True)
    
    @staticmethod
    def _get_consumer_zip_postal():
        """ Create random zip postal. """
        return random_string_generator(string_length=5, numeric_only=True)
  
    @classmethod
    def _create(cls, **kwargs):
        """ Create a single consumer instance. """
        email = cls._get_email()
        consumer = Consumer.objects.create(username=email,
           email=email,
           consumer_zip_postal=cls._get_consumer_zip_postal(), 
           site_id=2)
        add_flyer_subscription = kwargs.get('subscription_list', True)
        if add_flyer_subscription:
            consumer.email_subscription.add(1)
        return consumer
    
    def create_consumer(self, **kwargs):
        """ Create ONE basic consumer instance. """
        consumer = self._create(**kwargs)
        return consumer
       
    def create_consumers(self, create_count=1, **kwargs):
        """ Create 1 or more consumers and return them in a list. """
        consumer_list = []
        current_create_count = 0
        while current_create_count < create_count:
            consumer = self._create(**kwargs)
            current_create_count += 1
            consumer_list.append(consumer)
        return consumer_list

    @staticmethod
    def qualify_consumer(consumer):
        """ Make this consumer fully contest eligible. """
        consumer.is_email_verified = True
        subscriber = SUBSCRIBER_FACTORY.create_subscriber()
        subscriber.subscriber_zip_postal = consumer.consumer_zip_postal
        subscriber.save()
        consumer.subscriber = subscriber
        consumer.save()
        consumer.email_subscription.add(1)

CONSUMER_FACTORY = ConsumerFactory()
