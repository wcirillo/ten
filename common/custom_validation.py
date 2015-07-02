"""
Define the custom validation Classes here.
"""
#pylint: disable=W0212
import re

from django.forms.util import ErrorList

from common.utils import replace_problem_ascii
from ecommerce.models import PromotionCode


def validate_zip_postal(self, zip_postal, field_name):
    """
    Holtsville, NY 00501 is said to be the lowest zip code in the U.S.
    according to the U.S. Postal Service.  However 00401 exists for Reader's
    Digest Association, Pleasantville, NY.
    Ketchikan, Alaska 99950 is the highest zip code in the U.S.
    """
    if not re.match("\d{5}$", str(replace_problem_ascii(zip_postal))):
        self.errors[field_name] = ErrorList(["Please enter a 5 digit zip"])

def validate_passwords(self, fieldname, password1, password2):
    """ Clean password form fields and perform validation. """
    if password1:
        if password1 != password2:
            self.errors[fieldname] = ErrorList(["Passwords don't match."])
        if len(password1) < 6:
            # possibly remove min length
            self.errors[fieldname] = \
                ErrorList(["Passwords must contain at least 6 characters."])
    return self

def validate_phone_number(self, phone_number, field_name, generic=False):
    """ This validates the single phone number field. """
    if not re.match("\d{10}$", str(phone_number)):
        err_msg = 'Please enter the 10 digit number of your cell phone'
        if generic:
            err_msg = 'Please enter a 10 digit phone number.'
        self.errors[field_name] = ErrorList([err_msg])

def validate_promo_code(self, code, field_name):
    """
    This validates the promotion code field.
    """
    if code:
        promotion_code = PromotionCode(code=code)
        is_promo_good = promotion_code.clean_code()
        if not is_promo_good:
            self.errors[field_name] = ErrorList(["Tracking Code not valid"])