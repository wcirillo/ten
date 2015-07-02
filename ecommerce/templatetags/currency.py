""" 
Currency templatetag for ecommerce app, from comment at
http://djangosnippets.org/snippets/2365/

Added show_decimal and return '' for value ''.
"""

from django import template
from django.conf import settings

register = template.Library()

@register.filter()
def currency(value, show_decimal="True"):
    """ Currency formatting template filter. Arg wants to be a string. """
    if value == '':
        return ''
    symbol = getattr(settings, 'CURRENCY_SYMBOL', '$')
    thousand_sep = getattr(settings, 'THOUSAND_SEPARATOR', ',')
    decimal_sep = getattr(settings, 'DECIMAL_SEPARATOR', '.')

    intstr = str(int(value))
    f = lambda x, n, acc = []: f(x[:-n], n, [(x[-n:])]+acc) if x else acc
    intpart = thousand_sep.join(f(intstr, 3))
    currency_ = "%s%s" % (symbol, intpart)
    if show_decimal == "True" or int(("%0.2f" % value)[-2:]):
        currency_ = "%s%s%s" % (currency_, decimal_sep, ("%0.2f" % value)[-2:])
    return currency_
currency.is_safe = True
