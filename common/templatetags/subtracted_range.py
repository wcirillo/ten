""" Filter that replicates a while loop in a template. """

from django.template import Library

from common.templatetags.range import get_range

register = Library()

@register.filter
def subtracted_range(value, arg):
    """
    Subtracts the value from the arg and gives a list from 0 to the 
    difference.
    
    Example:    value = 2
                arg = 10
                difference_list = [0,1,2,3,4,5,6,7,8]
    """
    try:
        return get_range(int(arg) - int(value))
    except (ValueError, TypeError):
        try:
            return get_range(arg - value)
        except (ValueError, TypeError):
            return value
subtracted_range.is_safe = False
  
