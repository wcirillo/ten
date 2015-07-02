""" Ecommerce Service Testing. """

from datetime import datetime, timedelta
from decimal import Decimal

from django.test import TestCase

from advertiser.models import Advertiser
from common.session import build_advertiser_session, parse_curr_session_keys
from common.test_utils import EnhancedTestCase
from ecommerce.models import Payment, Product
from ecommerce.service.calculate_current_price import (calculate_current_price,
    get_product_price)
from ecommerce.service.check_order_paid import check_order_paid
from ecommerce.service.credit_card_service import CreditCardService
from market.models import Site


class TestCreditCardService(TestCase):
    """ Assert validation of CreditCardService instances work. """
    
    def test_validate_no_cc_type(self):
        """ Assert this credit card is not valid because of no cc_type. """
        credit_card_service = CreditCardService('311111111111111', None)
        test, message = credit_card_service.validate_cc_number()
        self.assertFalse(test)
        self.assertEqual(message[:], 'Card number is not valid.')
        
    def test_validate_bad_cc_type(self):
        """ Assert this credit card is not valid because of invalid cc_type. """
        credit_card_service = CreditCardService('311111111111111', 'Foo')
        test, message = credit_card_service.validate_cc_number()
        self.assertFalse(test)
        self.assertEqual(message[:], 'Card number is not valid.')
            

class TestCalculateCurrentPrice(TestCase):
    """ Assert price is calculated correctly for products. """
    fixtures = ['test_consumer']
    
    def test_flyer_placement(self):
        """ Assert flyer placement price is calculated correctly. """
        site = Site.objects.get(id=1)
        consumer_count = site.get_or_set_consumer_count()
        product = Product.objects.get(id=1)
        price = calculate_current_price(product.id,
            consumer_count=site.get_or_set_consumer_count())
        self.assertEqual(price,
            Decimal(str(consumer_count * .05)) + product.base_rate)

    def test_flyer_20000_consumers(self):
        """ Assert flyer placement to 20000 costs $420 """
        self.assertEqual(calculate_current_price(1, None, 20000),
            Decimal('420.0'))

    def test_flyer_5000_consumers(self):
        """ Assert flyer placement to 5000 costs $170 """
        self.assertEqual(calculate_current_price(1, None, 5000),
            Decimal('170.0'))

    def test_web_placement(self):
        """ Assert web placement price is calculated correctly. """
        site = Site.objects.get(id=1)
        product = Product.objects.get(id=2)
        price = get_product_price(2, site=site)
        self.assertEqual(price, product.base_rate + site.base_rate)
        
    def test_annual_web_placement(self):
        """
        Asserts annual web placement price is calculated correctly.
        """
        site = Site.objects.get(id=2)
        product3 = Product.objects.get(id=3)
        price = get_product_price(3, site)
        self.assertEqual(price, product3.base_rate)

    def test_product_price_cache(self):
        """ Test get and set of slot price for monthly and annual rates. """
        # Note: pricing does not currently vary by site when it does update.
        product2 = Product.objects.get(id=2)
        product3 = Product.objects.get(id=3)
        site = Site.objects.get(id=2)
        monthly_slot_price, annual_slot_price = \
            product2.base_rate, product3.base_rate
        self.assertEqual(get_product_price(product2.id, site), 
            monthly_slot_price)
        self.assertEqual(get_product_price(product3.id, site), 
            annual_slot_price)
        product2.base_rate += Decimal('26.00')
        product2.save()
        product3.base_rate += Decimal('101.00')
        product3.save()
        monthly_slot_price, annual_slot_price = \
            product2.base_rate, product3.base_rate
        self.assertEqual(get_product_price(product2.id, site), 
            monthly_slot_price)
        self.assertEqual(get_product_price(product3.id, site), 
            annual_slot_price)
        # Clean up.
        product2.base_rate -= Decimal('26.00')
        product2.save()
        product3.base_rate -= Decimal('101.00')
        product3.save()
        
