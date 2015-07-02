""" Tests middleware for market app """

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client, RequestFactory

from market.middleware import URLHandlerMiddleware

class TestMiddleware(TestCase):
    """
    Asserts behavoirs of market middleware.
    Rules: In cases where the domain and dir are both local, but mismatched, 
    prefer the domain.
    """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_promotion', 
        'test_ecommerce']

    def setUp(self):
        """ Init these string that get checked multiple times. """
        self.factory = RequestFactory()
        self.url_handler = URLHandlerMiddleware()
        self.subdomain = settings.HTTP_HOST[0].split('.')
        self.full_host = '%s/' % settings.HTTP_PROTOCOL_HOST

    def test_response_200(self):
        """ Test status of default homepage """
        client = Client(HTTP_HOST=settings.HTTP_HOST)
        response = client.get('/')
        self.failUnlessEqual(response.status_code, 200)

    def test_response_200_admin(self):
        """ Test admin interface reachable """
        client = Client(HTTP_HOST=settings.HTTP_HOST)
        response = client.get(reverse('admin:index'))
        self.failUnlessEqual(response.status_code, 200)

    def test_response_200_about_us(self):
        """ Test about us, a real subdir. """
        client = Client(HTTP_HOST=settings.HTTP_HOST)
        client.defaults['SERVER_NAME'] = '10coupons.com'
        client.defaults['PATH_INFO'] = '/about-us/'
        response = client.get('/about-us/')
        self.failUnlessEqual(response.status_code, 200)

    def test_response_200_hudson_valley(self):
        """ /hudson-valley/ with multiple subdirs is allowed, no redir. """
        request = self.factory.get('/hudson-valley/A/B/C/')
        request.META['SERVER_NAME'] = settings.HTTP_HOST
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response, None)

    def test_response_200_sp_us(self):
        """ Internationalization dirs of SUPPORTED_IL8N allowed, no redir. """
        request = self.factory.get('/sp-us/A/')
        request.META['SERVER_NAME'] = settings.HTTP_HOST
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response, None)

    def test_response_200_sp_us_local(self):
        """ Internationalization dirs of SUPPORTED_IL8N allowed, no redir. """
        request = self.factory.get('/sp-us/hudson-valley/A')
        request.META['SERVER_NAME'] = settings.HTTP_HOST
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response, None)

    def test_response_200_mobile(self):
        """ Assert mobile subdomain is allowed, no redir. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = 'm.10coupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response, None)

    def test_trim_port(self):
        """ Assert port is ignored. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = settings.HTTP_HOST
        request.META['SERVER_PORT'] = '8000'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response, None)

    def test_trim_port_no_subdomain(self):
        """ Assert port is ignored when the host has no subdomain. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = '10coupons.com'
        request.META['SERVER_PORT'] = '8000'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response, None)

    ####### TEST STATUS 301 PERMANENT REDIRECTS #######
    def test_bad_subdomain(self):
        """ Assert subdomains not specifically allowed get redir. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = 'foo.10coupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 'http://10coupons.com/')
    
    def test_multiple_subdomains(self):
        """ Assert subdomains multiple levels deep get redir. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = 'foo.www.10coupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 'http://10coupons.com/')
    
    def test_www_10coupons_com(self):
        """ Assert www.10coupons.com gets redir. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = 'www.10coupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 'http://10coupons.com/')
    
    def test_dev_10hvcoupons_com(self):
        """ Assert dev.10hudsonvalleycoupons.com gets redir. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = 'dev.10hudsonvalleycoupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 
            'http://dev.10coupons.com/hudson-valley/')
    
    def test_10localcoupons_com(self):
        """ Test 10localcoupons.com gets redir. """
        client = Client(HTTP_HOST='10localcoupons.com')
        response = client.get('/')
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 'http://10coupons.com/')

    def test_www_tenlocalcoupons_com(self):
        """ www.tenlocalcoupons.com gets redir. """
        request = self.factory.get('/')
        request.META['SERVER_NAME'] = 'www.tenlocalcoupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 'http://10coupons.com/')

    def test_10hvcoupons_triangle(self):
        """ Domain name overrides domain name with 10. """
        request = self.factory.get('/triangle/')
        request.META['SERVER_NAME'] = '10hudsonvalleycoupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 
            'http://10coupons.com/hudson-valley/')

    def test_tenhvcoupons_triangle(self):
        """ Domain name overrides dir name with ten. """
        request = self.factory.get('/triangle/')
        request.META['SERVER_NAME'] = 'tenhudsonvalleycoupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 
            'http://10coupons.com/hudson-valley/')

    def test_10hvcoupons_hv(self):
        """ Test local domain matches local dir. """
        request = self.factory.get('/hudson-valley/')
        request.META['SERVER_NAME'] = '10hudsonvalleycoupons.com'
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 
            'http://10coupons.com/hudson-valley/')

    def test_redirect_test_append_slash(self):
        """ Test trailing slashes get appended. """
        request = self.factory.get('/hudson-valley/test')
        response = self.url_handler.process_request(request)
        self.failUnlessEqual(response.status_code, 301)
        self.failUnlessEqual(response['location'], 
            'http://10coupons.com/hudson-valley/test/')

    def test_response_404(self):
        """ Tests that bad url returns 404. """
        client = Client(HTTP_HOST=settings.HTTP_HOST)
        response = client.get('/hudson-valley/foo/')
        self.failUnlessEqual(response.status_code, 404)

