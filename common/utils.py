#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
""" Common utilities, or at least things that don't seem to fit elsewhere. """
from BeautifulSoup import BeautifulSoup
from math import floor
from urlparse import urlparse 
import csv
import datetime
import hashlib
import logging
import os
import random
import re
import time
import urllib
import urllib2

from django.conf import settings 
from django.core.exceptions import ValidationError
from django.db.models.manager import Manager
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.template.defaultfilters import date as date_filter

from esapi.reference.default_randomizer import DefaultRandomizer

from common.custom_format_for_display import list_as_text

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

ALLOWED_SEPARATORS = ' -._'


class CurlBuffer():
    """
    Curl does not return a django response object.
    Fake it so we can use the special assert functions of 
    django.test.TestCase, which extends python unittest:
    """
    def __init__(self):
        self.content = ''
        self.header = ''
        self.status_code = 200
        self._charset = 'utf-8'

    def body_callback(self, buf):
        """ Append to buffer. """
        self.content += buf
    
    @classmethod
    def progress(cls, download_t, download_d):
        """
        Callback function invoked when progress information is updated.
        Keeps track of download progress.
        """
        print "Total to download %d bytes, have %d bytes so far" % (
                download_t, download_d
            )

def build_fb_like_meta(site, coupon=None):
    """ Build facebook meta tags for Like button Wall Display. """
    fb_like = {}
    if coupon:
        fb_like['ref'] = coupon.id
        fb_like['title'] = coupon.offer.headline + ' - Get this coupon! ' + \
            site.domain
        fb_like['description'] = coupon.offer.headline + ' ' + \
            coupon.offer.qualifier + ' - Valid through %s from %s %s.' \
            % (coupon.expiration_date,
            coupon.offer.business.business_name,
            list_as_text(coupon.get_location_string()[0]))
        fb_desc_length = len(fb_like['description'])
        try:
            if coupon.offer.business.get_business_description():
                fb_like['description'] += ' %s' \
                    % coupon.offer.business.get_business_description()[
                    :290 - fb_desc_length]
                if len(fb_like['description']) >= \
                len(fb_like['description']) - fb_desc_length:
                    fb_like['description'] += '...'
        except AttributeError:
            pass
    else:
        fb_like['ref'] = site.domain
        fb_like['title'] = 'Sign up for %s Coupons.' % site.name
        fb_like['description'] = "Save money at the best places to eat, " + \
        "drink, play and shop. It's simple, so get started today!" 
    return fb_like

def change_unicode_list_to_int_list(list_to_convert):
    """ Changes unicode list to integer. """
    for i in range(len(list_to_convert)):
        list_to_convert[i] = int(list_to_convert[i].encode())
    return list_to_convert
    
def check_spot_path_fs(site):
    """ 
    Returns the full file system path of the spots directory for a given site, 
    if it exists, False if the would-be directory doesn't exist.
    """
    spot_path = os.path.join(settings.SPOT_PATH, site.spot_name())
    abs_spot_path = os.path.join(settings.PROJECT_PATH, spot_path)
    try:
        os.stat(abs_spot_path)
        return abs_spot_path
    except OSError:
        return False
    
def create_unique_datetime_str():
    """
    Take the current date and time and returns a unique string that 
    can not be reproduced.
    """
    unique_datetime_str = str(time.mktime(
        datetime.datetime.now().timetuple())).split('.')[0]
    return unique_datetime_str

def get_core_path_info(request, site):
    """ Removes the directory_name off of PATH_INFO to get the core path. """
    core_path_info = request.META.get('PATH_INFO')
    if site.id != 1:
        core_path_info = core_path_info.replace('%s/' % site.directory_name, '')
    return core_path_info

def generate_email_hash(email, mode='db'):
    """
    Generates our unique user hash to be included in email bounce and 
    opt-out headers.
    """
    pre_hash = '%s%s' %  (settings.EMAIL_HASH_SALT, email)    
    prefix = random.randint (10000, 99999)
    postlen = random.randint(0, 6)
    postfix = random.randint (10 ** postlen, 10 ** (postlen + 1))
    if mode == 'db':
        return hashlib.sha1(pre_hash).hexdigest()   
    else:
        midhash = hashlib.sha1(pre_hash).hexdigest()
        hashed = "%d%s%d" % (prefix, midhash, postfix)
        return hashed

def generate_guid():
    """ Generates a Global Unique IDentifier. """
    return hashlib.sha1(str(random.random())).hexdigest()
   
def get_object_or_redirect(klass, destination, *args, **kwargs):
    """
    Uses get() to return an object, or rredirects to 'destination'
    klass may be a Model, Manager, or QuerySet object. All other passed
    arguments and keyword arguments are used in the get() query.
    Note: Like with get(), an MultipleObjectsReturned will be raised if more 
    than one object is found.
    """
    queryset = _get_queryset(klass)
    try:
        return queryset.get(*args, **kwargs)
    except queryset.model.DoesNotExist:
        return HttpResponseRedirect(destination)

