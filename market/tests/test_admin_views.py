""" Tests for admin views of market app. """

from common.test_utils import EnhancedTestCase
from market.models import Site

class TestAdminView(EnhancedTestCase):
    """ Test cases for market views. """
    fixtures = ['admin-views-users.xml', 'test_geolocation']
    urls = 'urls_local.urls_2'
    
    def setUp(self):
        super(TestAdminView, self).setUp()
        self.client.login(username='super', password='secret')

    def test_show_site_change_form(self):
        """ Assert site forms render. """
        response = self.client.get('/captain/market/site/2/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Domain name')
        self.assertContains(response,
            'name="domain" value="10HudsonValleyCoupons.com"')
        self.assertContains(response, 'Region')
        self.assertContains(response, 'Phase')
        self.assertContains(response, 'Us county')
        self.assertContains(response, 'Us state')
        
    def test_market_save(self):
        """ Assert the post of changes to a market save correctly. """
        site = Site.objects.get(id=2)
        post_data = {'domain': "10PurpleDashedCoupons.com", 
            'name': site.name, 'short_name': site.short_name,
            'region': site.region, 
            'directory_name': site.directory_name,
            'launch_date': site.launch_date,
            'base_rate': site.base_rate,
            'default_zip_postal': site.default_zip_postal, 
            'default_state_province': site.default_state_province.id,
            'market_cities': site.market_cities,
            'media_partner_allotment': site.media_partner_allotment,
            'phase': site.phase,
            'inactive_flag': site.inactive_flag,
            'us_county': site.us_county.all().values_list('id', flat=True)}
        response = self.client.post('/captain/market/site/2/', post_data, 
            follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/captain/market/site/')
        saved_site = Site.objects.get(id=2)
        self.assertEqual(saved_site.domain, '10PurpleDashedCoupons.com')