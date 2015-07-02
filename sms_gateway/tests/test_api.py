""" Tests of sms_gateway. Tests of EZTexting API. """

import pycurl

from django.test import TestCase


class TestApi(TestCase):
    """ All tests of sms_gateway for EzTexting API. """
        
    def test_api_reachable(self):
        """ Test to see if EzTexting API is reachable. """
        curl = pycurl.Curl()
        curl.setopt(curl.URL, 
            'http://api.eztexting.com/SMSSend?user=foo&pass=bar&smsfrom=71010&smsto=8455181898&note=foo&subaccount=bar')
        # curl.setopt(curl.VERBOSE, 1) 
        curl.perform()
        self.assertEquals(curl.getinfo(curl.HTTP_CODE), 403)
        self.assertEquals(
            curl.getinfo(curl.CONTENT_TYPE), 
            'text/plain;charset=US-ASCII'
            )
        # Their SSL cert is invalid
        curl.setopt(curl.URL, 
            'https://sms.mxtelecom.com/SMSSend?user=foo&pass=bar&smsfrom=71010&smsto=8455181898&note=foo&subaccount=bar')
        # curl.setopt(curl.VERBOSE, 1) 
        curl.perform()
        self.assertEquals(curl.getinfo(curl.HTTP_CODE), 403)                
        curl.close()
