""" Offer Factory used to help create quick Offer instances for 
tests.
"""

from advertiser.factories.business_factory import BUSINESS_FACTORY
from common.utils import random_string_generator
from coupon.models import Offer

class OfferFactory(object):
    """ Offer Factory Class """
    
    @staticmethod
    def _create(business):
        """ Create a single offer instance. """
        offer = Offer.objects.create(business=business, 
            headline=random_string_generator(),
            qualifier=random_string_generator())
        return offer
    
    def create_offer(self, business=None, **kwargs):
        """ Create a ONE basic offer instance with a business and 
        advertiser association.
        """
        if not business:
            business = BUSINESS_FACTORY.create_business(**kwargs)
        offer = self._create(business=business)
        return offer
        
    def create_offers(self, business=None, create_business=False,
            create_count=1):
        """ This method will do 1 of 3 things.
        
        default.) business == None
            create_business == False 
            Create 1 or more offers and associate them with 
            different offers -> businesses -> advertisers. 
            Ex: offer -> business -> advertiser
                offer1 -> business1 -> advertiser1
                offer2 -> business2 -> advertiser2
                offer3 -> business3 -> advertiser3 

        2.) business == None
            create_business == True
            Create a business -> advertiser.
            Then create offers for that business.
             Ex: offer -> business -> advertiser 
                offer1 -> business -> advertiser
                offer2 -> business -> advertiser
        
        3.) business != None
            create_business == False
            If a business is passed in use that business.
            Create 1 or more offers and associate them with the 
            same business -> advertiser. 
            Ex: offer -> business -> advertiser 
                offer1 -> business -> advertiser
                offer2 -> business -> advertiser       
        """
        offer_list = []
        current_create_count = 0
        create_many_businesses = True
        if create_business:
            business = BUSINESS_FACTORY.create_business()
            create_many_businesses = False
        else:
            if business:
                create_many_businesses = False
        while current_create_count < create_count:
            if create_many_businesses:
                business = BUSINESS_FACTORY.create_business()
            offer = self._create(business=business)
            current_create_count += 1
            offer_list.append(offer)
        return offer_list

OFFER_FACTORY = OfferFactory()
