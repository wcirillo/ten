""" Filter that replaces all instances of a specific string with its replacement
value. """

from django.template import Library
from django.utils.safestring import mark_safe, SafeData

register = Library()

@register.filter
def replace_all(string, args):
    """ String replace function for a template.
    
    Example:    string = 'Kodiak Island'
                substring_to_replace = ' '
                replaced_substring_value = '_'

        string == Kodiak_Island
    """
    try:
        string = str(string)
        arg_list = args.split(',')

        substring_to_replace = str(arg_list[0])
        replaced_substring_value = str(arg_list[1])
    except (ValueError, TypeError):
        pass
    safe = isinstance(string, SafeData)
    string = string.replace(substring_to_replace, replaced_substring_value)
    if safe and ';' not in (args[0], args[1]):
        return mark_safe(string)
    return string
replace_all.is_safe = False


