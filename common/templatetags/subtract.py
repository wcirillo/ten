""" Filter that subtracts 2 values. """

from django.template import Library

register = Library()

@register.filter
def subtract(value, arg):
    """Subtracts the value from the arg."""
    try:
        return int(arg) - int(value)
    except (ValueError, TypeError):
        try:
            return arg - value
        except (ValueError, TypeError):
            return value
subtract.is_safe = False
