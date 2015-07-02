""" Tests models of market app """

import os

from django.conf import settings
from django.contrib.gis.geos import Polygon, MultiPolygon
from django.db import connection, IntegrityError, transaction
from django.test import TestCase, TransactionTestCase
from django.test.client import RequestFactory

from geolocation.models import USCounty, USZip
from market.models import Site, TwitterAccount
from market.service import get_current_site


class TestSiteModel(TestCase):
    """ Test case for for Site model of market app. """
    
    fixtures = ['test_geolocation', 'test_orange_geom']

    def setUp(self):
        """ Tests needs access to the request factory. """
        self.factory = RequestFactory()
        
    def test_get_name_no_spaces(self):
        """ Test model method get_name_no_spaces. """
        # Assert site with no spaces in name returns properly.
        local_site = Site.objects.get(id=1)
        self.assertEqual(local_site.get_name_no_spaces(), 'local')
        # Assert site with spaces in name returns properly.
        hv_site = Site.objects.get(id=2)
        self.assertEqual(hv_site.get_name_no_spaces(), 'HudsonValley')

    def test_save_site(self):
        """ Assert that a minimal site can be saved with default values. """
        site = Site()
        site.name = 'foo'
        site.save()
        self.assertEqual(site.phase, 1)
        self.assertEqual(site.base_rate, 0)
        self.assertEqual(site.media_partner_allotment, 0)
        path = '%s/urls_local/urls_%s.py' % (settings.PROJECT_PATH, site.id)
        os.remove(path)
        site.delete()
        
    def test_save_hv(self):
        """ Assert a site can be updated. Tests coord generation since this has
        a county with geometry data.
        """
        site = Site.objects.get(id=2)
        self.assertEqual(site.coordinate_id, None)
        site.save()
        site = Site.objects.get(id=2)
        self.assertTrue(site.coordinate_id)
        
    def test_get_sites_this_zip(self):
        """ Tests a method of the site model manager, get_sites_this_zip(code).
        """
        # Check if zip 12550 belongs to site 2.
        site = Site.objects.get(id=2)
        sites = Site.objects.get_sites_this_zip('12550')
        self.assertTrue(site in sites)
        
    def test_site_default_state(self):
        """ Test method that retrieves the abbreviated default state for a given
        site, blank if not found (like local site 1). 
        """
        request = self.factory.get('/')
        request.META['site_id'] = 2
        test_site_hv = get_current_site(request)
        self.assertEqual(test_site_hv.get_abbreviated_state_province(), "NY")
        # current_site gets determined once per request, so need a new request:
        request = self.factory.get('/')
        request.META['site_id'] = 1
        test_site_local = get_current_site(request)
        self.assertEqual(test_site_local.get_abbreviated_state_province(), "")
    
    def test_geom_in_market(self):
        """  Test method that returns True/False based on evaluation of whether
        a given geometry exists inside a market.
        """
        # Test zip inside market.
        inside_zip = USZip.objects.get(code='12589')
        site = Site.objects.get(id=2)
        self.assertTrue(site.is_geom_in_market(inside_zip.geom))
        # Test county inside market.
        inside_county = USCounty.objects.get(name='Orange', id=1866)
        self.assertTrue(site.is_geom_in_market(inside_county.geom))
        # Test zip outside market.
        site = Site.objects.get(id=3)
        self.assertTrue(not site.is_geom_in_market(inside_zip.geom))
        # Test county outside market.
        self.assertTrue(not site.is_geom_in_market(inside_county.geom))
        # Test zip with no geom (not all zips have geoms).
        geomless_zip = USZip.objects.get(code='00927')
        self.assertTrue(not site.is_geom_in_market(geomless_zip.geom))
        
    def test_get_or_set_geom(self):
        """ Assert get_or_set_geom method always returns geom. """
        site = Site.objects.get(id=2)
        geom = site.get_or_set_geom()
        self.assertTrue(type(geom) in (Polygon, MultiPolygon))

    def test_state_division_type(self):
        """ Tests model USState method get_municipality_division. """
        sites = Site.objects.filter(id__in=(1, 2))
        for site in sites:
            if site.default_state_province:
                self.assertTrue(site.get_state_division_type())
            else:
                self.assertFalse(site.get_state_division_type())

class TestSiteConsumerCount(TestCase):
    """ Test site consumer count method. """
    
    fixtures = ['test_advertiser', 'test_consumer']
    
    def test_site_consumer_count(self):
        """ Test get_or_set cache consumer site count method to ensure it is
        getting the correct consumer count.
        """
        site2 = Site.objects.get(id=2)
        cursor = connection.cursor()
        cursor.execute("""
            SELECT count(*)
            FROM consumer_consumer c
            INNER JOIN consumer_consumer_email_subscription e
            ON c.user_ptr_id = e.consumer_id
            WHERE c.site_id=%s
            AND c.is_emailable=True
            AND e.emailsubscription_id=1""", [site2.id])
        self.assertEqual(cursor.fetchall()[0][0],
            site2.get_or_set_consumer_count())


class TestTwitterAccountModel(TransactionTestCase):
    """ Test case for Twitter Account model """
    fixtures = ['test_twitter_account']
    
    def test_twitter_account_dup_site(self):
        """ Test method that saves the twitter_name for this duped site """
        twitter_account = TwitterAccount.objects.get(id=3)
        twitter_account.site = Site.objects.get(id=2)
        try:
            twitter_account.save()
            self.assertTrue(False)
        except IntegrityError:
            transaction.rollback()
            self.assertTrue(True)
            
    def test_twitter_account_edit_name(self):
        """ Test method that saves the twitter_name for this new site """
        twitter_name = "testtwitter"
        site = Site.objects.get(id=4)
        twitter_account = TwitterAccount.objects.get(site=site)
        twitter_account.site = site
        twitter_account.twitter_name = twitter_name
        twitter_account.save()
        twitter_account2 = TwitterAccount(twitter_name=twitter_name)
        self.assertEqual(twitter_account2.twitter_name, twitter_name)
