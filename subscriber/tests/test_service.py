""" Unit tests for service functions of subscriber app. """

from django.test import TestCase

from market.models import Site
from subscriber.models import Subscriber, MobilePhone
from subscriber.service import add_update_subscriber, \
    update_default_site_subscribers
     
class TestService(TestCase):
    """
    TestCase for service functions of subscriber app.
    """    
    
    fixtures = ['test_subscriber']
    
    def test_add_update_subscriber_new(self):
        """
        Assert the service function add_update_subscriber() creates a new
        subscriber.
        """
        carrier_id = 2
        mobile_phone_number = '000'
        subscriber_zip_postal = '00000'
        site = Site.objects.get(id=1)
        subscriber = add_update_subscriber(carrier_id, mobile_phone_number, 
            subscriber_zip_postal, site)
        print(subscriber)
        self.assertTrue(subscriber)
        
    def test_add_update_subscriber_up(self):
        """
        Assert the service function add_update_subscriber() updates an existing
        subscriber with a new phone.
        
        Assert a mobile phone is related to a subscriber at most once.
        """
        carrier_id = 2
        subscriber_zip_postal = '00000'
        site = Site.objects.get(id=1)
        subscriber = Subscriber.objects.get(id=1)
        self.assertEquals(subscriber.mobile_phones.count(), 1)
        mobile_phone_number = '001'
        mobile_phone = MobilePhone()
        mobile_phone.mobile_phone_number = mobile_phone_number
        mobile_phone.carrier_id = carrier_id
        mobile_phone.subscriber_id = 1
        mobile_phone.save()
        subscriber = add_update_subscriber(carrier_id, mobile_phone_number, 
            subscriber_zip_postal, site)
        self.assertEquals(subscriber.id, 1)
        self.assertEquals(subscriber.mobile_phones.count(), 2)
        # Try attaching the same phone again.
        subscriber = add_update_subscriber(carrier_id, mobile_phone_number, 
            subscriber_zip_postal, site)
        self.assertEquals(subscriber.mobile_phones.count(), 2)
        
    def test_update_default_site_subs(self):
        """
        Tests a cleanup util. This sub has a zip for site 2 but is related to
        site 1.
        """
        subscriber = Subscriber()
        subscriber.subscriber_zip_postal = '12550'
        subscriber.site_id = 1
        subscriber.save()
        subscribers_before_1 = Subscriber.objects.filter(site=1).count()
        subscribers_before_2 = Subscriber.objects.filter(site=2).count()
        update_default_site_subscribers()
        subscribers_after_1 = Subscriber.objects.filter(site=1).count()
        subscribers_after_2 = Subscriber.objects.filter(site=2).count()
        self.assertEquals(subscribers_after_1, subscribers_before_1 - 1)
        self.assertEquals(subscribers_after_2, subscribers_before_2 + 1)
                
