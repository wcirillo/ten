""" Tests for the ecommerce app. """

import datetime
from decimal import Decimal
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.test import TestCase
        
from advertiser.models import BillingRecord
from ecommerce.models import (CreditCard, OrderItem, Order, Product, Payment,
    PaymentResponse, Promotion, PromotionCode)
from ecommerce.connector import USAePayConnector, ProPayConnector
from ecommerce.service.calculate_current_price import calculate_current_price
from ecommerce.service.product_list import calc_total_of_all_products
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class TestUSAePayConnector(TestCase):
    """ A test case for the Connector class of the ecommerce application. 
    In addition to testing the USAePayConnector, this also tests the 
    ProPayConnector. 
    """
    fixtures = ['test_advertiser', 'test_coupon', 'test_ecommerce',
        'test_promotion']
    
    TEST_CONNECTOR = USAePayConnector()
    TEST_CONNECTOR.test_mode = True
    CC_NUMBER = '4111111111111111'
    CCV2 = '1234'
    
    def test_order_object_flow(self):
        """ Creates several objects, demonstrating a typical order process.
        """
        site = Site.objects.get(id=2)
        product = Product.objects.get(id=2)
        promotion = Promotion.objects.create(promoter_id=1,
            description='test', promo_type='1', use_method='1',
            code_method=1)
        promotion.product.add(product.id)
        promotion.save()
        promotion_code = PromotionCode.objects.create(promotion=promotion,
            code='test')
        self.assertEqual(PromotionCode.objects.get(code='test').used_count, 0)
        billing_record = BillingRecord.objects.get(id=1)
        order = Order.objects.create(method='V', promotion_code=promotion_code,
            billing_record=billing_record)
        OrderItem.objects.create(
            order=order,
            site=site,
            product=product,
            content_type=ContentType.objects.get(
                app_label="coupon", model="coupon"),
            business_id=114,
            description=product.name,
            end_datetime = (datetime.datetime.now() +
                datetime.timedelta(days=product.base_days)))
        self.assertEqual(PromotionCode.objects.get(code='test').used_count, 1)
        product_price = calculate_current_price(product.id, site=site, 
            consumer_count=site.get_or_set_consumer_count())
        product_list = [(product.id, product_price)]
        all_products_total = calc_total_of_all_products(product_list)
        self.assertEqual(order.total, all_products_total)
        credit_card = CreditCard()
        credit_card.exp_month = 5
        credit_card.exp_year = 17
        credit_card.card_holder = 'Testy Test'
        credit_card.business_id = 114
        credit_card.cvv2 = self.CCV2 # Saved on the instance but not the model.
        credit_card.encrypt_cc(self.CC_NUMBER)
        credit_card.clean() # Gets cc_type from cc_number.
        credit_card.save()
        payment = self.TEST_CONNECTOR.process_payment(order, order.total,
            credit_card, billing_record)
        self.assertTrue(payment)
                                
    def test_process_payment(self):
        """ Process a payment through the gateway.
        Every environment gets a unique ESAPI Salt, so an encrypted number
        (like in a fixture) cannot migrate environments. So make it good
        before using it.
        """ 
        order = Order.objects.get(id=501)
        # An object encrypted in dev won't decrypt in prod, and vice versa:
        credit_card = CreditCard.objects.get(id=500)
        credit_card.cvv2 = self.CCV2 # Saved on the instance but not the model.
        cc_number = self.CC_NUMBER
        credit_card.encrypt_cc(cc_number)
        credit_card.clean() # Gets cc_type from cc_number.
        credit_card.save()
        billing_record = BillingRecord.objects.get(id=114)
        payment = self.TEST_CONNECTOR.process_payment(order, 25, credit_card,
            billing_record)
        self.assertTrue(payment)
    
    def test_expired_card(self):
        """ Assert a credit card that is now past expiration date fails to 
        process.
        """ 
        order = Order.objects.get(id=502)
        credit_card = CreditCard.objects.get(id=505)
        credit_card.cvv2 = self.CCV2
        credit_card.encrypt_cc(self.CC_NUMBER)
        billing_record = BillingRecord.objects.get(id=114)
        try: 
            self.TEST_CONNECTOR.process_payment(order, 25, credit_card,
                billing_record)
            self.fail('Expired card allowed.')
        except ValidationError as e:
            LOG.debug(e)
            self.assertTrue(True)
    
    def test_process_overpayment(self):
        """ Tests to see if a payment can be applied in excess of order amount.
        """
        order = Order.objects.get(id=501)
        credit_card = CreditCard.objects.get(id=500)
        credit_card.cvv2 = self.CCV2 # Saved on the instance but not the model.
        cc_number = self.CC_NUMBER
        credit_card.encrypt_cc(cc_number)
        credit_card.clean() # Gets cc_type from cc_number.
        credit_card.save()
        billing_record = BillingRecord.objects.get(id=114)
        try:
            self.TEST_CONNECTOR.process_payment(order, 500, credit_card,
                billing_record)
            self.fail('overpayment allow')
        except ValidationError:
            self.assertTrue(True)
        
    def test_double_payment(self):
        """ Attempt to pay the same order twice and assert it was not processed 
        both times.
        """  
        order = Order.objects.get(id=501)
        # An object encrypted in dev won't decrypt in prod, and vice versa:
        credit_card = CreditCard.objects.get(id=500)
        credit_card.cvv2 = self.CCV2 # Saved on the instance but not the model.
        credit_card.encrypt_cc(self.CC_NUMBER)
        credit_card.clean() # Gets cc_type from cc_number.
        credit_card.save()
        order.get_outstanding_balance()
        billing_record = BillingRecord.objects.get(id=114)
        payment1 = self.TEST_CONNECTOR.process_payment(order, '49.95', 
            credit_card, billing_record)
        first_payment_id = payment1.id
        payment_order = payment1.order
        if Payment.objects.filter(order=payment_order).count() != 1:
            self.fail("1st payment record missing")
        if PaymentResponse.objects.filter(
                payment=first_payment_id).count() != 1:
            self.fail("Missing 1st payment A response record")
        payment_response = PaymentResponse.objects.get(payment=first_payment_id)
        self.assertEqual(payment_response.status, 'A', 
            'This payment should be approved')
        self.assertTrue(payment1)
        # Make duplicate payment for this order.
        try:
            self.TEST_CONNECTOR.process_payment(order, '49.95', credit_card,
                billing_record)
        except ValidationError:
            pass 
        # Validation error is supposed to occur, test to ensure 2nd payment was 
        # not processed.
        if Payment.objects.filter(order=payment_order).count() != 1:
            self.fail("2nd payment was duplicate order")
        
    def test_two_half_payments(self):
        """ Attempt to pay two installments for the same order, not exceeding 
        the original total order. This test works for USAePay only.
        """ 
        order = Order.objects.get(id=501)
        # An object encrypted in dev won't decrypt in prod, and vice versa:
        credit_card = CreditCard.objects.get(id=500)
        credit_card.cvv2 = self.CCV2 # Saved on the instance but not the model.
        cc_number = self.CC_NUMBER
        credit_card.encrypt_cc(cc_number)
        credit_card.clean() # Gets cc_type from cc_number.
        credit_card.save()
        billing_record = BillingRecord.objects.get(id=114)
        payment1 = self.TEST_CONNECTOR.process_payment(order, '24.98', 
            credit_card, billing_record)
        payment_order = payment1.order.id
        if Payment.objects.filter(order=payment_order).count() != 1:
            self.fail("1st payment record missing")
        first_payment_id = payment1.id
        if PaymentResponse.objects.filter(
                payment=first_payment_id).count() != 1:
            self.fail("Missing 1st payment A response record")
        payment_response = PaymentResponse.objects.get(payment=first_payment_id)
        self.assertEqual(payment_response.status, 'A', 
            '1st payment should be approved')
        self.assertTrue(payment1)
        # Make final payment for this order.
        payment2 = self.TEST_CONNECTOR.process_payment(order, '24.97', 
                credit_card, billing_record)
        payment_order = payment2.order.id
        # Test to ensure 2nd payment was not processed.
        if Payment.objects.filter(order=payment_order).count() != 2:
            self.fail("2nd payment was unable to occur")
        second_payment_id = payment2.id
        payment_response = PaymentResponse.objects.get(
            payment=second_payment_id)
        self.assertEqual(payment_response.status, 'A', 
            '2nd payment should be approved')
        self.assertEqual(order.get_outstanding_balance(), Decimal('0.00'))

