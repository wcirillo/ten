""" Ecommerce View Testing for promotion codes. """
#pylint: disable=W0511
from decimal import Decimal

from django.core.urlresolvers import reverse
from django.template.defaultfilters import date as date_filter

from advertiser.models import Advertiser
from common.session import build_advertiser_session
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.models import SlotTimeFrame
from coupon.service.single_coupon_service import SINGLE_COUPON
from ecommerce.models import (OrderItem, Payment, PaymentResponse,
    PromotionCode)
from ecommerce.service.product_list import calc_total_of_all_products
from ecommerce.service.promotion_preapproval import check_promotion_preapproval
from ecommerce.tests.ecommerce_test_case import  EcommerceTestCase


class TestPromotion(EcommerceTestCase):
    """
    Class consisting of tests for coupon checkout form submissions pertaining
    to promotion codes getting submitted.
    """
    fixtures = ['test_consumer', 'test_ecommerce_views']
    urls = 'urls_local.urls_2'
    
    def test_post_free_promo_checkout(self):
        """ 
        Test coupon checkout with a valid promo that makes coupon purchase free 
        (FREE-ALL). Promo is passed in through session and submitted in form.
        Process of the order bypasses the checkout process, doesn't display
        payment forms, redirects to free-purchase and then to checkout-success.
        """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.session['promo_code'] = 'FREE-ALL'
        # Format expiration date the way it would be in the session at this 
        # point - in unicode format (for display).
        this_offer = self.session['consumer']['advertiser']['business'][0]\
            ['offer']
        this_coupon = this_offer[self.session['current_offer']]['coupon']\
            [self.session['current_coupon']]
        self.session['consumer']['advertiser']['business']\
            [self.session['current_business']]['offer']\
            [self.session['current_offer']]['coupon']\
            [self.session['current_coupon']]\
            ['expiration_date'] = date_filter(this_coupon['expiration_date'], 
                'n/j/y')
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)                
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data={"submit_frm_free_coupon":True}, follow=True) 
        # Display checkout page
        self.common_ecommerce_asserts(response)
        self.assertContains(response, "Receipt")
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 3)
        # Is coupon in orderItem table?
        # Get slot.id
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() < 1:
            self.fail("Failed to create slot.")
        slot = SlotTimeFrame.objects.filter(coupon=coupon.id).latest('id').slot
        order_item = OrderItem.objects.filter(item_id=slot.id).latest('id')
        # Does payment record exist for this coupon purchase?
        if Payment.objects.filter(order=order_item.order_id).count() > 0:
            self.fail("Order wrongly inserted into ecommerce_payment table! \
                Free-All promo used making product free.")
    
    def test_checkout_recalc_no_promo(self):
        """ 
        Test coupon checkout reload where the page loaded and the user 
        clicks the recalculate button without entering a promo code.
        """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '2'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        data = self.test_credit_card_data
        data.update({"post_reload": "1"})
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data)
        # Display checkout page. Not redirected, page reloaded with no changes.
        self.credit_card_asserts(response, data)
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1)
        # Is coupon in orderItem table?
        if OrderItem.objects.filter(item_id=coupon.id).count() > 0:
            self.fail("Processed payment on recalculate!")
        
    def test_recalc_valid_promo(self):
        """ 
        Test coupon checkout reload where the page loaded and the user 
        clicks the recalculate button without entering a promo code.
        """
        advertiser = self.prep_advertiser_slot_choice_1()
        data = self.test_credit_card_data.copy()
        data.update({"code": "charter1", "post_reload": "1"})
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data=data)
        # Display checkout page. Not redirected, page reloaded with no changes.
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "FL")
        self.assertContains(response, "55555")
        self.assertContains(response, "Fort Lauderdale")
        self.assertContains(response, "6671") # Page contains cvv code.
        self.assertContains(response, "20") # Page contains exp year.
        self.assertContains(response, "11") # Page contains exp month.
        self.assertContains(response, "4111111111111111") # cc number.
        self.assertContains(response, "Adam Eve") # Page contains card holder.
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1)
        # Is coupon in orderItem table?
        if OrderItem.objects.filter(item_id=coupon.id).count() > 0:
            self.fail("Processed payment on recalculate!")
        promotion_code = PromotionCode.objects.get(code__iexact='charter1')
        total = check_promotion_preapproval(
            promotion_code, advertiser, self.session['product_list'])[2]
        # Page contains our updated pricing.
        self.assertContains(response, str(total))
        self.assertContains(response, 'charter1')

    def test_recalc_freeall_promo(self):
        """ Test coupon checkout reload where the page loaded and the user 
        clicks the recalculate button after entering the Free-All promo.
        """
        self.prep_advertiser_slot_choice_1()
        data = self.test_credit_card_data.copy()
        data.update({"code" : "FREE-ALL", "post_reload": "1"})
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data)
        self.common_ecommerce_asserts(response)
        # Display checkout page. Not redirected, page reloaded with no changes.
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "Confirm")
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1)
        # Is slot in orderItem table?
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() > 0:
            self.fail("Should not create slot on recalculate.")
        promotion_code = PromotionCode.objects.get(code__iexact='FREE-ALL')
        all_products_total = calc_total_of_all_products(
            self.session['product_list'])
        promo_amount = (Decimal('.01') * 
            Decimal(str(promotion_code.promotion.promo_amount)) *
            Decimal(str(all_products_total)))
        total = all_products_total - promo_amount
        # Page contains our updated pricing.
        self.assertContains(response,
            str(Decimal(total).quantize(Decimal('0.01'))))
        self.assertContains(response, 'free-all')
        
    def test_checkout_recalc_bad_promo(self):
        """ 
        Test coupon checkout reload where the page loaded and the user 
        clicks the recalculate button with an invalid promo code.
        """
        self.prep_advertiser_slot_choice_1()
        data = self.test_credit_card_data.copy()
        data.update({"code" : "bad_promotion_code"})
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data)
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.credit_card_asserts(response, data)
        self.assertContains(response, "not valid")
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1)
        # Is coupon in OrderItem table?
        if OrderItem.objects.filter(item_id=coupon.id).count() > 0:
            self.fail("Processed payment on recalculate!")    
    
    def test_recalc_bad_cc_w_promo(self):
        """ 
        Test coupon recalculation of promotion code with bad form data.
        The result should be displaying promo-code calculation but should not 
        validate payment information until the payment is actually submitted.
        """
        self.prep_advertiser_slot_choice_1()
        data = self.test_credit_card_data.copy()
        data.update({"code" : "bad_promo_code"})
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data=data)
        # Not redirected, page reloaded with promo error.
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.credit_card_asserts(response, data)
        # Page contains tracking code validation error.
        self.assertContains(response, "Tracking Code not valid") 
        # Verify credit card not validated.
        self.assertNotIn("This field is required", response)
        self.assertContains(response, "Adam Eve") # Page contains card holder.
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1)
        # Is coupon in SlotTimeFrame table?
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() > 0:
            self.fail("Processed payment with incomplete form!")

    def test_fail_checkout_used_promo(self):
        """ Assert coupon cannot be purchased with used 'one time use' promo
        code.
        """
        advertiser = Advertiser.objects.get(id=603)
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        data = self.test_credit_card_data.copy()
        data.update({"code" : "onetimeuse"})
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data=data)
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.credit_card_asserts(response, data)
        self.assertNotContains(response, "error_list")# CHANGE WHEN FIXED.
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1)
        # Is coupon in a slot?
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() > 0:
            self.fail("Transaction was wrongly successful.")
        self.assertContains(response, "This promo has already been used")
        
    def test_checkout_valid_promo(self):
        """ Assert coupon checkout with valid promo code for successful purchase
        -uses one-time-use promo that hasn't been redeemed yet by this user.
        """
        coupon = COUPON_FACTORY.create_coupon(coupon_type_id=1)
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.session['promo_code'] = 'onetimeuse'
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        data = self.test_credit_card_data_complete.copy()
        data.update({"code" : self.session['promo_code']})
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data=data, follow=True)
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout-success/')
        self.assertContains(response, "Receipt")
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 3)
        # Is slot in order_item record for this coupon?
        try:
            slot_id = SlotTimeFrame.objects.filter(
                coupon=coupon.id).latest('id').slot.id
        except SlotTimeFrame.DoesNotExist:
            self.fail("Failed to create slot.")
        # Get order_item so we can get the order and check for it in Payments.
        try:
            order_item = OrderItem.objects.filter(item_id=slot_id).latest('id')
        except OrderItem.DoesNotExist:
            self.fail("Failed to process order items successfully!")
        try:
            payment = Payment.objects.get(order=order_item.order)
        except Payment.DoesNotExist:
            self.fail(
                "Missing payment record for successful payment with promo")
        promotion_code = PromotionCode.objects.get(
            code__iexact=self.session['promo_code'])
        # Get a different advertiser
        advertiser = Advertiser.objects.get(id=601)
        total = check_promotion_preapproval(
            promotion_code, advertiser, self.session['product_list'])[2]
        # Page contains our updated pricing.
        self.assertContains(response, str(total)) 
        self.assertEqual(payment.amount, total)
        if PaymentResponse.objects.filter(payment=payment.id).count() != 1:
            self.fail("""Missing payment response record for successful payment 
                with promo""")
        payment_response = PaymentResponse.objects.get(payment=payment.id)
        self.assertEqual(payment_response.status, 'A', 
            'Payment status declined for successful payment?')
