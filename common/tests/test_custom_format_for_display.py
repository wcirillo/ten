""" Tests for custom display format methods. """
from django.test import TestCase

from common.custom_format_for_display import format_phone, list_as_text
from market.models import Site

class TestCustomDisplayFormatter(TestCase):
    """ Assert custom display format methods work. """
    fixtures = []
    
    def test_list_to_string_display(self):
        """ Test conversion of list to grammatically correct string. """    
        test1 = list_as_text(['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(test1, 'a, b, c, d and e')
        test2 = list_as_text(['Atlanta, GA', 'New York City, NY',
            'Miami, FL'])
        self.assertEqual(test2, 'Atlanta, GA, New York City, NY and Miami, FL')
        test3 = list_as_text(['Apple a day...'])
        self.assertEqual(test3, 'Apple a day...')
        test4 = list_as_text(['love', 'hate'])
        self.assertEqual(test4, 'love and hate') 
        sites = Site.objects.filter(id__in=[2, 3, 4])
        test5 = list_as_text(sites)
        self.assertEqual(test5, 'Hudson Valley, Triangle and Capital Area')
    
    def test_format_phone_raw(self):
        """ Assert a phone number is formatted in proper format. """
        number = '8095551234'
        self.assertEqual(format_phone(number), '(809) 555-1234')
        
    def test_format_phone_formatted(self):
        """ Assert a phone number that is already formatted displays correctly.
        """
        number1 = '809.555.1234'
        self.assertEqual(format_phone(number1), '(809) 555-1234')
        number2 = '(888) 555-3456'
        self.assertEqual(format_phone(number2), '(888) 555-3456')   

    def test_format_phone_none(self):
        """ Assert a phone number that is NULL, returns nothing gracefully.
        """
        number1 = None
        self.assertEqual(format_phone(number1), None)