""" Unit tests for AdRepPhotoUpload functionality. """
import logging
import settings

from django.core.urlresolvers import reverse
from django.core.files.storage import FileSystemStorage
from common.test_utils import EnhancedTestCase
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRep

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class AdRepPhotoUploadTestCase(EnhancedTestCase):
    """ Setup/tearDown test case class for ad-rep-photo-upload tests. """

    urls = 'urls_local.urls_2'

    def setUp(self):
        super(AdRepPhotoUploadTestCase, self).setUp()
        self.ad_rep = AD_REP_FACTORY.create_ad_rep()
        
    def tearDown(self):
        super(AdRepPhotoUploadTestCase, self).tearDown()
        self.ad_rep = AdRep.objects.get(email=self.ad_rep.email)
        if self.ad_rep.ad_rep_photo:
            self.ad_rep.ad_rep_photo.delete()
        

class TestAdRepPhotoUpload(AdRepPhotoUploadTestCase):
    """ Tests for ad-rep-photo-upload. """

    def test_get_success(self):
        """ Test ad-rep-photo-upload view for a successful GET. """
        self.login(email=self.ad_rep.email)
        response = self.client.get(reverse('ad-rep-photo-upload')) 
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/ad-rep/photo-upload/')
        self.assertContains(response, "frm_ad_rep_photo_upload")
        self.assertContains(response, "id_ad_rep_photo")

    def test_nothing_filled_out(self):
        """ Assert no fields fille out. """
        self.login(email=self.ad_rep.email)
        response = self.client.post(reverse('ad-rep-photo-upload')) 
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/ad-rep/photo-upload/')
        self.assertContains(response, 'This field is required.')
        self.assertContains(response, "frm_ad_rep_photo_upload")
        self.assertContains(response, "id_ad_rep_photo")

    def test_upload_not_an_image(self):
        """ Assert form error when the file being uploaded is not an image. """
        self.login(email=self.ad_rep.email)
        file_path = '%s/settings.py' % (
            settings.PROJECT_PATH)
        file_to_upload = open(file_path, 'rb')
        response = self.client.post(reverse('ad-rep-photo-upload'),
            {'ad_rep_photo': file_to_upload}) 
        self.assertContains(response, '%s%s%s' % ('Upload a valid image. ',
            'The file you uploaded was either not ',
            'an image or a corrupted image.'))
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/ad-rep/photo-upload/')

    def test_file_upload(self):
        """ Assert file is uploaded. """
        self.assertEqual(self.ad_rep.ad_rep_photo, None)
        self.login(email=self.ad_rep.email)
        file_path = '%sdynamic/images/ad-rep/1.jpg' % (
            settings.MEDIA_ROOT)
        file_to_upload = open(file_path, 'rb')
        response = self.client.post(reverse('ad-rep-photo-upload'),
            {'ad_rep_photo': file_to_upload}) 
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/ad-rep/photo-upload/')
        self.ad_rep = AdRep.objects.get(email=self.ad_rep.email)
        path = self.ad_rep.ad_rep_photo.name
        self.assertTrue(FileSystemStorage().exists(path))
        self.assertNotContains(response, 'This field is required.')
        self.assertContains(response, "frm_ad_rep_photo_upload")
        self.assertContains(response, "id_ad_rep_photo")
        self.assertContains(response, path)
