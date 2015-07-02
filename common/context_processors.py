"""
A set of request processors specific to the 'ten' application.

Those that need to be universally available need to be referenced 
from the setting TEMPLATE_CONTEXT_PROCESSORS
"""
#pylint: disable=W0104,W0613
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse

from consumer.service import get_consumer_instance_type
from ecommerce.models import Product
from market.models import Site
from market.service import get_current_site

def current_site(request):
    """ A context processor that provides the various datapoints associated
    with the current site. Needs request.META['site_id'] which is set
    by market.middleware.URLHandlerMiddleware.
    """
    site = get_current_site(request)
    try:
        site.name_no_spaces = site.get_name_no_spaces()
    except AttributeError:
        pass
    return {'current_site': site}

def current_session(request):
    """ Checks to see if a user is logged in.  Used primarily in the header to 
    switch the 'Sign In/Sign Out' links.
    """
    try:
        this_consumer = request.session['consumer']
        email = this_consumer['email']
        user_type, is_ad_rep = get_consumer_instance_type(email)
        firestorm_URL = reverse('firestorm-virtual-office')
    except KeyError:
        email = ''
        user_type = ''
        is_ad_rep = None
        firestorm_URL = None
    return {'is_logged_in': email, 'user_type': user_type, 
        'is_ad_rep': is_ad_rep, 'firestorm_URL': firestorm_URL}

def current_url_no_subdomain(request):
    """ A context processor that returns the URL of the current page without the
    subdomain. This is used for the link that lets you leave the mobile version
    of the site and go to the non-mobile version.
    """
    request_protocol = 'http'
    # nginx as reverse proxy will set this on a secure request:
    if request.META.get('HTTP_X_FORWARDED_PROTO', False) == 'https' \
    or request.is_secure():
        request_protocol = 'https'
    host = request.get_host().split('.')
    if len(host) > 2:
        host = host[1:]
    host = '.'.join(host)
    return {'current_url_no_subdomain': '%s://%s%s' % (
        request_protocol, host, request.META['PATH_INFO'])}

def products(request):
    """ A context processor that provides the dictionary of Products. """
    products_ = list(Product.objects.order_by('id'))
    return {
        'flyer_placement': products_[0],
        'monthly_coupon_display': products_[1],
        'annual_coupon_display': products_[2]
    }

def page_locale(request):
    """ A context processor that provides the various datapoints associated
    with the current site.
    """
    try:
        page_locale_var = request.META['page_locale']
    except KeyError:
        page_locale_var = 'en-us'    
    return {
        'page_locale': page_locale_var,
    }

def site_cache(request):
    """ A context processor that provides a dictionary of all the sites,
    and all the data points that describe each site.
    """
    site_cache_dict = Site.objects.get_or_set_cache().values()
    return {
        'site_cache': site_cache_dict,
    }

def safe_urls(request):
    """ Return versions of STATIC_URL and MEDIA_URL that use the same protocol
    as request. Return request_protocol, for prefixing 3rd party resources like
    jquery in the same protocol as the request.
    """
    safe_static_url = settings.STATIC_URL
    safe_media_url = settings.MEDIA_URL
    request_protocol = 'http'
    # nginx as reverse proxy will set this on a secure request:
    if request.META.get('HTTP_X_FORWARDED_PROTO', False) == 'https' \
    or request.is_secure():
        request_protocol = 'https'
        safe_static_url = urlparse.urlunparse(
            ['https'] + list(urlparse.urlparse(safe_static_url)[1:]))
        safe_media_url = urlparse.urlunparse(
            ['https'] + list(urlparse.urlparse(safe_media_url)[1:]))
    return {
        'request_protocol': request_protocol,
        'safe_static_url': safe_static_url,
        'safe_media_url': safe_media_url
    }