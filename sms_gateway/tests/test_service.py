""" Tests of sms_gateway. Tests of EZTexting API. """

from django.core.exceptions import ValidationError
from django.test import TestCase

from sms_gateway.service import send_carrier_lookup, \
    save_phone_by_carrier_lookup, cleanup_mobile_phone_no_carrier
from subscriber.models import Carrier, Subscriber, MobilePhone


class TestService(TestCase):
    """ All tests of sms_gateway service functions. """
        
    def test_carrier_lookup_good(self):
        """
        Performs a carrier lookup for a valid number. This is Steve's cell. :)
        """
        carrier = send_carrier_lookup('8455181898')
        self.assertEquals(Carrier.objects.get(id=2), carrier)
                
    def test_carrier_lookup_invalid(self):
        """ Performs a carrier lookup for an invalid number. """
        try:
            send_carrier_lookup('8455551212')
        except ValidationError as exception:
            print exception.messages
            self.assertEquals(
                exception.messages[0], 
                u"Lookup Failed Due to Inaccurate Mobile Number"
                ) 
                
    def test_create_phone_carr_lookup(self):
        """
        Test save_phone_by_carrier_lookup service function. 
        This is Mandy's cell. :)
        """
        phone_number = '8455410602'
        save_phone_by_carrier_lookup(phone_number)
        self.assertTrue(
                MobilePhone.objects.get(mobile_phone_number=phone_number)
            )
            
    def test_cleanup_mobile_phone(self):
        """ Tests cleanup_mobile_phone_no_carrier. """
        # One bad mobile phone.
        subscriber = Subscriber()
        subscriber.save()
        mobile_phone = MobilePhone()
        mobile_phone.subscriber = subscriber
        mobile_phone.mobile_phone_number = '5550001111'
        mobile_phone.carrier = Carrier.objects.get(id=1)
        mobile_phone.save()
        mobile_phone.carrier = Carrier.objects.get(id=1)
        mobile_phone.save()
        other_mobile_phones = MobilePhone.objects.filter(carrier__id=1)
        self.assertEquals(other_mobile_phones.count(), 1)
        cleanup_mobile_phone_no_carrier(purge=True)
        cleaned_mobile_phones = MobilePhone.objects.filter(carrier__id=1)
        self.assertEquals(cleaned_mobile_phones.count(), 0)
        
