""" Tests for order models of the ecommerce app of project ten. """

import datetime
from decimal import Decimal
import logging

from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase 

from advertiser.models import BillingRecord
from coupon.factories.slot_factory import SLOT_FACTORY
from ecommerce.factories.order_factory import ORDER_FACTORY
from ecommerce.models import Product, Promoter, PromotionCode, Order, OrderItem
from ecommerce.service.calculate_current_price import calculate_current_price
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestOrderModels(TestCase):
    """ Tests for ecommerce models. """
    fixtures = ['test_promotion']

    def test_product_delete_bad(self):
        """ Assert deleting a product that has been ordered is not allowed. """
        ORDER_FACTORY.create_order()
        product = Product.objects.get(id=2)
        with self.assertRaises(ValidationError) as context_manager:
            product.delete()
        LOG.debug(context_manager.exception)

    def test_product_delete_good(self):
        """ Assert deleting a product that has never been ordered is allowed."""
        product = Product()
        product.name = 'foo'
        product.content_type = ContentType.objects.get(
            app_label='coupon', model='coupon')
        product.save()
        try:
            product.delete()
        except ValidationError:
            self.fail('Failed deleting a new product.')

    def test_calculate_promotion(self):
        """ Assert order items tallied and promotion applied for order saved.
        """
        order = ORDER_FACTORY.create_order(product_id=1)
        order_item = order.order_items.all()[0]
        site = Site.objects.get(id=2)
        rate_card_cost = calculate_current_price(
            product_id=1, site=site,
            consumer_count=site.get_or_set_consumer_count())
        # Assert rate card values, no discount.
        self.assertTrue(order.invoice is not None)
        self.assertEqual(order_item.amount, Decimal(rate_card_cost))
        self.assertEqual(order.subtotal, Decimal(rate_card_cost))
        self.assertEqual(order.amount_discounted, 0)
        self.assertEqual(order.total, Decimal(rate_card_cost))
        # Apply promotion to order. Check recalculated values.
        first_promo = PromotionCode.objects.get(id=201)
        order.promotion_code = first_promo
        initial_used_count = first_promo.used_count
        order.save()
        self.assertEqual(order_item.amount, Decimal(rate_card_cost))
        self.assertEqual(order.subtotal, Decimal(rate_card_cost))
        self.assertEqual(order.amount_discounted, Decimal(rate_card_cost))
        self.assertEqual(order.total, Decimal(0))
        # Check promo used_count was incremented.
        self.assertEqual(
            PromotionCode.objects.get(id=201).used_count,
            initial_used_count + 1
            )
        # Change order to a different promotion. Check recalculated values.
        # This promotion is 15% off.
        second_promo = PromotionCode.objects.get(id=205)
        second_used_count = second_promo.used_count
        order.promotion_code = second_promo
        order.save()
        self.assertEqual(
            order.order_items.all()[0].amount,
            Decimal(rate_card_cost)
            )
        self.assertEqual(order.subtotal, Decimal(rate_card_cost))
        self.assertEqual(
            order.amount_discounted, 
            Decimal(str(round(
                order.subtotal * Decimal('.15'),2))).quantize(Decimal('0.01')))
        self.assertEqual(
            order.total, 
            Decimal(order.subtotal - order.amount_discounted)
            )
        # Assert second promo used_count was incremented.
        self.assertEqual(
            PromotionCode.objects.get(id=205).used_count,
            second_used_count + 1
            )
        # Assert initial promo used_count was decremented.
        self.assertEqual(
            PromotionCode.objects.get(id=201).used_count,
            initial_used_count
            )
        # Finally change order to no promotion. Check recalculated values.
        order.promotion_code = None
        order.save()
        self.assertEqual(
            order.order_items.all()[0].amount,
            Decimal(rate_card_cost)
            )
        self.assertEqual(order.subtotal, Decimal(rate_card_cost))
        self.assertEqual(order.amount_discounted, Decimal(0))
        self.assertEqual(order.total, Decimal(rate_card_cost))
        # Assert second promo used_count was decremented.
        self.assertEqual(
            PromotionCode.objects.get(id=205).used_count,
            second_used_count
            )
        LOG.debug('order.invoice: %s ' % order.invoice)
        LOG.debug('order.subtotal: %s ' % order.subtotal)
        LOG.debug('order.amount_discounted: %s ' % order.amount_discounted)
        LOG.debug('order.total: %s ' % order.total)
    
    def test_order_clean_good(self):
        """ Assert when an order is cleaned, a valid promotion_code passes. """
        order = ORDER_FACTORY.create_order(product_id=1)
        site = Site.objects.get(id=2)
        rate_card_cost = calculate_current_price(product_id=1, site=site,
            consumer_count=site.get_or_set_consumer_count())
        # Apply promotion to order. Check recalculated values.
        first_promo = PromotionCode.objects.get(id=201)
        order.promotion_code = first_promo
        try:
            order.clean()
        except ValidationError as error:
            self.fail(error)
        self.assertEqual(order.subtotal, Decimal(rate_card_cost))
        self.assertEqual(order.amount_discounted, Decimal(rate_card_cost))
        # Order total not recalculated until save.
        self.assertEqual(order.total, Decimal(rate_card_cost))
    
    def test_order_clean_bad(self):
        """ Assert when an order is cleaned, an invalid promotion_code fails.
        """
        slot = SLOT_FACTORY.create_slot()
        billing_record = BillingRecord.objects.create(business=slot.business)
        order = Order.objects.create(billing_record=billing_record)
        product = Product.objects.get(id=1)
        site = Site.objects.get(id=2)
        order_item = OrderItem(product=product, site=site,
            business=slot.business,
            end_datetime=datetime.datetime.now())
        order.order_items.add(order_item)
        rate_card_cost = calculate_current_price(product.id, site=site,
            consumer_count=site.get_or_set_consumer_count())
        # Apply promotion to order. Check recalculated values.
        promotion_code = PromotionCode.objects.get(id=203)
        order.promotion_code = promotion_code
        with self.assertRaises(ValidationError) as context_manager:
            order.clean()
        LOG.debug(context_manager.exception)
        self.assertEqual(order.subtotal, Decimal(rate_card_cost))
        self.assertEqual(order.amount_discounted, Decimal(0))
    
    def test_delete_order_good(self):
        """ Assert that a new order can be deleted. """
        order = ORDER_FACTORY.create_order()
        try:
            order.delete()
        except ValidationError:
            self.fail('New order was not deleted.')
    
    def test_delete_order_bad(self):
        """ Assert that a locked order cannot be deleted. """
        order = ORDER_FACTORY.create_order(is_locked=True)
        with self.assertRaises(ValidationError) as context_manager:
            order.delete()
        LOG.debug(context_manager.exception)

    def test_modify_locked_order(self):
        """ Assert that a locked order cannot be modified. """
        order = ORDER_FACTORY.create_order(is_locked=True)
        order.promotion_code = PromotionCode.objects.get(id=201)
        with self.assertRaises(ValidationError) as context_manager:
            order.save()
        LOG.debug(context_manager.exception)

    def test_clean_order_item_bad(self):
        """ Assert an order item fails cleaning for bad dates. """
        order_item = OrderItem(product_id=1, site_id=2, business_id=114,
            start_datetime = (datetime.datetime.now() +
                datetime.timedelta(1)), end_datetime = datetime.datetime.now())
        with self.assertRaises(ValidationError) as context_manager:
            order_item.clean()
        LOG.debug(context_manager.exception)

    def test_delete_order_item_good(self):
        """ Assert an order item can be deleted if the order is not locked. """
        order = ORDER_FACTORY.create_order()
        order_item = order.order_items.all()[0]
        LOG.debug(order_item)
        try:
            order_item.delete()
        except ValidationError:
            self.fail('Unlocked order failed deletion.')
    
    def test_modify_locked_order_item(self):
        """ Assert that an order item of a locked order cannot be modified. """
        order = ORDER_FACTORY.create_order(is_locked=True)
        order_item = order.order_items.all()[0]
        order_item.description = 'Can this be changed?'
        with self.assertRaises(ValidationError) as context_manager:
            order_item.save()
        LOG.debug(context_manager.exception)

    def test_delete_order_item(self):
        """ Assert an order item an unlocked order can be deleted. """
        order = ORDER_FACTORY.create_order()
        order_item = order.order_items.all()[0]
        try:
            order_item.delete()
        except ValidationError:
            self.fail('Order item for unlocked order was not deleted.')
            
    def test_delete_locked_order_item(self):
        """ Assert that an order item of a locked order cannot be deleted. """
        order = ORDER_FACTORY.create_order(is_locked=True)
        order_item = order.order_items.all()[0]
        with self.assertRaises(ValidationError) as context_manager:
            order_item.delete()
        LOG.debug(context_manager.exception)

    def test_advertiser_promo_2x(self):
        """ Assert a promotion of use_type 2 cannot be used more than once. """
        def create_order_with_promo(billing_record_id, business_id):
            """ An order to be created. """
            order = Order.objects.create(billing_record_id=billing_record_id,
                promotion_code_id=209)
            order_item = OrderItem(product_id=1, site_id=2,
                business_id=business_id, end_datetime=datetime.datetime.now())
            order.order_items.add(order_item)
            order.clean()

        slot = SLOT_FACTORY.create_slot()
        billing_record = BillingRecord.objects.create(business=slot.business)
        # Works ok once.
        create_order_with_promo(billing_record.id, slot.business.id)
        with self.assertRaises(ValidationError) as context_manager:
            create_order_with_promo(billing_record.id, slot.business.id)
        LOG.debug(context_manager.exception)

    def test_promoter_cut_amount(self):
        """ Assert promoter cut amount is calculated correctly. """
        promoter = Promoter.objects.get(id=2)
        order = ORDER_FACTORY.create_order(product_id=1)
        order.promotion_code_id = 205
        order.save()
        self.assertEqual(order.promoter_cut_amount, Decimal(str(round(
                promoter.promoter_cut_percent * order.total / Decimal(100),
            2))))
