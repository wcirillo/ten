""" Template tag to format phone numbers. """    
from django.template import Library

from common.custom_format_for_display import format_phone
register = Library()

@register.filter
def format_phone_number(value):
    """ Formats any 10-digit string into (NNN) NNN-NNNN format. If length is not
    10, returns self.
    """
    return format_phone(value)
