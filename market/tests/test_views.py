""" Tests for views of consumer app. """
from django.core.urlresolvers import reverse

from common.test_utils import EnhancedTestCase
from geolocation.models import USZip
from market.models import Site

class TestViews(EnhancedTestCase):
    """ Test cases for consumer views. """
    fixtures = ['test_geolocation']
    urls = 'urls_local.urls_2'
    
    def test_get_site_zip_geoms(self):
        """ Assert zip data for this market is displayed. """
        response = self.client.get(reverse('get-or-set-site-geoms',
            kwargs={'requested_file': 'hudson-valley-zip-geoms.txt'}))
        self.assertEqual(response.status_code, 200)
        # No templates should be used to render this page, it is raw data.
        self.assertEqual(response.templates, [])
        # Ensure Hudson Valley zips are in this file.
        self.assertContains(response, ';12601;')
        self.assertContains(response, ';12550;')
        # Ensure non-hudson valley zips are excluded.
        self.assertNotContains(response, ';00777;')
        # 12602 has no geom, make sure points are included in this file. 
        self.assertContains(response, '|POINT')
    
    def test_get_market_markers(self):
        """ Assert market markers for all sites are returned. """
        response = self.client.get(reverse('get-or-set-market-markers'))
        site2 = Site.objects.get(id=2)
        site131 = Site.objects.get(id=131)
        site2.save()
        site131.save()
        coord = USZip.objects.get(code=site2.default_zip_postal).coordinate
        site2_list = [coord.longitude, coord.latitude, str(site2.name)]
        coord = USZip.objects.get(code=site131.default_zip_postal).coordinate
        site131_list = [coord.longitude, coord.latitude, str(site131.name)]
        self.assertContains(response, str(site2_list))
        self.assertContains(response, str(site131_list))