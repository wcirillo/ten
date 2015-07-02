""" Ecommerce Show Checkout View Testing. """
import datetime
from decimal import Decimal

from django.core.urlresolvers import reverse

from advertiser.models import Advertiser
from common.session import (build_advertiser_session, create_consumer_in_session)
from common.test_utils import EnhancedTestCase
from consumer.models import Consumer
from coupon.models import Coupon
from ecommerce.models import (Order, Promotion, PromotionCode)
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.promotion_preapproval import check_promotion_preapproval
from ecommerce.tests.ecommerce_test_case import EcommerceTestCase
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY

class TestShowCouponCheckout(EcommerceTestCase):
    """ Test case  for showing the coupon checkout page. """
    fixtures = ['test_consumer', 'test_ecommerce_views']
    urls = 'urls_local.urls_2'
    
    def toggle_assertions(self):
        """ Assertions that can be made when product selection is toggled. """
        # When price is toggled, we have to clear the process_payment_again
        # and order_id keys or we will process the previous order with the
        # previous product selection.
        self.assertEqual(
            self.client.session.get('process_payment_again', None), None)
        self.assertEqual(self.client.session.get('order_id', None), None)
        self.assertEqual(self.client.session.get('charge_amount', None), None)

    def test_deny_consumer(self):
        """ Test redirect when no advertiser. """
        consumer = Consumer.objects.get(id=600)
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('checkout-coupon-purchase'), 
            follow=True) 
        self.assertEqual(str(response.request['PATH_INFO']),
                         '/hudson-valley/coupons/')

    def test_no_coupon(self):
        """ Test redirect when no coupon. """
        advertiser = Advertiser.objects.get(id=601)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('checkout-coupon-purchase'), 
            follow=True) 
        # Redirected to home.
        self.assertEqual(str(response.request['PATH_INFO']),
                         '/hudson-valley/coupons/')

    def test_show_normal_checkout(self):
        """ Test normal coupon checkout (no promotion) display (not submitted). 
        """
        advertiser = Advertiser.objects.get(id=602)
        self.login(email=advertiser.email)      
        response = self.client.get(reverse('checkout-coupon-purchase')) 
        # Display checkout page. Redirected.
        self.assertEqual(response.status_code, 302)
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.get(reverse('checkout-coupon-purchase'))
        self.common_ecommerce_asserts(response)
        slot_price = get_product_price(2, advertiser.site)
        self.assertContains(response, slot_price)
        self.assertNotContains(response, 'id="id_pay_option"')
       
    def test_show_slot_with_ad_rep(self):
        """ Test normal coupon checkout (no promotion) display with ad rep in
        in session (not submitted) and monthly slot in session (should show
        option for annual).
        """
        advertiser = Advertiser.objects.get(id=602)  
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '0'
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.get(reverse('checkout-coupon-purchase'))
        self.common_ecommerce_asserts(response)
        self.assertContains(response, 'Get a whole year for $499')
    
    def test_show_annual_with_ad_rep(self):
        """ Test normal coupon checkout (no promotion) display with ad rep in
        in session (not submitted) and annual_slot_choice in session (should
        show option for monthly).
        """
        advertiser = Advertiser.objects.get(id=602)  
        build_advertiser_session(self, advertiser)
        self.session['add_annual_slot_choice'] = '0'
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.get(reverse('checkout-coupon-purchase'))
        self.common_ecommerce_asserts(response)
        self.assertContains(response, '$199 One-Month Plan')
        
    def test_show_used_promo_checkout(self):
        """ Test coupon checkout with used promo code (obtained from session), 
        display error message and allow resubmit.
        """
        # FUTURE TEST, issue in mantis.
        advertiser = Advertiser.objects.get(id=603)
        build_advertiser_session(self, advertiser)
        self.session['promo_code'] = 'onetimeuse' 
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)       
        response = self.client.get(reverse('checkout-coupon-purchase')) 
        # Display checkout page.
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "This promo has already been used")

    def test_show_valid_promo_checkout(self):
        """ Test coupon checkout with a valid promo, display check out page w/ 
        promo and discount (on page load, not form submit).
        """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.session['promo_code'] = 'charter1'
        self.assemble_session(self.session)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.get(reverse('checkout-coupon-purchase')) 
        self.common_ecommerce_asserts(response)
        # Page contains our promotion code.
        self.assertContains(response, str(self.session['promo_code'])) 
        promotion_code = PromotionCode.objects.get(
            code__iexact=self.session['promo_code'])
        total = check_promotion_preapproval(
            promotion_code, advertiser, self.session['product_list'])[2]
        # Page contains our updated pricing.
        self.assertContains(response, str(total))

    def test_get_free_promo_checkout(self):
        """ Test coupon checkout with a valid promo that makes coupon purchase 
        free (FREE-ALL). Promo code gets passed in through session, not 
        submitted. Processing a free order bypasses the checkout process and 
        doesn't display payment forms.
        """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.session['promo_code'] = 'FREE-ALL'
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)        
        response = self.client.get(reverse('checkout-coupon-purchase')) 
        self.common_ecommerce_asserts(response)
        self.assertTemplateUsed(response, 'include/frm/frm_free_coupon.html')
        # Page contains our promotion code.
        self.assertContains(response, str(self.session['promo_code']))
        promotion_code = PromotionCode.objects.get(
            code__iexact=self.session['promo_code'])
        total = check_promotion_preapproval(
            promotion_code, advertiser, self.session['product_list'])[2]
        # Is it free?
        self.assertEqual(total, Decimal('0.00'))
        # Page contains our updated pricing.
        self.assertContains(response, str(total))

    def test_annual_slot_free_checkout(self):
        """ Assert annual slot purchase with FREE promotion processes. """
        self.prep_advertiser_slot_choice_0()
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data={"selected_product_id": '3', 'code': 'free-annual-slot',
                  "post_reload": '1'},
            follow=True)
        # Display checkout page. Redirected (followed).
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.assertTemplateUsed(response, 'include/frm/frm_free_coupon.html')
        self.assertContains(response, "FREE Annual slot purchase")
        
    def test_promotion_ended(self):
        """ Test that a user can not use a promotion code for a promotion
        that has ended.
        """
        advertiser = Advertiser.objects.get(id=602)
        ended_date = datetime.date.today() - datetime.timedelta(days=7)
        promotion = Promotion.objects.get(id=600)
        promotion.end_date = ended_date
        promotion.save()
        build_advertiser_session(self, advertiser)
        self.session['promo_code'] = 'charter1'
        self.assemble_session(self.session)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.get(reverse('checkout-coupon-purchase'))
        self.assertContains(response, 'This promotion is already over.')

    def test_toggle_monthly_price(self):
        """ Test checkout page post that toggles payment option from annual
        to monthly.
        """
        advertiser = Advertiser.objects.get(id=602)  
        build_advertiser_session(self, advertiser)
        self.session['add_annual_slot_choice'] = '0'
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data={  "cc_number" : "4222222222222222",
                    "selected_product_id": '2'
                    })
        self.assertContains(response, '4222222222222222')
        self.assertContains(response, 'Get a whole year for $499')
        self.assertContains(response, 'name="selected_product_id" value="2"')
        self.assertContains(response, 
            'Monthly Publishing involves a recurring charge')
        self.toggle_assertions()

    def test_toggle_annual_price(self):
        """ Test checkout page post that toggles payment option from monthly
        to annual.
        """
        advertiser = Advertiser.objects.get(id=602)  
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '0'
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data={  "cc_number" : "43333333333333333",
                    "selected_product_id": 3 
                    })
        self.assertContains(response, '43333333333333333')
        self.assertContains(response, '$199 One-Month Plan')
        self.assertContains(response, 'saves $1,889')
        self.assertContains(response, 'name="selected_product_id" value="3"')
        self.assertNotContains(response, 
            'Monthly Publishing involves a recurring charge')
        self.toggle_assertions()
    
    def test_promo_wrong_product(self):
        """ Test coupon checkout reload with promo errors for wrong product.
        Make sure any cc info submitted is retained and that no cc errors
        are displayed.
        """
        self.prep_advertiser_slot_choice_0()
        data = self.test_credit_card_data.copy()
        # Forces "This field is required" error.
        data.update({"cc_number" : "", "code" : "onetimeuse"})
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data)
        # Display checkout page. Not redirected, page reloaded with no changes.
        self.credit_card_asserts(response, data)
        self.assertNotContains(response, 'This field is required.')
        self.assertContains(response, 
            'This promotion is not valid for this product.')

    def test_toggle_after_decline(self):
        """ Test changing product after making a declined payment. The keys
        should be wiped out from session or the previous order will get
        processed after the form submission is corrected - even though they
        chose another product afterward.
        """
        advertiser = Advertiser.objects.get(id=606)
        build_advertiser_session(self, advertiser)
        self.session['add_annual_slot_choice'] = '0'
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.session['process_payment_again'] = True
        self.session['credit_card_id'] = 601
        self.session['billing_record_id'] = 605
        self.session['order_id'] = 604
        self.session['charge_amount'] = '499.99'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        if self.client.session['product_list'][0][0] != 3:
            self.fail('This test assumes product to be annual.')
        data = { 'selected_product_id': 2}
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/create-coupon/checkout/')
        self.toggle_assertions()


