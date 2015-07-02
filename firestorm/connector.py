""" Provides the interface between ten and the remote Firestorm system. """
import base64
import binascii
import hashlib
import logging
from netaddr import all_matching_cidrs
import pycurl
import urllib

from django.http import Http404

from common.utils import CurlBuffer
from firestorm import FIRESTORM_BASE_URL, FIRESTORM_REPL_WEBSITE_API
from firestorm.models import AdRep, AdRepWebGreeting
from firestorm.tasks.create_or_update_ad_rep import CREATE_OR_UPDATE_AD_REP

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class FirestormConnector(object):
    """ Provides the interface to and from the remote Firestorm service."""
    repl_website_API = FIRESTORM_REPL_WEBSITE_API
    dealer_API = '%swebservices/firestormdealer.asmx' % FIRESTORM_BASE_URL
    auth_login_URL = '%sFirestormAuthenticatedLogin.aspx' % repl_website_API
    account_URL_suffix = "MembersAreaHome.aspx"
    reset_password_URL = "https://%sForgotPassword.aspx" % repl_website_API
    
    # These IPs are allowed to access our Firestorm data feeds:
    # Loopback IP:
    allowed_IPs = ['127.0.0.1']
    # Office private range and public range:
    allowed_cidr_blocks = ['192.168.88.0/24', '173.220.217.192/29']
    # Firestorm production IPs:
    allowed_IPs.extend(['67.108.141.130', '67.108.141.136',
        '67.108.141.144', '67.108.141.166'])

    def check_allowed_ip(self, request):
        """ Raise a 404 if this request is not from an allowed IP. """
        if request.META['REMOTE_ADDR'] in self.allowed_IPs:
            return
        if bool(len(all_matching_cidrs(request.META['REMOTE_ADDR'],
                self.allowed_cidr_blocks))):
            return
        raise Http404

    def get_replicated_website_details(self, ad_rep_url):
        """ Request replicated website details for this _ad_rep_url and return
        them as a list.
        """
        api_url = str('http://%s/Utils/GetReplicatedDetails.aspx?DealerURL=%s' %
                  (self.repl_website_API, ad_rep_url))
        LOG.debug(api_url)
        curl_buffer = CurlBuffer()
        curl = pycurl.Curl()
        curl.setopt(curl.WRITEFUNCTION, curl_buffer.body_callback)
        curl.setopt(curl.FOLLOWLOCATION, 1)
        curl.setopt(curl.URL, api_url)
        curl.perform()
        return curl_buffer.content.split('|')

    def parse_replicated_details(self, ad_rep_url):
        """ Go to ad rep url and get replicated details. Parse the details
        into the ad rep model and return it plus the ad_rep_dict.
        """
        repl_website_details = self.get_replicated_website_details(ad_rep_url)
        LOG.debug('repl_website_details: %s' % repl_website_details)
        if repl_website_details[0] != 'Success':
            if repl_website_details[0] != 'Not Found':
                LOG.error('Firestorm returned "%s"' % repl_website_details[0])
            raise Http404
        # Covert the response from pipe delimited string to dict. This
        # dict will be passed to a celery create or update task.
        ad_rep_dict = {'url': ad_rep_url}
        # Also, create an AdRep instance that does not get saved here, but is
        # set into the session for use by
        # firestorm.context_processor.referring_ad_rep().
        ad_rep = AdRep(url=ad_rep_url)
        # Firestorm names for these variables:
        # STATUS|DEALERID|FIRSTNAME|LASTNAME|COMPANY|HPHONE|WPHONE|EMAIL|
        # WEBGREETING|RANK|IS_CUSTOMER
        for index, field in enumerate(['status', 'firestorm_id', 'first_name',
                'last_name', 'company', 'home_phone_number',
                'primary_phone_number', 'email', 'web_greeting', 'rank']):
            ad_rep_dict[field] = repl_website_details[index]
            setattr(ad_rep, field, repl_website_details[index])
            LOG.debug('%s: %s' % (field, repl_website_details[index]))
        return ad_rep_dict, ad_rep

    @staticmethod
    def call_update_task(ad_rep_dict):
        """ Update the ad_rep details. Born to be skipped by MockConnector. """
        CREATE_OR_UPDATE_AD_REP.delay(ad_rep_dict)

    @staticmethod
    def get_ad_rep_or_404(request, ad_rep_url):
        """ Set referring_ad_rep into session and return a dict of ad rep data
        sourced from Firestorm, or a 404 response.

        In the session, 'referring_ad_rep' is an ad_rep.firestorm_id.
        'ad_rep_dict' is passed to a celery task which creates or updates an
        ad_rep instance and an ad_rep_web_greeting instance. 'ad_rep_dict' is
        also stored in session as 'referring_ad_rep_dict' for use by the
        firestorm.context_processors.referring_ad_rep().
        """
        try:
            str(ad_rep_url)
        except UnicodeEncodeError:
            raise Http404
        try:
            ad_rep = AdRep.objects.get(url__iexact=ad_rep_url)
        except AdRep.DoesNotExist:
            raise Http404
        try:
            web_greeting = ad_rep.ad_rep_web_greeting.web_greeting
        except AdRepWebGreeting.DoesNotExist:
            web_greeting = ''
        ad_rep_dict = {
            'first_name': ad_rep.first_name,
            'last_name': ad_rep.last_name,
            'company': ad_rep.company,
            'home_phone_number': ad_rep.home_phone_number,
            'primary_phone_number': ad_rep.primary_phone_number,
            'email': ad_rep.email,
            'web_greeting': web_greeting
            }
        # Add referring_ad_rep to session.
        request.session['referring_ad_rep'] = None
        request.session['ad_rep_id'] = ad_rep.id
        return ad_rep_dict

    def login_ad_rep(self, request, ad_rep, password=''):
        """ Login the ad_rep to the Firestorm back office. """
        _secret_key = 'vieko4fo3zouchiust6e8leqie38i9z4'
        _string = '%s%s%s' % (ad_rep.firestorm_id, password, _secret_key)
        _string = _string.encode('utf_16_le')
        _md5_hash = binascii.unhexlify(hashlib.md5(_string).hexdigest())
        _hash = base64.b64encode(_md5_hash)
        _url_encode = urllib.quote(_hash)
        path = 'https://%s?DealerID=%s&SecurityToken=%s' % (
            self.auth_login_URL, ad_rep.firestorm_id, _url_encode)
        
        request.session['referring_ad_rep'] = ad_rep.firestorm_id
        request.session['referring_ad_rep_dict'] = ad_rep
        return path
    
    def load_virtual_office_home(self, request):
        """ Go to virtual office home page, used as Virtual Office link. """
        # Ensure session has not been hijacked, check browser and ip against
        # stored credentials to ensure they match.
        if request.META.get('REMOTE_ADDR', None) == \
        request.session.get('referrer_IP', None) \
        and request.META.get('HTTP_USER_AGENT', None) == \
        request.session.get('referrer_browser', None):
            _firestorm_session = '(S(%s))/' % \
                request.session.get('firestorm_session_key', '')
        else:
            _firestorm_session = ''
        path = 'https://%s%s%s' % (self.repl_website_API,
            _firestorm_session, self.account_URL_suffix)
        return path