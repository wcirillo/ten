""" Tests for widget views of coupon app. """
#pylint: disable=C0103
from django.conf import settings
from django.core.urlresolvers import reverse

from common.test_utils import EnhancedTestCase
from coupon.factories.slot_factory import SLOT_FACTORY
from market.models import Site


class TestWidgetViews(EnhancedTestCase):
    """ Tests for create_widget_from_web view. """
    urls = 'urls_local.urls_2'

    @classmethod
    def setUpClass(cls):
        super(TestWidgetViews, cls).setUpClass()
        slot = SLOT_FACTORY.create_slot()
        cls.advertiser_id = str(slot.business.advertiser.id)
    
    def test_create_widget_good_web(self):
        """ Assert request of 'create-widget-from-web' with valid market. """
        site = Site.objects.get(id=2)
        response = self.client.get(reverse('create-widget-from-web',
            kwargs={
                'widget_type': 'markets', 
                'widget_identifier': site.directory_name,
                'widget_file': '10CouponsWidget160x600.js'}
            ))
        self.assertContains(response, 
            '"site_url": "%s/hudson-valley/"' % settings.HTTP_PROTOCOL_HOST)
            
    def test_create_widget_good_adv(self):
        """ Assert request of 'create-widget-from-web' with valid advertiser. """
        response = self.client.get(reverse('create-widget-from-web',
            kwargs={
                'widget_type': 'advertisers', 
                'widget_identifier': self.advertiser_id,
                'widget_file': '10CouponsWidget160x600.js'}
            ))
        self.assertContains(response, 
            '"site_url": "%s/hudson-valley/"' % settings.HTTP_PROTOCOL_HOST)
            
    def test_create_widget_good_bus(self):
        """ Assert request of 'create-widget-from-web' with valid business. """
        response = self.client.get(reverse('create-widget-from-web',
            kwargs={
                'widget_type': 'advertisers', 
                'widget_identifier': self.advertiser_id,
                'widget_file': '10CouponsWidget160x600.js'}
            ))
        self.assertContains(response, 
            '"site_url": "%s/hudson-valley/"' % settings.HTTP_PROTOCOL_HOST)
            
    def test_create_widget_bad_site(self):
        """  Assert 'create-widget-from-web' for invalid site returns 404. """
        response = self.client.get(reverse('create-widget-from-web',
            kwargs={
                'widget_type': 'markets', 
                'widget_identifier': 'foo',
                'widget_file': '10CouponsWidget160x600.js'}
            ))
        self.assertEquals(response.status_code, 404)
        
    def test_create_widget_bad_adv(self):
        """  Assert 'create-widget-from-web' for invalid advertiser returns 404.
        """
        response = self.client.get(reverse('create-widget-from-web',
            kwargs={
                'widget_type': 'advertisers', 
                'widget_identifier': '0',
                'widget_file': '10CouponsWidget160x600.js'}
            ))
        self.assertEquals(response.status_code, 404)
        
    def test_create_widget_bad_bus(self):
        """ Assert 'create-widget-from-web' for invalid business returns 404."""
        response = self.client.get(reverse('create-widget-from-web',
            kwargs={
                'widget_type': 'businesses', 
                'widget_identifier': '0',
                'widget_file': '10CouponsWidget160x600.js'}
            ))
        self.assertEquals(response.status_code, 404)
        
    def test_create_widget_bad_type(self):
        """ Assert 'create-widget-from-web' for invalid widget-type returns 404.
        """
        response = self.client.get(reverse('create-widget-from-web',
            kwargs={
                'widget_type': 'foo',
                'widget_identifier': '1',
                'widget_file': '10CouponsWidget160x600.js'}
            ))
        self.assertEquals(response.status_code, 404)

    def test_create_widget_bad_file_case(self):
        """ Assert improperly cased widget-file returns 200.
        Here, the file name is lower case instead of proper cased.
        """
        response = self.client.get(reverse('create-widget-from-web',
         kwargs={
             'widget_type': 'advertisers',
             'widget_identifier': self.advertiser_id,
             'widget_file': '10couponswidget160x600.js'}
         ))
        self.assertEquals(response.status_code, 200)
        # Assert widget contents.
        self.assertContains(response, '"site_name": "Hudson Valley"')

    def test_create_widget_bad_file(self):
        """ Assert improperly cased widget-file returns 200.
        Here, the file name is lower case instead of proper cased.
        """
        response = self.client.get(reverse('create-widget-from-web',
         kwargs={
             'widget_type': 'advertisers',
             'widget_identifier': self.advertiser_id,
             'widget_file': 'foo'}
         ))
        self.assertEquals(response.status_code, 404)
