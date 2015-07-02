""" Advertiser Factory used to help create quick Advertiser instances for 
tests.
"""

from advertiser.models import Advertiser
from common.utils import random_string_generator


class AdvertiserFactory(object):
    """ Advertiser Factory Class """
    
    @staticmethod
    def _create():
        """ Create a single advertiser instance. """
        email = '%s@example.com' % random_string_generator(
            lower_alpha_only=True)
        consumer_zip_postal = random_string_generator(
            string_length=5, numeric_only=True)
        advertiser = Advertiser.objects.create(username=email,
           email=email,
           consumer_zip_postal=consumer_zip_postal, 
           site_id=2)
        advertiser.set_password('password')
        advertiser.save()
        return advertiser
    
    def create_advertiser(self):
        """ Create ONE basic advertiser instance. """
        advertiser = self._create()
        return advertiser
       
    def create_advertisers(self, create_count=1):
        """ Create 1 or more advertiser and return them in a list. """
        advertiser_list = []
        current_create_count = 0
        while(current_create_count < create_count):
            advertiser = self._create()
            current_create_count += 1
            advertiser_list.append(advertiser)
        return advertiser_list

ADVERTISER_FACTORY = AdvertiserFactory()
