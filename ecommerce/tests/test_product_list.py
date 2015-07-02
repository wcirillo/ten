""" Test cases for ecommerce product_list.py. """
import datetime
from decimal import Decimal

from django.test.client import RequestFactory

from common.test_utils import EnhancedTestCase
from ecommerce.models import Product
from ecommerce.service.product_list import (create_products_list,
    get_product_quantity, get_selected_product, set_selected_product)


class TestProductService(EnhancedTestCase):
    """ Test case for ecommerce product service methods.
    """
    def setUp(self):
        super(TestProductService, self).setUp()
        self.product_list = [(
            2, Decimal('99.00'),
            u'Monthly Coupon Display 8/10/11 - 9/10/11.',
            datetime.datetime(2011, 8, 10, 13, 28, 37, 121697),
            datetime.datetime(2011, 9, 10, 0, 0)),
            (1, Decimal('156.00'),
            u'Email Flyer scheduled for Aug 10, 2011.',
            datetime.datetime(2011, 8, 10, 13, 28, 37, 121697),
            datetime.datetime(2011, 9, 10, 0, 0)),
            (1, Decimal('156.00'),
            u'Email Flyer scheduled for Aug 17, 2011.',
            datetime.datetime(2011, 8, 10, 13, 28, 37, 121697),
            datetime.datetime(2011, 9, 10, 0, 0)),
            (1, Decimal('156.00'),
            u'Email Flyer scheduled for Aug 24, 2011.',
            datetime.datetime(2011, 8, 10, 13, 28, 37, 121697),
            datetime.datetime(2011, 9, 10, 0, 0)),
            (3, Decimal('499.00'),
            u'Annual Coupon Display 8/10/11 - 8/10/12.',
            datetime.datetime(2011, 8, 10, 13, 28, 37, 121697),
            datetime.datetime(2011, 9, 10, 0, 0)),
            (3, Decimal('499.00'),
            u'Annual Coupon Display 8/10/12 - 8/10/13.',
            datetime.datetime(2011, 8, 10, 13, 28, 37, 121697),
            datetime.datetime(2011, 9, 10, 0, 0)),
            ]

    def create_request(self, this_session):
        """ Create the request to use in get_product_quantity service tests. """
        factory = RequestFactory()
        this_session['locked_flyer_price'] = Decimal('22.00')
        self.assemble_session(this_session)
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        return request
    
    def test_flyer_count(self):
        """ Assert the flyer product count reported by test is accurate. """
        self.assertEqual(get_product_quantity(self.product_list, 1), 3)
        
    def test_monthly_slot_count(self):
        """ Assert the monthly slot product count reported by test is accurate. 
        """
        self.assertEqual(get_product_quantity(self.product_list, 2), 1)

    def test_annual_slot_count(self):
        """ Assert the monthly slot product count reported by test is accurate. 
        """
        self.assertEqual(get_product_quantity(self.product_list, 3), 2)
    
    def test_session_annual_choice(self):
        """ Test function get_selected_product returns add_annual_slot_choice. 
        """
        self.session['add_annual_slot_choice'] = 0
        request = self.create_request(self.session)
        add_flyer_choice, add_slot_choice, add_annual_slot_choice = \
            get_selected_product(request)
        self.assertEqual(add_annual_slot_choice, 0)
        self.assertEqual(add_flyer_choice, None)
        self.assertEqual(add_slot_choice, None)
        
    def test_session_slot_choice(self):
        """ Test function get_selected_product returns add_slot_choice. """
        self.session['add_slot_choice'] = 1
        request = self.create_request(self.session)
        add_flyer_choice, add_slot_choice, add_annual_slot_choice = \
            get_selected_product(request)
        self.assertEqual(add_slot_choice, 1)
        self.assertEqual(add_flyer_choice, None)
        self.assertEqual(add_annual_slot_choice, None)


class TestProductList(EnhancedTestCase):
    """ Test case for ecommerce product_list creation. """
    urls = 'urls_local.urls_2'
    
    def create_request(self, session):
        """ Create the request to use in create_products_list service tests. """
        factory = RequestFactory()
        session['locked_flyer_price'] = '10.00'
        self.assemble_session(session)
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        self.today = datetime.date.today()
        return request
    
    def test_add_one_slot(self):
        """ Test product_list creation for one slot. """
        self.session['add_slot_choice'] = 0
        request = self.create_request(self.session)
        prod_list = create_products_list(request)
        self.assertEqual(len(prod_list), 1)
        self.assertEqual(prod_list[0][0], 2)
        self.assertEqual(prod_list[0][3].date(), self.today) # Start date.
        self.assertTrue(prod_list[0][4]-prod_list[0][3] >= 
            datetime.timedelta(28))
        self.assertEqual(prod_list[0][1], Product.objects.get(id=2).base_rate)
        self.assertTrue('Monthly 10Coupon Publishing Plan: ' in prod_list[0][2])
    
    def test_add_annual_slot(self):
        """ Test product_list creation for one annual slot. """
        self.session['add_annual_slot_choice'] = 0
        request = self.create_request(self.session)
        prod_list = create_products_list(request)
        self.assertEqual(len(prod_list), 1)
        self.assertEqual(prod_list[0][0], 3)
        self.assertEqual(prod_list[0][3].date(), self.today) # Start date.
        self.assertTrue(prod_list[0][4]-prod_list[0][3] >= 
            datetime.timedelta(360))
        self.assertEqual(prod_list[0][1], Decimal('499.00'))
        self.assertTrue('Annual 10Coupon Publishing Plan: ' in prod_list[0][2])
    
    def test_set_session_slot_choice(self):
        """ Test set slot in product_list in session. """
        request = self.create_request(self.session)
        set_selected_product(request, 2)
        self.assertEqual(request.session.get('add_slot_choice', None), 0)
        self.assertEqual(len(request.session.get('product_list', 0)), 1)
        self.assertEqual(request.session['product_list'][0][0], 2)
        self.assertEqual(request.session.get('add_flyer_choice', None), None)
        self.assertEqual(request.session.get('add_annual_slot_choice', None), 
            None)
    
    def test_set_session_annual_choice(self):
        """ Test set annual slot choice in product_list in session. """
        request = self.create_request(self.session)
        set_selected_product(request, 3)
        self.assertEqual(request.session.get('add_annual_slot_choice', None), 0)
        self.assertEqual(len(request.session.get('product_list', 0)), 1)
        self.assertEqual(request.session['product_list'][0][0], 3)
        self.assertEqual(request.session.get('add_flyer_choice', None), None)
        self.assertEqual(request.session.get('add_slot_choice', None), None)
        
    def test_verify_one_choice(self):
        """ Test set product choice in session only has one choice in session
        at a time.
        """
        # Improperly create choices for all our products.
        self.session['add_annual_slot_choice'] = 0
        self.session['add_flyer_choice'] = 1
        self.session['add_slot_choice'] = 3
        request = self.create_request(self.session)
        set_selected_product(request, 3)
        self.assertEqual(request.session.get('add_annual_slot_choice', None), 0)
        self.assertEqual(request.session.get('add_flyer_choice', None), None)
        self.assertEqual(request.session.get('add_slot_choice', None), None)
