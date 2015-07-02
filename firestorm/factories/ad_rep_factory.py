""" A factory for creating ad_reps for easy testing. """
from random import random

from common.utils import random_string_generator
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from firestorm.models import AdRep, AdRepConsumer


class AdRepFactory(object):
    """ Factory class for the AdRep model. """

    @staticmethod
    def _create(**kwargs):
        """ Create an ad_rep instance. """
        random_string = random_string_generator(lower_alpha_only=True)
        email = '%s@example.com' % random_string.lower()
        firestorm_id = int(random() * 100000)
        try:
            ad_rep = AdRep.objects.get(firestorm_id=firestorm_id)
            firestorm_id = AdRep.objects.all().order_by(
                '-id')[0].firestorm_id + 1
        except AdRep.DoesNotExist:
            pass
        ad_rep = AdRep.objects.create(username=email,
            email=email,
            first_name=random_string.title(),
            last_name=random_string_generator(lower_alpha_only=True).title(),
            site_id=2,
            us_zip_id=23181,
            firestorm_id=firestorm_id,
            rank='ADREP',
            url=kwargs.get('url', random_string),
            company=random_string_generator(),
            home_phone_number=random_string_generator(numeric_only=True),
            primary_phone_number=random_string_generator(numeric_only=True),
            )
        ad_rep.set_password('password')
        ad_rep.save()
        return ad_rep

    def create_ad_rep(self, **kwargs):
        """ Return an ad_rep instance. """
        return self._create(**kwargs)

    def create_ad_reps(self, create_count=1):
        """ Return a list of ad_reps. """
        ad_rep_list = []
        while len(ad_rep_list) < create_count:
            ad_rep = self._create()
            ad_rep_list.append(ad_rep)
        return ad_rep_list

    def create_generations(self, create_count=1):
        """ Return a list of ad_reps, each of which (except the last) is a child
        of the next.
        """
        ad_rep_list = self.create_ad_reps(create_count)
        for index, ad_rep in enumerate(ad_rep_list[:create_count - 1]):
            ad_rep.parent_ad_rep = ad_rep_list[index + 1]
            ad_rep.save()
        return ad_rep_list

    @staticmethod
    def qualify_ad_rep(ad_rep):
        """ Set the condition such that ad_rep.is_qualified() returns True. """
        consumers = CONSUMER_FACTORY.create_consumers(create_count=10)
        for consumer in consumers:
            CONSUMER_FACTORY.qualify_consumer(consumer)
            AdRepConsumer.objects.create(ad_rep=ad_rep, consumer=consumer)

AD_REP_FACTORY = AdRepFactory()
