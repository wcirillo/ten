""" Unit tests for views of the business of an advertiser. """

import datetime

from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from advertiser.factories.business_factory import BUSINESS_FACTORY
from advertiser.models import Business
from advertiser.business.views import show_edit_business_profile
from common.session import build_advertiser_session
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY


class TestBusinessProfile(EnhancedTestCase):
    """ Class that contains tests for business profile views. """
    urls = 'urls_local.urls_2'
    
    def setUp(self):
        """ Login advertiser and add business to the session. """
        super(TestBusinessProfile, self).setUp()
        self.business = BUSINESS_FACTORY.create_business()
        self.login(self.business.advertiser.email)
        build_advertiser_session(self, self.business.advertiser)
        self.post_data = {'slogan': 'slogan',
            'business_description': 'description',
            'show_map': True,
            'business_id': self.business.id,
            'category': 1,
            'web_url': 'test.com'}
    
    def common_asserts(self, response, business):
        """ Common asserts for business profile display. """
        self.assertContains(response, '<h3>%s Display Page</h3>' % (
            business.business_name))
        self.assertContains(response, 'Supply a description of %s.' % (
            business.business_name))
        self.assertContains(response, 'Choose a category for %s.' % (
            business.business_name))
        self.assertContains(response, '>Website URL<')
    
    def test_update_biz_profile(self):
        """ Assert update of existing business profile. """
        factory = RequestFactory()
        self.assemble_session(self.session)
        post_data = self.post_data
        post_data.update({'category': 7})
        request = factory.post('/business/edit/%s/' % self.business.id, 
            post_data, follow=True)
        request.session = self.session
        response = show_edit_business_profile(request, business_id=str(
            self.business.id))
        self.assertEqual(response['location'], '/hudson-valley/advertiser/')
        business = Business.objects.get(id=self.business.id)
        # Was business updated?
        self.assertEqual(business.slogan, 'slogan')
        self.assertEqual(str(business.categories.values_list('id', 
            flat=True)), '[7]')
        self.assertEqual(business.web_url, 'http://test.com/')
        
    def test_biz_profile_with_coupons(self):
        """ Assert display of existing business profile. """
        coupon = COUPON_FACTORY.create_coupon()
        coupon.expiration_date = datetime.date.today() + \
            datetime.timedelta(weeks=1)
        coupon.save()
        build_advertiser_session(self, coupon.offer.business.advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('edit-business-profile', 
            kwargs={'business_id': coupon.offer.business.id}))
        # Business with no category defaults to 7.
        self.assertContains(response, 'option value="7" selected="selected"')
        self.assertContains(response, 'frm_edit_business_profile')
        self.common_asserts(response, coupon.offer.business)
    
    def test_update_biz_category(self):
        """ Assert update of existing business profile to change category. """
        factory = RequestFactory()
        request = factory.post('/business/edit/%s/' % self.business.id, 
            self.post_data, follow=True)
        request.session = self.session
        response = show_edit_business_profile(request, business_id=str(
            self.business.id))
        self.assertEqual(response['location'], '/hudson-valley/advertiser/')
        # Check if business category saved.
        business = Business.objects.get(id=self.business.id)
        self.assertEqual(str(business.categories.values_list('id', 
            flat=True)), '[1]')
        self.assertEqual(business.web_url, 'http://test.com/')

    def test_update_biz_web_url_error(self):
        """ Assert update of existing business profile with invalid url shows 
        an error.
        """
        factory = RequestFactory()
        post_data = self.post_data
        post_data.update({'web_url': 'test.com '})
        request = factory.post('/business/edit/%s/' % self.business.id, 
            post_data, follow=True)
        request.session = self.session
        response = show_edit_business_profile(request, business_id=str(
            self.business.id))
        self.common_asserts(response, self.business)
        self.assertContains(response, 'Enter a valid URL.')

    def test_biz_profile_captions(self):
        """ Assert display of business profile captions when business has no 
        current coupons. 
        """
        response = self.client.get(reverse('edit-business-profile', 
            kwargs={'business_id': '%s' % self.business.id}))
        self.common_asserts(response, self.business)
