""" Media Partner application view testing. """
from datetime import datetime
import logging

from django.core.urlresolvers import reverse
from django.template.defaultfilters import date as date_filter

from consumer.models import Consumer
from common.test_utils import EnhancedTestCase
from ecommerce.models import Payment, Order
from market.models import Site
from media_partner.models import MediaPartner, MediaPieShare

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestTransactionReport(EnhancedTestCase):
    """ TestCase for view show_transaction_report. """
    fixtures = ['test_advertiser', 'test_ecommerce', 'test_media_partner']
    
    def test_deny_consumer(self):
        """ Assert consumer who is not a media_partner is prohibited."""
        consumer = Consumer.objects.get(id=403)
        self.login(consumer.email)
        response = self.client.get('/hudson-valley/media-partner/')
        self.assertEqual(response.status_code, 302)

    def test_media_partner_user_type(self):
        """ Assert a media_partner for this site is permitted."""
        media_partner = MediaPartner.objects.get(id=402)
        self.login(media_partner.email)
        response = self.client.get('/hudson-valley/media-partner/')
        self.assertEqual(response.status_code, 200)

    def test_get_affiliate_this_site(self):
        """ Assert consumers associated with this affiliate and this site is
        required. """
        affiliate_partner = MediaPartner.objects.get(id=401)
        self.login(affiliate_partner.email)
        response = self.client.get('/hudson-valley/media-partner/')
        self.assertEqual(response.status_code, 200)
    
    def test_get_affiliate_other_site(self):
        """ Assert affiliate is not associated with this site can not view the
        report.
        """
        affiliate_partner = MediaPartner.objects.get(id=401)
        self.login(affiliate_partner.email)
        response = self.client.get('/media-partner/')
        self.assertTrue('/media-partner-sign-in/' in response['location'])
        self.assertEqual(response.status_code, 302)
    
    def test_aff_site_from_launch(self):#
        """ Assert we can post to the page to view the From Launch report. """
        affiliate_partner = MediaPartner.objects.get(id=401)
        self.login(affiliate_partner.email)
        site = Site.objects.get(id=2)
        launch_date = site.launch_date
        inception = 'From Launch Date (' + date_filter(launch_date, 'F') + ' ' \
            + date_filter(launch_date, 'Y') + ')'
        response = self.client.post('/hudson-valley/media-partner/', 
            {'report':inception})
        self.assertEqual(response.status_code, 200)

    def test_aff_site_current_month(self):#
        """ Assert we can post to the page to view the Current Month report."""
        affiliate_partner = MediaPartner.objects.get(id=401)
        self.login(affiliate_partner.email)
        today = datetime.today()
        payment = Payment.objects.get(id=401)
        payment.create_datetime = today
        payment.save()
        media_pie_share = MediaPieShare.objects.get(id=2)
        media_pie_share.start_date = today.date()
        media_pie_share.save()
        current_month = 'Current Month (' + date_filter(today, 'F') + ' ' + \
            date_filter(today, 'Y') + ')' 
        response = self.client.post('/hudson-valley/media-partner/', 
            {'report':current_month})
        self.assertEqual(response.status_code, 200)
    
    def test_aff_site_qtr_one_share(self):#
        """ Assert we can post to the page to view the quarter report."""
        affiliate_partner = MediaPartner.objects.get(id=401)
        self.login(affiliate_partner.email)
        response = self.client.post('/hudson-valley/media-partner/', 
            {'report':'Q2 2010'})
        self.assertEqual(response.status_code, 200)

    def test_aff_amount_discounted(self):#
        """ Assert we can post to the page to view the quarter report."""
        affiliate_partner = MediaPartner.objects.get(id=401)
        self.login(affiliate_partner.email)
        order = Order.objects.get(id=401)
        order.amount_discounted = 20
        order.save()
        response = self.client.post('/hudson-valley/media-partner/', 
            {'report':'Q2 2010'})
        self.assertEqual(response.status_code, 200)
        
    def test_aff_site_qtr_many_shares(self):
        """ Assert affiliate with multiple shares can post to the page to view
        the quarter report.
        """
        affiliate_partner = MediaPartner.objects.get(id=405)
        self.login(affiliate_partner.email)
        response = self.client.post('/hudson-valley/media-partner/', 
            {'report':'Q3 2010'})
        self.assertEqual(response.status_code, 200)
    
    def test_get_media_group_this_site(self):#
        """ Assert media_group user associated with this site has access to this
        report.
        """
        media_group_partner = MediaPartner.objects.get(id=402)
        self.login(media_group_partner.email)
        response = self.client.get('/hudson-valley/media-partner/')
        self.assertEqual(response.status_code, 200)

    def test_get_media_group_other_site(self):
        """ Assert media_group user that is not associated with this site is not
        given access to view this report.
        """
        media_group_partner = MediaPartner.objects.get(id=402)
        self.login(media_group_partner.email)
        response = self.client.get('/media-partner/')
        self.assertEqual(response.status_code, 302)

class TestViews(EnhancedTestCase):
    """ Media partner view tests. """
    
    fixtures = ['test_media_partner']
    
    def test_media_partner_sign_in(self):
        """ Test media partner sign in view renders proper. """
        response = self.client.get(reverse('media-partner-sign-in'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'include/frm/frm_sign_in.html')
        self.assertContains(response, '/password-help/')
    
    def test_mp_invalid_sign_in(self):
        """ Assert when media partner tries to sign in and fails, the password
        reset link doesnt point to firestorm.
        """
        response = self.client.post(reverse('media-partner-sign-in'), data=
            {'email': 'test_affiliate@example.com', 'password': 'wrong_one'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'include/frm/frm_sign_in.html')
        self.assertContains(response, '/password-help/')


class TestConsumerAcquisitionReport(EnhancedTestCase):
    """ Tests for the Consumer Acquisition Report. """
    fixtures = ['test_media_partner', 'test_consumer']

    def test_report_good(self):
        """ Assert the consumer acquisition report displays correct data. """
        media_group_partner = MediaPartner.objects.get(id=402)
        self.login(media_group_partner.email)
        response = self.client.get(
            '/hudson-valley/media-partner/consumer-sign-ups/last-12-months/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<strong>Consumer Trends</strong>')
        self.assertContains(response, '"#monthly-breakdown-graph"')
        self.assertContains(response, '"label": "My Site"')
 
