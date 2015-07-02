""" Custom methonds of formatting for ten project """

from django.template.defaultfilters import slugify
from django.utils.stopwords import strip_stopwords

from common.custom_cleaning import clean_phone_number


def format_phone(phone, delimiter=None):
    """ Format a phone number for display purposes. """
    raw_phone = clean_phone_number(phone)
    if raw_phone:
        if delimiter:
            phone = '%s%s%s%s%s' % (raw_phone[0:3], delimiter, raw_phone[3:6], 
                delimiter, raw_phone[6:])
        else:
            phone = '(%s) %s-%s' % (raw_phone[0:3], raw_phone[3:6], 
                raw_phone[6:])
    return phone

def build_slug(slug):
    """ Builds a slug and strips all stopwords from a slug and builds it again.
    """
    slug = strip_stopwords(slug)
    slug = slugify(slug)
    words = slug.split('-')
    sentence = []
    for word in words:
        try:
            float(word)
        except ValueError:
            sentence.append(word)
    slug = u'-'.join(sentence) 
    return slug

def list_as_text(obj_, last_=' and '):
    """
    Iterates over object and returns string representation of each item in a
    grammatical list for display.
        ie: ['a', 'b', 'c'] becomes 'a, b and c'.
    If obj_ passed in is None, return its value back.
    last_ is the last conjunction to use at the end of the list.
    """
    try:
        obj_length = len(obj_)
    except TypeError:
        return obj_
    to_string = conjunction = ''
    for index, item in enumerate(obj_):
        if obj_length > 1 and index == obj_length-1:
            conjunction = last_
        to_string  += conjunction + str(item).strip()
        conjunction = ', '
    return to_string

