""" Tests for custom cleaning functions. """

from common.custom_cleaning import trim_fields_in_form
from common.test_utils import EnhancedTestCase
from coupon.forms import EditCouponForm

class TestCustomCleans(EnhancedTestCase):
    """ Test case for custom cleaning functions."""
    
    def test_trim_fields_in_form(self):
        """ Assert that we trim each field in the form. """
        business_name = " Scissors and trimming "
        slogan = " spaces give meaning "
        headline = " Spacing out "
        qualifier  = ' between the clouds'
        web_url = " intheline.com "
        form = EditCouponForm(data={
            'business_name':business_name,
            'slogan':slogan,
            'headline':headline,
            'qualifier':qualifier,
            'web_url':web_url,
            'default_restrictions':[1],
            'is_redeemed_by_sms': 1,
            'expiration_date': '1/1/2020',
             'is_valid_monday': 1,
             'is_valid_tuesday': 1,
             'is_valid_wednesday': 1,
             'is_valid_thursday': 1,
             'is_valid_friday': 1,
             'is_valid_saturday': 1,
             'is_valid_sunday': 1})
        form.is_valid()
        form.cleaned_data = trim_fields_in_form(form)
        # Ensure fields were left and right trimmed of spaces.
        self.assertEqual(form.cleaned_data['is_valid_monday'], True)
        self.assertEqual(form.cleaned_data['web_url'], 
            "http://%s" %web_url.strip())
        self.assertEqual(form.cleaned_data['headline'], headline.strip())
        self.assertEqual(form.cleaned_data['qualifier'], qualifier.strip())
        self.assertEqual(form.cleaned_data['slogan'], slogan.strip())
        self.assertEqual(form.cleaned_data['business_name'], 
            business_name.strip())
        # Ensure fields that were not populated in the form exist.
        self.assertNotEqual(form.cleaned_data.get(
                'location_zip_postal_1', 'missing_field'), 'missing_field')
        self.assertNotEqual(form.cleaned_data.get(
                'location_state_province_10', 'missing_field'), 'missing_field')
    
    def test_check_field_length(self):
        """ Assert that check_field_length called in trim_fields_in_form
        respects form field attribute max length. """
        form = EditCouponForm(data={
            'headline': 'This headline is over twenty-five characters'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['headline'][0], 
            'Please limit this field to 25 characters')