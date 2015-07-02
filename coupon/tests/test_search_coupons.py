""" Test case for search views of coupon app. """
#pylint: disable=C0103
import logging

from django.conf import settings
from django.core.urlresolvers import reverse

from haystack.sites import site as haystack_site

from common.test_utils import EnhancedTestCase
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import Coupon
from coupon.service.coupons_service import ALL_COUPONS
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class SearchCouponsTestCase(EnhancedTestCase):
    """ Test case for search_coupons view. """

    urls = 'urls_local.urls_2'

    @classmethod
    def setUpClass(cls):
        super(SearchCouponsTestCase, cls).setUpClass()
        settings.HAYSTACK_INCLUDE_SPELLING = True
        
    def setUp(self):
        super(SearchCouponsTestCase, self).setUp()
        self.slot_list = SLOT_FACTORY.create_slots(create_count=5)
        haystack_site.get_index(Coupon).reindex()
        self.coupon_list = SLOT_FACTORY.get_active_coupons(
            slot_list=self.slot_list)
        self.coupon0 = self.coupon_list[0]
        self.all_coupons = ALL_COUPONS.get_all_coupons(
            Site.objects.get(id=2))[0]
        self.request_data = None
        self.response = None
        
    def assert_all_returned(self):
        """ Assert that all current coupons are returned because search query
        and category was not found.
        """
        for coupon in self.all_coupons:
            self.assertContains(self.response, 
                'href="/hudson-valley/coupon-%s/%d/"' 
                    % (coupon.slug(), coupon.id))
            self.assertContains(self.response,
                coupon.location.all()[0].location_city.capitalize())
        return self

    def assert_one_returned(self):
        """ Assert that only the 1 matching result is returned from the search
        query or category that was found.
        """
        for coupon in self.all_coupons:
            if coupon.id == self.coupon0.id:
                self.assertContains(self.response, 
                'href="/hudson-valley/coupon-%s/%d/"' 
                    % (coupon.slug(), coupon.id))
                self.assertContains(self.response,
                    coupon.location.all()[0].location_city.capitalize())
            else:
                self.assertNotContains(self.response, 
                'href="/hudson-valley/coupon-%s/%d/"' 
                    % (coupon.slug(), coupon.id))
        return self

    def set_all_to_same_category(self):    
        """ Set every coupon in the database to the same category. """
        for coupon in self.all_coupons:
            coupon.offer.business.categories = [2]


class TestSearchNothing(SearchCouponsTestCase):
    """ Test case for searching on a get or post of nothing. """
    
    def test_get(self):
        """ Assert that on a GET the search form loads. """
        self.response = self.client.get(reverse('all-coupons'))
        LOG.debug("test_get = %s" % self.response.__dict__)
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response,
            'include/frm/frm_search_coupons.html')
        self.assertContains(self.response, 'frm_search_coupons')
        self.assert_all_returned()
    
    def test_post_nothing_filled_out(self):
        """ Assert that when the search form is submitted with All Categories
        and no specific query to search on, all coupons are returned back to the 
        screen. 
        """
        self.request_data = {'q': '', 'cat': '0', 'process_search_btn':True}
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_all_returned()
        
        
class TestSearchCategoryAndQuery(SearchCouponsTestCase):
    """ Test case for searching against a category and a query. """

    def test_get_both_one_found(self):
        """ Assert that when a category and query string gets searched on as a 
        GET request, all matched category results return because the string 
        was not found. 
        """
        self.request_data = {'q': 'No match string', 'cat': '1'}
        self.set_all_to_same_category()       
        self.coupon0.offer.business.categories = [1]
        haystack_site.get_index(Coupon).update()
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()
            
    def test_post_both_one_found(self):
        """ Assert that when a category and query string gets searched on as a 
        POST request, all matched category results return because the string 
        was not found. 
        """
        self.request_data = {'q': 'both', 'cat': '1',
            'process_search_btn':True}
        self.coupon0.offer.business.categories = [1]
        self.coupon0.update_index()
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()
    
    def test_get_both_found(self):
        """ Assert that when a category and query string gets searched on as a 
        GET request, all matched category/query string results return. 
        """
        self.request_data = {'q': self.coupon0.offer.headline, 'cat': '1'}
        self.coupon0.offer.business.categories = [1]
        self.coupon0.update_index()
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()

    def test_post_both_found(self):
        """ Assert that when a category and query string gets searched on as a 
        POST request, all matched category/query string results return. 
        """
        self.request_data = {'q': self.coupon0.offer.headline, 'cat': '1',
            'process_search_btn':True}
        self.coupon0.offer.business.categories = [1]
        self.coupon0.update_index()
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()

    def test_get_both_not_found(self):
        """ Assert that when a category and query string gets searched on as a 
        GET request, all coupons are returned because there is not match 
        for this search set. 
        """
        self.request_data = {'q': 'Return all coupons', 'cat': '1'}
        self.set_all_to_same_category()
        haystack_site.get_index(Coupon).update()
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assert_all_returned()

    def test_post_both_not_found(self):
        """ Assert that when a category and query string gets searched on as a 
        POST request, all coupons are returned because there is not match 
        for this search set. 
        """
        self.request_data = {'q': 'both', 'cat': '1',
            'process_search_btn':True}
        self.set_all_to_same_category()
        haystack_site.get_index(Coupon).update()
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_all_returned()


