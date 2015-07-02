""" Tests for common context_processors of project ten. """

from django.test import TestCase
from django.test.client import RequestFactory

from common.context_processors import current_url_no_subdomain, safe_urls


class TestCurrentURLNoSubdomain(TestCase):
    """ Test case for the context_processor current_url_no_subdomain."""

    def test_correct_url(self):
        """ Assert the correct URL is returned by current_url_no_subdomain. """
        factory = RequestFactory()
        request = factory.get('/foo/bar/')
        request.get_host = (lambda: 'mobile.10coupons.com')
        context = current_url_no_subdomain(request)
        self.assertEqual(context['current_url_no_subdomain'],
            'http://10coupons.com/foo/bar/')


class TestSafeUrls(TestCase):
    """ Test case for safe_urls context_processor."""

    def test_safe_urls_secure(self):
        """ Assert protocol matches context vars. """
        factory = RequestFactory()
        request = factory.get('/')
        request.is_secure = (lambda: True)
        context = safe_urls(request)
        self.assertEqual(context['safe_static_url'][:8], 'https://')
        self.assertEqual(context['safe_media_url'][:8], 'https://')
