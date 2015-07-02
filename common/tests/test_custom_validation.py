""" Tests for custom validation functions. """

from django.test import TestCase

from common.custom_validation import validate_zip_postal
from consumer.forms import ConsumerRegistrationForm

class TestCustomValidator(TestCase):
    """ Test case for common custom validations work."""
    
    def test_validate_zip_postal(self):
        """ Assert zip code not valid when string is not numeric and 5 digits in
         length.
        """
        test_cases = [('', False), ('1', False), ('1234', False), 
            ('999999', False), ('1111' + u'\u01B7', True), 
            ('2222' + u'\u0439', False), ('2222' + u'\u0439' + '1', True)]
        for case in test_cases:
            initial_data = {'consumer_zip_postal':case[0]}
            form = ConsumerRegistrationForm(initial=initial_data)
            form._errors = {'consumer_zip_postal':''}
            validate_zip_postal(form, case[0], 
                'consumer_zip_postal')
            if case[1]:
                self.assertEqual(form['consumer_zip_postal'].errors, '')
            else:
                self.assertEqual(form['consumer_zip_postal'].errors[0], 
                'Please enter a 5 digit zip')
