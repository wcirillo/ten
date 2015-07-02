""" Tests for caching qr code images. """
import os
import shutil

from django.conf import settings

from common.service.qr_image_cache import QRImageCache
from common.test_utils import EnhancedTestCase


class TestQRImageCache(EnhancedTestCase):
    """ Test cases for QRImageCache. """
    fixtures = ['activate_switch_replicated_website']
    urls = 'urls_local.urls_2'
      
    def tearDown(self):
        try:
            shutil.rmtree("%s/media/dynamic/images/QR/%s" %
                (settings.PROJECT_PATH, 'new-market/'))
        except OSError:
            pass

    def assert_file_exists(self, img_path):
        """ Assert file exists. """
        if not os.path.exists(
            "%s/media/%s" % (settings.PROJECT_PATH, img_path)):
            self.fail('QR Code did not get created.')

    def test_get_default_qr(self):
        """ Test get QR Code for 10coupons.com domain, no ad rep. """
        img_path = QRImageCache().get_qr_code(url='', site_directory='')
        self.assertEqual('dynamic/images/QR/_default_domain.gif', img_path)
        self.assert_file_exists(img_path)
    
    def test_get_qr_for_ad_rep(self):
        """ Test get QR code for ad rep with no site. """
        img_path = QRImageCache().get_ad_rep_qr_code(url='jenkins_test')
        self.assertEqual('dynamic/images/QR/ad_rep/jenkins_test.gif', img_path)
        self.assert_file_exists(img_path)

    def test_create_qr_ad_rep_new_site(self):
        """ Test create QRCode image for an ad rep on a new site. """
        img_path = QRImageCache().get_ad_rep_qr_code(
            url='my_ad_rep_url_is_awesome', site_directory='new-market')
        self.assertEqual(img_path,
            'dynamic/images/QR/new-market/ad_rep/my_ad_rep_url_is_awesome.gif')
        self.assert_file_exists(img_path)
        
    def test_create_default_site_qr(self):
        """ Test create QRCode image for a new site, no ad rep. """
        img_path = QRImageCache().get_qr_code(
            url='', site_directory='new-market')
        self.assertEqual(img_path,
            'dynamic/images/QR/new-market/_default_domain.gif')
        self.assert_file_exists(img_path)