class TestCheckOrderPaid(EnhancedTestCase):
    """ This is a class housing test methods for ecommerce service methods. 
    """
    fixtures = ['test_ecommerce_views'] 
    
    def test_check_order_unpaid_coupon(self):
        """ Test method check_order_paid for coupon that is not yet paid -
        (within last 3 hours). 
        """
        advertiser = Advertiser.objects.get(id=603)
        build_advertiser_session(self, advertiser)
        # Format expiration date the way it would be in the session at this point -
        # in unicode format (for display).
        self.assemble_session(self.session)
        session_dict = parse_curr_session_keys(
            self.client.session, ['this_offer', 'this_coupon'])
        site_id = self.session['consumer']['site_id']
        product = Product.objects.get(id=1)
        item_dict = {'item_id': session_dict['this_coupon']['coupon_id'], 
            'offer_id':session_dict['this_offer']['offer_id'],
            'is_valid_monday': session_dict['this_coupon']['is_valid_monday'], 
            'is_valid_tuesday': session_dict['this_coupon']['is_valid_tuesday'], 
            'is_valid_wednesday': session_dict['this_coupon']['is_valid_wednesday'], 
            'is_valid_thursday': session_dict['this_coupon']['is_valid_thursday'],
            'is_valid_friday': session_dict['this_coupon']['is_valid_friday'], 
            'is_valid_saturday': session_dict['this_coupon']['is_valid_saturday'],
            'is_valid_sunday': session_dict['this_coupon']['is_valid_sunday'], 
            'start_date': session_dict['this_coupon']['start_date'], 
            'expiration_date':session_dict['this_coupon']['expiration_date'], 
            'custom_restrictions':session_dict['this_coupon']['custom_restrictions'],
            'is_redeemed_by_sms':session_dict['this_coupon']['is_redeemed_by_sms'], 
            'site_id':site_id,
            'product_id':product.id, 'total':product.base_rate}
        result = check_order_paid(item_dict)                                 
        self.assertEqual(result, False)
        
    def test_check_order_paid_coupon(self):
        """ Test method check_order_paid for coupon that is paid. """
        advertiser = Advertiser.objects.get(id=603)
        build_advertiser_session(self, advertiser)
        self.session['current_offer'] = 0
        self.assemble_session(self.session)
        session_dict = parse_curr_session_keys(
            self.client.session, ['this_offer', 'this_coupon'])
        site_id = self.session['consumer']['site_id']
        product = Product.objects.get(id=1)
        # Update payment to have created payment datetime within last 3 hours
        payment = Payment.objects.get(id=600)
        payment.create_datetime = datetime.now() - timedelta(hours=2)
        payment.save()        
        item_dict = {'coupon_id':session_dict['this_coupon']['coupon_id'], 
            'offer_id':session_dict['this_offer']['offer_id'],
            'is_valid_monday':session_dict['this_coupon']['is_valid_monday'], 
            'is_valid_tuesday':session_dict['this_coupon']['is_valid_tuesday'], 
            'is_valid_wednesday' : session_dict['this_coupon']['is_valid_wednesday'], 
            'is_valid_thursday':session_dict['this_coupon']['is_valid_thursday'],
            'is_valid_friday':session_dict['this_coupon']['is_valid_friday'], 
            'is_valid_saturday':session_dict['this_coupon']['is_valid_saturday'],
            'is_valid_sunday':session_dict['this_coupon']['is_valid_sunday'], 
            'start_date':session_dict['this_coupon']['start_date'], 
            'expiration_date':session_dict['this_coupon']['expiration_date'], 
            'custom_restrictions':session_dict['this_coupon']['custom_restrictions'],
            'is_redeemed_by_sms':session_dict['this_coupon']['is_redeemed_by_sms'], 
            'site_id':site_id,
            'product_id':product.id, 'total':'39.95'}
        result = check_order_paid(item_dict)         
        self.assertEqual(result, True) 
         
    def test_check_order_paid_error(self):
        """ Test method check_order_paid for handling on KeyError. Test case
        would return True (paid) if successful, defaults false on error.
        """
        advertiser = Advertiser.objects.get(id=603)
        build_advertiser_session(self, advertiser)
        self.session['current_offer'] = 0
        self.assemble_session(self.session)
        session_dict = parse_curr_session_keys(
            self.client.session, ['this_offer', 'this_coupon'])
        site_id = self.session['consumer']['site_id']
        product = Product.objects.get(id=1)
        # Update payment to have created payment datetime within last 3 hours.
        payment = Payment.objects.get(id=600)
        payment.create_datetime = datetime.now() - timedelta(hours=2)
        payment.save() 
        # Exclude item_id from item_dict to cause key error.       
        item_dict = {'offer_id':session_dict['this_offer']['offer_id'],
            'is_valid_monday':session_dict['this_coupon']['is_valid_monday'], 
            'is_valid_tuesday':session_dict['this_coupon']['is_valid_tuesday'], 
            'is_valid_wednesday' : session_dict['this_coupon']['is_valid_wednesday'], 
            'is_valid_thursday':session_dict['this_coupon']['is_valid_thursday'],
            'is_valid_friday':session_dict['this_coupon']['is_valid_friday'], 
            'is_valid_saturday':session_dict['this_coupon']['is_valid_saturday'],
            'is_valid_sunday':session_dict['this_coupon']['is_valid_sunday'], 
            'start_date':session_dict['this_coupon']['start_date'], 
            'expiration_date':session_dict['this_coupon']['expiration_date'], 
            'custom_restrictions':session_dict['this_coupon']['custom_restrictions'],
            'is_redeemed_by_sms':session_dict['this_coupon']['is_redeemed_by_sms'], 
            'site_id':site_id,
            'product_id':product.id, 'total':'39.95'}
        result = check_order_paid(item_dict)         
        self.assertEqual(result, False) 