def _get_queryset(klass):
    """
    Returns a QuerySet from a Model, Manager, or QuerySet. Created to make
    get_object_or_404 and get_list_or_404 more DRY.
    """
    if isinstance(klass, QuerySet):
        return klass
    elif isinstance(klass, Manager):
        manager = klass
    else:
        manager = klass.objects
    return manager.all()

def normalize_code(code):
    """ Returns code stripped of expected punctuation, upper case. """
    for x in ALLOWED_SEPARATORS:
        code = code.replace(x, '')
    return code.upper()

def random_code_generator(length=6, chunk=0, separator=None, banned_chars=''):
    """
    Generates random codes with the following parameters:
    length: How long with the code be, not counting separators (if any).
    chunk:  0 = don't separate code into chunks.
            n = separate code into chucks of n legth, for usability.
        Allowed values: 0,2,3,4
    separator: The punctuation used to separate code chunks.
    banned_chars: Besides the characters that are universally prohibited from
        codes, specific prohibitions.
    
    Note: It is expected that length is evenly divisible by chunk.
    """
    if separator and separator not in ALLOWED_SEPARATORS:
        raise ValidationError("Codes do not allow separator %s" % separator)
    # No 0,1,O, I, or L (L is out in case the result converted to lower case.)
    character_set = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    for bad_char in banned_chars:
        character_set = character_set.replace(bad_char, '')
    instance = DefaultRandomizer()
    code = DefaultRandomizer.get_random_string(instance, length, character_set)
    if chunk in (2, 3, 4) and chunk * 2 <= length and separator:
        pretty_code = []
        current_index = 0
        next_index = int(floor(length/chunk))
        while current_index + next_index <= length:
            pretty_code.append(code[current_index:current_index+next_index])
            current_index = current_index + next_index
        code = separator.join(pretty_code)
    return code

def remove_non_ascii_chars(string):
    """ Remove all non-ascii characters """
    return "".join(i for i in string if ord(i)<128)

def replace_problem_ascii(string):
    """
    Replace certain high ascii characters, such as smart quotes, with their
    low ascii equivalent.
    """
    try:
        return str(string)
    except UnicodeEncodeError:
        # Check escaped double and single slashes converts unicode inputted.
        # Double curly quotes.
        string = string.replace(u"\u201c", "\"").replace(u"\u201d", "\"")
        string = string.replace(u"\u2026", "...").replace(u"\u2013", "--")
        # Spanish-likely characters:
        string = string.replace(u"\u00E0", "a").replace(u"\u00E1", "a")
        string = string.replace(u"\u00C1", "A").replace(u"\u00E2", "a")
        string = string.replace(u"\u00E3", "a").replace(u"\u00E8", "e")
        string = string.replace(u"\u00E4", "a").replace(u"\u00C8", "E")
        string = string.replace(u"\u00E9", "e").replace(u"\u00Eb", "e")
        string = string.replace(u"\u00C9", "E").replace(u"\u00Cb", "E")
        string = string.replace(u"\u00F3", "o").replace(u"\u00D3", "O")
        string = string.replace(u"\u00FC", "u").replace(u"\u00DA", "U")
        string = string.replace(u"\u00C8", "E").replace(u"\u00BF", "?")
        string = string.replace(u"\u00BB", ">>").replace(u"\u043F", "II")
        string = string.replace(u"\u00A1", "!").replace(u"\u0432", "B")
        # Single curly quotes:
        string = string.replace(u"\u2018", "'").replace(u"\u2019", "'")
        string = string.replace(u"\u2122", "(tm)").replace(u"\u02BC", "'")
        string = string.replace(u"\u00AE", "(R)").replace(u"…", "...")
        string = string.replace(u"\u24C7", "(R)").replace(u"©", "(C)")
        string = string.replace(u"®", "(R)").replace(u"™", "(tm)")
        string = string.replace(u"–", "--").replace(u"\u01B7", "3")
        string = string.replace(u"\u01BC", "5").replace(u"\u01BD", "5")
        string = string.replace(u"\u012C", "3").replace(u"\u012D", "3")
        string = string.replace(u"\u0222", "8").replace(u"\u0223", "8")
        string = string.replace(u"\u0437", "3").replace(u"\u04E0", "3")
        string = string.replace(u"\u04E1", "3")
    try:
        return str(string)
    except UnicodeEncodeError:
        # Log unhandled exception and ignore invalid ascii characters.
        LOG.error('replace_problem_ascii: Unhandled unicode in string: %s' 
            % string)
        return str(string.encode('ascii', 'ignore'))

def shorten_url(long_url):
    """
    Call TinyURL API and returned shortened URL result
    Args: 
        longURL: URL string to shorten
    Returns:
        The shortened URL as a string
    """
    result = None
    f = urllib.urlopen("http://tinyurl.com/api-create.php?url=%s" % long_url)
    try:
        result = f.read()
    finally:
        f.close()
    return result

def format_date_for_dsp(date):
    """ Format the type(date()) into a unicode type for display. """
    return date_filter(date, 'n/j/y')

def open_url(web_url):
    """ Get web page for this url. """
    request = urllib2.Request(web_url)
    try:
        response = urllib2.urlopen(request)
    except urllib2.URLError as e:
        LOG.error('web_url: %s msg: %s' % (web_url, e.args))
        return
    web_page = response.read()
    return web_page

