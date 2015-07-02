""" Tests urls for market app """
import logging
import os

from django.conf import settings
from django.test import TestCase
from django.test.client import Client

from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class TestUrls(TestCase):
    """
    Test for creation of local urlconf files.
    """
    
    def tearDown(self):
        """
        Cleanup files created during save site process that are not
        needed by other tests.
        """
        for site in Site.objects.filter(id__gt=5, inactive_flag=False):
            path = '%s/urls_local/urls_%s.py' % (settings.PROJECT_PATH, 
                    site.id)
            os.remove(path)
            
    def test_response_200_local(self):
        """ 
        Test status of all local homepages. middleware assumes all local 
        urlconfs exist, so save all site to avoid ImportError. 
        """
        client = Client(HTTP_HOST=settings.HTTP_HOST)
        for site in Site.objects.filter(id__gt=1, inactive_flag=False):
            LOG.debug("Testing %s homepage" % site)
            site.save()
            response = client.get('/%s/' % site.directory_name)
            if response.status_code != 200:
                LOG.debug('site.directory_name: %s' % site.directory_name)
                LOG.debug('response.status_code: %s' % response.status_code)
                LOG.debug('response.content: %s' % response.content)
                self.failUnlessEqual(response.status_code, 200)
            
