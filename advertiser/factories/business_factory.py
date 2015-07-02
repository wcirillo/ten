""" Business Factory used to help create quick Business instances for tests. """

from advertiser.models import Business
from advertiser.factories.advertiser_factory import ADVERTISER_FACTORY
from advertiser.factories.location_factory import BUSINESS_LOCATION_FACTORY
from common.utils import random_string_generator


class BusinessFactory(object):
    """ Business Factory Class """
    
    @staticmethod
    def _create(advertiser):
        """ Create a single business instance. """
        business = Business.objects.create(advertiser_id=advertiser.id, 
            business_name=random_string_generator(), 
            short_business_name=random_string_generator(),
            slogan=random_string_generator())
        return business
    
    def create_business(self, advertiser=None, **kwargs):
        """ Create a ONE basic business instance with an 
        advertiser association. """
        create_location = kwargs.get('create_location', True)
        if not advertiser:
            advertiser = ADVERTISER_FACTORY.create_advertiser()
        business = self._create(advertiser=advertiser)
        if create_location:
            BUSINESS_LOCATION_FACTORY.create_business_location(business,
                **kwargs)
        return business
        
    def create_businesses(self, advertiser=None, create_advertiser=False,
            create_count=1, create_location=True):
        """ This method will do 1 of 3 things.
        
        default.) advertiser == None
            create_advertiser == False 
            Create 1 or more businesses and associate them with 
            different advertisers. 
            Ex: business -> advertiser
                business1 -> advertiser1
                business2 -> advertiser2
                business3 -> advertiser3 

        2.) create_advertiser == True
            Create an advertiser.
            Then create businesses for that advertiser.
             Ex: business -> advertiser 
                business1 -> advertiser
                business2 -> advertiser
                
        
        3.) advertiser != None
            create_advertiser == False
            If an advertiser is passed in use that advertiser.
            Create 1 or more businesses and associate them with the 
            same advertiser. 
            Ex: business -> advertiser 
                business1 -> advertiser
                business2 -> advertiser       
        """
        business_list = []
        current_create_count = 0
        create_many_advertisers = True
        if create_advertiser:
            advertiser = ADVERTISER_FACTORY.create_advertiser()
            create_many_advertisers = False
        else:
            if advertiser:
                create_many_advertisers = False
        while current_create_count < create_count:
            if create_many_advertisers:
                advertiser = ADVERTISER_FACTORY.create_advertiser()
            business = self._create(advertiser=advertiser)
            if create_location:
                BUSINESS_LOCATION_FACTORY.create_business_location(business)
            current_create_count += 1
            business_list.append(business)
        return business_list

    def create_business_many_locations(self, advertiser=None,
            location_create_count=1):
        """ Create ONE basic business instance with an advertiser association
        and more than one business location.
        """
        business = self.create_business(advertiser=advertiser)
        current_create_count = 1
        while current_create_count < location_create_count:
            BUSINESS_LOCATION_FACTORY.create_business_location(business)
            current_create_count += 1
        return business
    
    def create_businesses_many_locs(self, advertiser=None, create_count=1,
             location_create_count=1):
        """ Create ONE basic business instance with an advertiser association
        and more than one business location.
        """
        business_list = self.create_businesses(advertiser=advertiser,
            create_count=create_count)
        for business in business_list:
            current_create_count = 1
            while current_create_count < location_create_count:
                BUSINESS_LOCATION_FACTORY.create_business_location(business)
                current_create_count += 1
        return business_list

BUSINESS_FACTORY = BusinessFactory()