def is_datetime_recent(my_datetime, days): 
    """ Return True if created (recently) under days """
    return (my_datetime.date() > (datetime.date.today() - datetime.timedelta(
        days=days)))

def is_gmtime_recent(gmtime_string, local_datetime):
    """
    Return True if gmtime is more recent than local time.
    Test: is_gmtime_recent("2011-06-06 17:03:21", datetime.datetime.now())
    """
    utc_offset_timedelta = datetime.datetime.utcnow() - datetime.datetime.now()
    local_to_utc_datetime = local_datetime + utc_offset_timedelta
    datetime_format = '%Y-%m-%d %H:%M:%S'
    gm_datetime = datetime.datetime.strptime(gmtime_string, datetime_format)
    return gm_datetime > local_to_utc_datetime

def parse_phone(phone_number):
    """ 
    Parse phone number and return a dict of 3 values: area_code, exchange, 
    number. 
    """
    phone_pattern = re.compile(r'(\d{3})\D*(\d{3})\D*(\d{4})$', re.VERBOSE)
    if phone_number != '' and phone_number:
        try:
            phone_match = phone_pattern.search(phone_number)
            if phone_match:
                phone_tuple = phone_match.groups()
                phone_dict = {'area_code': phone_tuple[0],
                    'exchange': phone_tuple[1], 'number': phone_tuple[2]}
                return phone_dict
        except TypeError:
            pass
    return None

def split_csv(infile, outprefix, maxrows, delimiter=',', **kwargs):
    """ Split a csv file by records/rows instead of lines. """
    auto_header = kwargs.get('auto_header', False)
    quotechar = kwargs.get('quotechar', '"')
    csvreader = csv.reader(open(infile, 'rb'), delimiter=delimiter,
        quotechar=quotechar)
    rowcount = 0
    filecount = 0
    total_rows = 0 
    for row in csvreader:
        if total_rows == 0:
            header_row = row
        if rowcount == 0:
            filecount = filecount + 1
            csvwriter = csv.writer(open("%s-%d.csv" % (outprefix, filecount), 
                'wb'), delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
            # add the header row for all file after the first
            if filecount > 1:
                if auto_header:
                    csvwriter.writerow(header_row)
        csvwriter.writerow(row)
        total_rows = total_rows + 1
        rowcount = rowcount + 1
        if rowcount == maxrows:
            rowcount = 0
    print "Total rows: %d,  Total Files: %d" % (total_rows, filecount)

def uniquify_sequence(seq):
    """ Return sequence uniquified, as a list. """
    return list(uniquify_generator(seq))
    
def uniquify_generator(seq):
    """ A generator used to uniquify a sequence, preserving order. """
    seen = set()
    for x in seq:
        if x in seen:
            continue
        seen.add(x)
        yield x

def parse_url_from_html(web_url):
    """ Get url from html frameset. Also follow redirect and return url. """
    
    def get_redirect_url(web_url):
        """ Takes a website address and returns the redirected website address, 
        if it is a redirect. 
        """
        request = urllib2.Request(web_url)
        opener = urllib2.build_opener()
        open_info = opener.open(request)
        return open_info.url

    web_page = open_url(web_url)
    if web_page:
        soup = BeautifulSoup(web_page)
        if (not soup.find('img') and soup.find('frameset') 
            and soup.find('frame')):
            try:
                if ('100%' in soup.find('frameset')['rows'] 
                    and soup.find('frame')['src']):
                    if 'http' == (soup.find('frame')['src'])[:4]:
                        web_url = str(soup.find('frame')['src'])
                    elif '..' == (soup.find('frame')['src'])[:2]: 
                        web_url = get_redirect_url(web_url)
                        web_domain = urlparse(web_url).hostname
                        web_suffix = str(soup.find('frame')['src'])[2:]
                        web_url = 'http://' + web_domain + web_suffix
            except KeyError:
                pass
        web_url = get_redirect_url(web_url) 
    return web_url

def random_string_generator(string_length=10, alpha_only=False,
        numeric_only=False, lower_alpha_only=False, lower_numeric_only=False):
    """ Pseudo-random generator for an alphanumeric string 
    of length string_length.
    For each character, randomly choose whether it will be numeric, alpha-lower,
    or alpha-upper... then chooses a random value within the ASCII 
    respective range.
    """
    current_string_length = 0
    random_string = ''
    while(current_string_length < string_length):
        if numeric_only:
            case_type = 1
        elif lower_alpha_only:
            case_type = 2
        elif lower_numeric_only:
            case_type = random.randint(1, 2)
        elif alpha_only:
            case_type = random.randint(2, 3)
        else:
            case_type = random.randint(1, 3)
        if case_type == 1:
            #Digits
            random_string = "%s%s" % (
                random_string, chr(random.randint(48, 57)))
        elif case_type == 2:
            #Lower Alpha
            random_string = "%s%s" % (
                random_string, chr(random.randint(97, 122)))
        else:
            #Upper Alpha
            random_string = "%s%s" % (
                random_string, chr(random.randint(65, 90)))
        current_string_length += 1
    return random_string


