""" Custom validators for the ecommerce app. """

import re        
import datetime

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from common.custom_cleaning import strip_to_numbers

# Regex for valid card numbers.
CC_PATTERNS = {
    'amex':         '^3[47][0-9]{13}$',
    'discover':     '^6(?:011|5[0-9]{2})[0-9]{12}$',
    'mastercard':   '^5[12345]([0-9]{14})$',
    'visa':         '^4([0-9]{12,15})$',
}

def require_date_not_past(value):
    """ Date cannot be past. """
    if value < datetime.date.today():
        raise ValidationError(_(u'Date cannot be in the past.'))
        
def require_datetime_not_past(value):
    """ Datetime cannot be past. """
    # Now is later than it was a moment ago, so give leeway.
    if value < datetime.datetime.now() - datetime.timedelta(days=1):
        raise ValidationError(_(u'Date/time cannot be in the past.'))
        
def require_percent(value):
    """ Value must be between 0 and 100. """
    if value < 0 or value > 100:
        raise ValidationError(_(u'Value must be between 0 and 100.'))

def require_valid_month(value):
    """ Value must be an ordinal month. """
    if value == 0 or value > 12:
        raise ValidationError(_(u'Please enter a valid month.'))

def validate_number(number):
    """ Checks to make sure string isnumeric. """
    if not number.isdigit():
        raise Exception('Number has invalid digits')
    return True

def validate_credit_card(cc_type, number):
    """ 
    Check that a credit card number matches the type and validates the Luhn
    Checksum.
    """
    cc_type = cc_type.strip().lower()
    if validate_number(number):
        number = strip_to_numbers(number)
        if CC_PATTERNS.has_key(cc_type):
            if validate_digits(cc_type, number):
                return validate_luhn_checksum(number)
    return False


def validate_digits(cc_type, number):
    """ Checks to make sure that the Digits match the CC pattern. """
    regex = CC_PATTERNS.get(cc_type.lower(), False)
    if regex:
        return re.compile(regex).match(number) != None
    else:
        return False
                
def validate_luhn_checksum(number_as_string):
    """ Checks to make sure that the card passes a luhn mod-10 checksum. """
    checksum = 0
    num_digits = len(number_as_string)
    oddeven = num_digits & 1
    for i in range(0, num_digits):
        digit = int(number_as_string[i])
        if not (( i & 1 ) ^ oddeven ):
            digit = digit * 2
        if digit > 9:
            digit = digit - 9
        checksum = checksum + digit
    return ( (checksum % 10) == 0 )

def get_cc_type_from_number(number):
    """ Derives cc_type from card number. """
    for key in CC_PATTERNS:
        if re.compile(CC_PATTERNS[key]).match(number):
            return key
    return False
