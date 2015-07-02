""" Tests service functions for market app """

import logging

from django.contrib.gis.geos import Polygon, MultiPolygon
from django.contrib.gis.measure import D
from django.test import TestCase
from django.test.client import RequestFactory

from market.models import Site
from market.service import (append_geoms_to_close_sites, 
    check_for_cross_site_redirect, check_for_site_redirect, get_close_sites, 
    get_current_site, get_or_set_market_state_list, strip_market_from_url)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestService(TestCase):
    """
    Tests for service functions of market app.
    """
    
    fixtures = ['test_geolocation']
    
    def setUp(self):
        """
        Tests needs access to the request factory.
        """
        self.factory = RequestFactory()
    
    def test_get_current_site(self):
        """
        Tests the service function get_current_site().
        This test uses the request factory to make requests.
        """
        request = self.factory.get('/')
        site = get_current_site(request)
        # Default site.
        self.assertEqual(site, 
            Site.objects.defer('envelope','geom','point').get(id=1))
        # current_site gets determined once per request, so need a new request:
        request = self.factory.get('/')
        # Middleware would set this in a normal request.
        request.META['site_id'] = 2
        site = get_current_site(request)
        request = self.factory.get('/')
        self.assertEqual(site, Site.objects.defer(
            'envelope','geom','point').get(id=2))
        request.META['site_id'] = 3
        site = get_current_site(request)
        self.assertEqual(site, 
            Site.objects.defer('envelope','geom','point').get(id=3))
    
    def test_cross_site_redirect(self):
        """
        Tests the service function check_for_cross_site_redirect() from default
        site to a local site.
        """
        request = self.factory.get('/')
        request.META['site_id'] = 1
        zip_postal = '12550'
        site, redirect_path, curr_site = check_for_cross_site_redirect(
            request, zip_postal, redirect_path='/foo/')
        LOG.debug('site: %s' % site)
        LOG.debug('redirect_path: %s' % redirect_path)
        self.assertEqual(Site.objects.get(id=2).id, site.id)
        self.assertEqual(curr_site.id, 1)
        self.assertEqual(redirect_path, 
            u'http://testserver/hudson-valley/foo/')

    def test_cross_site_redirect_local(self):
        """
        Tests the service function check_for_cross_site_redirect() from one
        local site to a different local site.
        """
        request = self.factory.get('/triangle/')
        request.META['site_id'] = 3
        zip_postal = '12550'
        site, redirect_path, curr_site = check_for_cross_site_redirect(
            request, zip_postal, redirect_path='/foo/')
        LOG.debug('site: %s' % site)
        LOG.debug('redirect_path: %s' % redirect_path)
        self.assertEqual(Site.objects.get(id=2).id, site.id)
        self.assertEqual(curr_site.id, 3)
        self.assertEqual(redirect_path, 
            u'http://testserver/hudson-valley/foo/')

    def test_cross_site_redirect_none(self):
        """ Test no redirect. """
        request = self.factory.get('/')
        request.META['site_id'] = 1
        zip_postal = '00000'
        site, redirect_path = check_for_cross_site_redirect(
            request, zip_postal, redirect_path='/foo/')[:2]
        LOG.debug('site: %s' % site)
        LOG.debug('redirect_path: %s' % redirect_path)
        self.assertEqual(site, 
            Site.objects.defer('envelope','geom','point').get(id=1))
        self.assertEqual(redirect_path, '/foo/')  
    
    def test_get_close_sites(self):
        """ Test a zip within 100 miles of a market have a site for and one we 
        do not.
        """
        site2 = Site.objects.get(id=2)
        site2.save()
        zip1 = '00077' # Puerto Rico.
        neighboring_markets = get_close_sites(zip1, 100)
        self.assertEqual(neighboring_markets, None)
        zip2 = '12601' # Poughkeepsie.
        neighboring_markets = get_close_sites(zip2, 100)
        self.assertTrue(neighboring_markets.count() >= 1)
        self.assertTrue(neighboring_markets.count() <= 5)
    
    def test_geoms_w_close_sites(self):
        """ Test append_geoms_to_close_sites service function that adds a site's
        geom to the list of close sites (not all places use the geometry and
        it is too big to store in the same cache key (list of 5 site geoms).
        """
        site = Site.objects.get(id=2)
        close_sites = append_geoms_to_close_sites(site.get_or_set_close_sites())
        try:
            self.assertTrue(type(close_sites[0]['geom']) in
                (Polygon, MultiPolygon))
            self.assertEqual(type(close_sites[0]['id']), int)
            close_site = Site.objects.get(id=int(close_sites[0]['id']))
            self.assertEqual(close_sites[0]['name'], close_site.name)
            self.assertEqual(close_sites[0]['directory_name'],
                close_site.directory_name)
            self.assertEqual(close_sites[0]['domain'], close_site.domain)
            self.assertEqual(
                close_sites[0]['default_state_province__abbreviation'], 
                close_site.default_state_province.abbreviation)
            self.assertEqual(type(close_sites[0]['distance']), D)
        except KeyError:
            self.fail('Close_sites not built properly.')
        
    def test_check_for_site_redirect(self):
        """
        Tests the service function check_for_site_redirect() for duplicate
        market name in URL.
        """
        request = self.factory.get('/')
        request.META['site_id'] = 1
        test_path = check_for_site_redirect(request, site_id=2, 
                redirect_path="/hudson-valley/advertiser/")[1]
        if 'hudson-valley/hudson-valley/' in test_path:
            self.fail('Market name not scrubbed properly.')
        request.META['site_id'] = 2
        # Check if site 1 submitted.
        test_path = check_for_site_redirect(request, site_id=1, 
                redirect_path="/hudson-valley/advertiser/")[1]
        if '/hudson-valley/hudson-valley/' in test_path:
            self.fail('Market name not scrubbed properly.')

    def test_get_market_state_list(self):
        """ 
        Test get_or_set_market_state_list returns a dict of states identifying
        each market within.
        """
        state_list = get_or_set_market_state_list()
        state_set = set([])
        for site in Site.objects.all(): 
            state = site.get_abbreviated_state_province()
            if state:
                state_set.add(state)      
        self.assertEqual(len(state_set), len(state_list))
        for index, state in enumerate(state_list):
            if (state['state'] == 'New York'):
                ny_index = index
                break
        self.assertEqual(state_list[ny_index]['state_url'], 'new-york')
        self.assertEqual(state_list[ny_index]['market'][0]['domain'], 
            '10CapitalAreaCoupons.com')
        self.assertEqual(state_list[ny_index]['market'][1]['domain'], 
            '10HudsonValleyCoupons.com')
        self.assertEqual(state_list[ny_index]['market'][1]['directory_name'], 
            'hudson-valley')
    
    def test_strip_url_w_market(self):
        """ Assert that the market is stripped from the url and in correct
        format.
        """ 
        test_url = '/hudson-valley/immus/palatus/immaculus/'
        stripped_url = strip_market_from_url(test_url)
        self.assertEqual(stripped_url, 'immus/palatus/immaculus/')
        # Test without leading and trailing slashes:
        test_url = 'hudson-valley/immus/palatus/immaculus'
        stripped_url = strip_market_from_url(test_url)
        self.assertEqual(stripped_url, 'immus/palatus/immaculus/')

    def test_strip_url_no_market(self):
        """ Assert that the original url is returned when the first directory is
        not a market.
        """ 
        test_url = '/gamma/beta/phi/'
        stripped_url = strip_market_from_url(test_url)
        self.assertEqual(stripped_url, 'gamma/beta/phi/')
        # Test without leading and trailing slashes:
        test_url = 'gamma/beta/phi'
        stripped_url = strip_market_from_url(test_url)
        self.assertEqual(stripped_url, 'gamma/beta/phi')