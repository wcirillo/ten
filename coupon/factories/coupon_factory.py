""" Coupon Factory used to help create quick Coupon instances for tests. """
from advertiser.factories.location_factory import COUPON_LOCATION_FACTORY
from coupon.factories.offer_factory import OFFER_FACTORY
from coupon.models import Coupon

class CouponFactory(object):
    """ Coupon Factory Class """
    @staticmethod
    def _create(offer, coupon_type_id=3):
        """ Create a single coupon instance. """
        coupon = Coupon.objects.create(offer=offer, 
            coupon_type_id=coupon_type_id)
        return coupon
    
    def create_coupon(self, offer=None, **kwargs):
        """ Create a ONE basic coupon instance with an offer, business and 
        advertiser association. """
        create_location = kwargs.get('create_location', True)
        if not offer:
            offer = OFFER_FACTORY.create_offer(**kwargs)
        coupon = self._create(offer=offer)
        if create_location:
            COUPON_LOCATION_FACTORY.create_coupon_location(coupon)
        return coupon
        
    def create_coupons(self, offer=None, create_offer=False, create_count=1):
        """ This method will do 1 of 3 things.
        
        default.) offer == None
            create_offer == False 
            Create 1 or more offers and associate them with 
            different offers -> businesses -> advertisers. 
            Ex: coupon -> offer -> business -> advertiser
                coupon1 -> offer1 -> business1 -> advertiser1
                coupon2 -> offer2 -> business2 -> advertiser2
                coupon3 -> offer3 -> business3 -> advertiser3 

        2.) offer == None
            create_offer == True
            Create an offer -> business -> advertiser.
            Then create coupons for that offer.
             Ex: coupon -> offer -> business -> advertiser 
                coupon1 -> offer -> business -> advertiser
                coupon2 -> offer -> business -> advertiser
        
        3.) offer != None
            create_offer == False
            If an offer is passed in use that offer.
            Create 1 or more coupons and associate them with the 
            same offer -> business -> advertiser. 
            Ex: coupon -> offer -> business -> advertiser 
                coupon1 -> offer -> business -> advertiser
                coupon2 -> offer -> business -> advertiser       
        """
        coupon_list = []
        current_create_count = 0
        create_many_offers = True
        if create_offer:
            offer = OFFER_FACTORY.create_offer()
            create_many_offers = False
        else:
            if offer:
                create_many_offers = False
        while current_create_count < create_count:
            if create_many_offers:
                offer = OFFER_FACTORY.create_offer()
            coupon = self._create(offer=offer)
            COUPON_LOCATION_FACTORY.create_coupon_location(coupon)
            current_create_count += 1
            coupon_list.append(coupon)
        return coupon_list
    
    def create_coupon_many_locations(self, offer=None, create_all=True, 
            business_location_count=1, coupon_location_count=1):
        """ Create a coupon with multiple locations associated with it.
                
        ARG Definitions:
        create_all == True will ensure that every business_location will get 
            associated with this coupon. 
        business_location_count == the number of locations that the respective
            business of this coupon will have in total.
        coupon_location_count == The number of business_locations that will be
            associated with this coupon.
        """
        coupon = self.create_coupon(offer=offer)
        #current_create_count = 1
        #while(current_create_count < business_location_count):
        COUPON_LOCATION_FACTORY.create_coupon_locations(coupon, 
            create_all=create_all,
            business_location_count=business_location_count,
            coupon_location_count=coupon_location_count)
         #   current_create_count += 1
        return coupon
    
    def create_coupons_many_locations(self, offer=None, create_all=True, 
            create_count=1, **kwargs):
        """ Create multiple coupons with multiple locations associated with each
        one.
                
        ARG Definitions:
        create_all == True will ensure that every business_location will get 
            associated with this coupon. 
        business_location_count == the number of locations that the respective
            business of this coupon will have in total.
        coupon_location_count == The number of business_locations that will be
            associated with this coupon.
        """
        coupon_list = self.create_coupons(offer=offer,
            create_count=create_count)
        for coupon in coupon_list:
            COUPON_LOCATION_FACTORY.create_coupon_locations(coupon, 
                create_all=create_all,
                business_location_count=kwargs.get('business_location_count', 1),
                coupon_location_count=kwargs.get('coupon_location_count', 1))
        return coupon_list

    @staticmethod
    def normalize_coupon_locations(coupon):
        """ Normalize locations of this coupon to NY state. """
        locations = coupon.location.all()
        for location in locations:
            location.location_state_province = 'NY'
            location.save()

COUPON_FACTORY = CouponFactory()
