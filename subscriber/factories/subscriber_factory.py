"""
Subscriber factory used to help create quick Subscriber instances for tests.
"""
from common.utils import random_string_generator
from subscriber.models import MobilePhone, Subscriber

def _generate_phone_number():
    """ A generator factory for unique phone numbers. """
    phone_number = 1112220000
    while True:
        phone_number += 1
        yield str(phone_number)


class SubscriberFactory(object):
    """ A factory for subscribers. """

    _get_phone_number = _generate_phone_number()

    @staticmethod
    def _get_subscriber_zip_postal():
        """ Create random zip postal. """
        return random_string_generator(string_length=5, numeric_only=True)

    def _create(self, **kwargs):
        """ Create a subscriber. """
        subscriber = Subscriber.objects.create(
            subscriber_zip_postal=self._get_subscriber_zip_postal())
        MobilePhone.objects.create(
            subscriber=subscriber,
            is_verified=True,
            mobile_phone_number=next(self._get_phone_number),
            carrier_id=kwargs.get('carrier_id', 2))
        return subscriber
    
    def create_subscriber(self, **kwargs):
        """ Create ONE basic subscriber instance. """
        subscriber = self._create(**kwargs)
        return subscriber
       
    def create_subscribers(self, create_count=1, **kwargs):
        """ Create 1 or more subscribers and return them in a list. """
        subscriber_list = []
        current_create_count = 0
        while current_create_count < create_count:
            subscriber = self._create(**kwargs)
            current_create_count += 1
            subscriber_list.append(subscriber)
        return subscriber_list

SUBSCRIBER_FACTORY = SubscriberFactory()