class TestShowReceipt(EnhancedTestCase):
    """ Test case  for display of a receipt. """

    fixtures = ['test_ecommerce_views']
    urls = 'urls_local.urls_2'

    def test_deny_consumer(self):
        "Prove consumer is not authorized to view an advertiser's receipt."
        consumer = Consumer.objects.get(id=600)
        self.login(consumer.email)
        self.assemble_session(self.session)       
        response = self.client.post(reverse('receipt', args=[600]), follow=True)
        # Redirected to home.
        self.assertEqual(str(response.request['PATH_INFO']),
                         '/hudson-valley/coupons/')

    def test_invalid_order_id(self):
        "Try to display a receipt of a non-existant order."
        advertiser = Advertiser.objects.get(id=603)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)       
        response = self.client.post(reverse('receipt', args=[900]), follow=True)
        # Redirected to home.
        self.assertEqual(str(response.request['PATH_INFO']),
                         '/hudson-valley/coupons/')
        
    def test_invalid_order_coupon(self):
        """Show receipt of a coupon purchase for order with no coupon."""
        advertiser = Advertiser.objects.get(id=604)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)       
        response = self.client.post(reverse('receipt', args=[601]), follow=True)
        # Redirected to home.
        self.assertEqual(str(response.request['PATH_INFO']),
                         '/hudson-valley/coupons/')
    
    def test_advertiser_order_mismatch(self):
        """ Try to show coupon purchase receipt for another advertiser, 
        redirects to home page.
        """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)       
        response = self.client.post(reverse('receipt', args=[602]), follow=True)
        # Redirected to home.
        self.assertEqual(str(response.request['PATH_INFO']),
                         '/hudson-valley/coupons/')
    
    def test_show_order_with_payment(self):
        """Try to show normal payment receipt for coupon."""
        advertiser = Advertiser.objects.get(id=603)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)       
        order_id = 600
        response = self.client.post(reverse('receipt', args=[order_id]), 
            follow=True)
        # Redirected to home.
        order = Order.objects.select_related().get(id=order_id)
        coupon = Coupon.objects.get(id=order.order_items.all()[0].item_id)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/ecommerce/receipt/%s/' % order.id)
        self.assertContains(response, str(coupon.id))
    
    def test_show_order_free(self):
        """ Try to show paid receipt when there is no payment record, assumes 
        cost is free but displays data from order record.
        """
        advertiser = Advertiser.objects.get(id=604)
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session) 
        order_id = 602      
        response = self.client.post(reverse('receipt', args=[order_id]), 
            follow=True)
        order = Order.objects.select_related().get(id=order_id)
        coupon = Coupon.objects.get(id=order.order_items.all()[0].item_id)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/ecommerce/receipt/%s/' %order.id)
        self.assertContains(response, str(coupon.id))