""" Service class for handling QR Images for common app of project ten. """
import logging
import pycurl
import os

from django.conf import settings

from gargoyle.decorators import switch_is_active

from common.utils import CurlBuffer

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)


class QRImageCache(object):
    """ Class for handling methods to retrieve QR Code from google or storing 
    our own local copy. """
    
    def __init__(self):
        """ Set test_mode and instantiate file_path. """
        self.file_path = None
        self.site_directory = ''
    
    @switch_is_active('replicated-website')
    def get_ad_rep_qr_code(self, url, site_directory=None):
        """ Get QR code for ad rep's url (stored in ad_rep subdirectory). """
        if url:
            self.file_path = "ad_rep/%s" % url.lower()
        return self.get_qr_code(url, site_directory)

    def get_qr_code(self, url, site_directory=None):
        """ Return path to qr image for this URL. """
        if not url:
            self.url = ''
            url = '_default_domain'
        else:
            self.url = url.lower()
        if site_directory:
            self.site_directory = '%s/' % site_directory
        self.file_path = "QR/%s%s.gif" % \
            (self.site_directory, (self.file_path or url))
        if not self._check_file_exists():
            self._cache_qr_code()
        return "dynamic/images/%s" % self.file_path
    
    def _check_file_exists(self):
        """ Check if file exists, return Boolean. """
        if os.path.exists(
            "%s/media/dynamic/images/%s" % 
            (settings.PROJECT_PATH, self.file_path)):
            return True
        else:
            test_path = ''
            for _dir in self.file_path.split('/')[:-1]:
                test_path += "/%s" % _dir
                # Make sure site-directory folder exists.
                directory_path = os.path.dirname("%s/media/dynamic/images%s/"
                ) % (settings.PROJECT_PATH, test_path)
                if not os.path.exists(directory_path):
                    os.makedirs(directory_path, 0775)
                    os.chmod(directory_path, 0775)
            return False
    
    def _cache_qr_code(self):
        """ Retrieve QR Code from google chart api and cache it. """
        url = str('http://chart.apis.google.com/chart?chs=225x225&cht=%s%s%s' %
            ('qr&chld=M|2&chl=http://10coupons.com/', 
            self.site_directory, self.url)) 
        curl_buffer = CurlBuffer()
        curl = pycurl.Curl()
        curl.setopt(curl.WRITEFUNCTION, curl_buffer.body_callback)
        curl.setopt(curl.URL, url)
        curl.perform() 
        if curl.getinfo(curl.HTTP_CODE) != 200:
            LOG.error('QrImageCache.retrieve_qr_code failed with %s' 
                % curl.getinfo(curl.HTTP_CODE))
            self.file_path = None
        else:
            LOG.debug('QrImageCache.retrieve_qr_code successful')
            image = open("%s/media/dynamic/images/%s" % 
                (settings.PROJECT_PATH, self.file_path), "w")
            image.write(curl_buffer.content.rstrip())
        curl.close()
        return True