class TestSearchCategory(SearchCouponsTestCase):
    """ Test case for searching against just a category. """

    def setUp(self):
        super(TestSearchCategory, self).setUp()
        self.request_data = {'cat': '1', 'q':''}

    def test_get_category_found(self):
        """ Assert that when a category gets searched on as a GET request, all
        matched category results return. 
        """
        self.coupon0.offer.business.categories = [1]
        self.coupon0.update_index()
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()

    def test_post_category_found(self):
        """ Assert that when a category gets searched on as a POST request,
        all matched category results return. 
        """
        self.request_data.update({'process_search_btn':True})
        self.coupon0.offer.business.categories = [1]
        self.coupon0.update_index()
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()
        
    def test_get_category_not_found(self):
        """ Assert for a GET search for a category without any coupons, all
        coupons are returned.
        """
        self.set_all_to_same_category()
        haystack_site.get_index(Coupon).update()
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assertEqual(self.response.status_code, 200)
        LOG.debug("test_get_category_not_found = %s" % self.response.__dict__)
        self.assert_all_returned()
    
    def test_post_category_not_found(self):
        """ Assert that when a category gets searched on as a POST request,
        all results are returned if there are no results for this category. 
        """
        self.request_data.update({'process_search_btn':True})
        self.set_all_to_same_category()
        haystack_site.get_index(Coupon).update()
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_all_returned()


class TestSearchQuery(SearchCouponsTestCase):
    """ Test case for searching against just a query string. """

    def test_get_query_not_found(self):
        """ Assert that on a GET of the keyword 'pizza', no search results are
        found so all coupons loads. 
        """
        self.request_data = {'q': 'Get q Not Found'}
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assert_all_returned()
        self.assertContains(self.response, 
            'No results found for <strong>%s</strong>.' % 
            self.request_data['q'])
        
    def test_post_query_not_found(self):
        """ Assert that on a POST of the keyword 'pizza', no search results are
        found so all coupons loads. 
        """
        self.request_data = {'q': 'Post q Not Found',
            'process_search_btn':True}
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_all_returned()
        self.assertContains(self.response,
            'No results found for <strong>%s</strong>.' % 
                self.request_data['q'])
        
    def test_get_query_found(self):
        """ Assert that on a GET of the keyword 'pizza', search results are
        found so only the matched results will show on the page. 
        """
        self.request_data = {'q': self.coupon0.offer.headline}
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()

    def test_post_query_found(self):
        """ Assert that on a POST of the keyword 'pizza', search results are
        found so only the matched results will show on the page. 
        """
        self.request_data = {'q': self.coupon0.offer.headline,
            'process_search_btn':True} 
        self.response = self.client.post(reverse('all-coupons'),
            self.request_data)
        self.assert_one_returned()


class TestSpellingSuggestion(SearchCouponsTestCase):
    """ Test case for searching for an unknown string and having a spelling
    suggestion appear. """ 

    def test_spelling_suggestion(self):
        """ Assert that a spelling suggestion will get returned if for this 
        specific search which is not found. 
        """
        self.coupon0.offer.business.business_name = 'Luigis Pizzeria'
        self.coupon0.offer.business.save()
        self.coupon0.update_index()
        self.request_data = {'q': 'Pizzaria',
            'process_search_btn':True}
        self.response = self.client.get(reverse('all-coupons'),
            self.request_data)
        self.assertContains(self.response, '%s%s%s' % ('Did you mean: </span>',
            '<strong><em><a href="/hudson-valley/coupons/',
            '?q=pizzeria" alt="pizzeria">pizzeria</a>'))

################################################################################
#    def test_bad_page(self):
#        """ Assert that on a GET of the keyword 'pizza' and a page number that 
#        exceeds the results, returns page 1 instead of 404.
#        """
#        self.request_data = {'q': 'pizza', 'page': 999}
#        self.response = self.client.get(reverse('search'), self.request_data)
#        self.assertEqual(self.response.status_code, 200)  
#        self.assertContains(self.response, '%s%s' % (
#            'form name="frm_search_coupons',
#            '" action="" method="get"'))
#        self.assertContains(self.response, 'No matches')