class MockProPayConnector(ProPayConnector):
    """ For ProPay tests, this class will not connect to the test payment 
    gateway. 
    """
    def call_payment_gateway(self, url, data):
        """ Mock call to the ProPay payment gateway. """
        return """<?xml version="1.0"?><XMLResponse><XMLTrans>
            <transType>04</transType><accountNum>test</accountNum>
            <invNum>test</invNum><transNum>121</transNum>
            <authCode>A11111</authCode><AVS>T</AVS><CVV2Resp>M</CVV2Resp>
            <status>00</status><responseCode>0</responseCode></XMLTrans>
            </XMLResponse>"""

class TestMockProPayConnector(TestUSAePayConnector):
    """ Test for Mock ProPay Connector. These tests will not connect to ProPay
    payment gateway. 
    """
    TEST_CONNECTOR = MockProPayConnector()
    TEST_CONNECTOR.test_mode = True 
    
    def test_expired_card(self):
        """ This test is not run here. See TestProPayConnector for this test. 
        """
        pass

class TestProPayConnector(TestUSAePayConnector):
    """ Test for ProPay Connector. Run test for expired card only just to 
    test connection to ProPay. 
    """
    TEST_CONNECTOR = ProPayConnector()
    TEST_CONNECTOR.test_mode = True 
    CC_NUMBER = '4747474747474747' 
    CCV2 = '999'
    
    def test_order_object_flow(self):
        """ This test should not connect to ProPay. """
        pass
    
    def test_process_payment(self):
        """ This test should not connect to ProPay. """
        pass    
    
    def test_two_half_payments(self):
        """ This test should not connect to ProPay. """
        pass

    def test_double_payment(self):
        """ This test should not connect to ProPay. """
        pass
    
    def test_process_overpayment(self):
        """ This test should not connect to ProPay. """
        pass