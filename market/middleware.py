""" Middleware logic for market app. """
import copy
import datetime
import logging
import re

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponsePermanentRedirect

from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class URLHandlerMiddleware(object):
    """Handles redirecting local domains to 10coupons.com subdirectory

    Local domain names are in the pattern 10{market}coupons.com OR
    ten{market}coupons.com.
    Local domain names are unique.

    Redirect will be be to
    10coupons.com/{market}/{extra_path_info_if_needed}

    For supported L10n and i18n pages, redirects will be to
    10coupons.com/{xx-yy}/{local}/{extra_path_info_if_needed}
    or
    10coupons.com/{xx}/{local}/{extra_path_info_if_needed}
    where xx equals language code and yy equals country code
    language codes: http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    country codes http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
    Responses on site.id != 1 (10coupons sites for a given market) will maintain
    a cookie "stamp" of the last market rendered.
    """
    def __init__(self):
        self.unified_host = '10coupons.com'

        # Variations of settings.HTTP_HOST that we know.
        self.unified_host_aliases = ['10localcoupons.com', '10static.com']

        self.mobile_subdomains = ['m', 'm-local', 'm-dev', 'm-local-shawn']

        self.other_allowed_subdomains = ['dev', 'dev2', 'devweb02', 'demo',
            'hsdemo', 'hs1', 'hs2', 'hs3', 'lb', 'lb-dev', 'local', 'staging',
            'test']

        # List of supported internationalization/localization customizations.
        # DO NOT add 'en-us' which, as the default, is not a customization!
        # Items must be in the form 'xx' or 'xx-yy',
        # where xx equals language code and yy equals country code.
        # Ex: language codes:
        #   http://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
        # Ex: country codes http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
        # Items should this test:
        # len(var) == 2 | re.match('^[a-z]{2}-[a-z]{2}$', var)

        # Supported Internationalizations (il8n). Really we don't support any
        # yet except for here in market.middleware.
        self.supported_i18n = ['sp-us',]

        # Initialize "flags" (ok, some of these are not booleans...):
        self.flags = {
            'site_id': 1, # Unless proven otherwise, assume main site.
            'redirect_flag': 0, # Set flag to do ResponseRedirect?
            'i18n_flag': 0, # Does path contain i18n data?
            'local_dir_site_id': 0, # Which local dir (if any) is in the path?
            'subdomain_flag': 0,
            'is_mobile': 0, # Serve the mobile version of the web site.
            }

    def subdomain_checker(self, request, host, split_host):
        """ Trim subdomain from host unless its configured as allowed. """
        if len(split_host) > 2:
            LOG.debug('split_host[-3]: %s' % split_host[-3])
            if split_host[-3] in self.mobile_subdomains or (
                    split_host[-3] in self.other_allowed_subdomains):
                request.flags['subdomain_flag'] = 1
                if split_host[-3] in self.mobile_subdomains:
                    request.flags['is_mobile'] = 1
                if len(split_host) > 3:
                    request.flags['redirect_flag'] = 1
            else:
                request.flags['redirect_flag'] = 1
            host[0] = '.'.join(split_host[-2:])
        return host

    def redirect_checker(self, request, host, path_info):
        """ If the domain name is NOT the unified name, configure redirect. """
        # Example paths: '/', '/reno/', '/reno/sales/', '/sales/'
        # Leading and trailing slashes create empty nodes, so remove them.
        path_list = path_info.split('/')
        for node in path_list:
            if node == '':
                path_list.remove(node)
        if len(path_list) > 0:
            # Check to see if first dir is i18n data.
            dir_to_check = 0
            if path_list[0] in self.supported_i18n:
                dir_to_check = 1
                request.flags['i18n_flag'] = 1
                # This will be used by the template:
                request.META['page_locale'] = path_list[0]
            # Check relevant dir to see if it is a valid local directory_name.
            # Ex: 'hudson-valley', 'reno'
            try:
                this_site = Site.objects.get_or_set_cache().values('id',
                    'id').get(directory_name__iexact=path_list[dir_to_check])
                request.flags['local_dir_site_id'] = this_site['id']
            except (IndexError, ObjectDoesNotExist):
                # The directory is not a valid local site dir.
                # They are on the 10coupons.com corp site.
                # or deep in a local site: 10renocoupons.com/sales/hello/
                # or their only path is i18n: 10hudsonvalleycoupons.com/sp-us/
                pass
        if host[0] != self.unified_host.lower():
            # Check normalized host againt site cache.
            request.flags['redirect_flag'] = 1
            try:
                this_site = Site.objects.get_or_set_cache().values('id',
                    'directory_name').get(domain__iexact=host[0])
                request.flags['site_id'] = this_site['id']
                if request.flags[
                        'local_dir_site_id'] == request.flags['site_id']:
                    # This case like 10hudsonvalleycoupons.com/hudson-valley/.
                    # Skip the insertion logic.
                    pass
                else:
                    insert_at = 0
                    if request.flags['local_dir_site_id'] > 0:
                        # This is conflicting input.
                        # Ex: http://www.10hudsonvalleycoupons.com/reno/.
                        # Give precedence to domain name.
                        del path_list[dir_to_check]
                        request.flags['local_dir_site_id'] = 0
                    if request.flags['i18n_flag']:
                        insert_at = 1
                    path_list.insert(insert_at, this_site['directory_name'])
            except ObjectDoesNotExist:
                # Not unified domain and not valid local domain...
                # Case: local site not launched yet?
                # 10localcoupons.com and strausmedia.com etc will also end up
                # here if pointed to this server.
                request.flags['site_id'] = 1
        elif request.flags['local_dir_site_id'] > 0:
            # For a url like 10coupons.com/hudson-valley.
            request.flags['site_id'] = request.flags['local_dir_site_id']
        LOG.debug('redirect_flag: %s' % request.flags['redirect_flag'])

        #if request.META['HTTP_USER_AGENT'] == 'ELB-HealthChecker/1.0':
        #    request.flags['site_id'] = 29
        #    request.flags['redirect_flag'] = 0

        return path_list

    def process_request(self, request):
        """
        If the request host is the self.unified_host then, based on domain name
        and path, set request.site_id that has all the settings for the current
        site.

        If the request host is a local site, redirect to the appropriate
        subdirectory of self.unified_host.

        www subdomain redirects to no subdomain.

        Because we want to do string manipulation with 'host', it will be a
        (mutable) list of one item.
        """
        request.flags = copy.deepcopy(self.flags)
        # Get the domain name of the current request, as a (mutable) list.
        host = [request.get_host()]
        path_info = request.META['PATH_INFO']
        split_host = host[0].split('.')
        LOG.debug(split_host)
        host = self.subdomain_checker(request, host, split_host)
        #if request.META['HTTP_USER_AGENT'] == 'ELB-HealthChecker/1.0':
        #    host[0] = "10couon.com"
        #    request.META['site_id'] = 29
        #    request.urlconf = 'urls_local.urls_29' 
        #    return
        # Trim port from host if necessary (ex: when running dev on :8000).
        if request.META['SERVER_PORT'] not in ['80', '443']:
            match_parts = re.match('^(.*):.*$', host[0])
            try:
                host[0] = match_parts.group(1)
            except IndexError:
                pass
        # Convert domain names beginning with 'ten' to '10'.
        if str(host[0])[:3] == 'ten':
            # Might now be 10local or 10reno etc.
            host[0] = '10' + str(host[0])[3:] 
            request.flags['redirect_flag'] = 1
        # Normalize unified_host_aliases to unified host.
        if host[0] in self.unified_host_aliases:
            host[0] = self.unified_host
            request.flags['redirect_flag'] = 1
        path_list = self.redirect_checker(request, host, path_info)
        if request.flags['redirect_flag'] == 1:
            LOG.debug('subdomain_flag: %s' % request.flags['subdomain_flag'])
            final_host = self.unified_host
            protocol = 'http://'
            final_dir = '/' + '/'.join(path_list) + '/'
            if request.flags['subdomain_flag']:
                final_host = split_host[-3] + '.' + self.unified_host
            if path_list[0] == '':
                final_dir = '/'
            if request.is_secure():
                protocol = 'https://'
            full_url = '%s%s%s' % (protocol, final_host, final_dir)
            LOG.debug('full_url: %s' % full_url)     
            return HttpResponsePermanentRedirect(full_url)
        else:
            request.META['site_id'] = request.flags['site_id']
            request.urlconf = 'urls_local.urls_%s' % request.flags['site_id']
            return

    @classmethod
    def process_response(cls, request, response):
        """ 
        Store market's site ID in a persistent cookie so we can perform 
        redirects from local site (1) to a marketed site page if we can find it 
        in the cookie "stamp." (The cookie is named stamp to be vague enough for
        ill-willed people to know what it pertains to and loose enough for use 
        if we want to add data to it later. Everytime a new market is rendered, 
        the cookie is stamped to their browser).
        A preliminary check is performed to make sure the request object has a 
        META tag and site_id because in local dev environments multiple
        responses are sent for a given request (for js, images etc). 
        If the current site is not equal to the site in the cookie, this method 
        will update the cookie with the new site id so that the cookie always 
        holds the last site ID visited.
        """
        if getattr(request, 'META', None) \
        and request.META.has_key('site_id') and request.META['site_id'] > 1:
            # Add cookie if it doesn't exist or it exists for another site.
            try:
                if not request.COOKIES.has_key('stamp') \
                or request.session.decode(
                        request.COOKIES['stamp']) != request.META['site_id']:
                    expires = datetime.datetime.strftime(
                        datetime.datetime.utcnow() + \
                        datetime.timedelta(seconds=(365*24*60*60)),
                                "%a, %d-%b-%Y %H:%M:%S GMT")
                    response.set_cookie(key='stamp', 
                        value=request.session.encode(request.META['site_id']),
                        expires=expires)
            except (AttributeError, KeyError):
                pass
        return response
