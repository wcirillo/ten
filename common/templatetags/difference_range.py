""" Filter that builds a list range between 2 values. """

from django.template import Library

register = Library()

@register.filter
def difference_range(value, arg):
    """
    Creates a list with items from arg+1 --> value.
    
    Example:    value = 2
                arg = 10
                difference_list = [3,4,5,6,7,8,9,10]
    """
    difference_list = []
    try:
        arg = int(arg)
        value = int(value)
    except (ValueError, TypeError):
        pass
    while value < arg:
        difference_list.append(value)
        value = value + 1
    return difference_list
difference_range.is_safe = False