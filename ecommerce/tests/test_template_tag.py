""" Tests of ecommerce template tags. """
from django.test import TestCase

from ecommerce.templatetags.currency import currency


class TestCurrencyTag(TestCase):
    """ Assert currency tag renders properly with varying args passed in. """
    
    def test_default_w_decimals(self):
        """ Assert a number passed to tag with args defaulted displays decimals.
        """
        self.assertEqual(currency(188.00), "$188.00")

    def test_no_decimals_00(self):
        """ Assert a number passed to tag with argument display_decimals False
        does not display decimals when 00.
        """
        self.assertEqual(currency(188.00, False), "$188")
        
    def test_no_decimals_01(self):
        """ Assert a number passed to tag with argument display_decimals False
        shows decimals when decimals are > 0.
        """
        self.assertEqual(currency(188.01, False), "$188.01")
