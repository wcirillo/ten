""" Credit card service class for ecommerce app """

from django.utils.translation import ugettext_lazy as _

from ecommerce.validators import get_cc_type_from_number, validate_credit_card

class CreditCardService(object):
    """
    Allows attaching of cc_number to a credit card, without a model field for
    it because we never want to save it, but need to pass it around with the
    object during a purchase process.
    """
    def __init__(self, cc_number, cc_type):
        self.cc_number = cc_number
        self.cc_type = cc_type
    
    def validate_cc_number(self):
        """
        Does the credit card type match the credit card number.
        """
        if self.cc_type == None:
            self.cc_type = get_cc_type_from_number(self.cc_number)
        if self.cc_type == False:
            return (False, _("Card number is not valid."))
        else:
            if validate_credit_card(self.cc_type, self.cc_number):
                return (True, None)
            else:
                return (False, _("Card number is not valid."))