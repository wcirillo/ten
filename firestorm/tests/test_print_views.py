""" Tests for print views (iframes) displayed by firestorm app. """

from django.core.urlresolvers import reverse

from common.test_utils import EnhancedTestCase
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY


class TestPrintViews(EnhancedTestCase):
    """ Test case for firestorm print views (served in iframes). """
    fixtures = ['activate_switch_replicated_website',]
    
    def common_asserts(self, response, url):
        """ Common assertions to be made on firestorm print views. """
        self.assertContains(response, \
            'annually by working with an Independent Advertising Representati')
        self.assertContains(response, \
            'dynamic/images/QR/ad_rep/%s.gif' % url)

    def test_bulletin_board_print(self):
        """ Assert ad_rep can view printable version of bulletin board. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(ad_rep)
        response = self.client.get(reverse('bulletin-board-print'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "10coupons.com/%s" % ad_rep.url)
        self.common_asserts(response, ad_rep.url)

    def test_biz_benefits_print(self):
        """ Assert ad_rep can view printable version of benefits for 
        business. 
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(ad_rep)
        response = self.client.get(reverse('benefits-for-business-print'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 
            'marketing_resources/display_benefits_for_business_print.html')
        self.assertContains(response, 'IT WORKS!')
        self.assertContains(response, 'PROFITABLE')
        self.common_asserts(response, ad_rep.url)
    
    def test_our_competition_print(self):
        """ Assert ad_rep can view printable version of our competition print
        view.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(ad_rep)
        response = self.client.get(reverse('our-competition-print'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 
            'marketing_resources/display_our_competition_print.html')
        self.assertContains(response, 'Competition')
        self.assertContains(response, 'a local business can publish')
        self.assertContains(response, 
            'other companies mentioned on this website in no way endorse')
        self.common_asserts(response, ad_rep.url)

    def test_single_step_print(self):
        """ Assert ad_rep can view printable version of single step print view. 
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(ad_rep)
        response = self.client.get(reverse('simple-steps-print'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 
            'marketing_resources/display_simple_steps_print.html')
        self.assertContains(response, 'Simple Steps to Increase Your Profits')
        self.assertContains(response, 
            'Increase visits from your current customers')
        self.assertContains(response, 'Receive valuable, money-saving,')
        self.common_asserts(response, ad_rep.url)
        
    def test_pdf_business_cards(self):
        """ Assert ad_rep can view printable version of single step print view. 
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.login(email=ad_rep.email) 
        self.add_ad_rep_to_session(ad_rep)
        response = self.client.get(reverse('ad-rep-business-cards'))
        self.assertEqual(response.status_code, 200)
        response_headers = response._headers
        self.assertEqual(response_headers['content-disposition'][1],
            'filename=BusinessCards.pdf')
        self.assertEqual(response_headers['content-type'][1], 'application/pdf')