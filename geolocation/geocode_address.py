""" GeocodeLocation class methods for Geolocation app. """
from decimal import Decimal
import logging
import pycurl

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import simplejson
from django.utils.http import urlquote

from common.utils import CurlBuffer

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class GeocodeLocation(object):
    """ Retrieve latitude/longitude coordinate for an address.
    Production uses Google's geocoding service.
    Test mode uses Open Street Maps' geocoding service.
    Option (for performance boost) to allow Jenkins to return static location.
    """
    coord = None
    static_coord = (Decimal('-73.784709'), Decimal('41.138069')) # Lon, Lat.

    def _execute_curl(self):
        """ Use curl to submit request to geocoder service. """
        self.curl_buffer = CurlBuffer()
        self.curl = pycurl.Curl()
        self.curl.setopt(self.curl.VERBOSE, 0) 
        self.curl.setopt(self.curl.WRITEFUNCTION,
            self.curl_buffer.body_callback)
        self.curl.setopt(self.curl.URL, self.url)
        self.curl.perform()

    def _google_service(self, address):
        """ Use google API to retrieve lat/long coords for this address. """
        query_string = '?sensor=false&address=%s' % urlquote(address)
        # Url can't be Unicode.
        self.url = str('http://maps.googleapis.com/maps/api/geocode/json%s' % 
            query_string)
        self._execute_curl()
        json_results = self._parse_curl_results('googleapis')
        
        if json_results and json_results['status'] == 'OK':
            self.coord = (
                Decimal(repr(json_results['results'][0]['geometry']\
                    ['location']['lng'])),
                Decimal(repr(json_results['results'][0]['geometry']\
                    ['location']['lat'])))
        else:
            if json_results and json_results['status'] == 'OVER_QUERY_LIMIT':
                err_msg = "602: Google's geocoder is over query limit."
                LOG.error(err_msg)
                raise ValidationError(err_msg)
        self.curl.close()
        return self.coord
    
    def _osm_service(self, address):
        """ Use Open Street Map Nominatim API to retrieve latitude/longitude
        coords for this address. Append email address so they can contact us
        should we begin to exceed the limits they are agreeable to.

        *** This is our backup geocoder, primarily used for tests. ***
        (Not as accurate as google's and queries take longer to retrieve).
        """
        address = address.replace(' ', '+')
        query_string = '?format=json&limit=1&email=%s&q=%s'% (
            settings.GEOCODER_AGENT, address)
        # Url can't be Unicode.
        self.url = str('http://nominatim.openstreetmap.org/search%s' 
            % query_string)
        self._execute_curl()
        json_results = self._parse_curl_results('openstreetmap')
        if json_results and len(json_results) > 0:
            self.coord = (json_results[0]['lon'], json_results[0]['lat'])
        self.curl.close()
        return self.coord
    
    def _parse_curl_results(self, method):
        """ Check return status code and parse returned results into json
        format.
        """
        if self.curl.getinfo(self.curl.HTTP_CODE) != 200:
            LOG.error('%s api returned bad status code %s'
                % (method, self.curl.getinfo(self.curl.HTTP_CODE)))
        else:
            LOG.debug('%s received valid response. content: %s' 
                % (method, self.curl_buffer.content))
            return simplejson.loads(self.curl_buffer.content.rstrip())
        return False

    def get_coordinate(self, location):
        """ Execute the appropriate geocode service method based on TEST_MODE in 
        config. 
        """
        address = location.geo_purge()
        if address is None:
            return None
        if settings.ENVIRONMENT['environment'] == 'prod' \
            or not settings.ENVIRONMENT['is_test'] \
            or settings.ENVIRONMENT.get('use_geo_method') == 'gg':
            return self._google_service(address)
        else:
            use_method = settings.ENVIRONMENT.get('use_geo_method', 'static')
            if use_method == 'static':
                return self.static_coord
            elif use_method == 'osm':
                LOG.warning('GEOCODER is in TEST_MODE! using OpenStreetMaps!!')
                return self._osm_service(address)
            else:
                return self._google_service(address)
    
GEOCODE_LOCATION = GeocodeLocation()
