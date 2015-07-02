""" Ecommerce Purchase Product View Testing. """
#pylint: disable=W0511
from decimal import Decimal
import datetime
from dateutil.relativedelta import relativedelta
import logging

from django.core import mail
from django.core.urlresolvers import reverse
from django.template.defaultfilters import date as date_filter
from django.test.client import RequestFactory

from advertiser.models import Advertiser
from common.session import (build_advertiser_session, get_coupon_id)
from coupon.models import (Coupon, SlotTimeFrame, FlyerPlacement,
    FlyerPlacementSubdivision)
from coupon.service.flyer_service import next_flyer_date
from coupon.service.single_coupon_service import SINGLE_COUPON
from ecommerce.models import (Order, OrderItem, Payment, PaymentResponse,
    PromotionCode)
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.product_list import calc_total_of_all_products
from ecommerce.service.promotion_preapproval import check_promotion_preapproval
from ecommerce.tests.ecommerce_test_case import EcommerceTestCase
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import (AdRepAdvertiser, AdRepConsumer, AdRepOrder)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

def debug_test_emails(outbox, test_name):
    """ Used in 2 tests that randomly pass and fail, try to isolate what emails
    are being passed into the outbox on test onset.
    """
    for counter, email in enumerate(outbox):
        LOG.debug('%s > mail subject %s' % (test_name, email[counter].subject))


class TestFlyerPurchase(EcommerceTestCase):
    """ Test case for flyer checkout form submissions. """
    fixtures = ['test_geolocation', 'test_consumer', 'test_ecommerce_views']
    urls = 'urls_local.urls_2'

    def test_checkout_flyer_dates(self):
        """ Assert multiple flyer dates get purchased for this advertisers slot.
        Assert no FlyerPlacementSubdivisions get inserted into the db since this
        purchase is for the entire market.
        """
        kwargs = {'email':'will+purchaseflyerdates@10coupons.com',
                'consumer_zip_postal':'10990',
                'business_name':'purchase flyer dates',
                'short_business_name':'purchase flyer dates',
                'headline':'purchase flyer dates'}
        self.make_advertiser_with_slot(**kwargs)
        SlotTimeFrame.objects.create(slot_id=self.slot.id,
            coupon_id=self.advertiser.businesses.all(
                )[0].offers.all()[0].coupons.all()[0].id)
        self.login_build_set_assemble(self.advertiser)
        self.session['current_slot_id'] = self.slot.id
        first_purchase_date = next_flyer_date()
        second_purchase_date = next_flyer_date() + datetime.timedelta(days=28)
        third_purchase_date = next_flyer_date() + datetime.timedelta(days=42)
        self.assertEqual(0, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=first_purchase_date).count())
        self.assertEqual(0, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=second_purchase_date).count())
        self.assertEqual(0, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=third_purchase_date).count())
        flyer_subdivision_count = FlyerPlacementSubdivision.objects.count()
        flyer_dates_list = [unicode(first_purchase_date),
                            unicode(second_purchase_date),
                            unicode(third_purchase_date)]
        self.session['flyer_dates_list'] = flyer_dates_list
        self.create_product_list(self.advertiser.site)
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        # Display checkout page. Redirected (followed).
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/')
        self.common_flyer_purchase_asserts(response, first_purchase_date,
            second_purchase_date)
        self.assertContains(response,
            'Email Flyer scheduled for %s.' % 
            date_filter(third_purchase_date, "M j, Y"))
        self.assertEqual(1, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=first_purchase_date).count())
        self.assertEqual(1, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=second_purchase_date).count())
        self.assertEqual(1, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=third_purchase_date).count())
        # Make sure no subdivision got inserted for this flyer placement since
        # the flyers were being purchased for the entire market.
        self.assertEqual(flyer_subdivision_count,
            FlyerPlacementSubdivision.objects.count())
        
    def test_checkout_flyer_subdivision(self):
        """ Assert multiple flyer dates get purchased for this advertisers slot.
        Assert FlyerPlacementSubdivisions get inserted into the db since this
        purchase is not for the entire market.
        """
        kwargs = {'email':'will+purchaseflyersubdivisions@10coupons.com',
                'consumer_zip_postal':'10990',
                'business_name':'purchase subdivisions',
                'short_business_name':'purchase subdivisions',
                'headline':'purchase subdivisions'}
        self.make_advertiser_with_slot(**kwargs)
        SlotTimeFrame.objects.create(slot_id=self.slot.id,
            coupon_id=self.advertiser.businesses.all(
                )[0].offers.all()[0].coupons.all()[0].id)
        self.login_build_set_assemble(self.advertiser)
        self.session['current_slot_id'] = self.slot.id
        self.session['subdivision_dict'] = {
            'subdivision_consumer_count':123,
            'county_array': (1844, 1866),
            'city_array': (),
            'zip_array': (),
            } 
        first_purchase_date = next_flyer_date()
        second_purchase_date = next_flyer_date() + datetime.timedelta(days=28)
        self.assertEqual(0, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=first_purchase_date).count())
        self.assertEqual(0, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=second_purchase_date).count())
        flyer_subdivision_count = FlyerPlacementSubdivision.objects.count()
        flyer_dates_list = [unicode(first_purchase_date),
                            unicode(second_purchase_date)]
        self.session['flyer_dates_list'] = flyer_dates_list
        self.create_product_list(self.advertiser.site)
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        # Display checkout page. Redirected (followed).
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/')
        self.common_flyer_purchase_asserts(response, first_purchase_date,
            second_purchase_date)
        self.assertEqual(1, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=first_purchase_date).count())
        self.assertEqual(1, FlyerPlacement.objects.filter(slot__id=self.slot.id,
            send_date=second_purchase_date).count())
        # Make sure subdivisions got inserted for this flyer placement since
        # the flyers were not being purchased for the entire market.
        self.assertEqual(flyer_subdivision_count + 4,
            FlyerPlacementSubdivision.objects.count())
        self.assertTrue('10 different coupon offers' in 
            mail.outbox[0].alternatives[0][0])


class TestCouponPurchaseRequest(EcommerceTestCase):
    """ Test case for coupon checkout form submissions. """
    fixtures = ['test_geolocation', 'test_consumer', 'test_ecommerce_views']
    urls = 'urls_local.urls_2'

    def test_checkout_success_normal(self):
        """ Assert normal coupon checkout (no coupons) successful purchases. """
        advertiser = self.prep_advertiser_slot_choice_1()
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        # Display checkout page. Redirected (followed).
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout-success/')
        # Check to ensure submitted fields still exist.
        self.common_ecommerce_asserts(response)
        self.assertContains(response, "Receipt")
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 3)
        # Is coupon in orderItem table? Get slot.id
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() < 1:
            self.fail("Failed to create slot.")
        slot_id = SlotTimeFrame.objects.filter(
            coupon=coupon.id).latest('id').slot.id
        if OrderItem.objects.filter(item_id=slot_id).count() != 1:
            self.fail("Failed to process order items successfully!")
        order_item = OrderItem.objects.get(item_id=slot_id)
        if Payment.objects.filter(order=order_item.order).count() != 1:
            self.fail("Missing payment record for successful payment")
        payment = Payment.objects.get(order=order_item.order)
        # Page contains our updated pricing.
        all_products_total = calc_total_of_all_products(
            self.session['product_list'])
        self.assertContains(response, str(all_products_total))
        self.assertEqual(payment.amount, all_products_total)
        if PaymentResponse.objects.filter(payment=payment.id).count() != 1:
            self.fail("Missing payment response record for successful")
        payment_response = PaymentResponse.objects.get(payment=payment.id)
        self.assertEqual(payment_response.status, 'A',
            'Payment status declined for successful payment?')
        # Assert receipt email sent.
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].to[0], advertiser.email)
        self.assertEqual(mail.outbox[0].subject,
            'Business With Coupons receipt: 2-%s' % order_item.order.id)
        self.assertEqual(mail.outbox[0].extra_headers['Reply-To'],
            'consumer@10Coupons.com')
        self.assertEqual(mail.outbox[0].extra_headers['From'],
            '10HudsonValleyCoupons.com <Coupons@10Coupons.com>')
        self.assertEqual(mail.outbox[0].from_email[:33],
            'bounce-ecommerce_welcome_receipt-')
        self.assertEqual(mail.outbox[0].from_email[-22:],
            '@bounces.10coupons.com')
        # Assert email contents. Text version:
        self.assertTrue("15% off dine in" in mail.outbox[0].body)
        self.assertTrue("/hudson-valley/login-advertiser/" in
            mail.outbox[0].body)
        #locked_string = "You will be charged $%s each month" % (
            #str(self.session['product_list'][0][1]))
        self.assertTrue('You will be charged each month'
            in mail.outbox[0].body)
        self.assertTrue("Total charged to Visa card XXXX-XXXX-XXXX-1111" in
            mail.outbox[0].body)
        self.assertTrue("$%s" % Decimal(all_products_total) in
            mail.outbox[0].body)
        self.assertTrue("Please contact us with any qu" in  mail.outbox[0].body)
        # Assert same info appears in HTML version:
        self.assertTrue("15% off dine in" in mail.outbox[0].alternatives[0][0])
        self.assertTrue("/hudson-valley/login-advertiser/" in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue('10 different coupon offers' in
            mail.outbox[0].alternatives[0][0])
        self.assertFalse("is currently labeled"
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("Monthly 10Coupon Publishing Plan"
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("ReturnDealerImage.aspx"
            not in mail.outbox[0].alternatives[0][0])
        self.assertTrue(
            "/hudson-valley/coupon-business-with-coupons-off-dine/600/" in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue(
            "This is a recurring monthly charge. Change auto-renew setting"
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("Total charged to Visa card XXXX-XXXX-XXXX-1111" in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue("$%s" % Decimal(all_products_total) in 
            mail.outbox[0].alternatives[0][0])
        self.assertTrue("(800) 581-3380" in  mail.outbox[0].alternatives[0][0])
        self.assertTrue("ReturnDealerImage.aspx"
            not in mail.outbox[0].alternatives[0][0])

    def test_annual_slot_purchase(self):
        """ Assert normal annual slot purchase performs perfectly. """
        advertiser = self.prep_advertiser_slot_choice_0()
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create_update_rep(
            self.client, advertiser, ad_rep)
        data = self.test_credit_card_data_complete.copy()
        data.update({"cvv_number" : "999"})
        mail.outbox = []
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data, follow=True)
        # Display checkout page. Redirected (followed).
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout-success/')
        self.assertContains(response, "Receipt")
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 3)
        # Is coupon in orderItem table? Get slot.id
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() < 1:
            self.fail("Failed to create slot.")
        slot = SlotTimeFrame.objects.filter(
            coupon=coupon.id).latest('id').slot
        self.assertEqual(slot.is_autorenew, False)
        self.assertEqual(slot.start_date, datetime.date.today())
        self.assertEqual(slot.end_date, 
            datetime.date.today() + relativedelta(years=1))
        slot_time_frame = SlotTimeFrame.objects.get(slot=slot)
        self.assertEqual(slot_time_frame.end_datetime, None)
        if OrderItem.objects.filter(item_id=slot.id).count() != 1:
            self.fail("Failed to process order items successfully!")
        # Get max order_item and the order and check for it in Payments.
        order_item = OrderItem.objects.filter(
            item_id=slot.id).latest('id')
        if Payment.objects.filter(order=order_item.order).count() != 1:
            self.fail("Missing payment record for successful payment")
        payment = Payment.objects.get(order=order_item.order)
        # Page contains our updated pricing.
        all_products_total = calc_total_of_all_products(
            self.session['product_list'])
        self.assertContains(response, str(all_products_total))
        self.assertEqual(payment.amount, all_products_total)
        if PaymentResponse.objects.filter(payment=payment.id).count() != 1:
            self.fail("Missing payment response record for successful")
        payment_response = PaymentResponse.objects.get(payment=payment.id)
        self.assertEqual(payment_response.status, 'A', 
            'Payment status declined for successful payment?')
        self.assertEqual(len(mail.outbox), 3)
        _index = 0
        for _index, email in enumerate(mail.outbox):
            if 'receipt:' in email.subject:
                break
        self.assertTrue("ReturnDealerImage.aspx"
            in mail.outbox[_index].alternatives[0][0])
    
    def test_annual_slot_purch_promo(self):
        """ Assert annual slot purchase with promotion executes w/ success. """
        self.prep_advertiser_slot_choice_0()
        data = self.test_credit_card_data_complete.copy()
        data.update({"code" : "annual-100-off", "cvv_number" : "999"})
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data, follow=True)
        # Display checkout page. Redirected (followed).
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout-success/')
        self.assertContains(response, "Receipt")
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 3)
        # Is coupon in orderItem table? Get slot.id
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() < 1:
            self.fail("Failed to create slot.")
        slot_time_frame = SlotTimeFrame.objects.filter(
            coupon=coupon.id).latest('id')
        slot = slot_time_frame.slot
        self.assertEqual(slot.is_autorenew, False)
        self.assertEqual(slot.start_date, datetime.date.today())
        self.assertEqual(slot.end_date, 
            datetime.date.today() + relativedelta(years=1))
        self.assertEqual(slot_time_frame.end_datetime, None)
        if OrderItem.objects.filter(item_id=slot.id).count() != 1:
            self.fail("Failed to process order items successfully!")
        order_item = OrderItem.objects.get(item_id=slot.id)
        self.assertEqual(order_item.amount, Decimal('499.00'))
        order = order_item.order
        self.assertEqual(order.subtotal, Decimal('499.00'))
        self.assertEqual(order.total, Decimal('399.00'))
        if Payment.objects.filter(order=order_item.order).count() != 1:
            self.fail("Missing payment record for successful payment")
        payment = Payment.objects.get(order=order_item.order)
        self.assertEqual(payment.amount, Decimal('399.00'))
        self.assertEqual(payment.status, 'A')
        self.assertEqual(len(mail.outbox), 2)
        
    def test_first_time_order(self):
        """ Test the email receipt for first-time paying advertisers (for 
        specific business).
        """
        self.prep_advertiser_slot_choice_0(605)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/')
        order = Order.objects.latest('id')
        self.assertEqual(mail.outbox[0].subject, 
            'Quick Check receipt: 2-%s Welcome to 10HudsonValleyCoupons.com'
            % order.id)
        self.assertTrue("is currently included in our <strong>Automotive" 
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("Welcome to 10HudsonValleyCoupons.com" 
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue("Welcome to 10HudsonValleyCoupons.com" 
            in mail.outbox[0].body)
        self.assertEqual(2, len(mail.outbox))
    
    def test_first_order_emails(self):
        """ Assert first order emails are sent (with an ad rep). The ad rep gets 
        cc'd on the receipt and gets an email with the window display.
        """
        prior_count = len(mail.outbox)
        debug_test_emails(mail.outbox, 'test_first_order_emails')
        advertiser = self.prep_advertiser_slot_choice_0(605)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create_update_rep(
            self.client, advertiser, ad_rep)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/')
        # 5 emails! ad rep enrollment causes promo code emails to go out and
        # admin gets cc'd, advertiser gets receipt, admin
        # gets sale notification, + 1 email to ad rep (receipt cc or
        # window-display).
        email_dict = {'ad_rep_enrollment': False,
            'advertiser_receipt': False,
            'ad_rep_receipt_or_window_display': False,
            'admin_sale_notify': False}
        for email in mail.outbox:
            subject = str(email.subject)
            if subject == "Welcome Aboard! Here's some help getting started.":
                if email.to[0] == ad_rep.email:
                    email_dict['ad_rep_enrollment'] = True
            elif subject.startswith('WEB SALE'):
                email_dict['admin_sale_notify'] = True
            elif subject.endswith('Welcome to 10HudsonValleyCoupons.com'):
                if email.to[0] == ad_rep.email:
                    email_dict['ad_rep_receipt_or_window_display'] = True
                else:
                    email_dict['advertiser_receipt'] = True
            elif subject == 'Send More Customers to Quick Check':
                email_dict['advertiser_window_display'] = True
            elif subject == 'Help Quick Check Succeed':
                email_dict['ad_rep_receipt_or_window_display'] = True
        for key in email_dict:
            if not email_dict[key]:
                self.fail("Ecommerce purchase is missing an email: %s"
                    % key)
        self.assertEqual(len(mail.outbox), 4 + prior_count)

    def test_checkout_incomplete_form(self):
        """ Test coupon checkout reload with errors where the user submits a
        payment without submitting all required fields and displays error.
        """
        self.prep_advertiser_slot_choice_1()
        data = self.test_credit_card_data_complete.copy()
        # Force "This field is required" error.
        data.update({"cc_number" : ""})
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data=data)
        # Display checkout page. Not redirected, page reloaded with no changes.
        self.credit_card_asserts(response, data)
        # Page contains cc number validation error.
        self.assertContains(response, "This field is required") 
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1)
        # Is coupon in orderItem table?
        if OrderItem.objects.filter(item_id=coupon.id).count() > 0:
            self.fail("Processed payment with incomplete form!")

    def test_submit_bad_form_w_promo(self):
        """  Test coupon checkout submission with form errors and a valid 
        promotion to get form errors displayed but also retain the promo code 
        discount display.
        """
        advertiser = self.prep_advertiser_slot_choice_1()
        self.session['promo_code'] = "onetimeuse"
        self.assemble_session(self.session)
        data = self.test_credit_card_data_complete.copy()
        data.update({"code" : self.session['promo_code'],
                "cc_number" : "1546565565646565"}) # Bad cc.
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data=data)
        # Display checkout page.
        self.common_ecommerce_asserts(response)
        rendered_html = response.content
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        # Check to ensure submitted fields still exist.
        self.assertTrue("FL" in rendered_html) # Page contains state.
        self.assertTrue("55555" in rendered_html) # Page contains zip.
        self.assertTrue("Fort Lauderdale" in rendered_html) # city
        self.assertTrue("6671" in rendered_html) # Page contains cvv code.
        self.assertTrue("20" in rendered_html) # Page contains exp year.
        self.assertTrue("11" in rendered_html) # Page contains exp month.
        self.assertTrue("card number" in rendered_html.lower(),
            "Invalid card number error not displayed")
        self.assertTrue("Adam Eve" in rendered_html) # Page contains card holder
        # Is coupon_id updated in table?
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.coupon_type_id, 1) # In Progress
        # Is coupon in orderItem table?
        if OrderItem.objects.filter(item_id=coupon.id).count() > 0:
            raise Exception, "Error: Processed payment with incomplete form!"
        promotion_code = PromotionCode.objects.get(
            code__iexact=self.session['promo_code'])
        total = check_promotion_preapproval(
            promotion_code, advertiser, self.session['product_list'])[2]
        # Page contains our updated pricing.
        self.assertTrue(str(total) in rendered_html,
            "AssertError: Promo discount not applied to failed checkout!")

    def test_repayment_after_decline(self):
        """ Assert coupon purchase after credit card declined succeeds. """
        self.prep_advertiser_slot_choice_1()
        data = self.test_credit_card_data_complete.copy()
        # Card number will declined
        data.update({"cc_number" : "4000300011112220"})
        response = self.client.post(reverse('checkout-coupon-purchase'), 
            data=data)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        first_order_id = self.client.session['order_id']
        if Payment.objects.filter(order=first_order_id).count() != 1:
            self.fail("Missing payment record for failed \
                transaction attempt")
        payment = Payment.objects.get(order=first_order_id)
        if PaymentResponse.objects.filter(payment=payment).count() != 1:
            self.fail("Missing payment response record for \
                failed transaction attempt")
        payment_response = PaymentResponse.objects.get(payment=payment)
        self.assertEqual(payment_response.status, 'D', 
            'This payment should be declined')
        # Now make a 2nd payment, successful this time:
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        coupon_id = get_coupon_id(self)
        coupon = Coupon.objects.get(id=coupon_id)
        self.assertEqual(coupon.coupon_type_id, 3)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/')
        self.assertContains(response, "Receipt")
        # Get slot ID
        if SlotTimeFrame.objects.filter(coupon=coupon_id).count() < 1:
            self.fail("Failed to create slot.")
        slot = SlotTimeFrame.objects.filter(
            coupon=coupon_id).latest('id').slot
        if OrderItem.objects.filter(item_id=slot.id).count() != 1:
            self.fail("Failed to process existing order items correctly!")
        if Payment.objects.filter(order=first_order_id).count() != 2:
            self.fail("2nd payment record missing")
        payment = Payment.objects.filter(order=first_order_id).latest('id')
        if PaymentResponse.objects.filter(payment=payment).count() != 1:
            self.fail("Missing 2nd payment A response record.")
        payment_response = PaymentResponse.objects.get(payment=payment)
        self.assertEqual(payment_response.status, 'A', 
            'This payment should be approved')

    def test_ecom_post_static_pricing(self):
        """ Make sure that static pricing is used when a user is on the 
        ecommerce coupon checkout page and POSTS off a static pricing site. 
        Checks that the email receipt is rendering the correct data.
        """
        advertiser = self.prep_advertiser_slot_choice_1()
        site = advertiser.site
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        # Display checkout page. Redirected (followed).
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/')        
        slot_price = get_product_price(2, site)
        self.assertContains(response, slot_price)
        self.assertTrue(str(slot_price) in mail.outbox[0].body)     
        self.assertTrue(str(slot_price) in mail.outbox[0].alternatives[0][0])     

    def test_annual_slot_free_purchase(self):
        """ Assert db transactions for free annual slot purchase. """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.session['add_annual_slot_choice'] = '0'
        self.session['promo_code'] = 'free-annual-slot'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data={"selected_product_id": '3', 'code': 'free-annual-slot',
                  "submit_frm_free_coupon" : "Confirm >>"},
            follow=True)
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertTemplateUsed(response, 
            'include/dsp/dsp_checkout_purchase_success.html')
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/create-coupon/checkout-success/')
        self.assertEqual(coupon.coupon_type_id, 3)
        # Is coupon in orderItem table? Get slot.id
        if SlotTimeFrame.objects.filter(coupon=coupon.id).count() < 1:
            self.fail("Failed to create slot.")
        slot_time_frame = SlotTimeFrame.objects.filter(
            coupon=coupon.id).latest('id')
        slot = slot_time_frame.slot
        self.assertEqual(slot.is_autorenew, False)
        self.assertEqual(slot.start_date, datetime.date.today())
        self.assertEqual(slot.end_date, 
            datetime.date.today() + relativedelta(years=1))
        self.assertEqual(slot_time_frame.end_datetime, None)
        if OrderItem.objects.filter(item_id=slot.id).count() != 1:
            self.fail("Failed to process order items successfully!")
        order_item = OrderItem.objects.get(item_id=slot.id)
        self.assertEqual(order_item.amount, Decimal('499.00'))
        order = order_item.order
        self.assertEqual(order.subtotal, Decimal('499.00'))
        self.assertEqual(order.amount_discounted, Decimal('499.00'))
        self.assertEqual(order.total, Decimal('0.00'))
        if Payment.objects.filter(order=order_item.order).count() != 0:
            self.fail("Created payment record for free item.")
        self.assertEqual(len(mail.outbox), 2)


class TestAdRepOrder(EcommerceTestCase):
    """ Tests for the AdRepOrder functionality. """
    fixtures = ['test_consumer', 'test_ecommerce_views', 'test_promotion']
    urls = 'urls_local.urls_2'

    def test_create_order_rep(self):
        """ Assert an AdRepOrder, AdRepAdvertiser, and AdRepConsumer gets
        associated with this advertiser since one did not exist prior.
        """
        prior_count = len(mail.outbox)
        debug_test_emails(mail.outbox, 'test_create_order_rep')
        advertiser = Advertiser.objects.get(id=605)
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/')
        order = advertiser.businesses.all(
            )[0].order_items.order_by('-id')[0].order
        try:
            AdRepOrder.objects.get(ad_rep=ad_rep, order=order)
        except AdRepOrder.DoesNotExist as error:
            self.fail(error)
        # Assert order is created with the "default promotion" of the promoter
        # 'Firestorm Ad Reps'.
        self.assertEqual(order.promotion_code,
            PromotionCode.objects.get_by_natural_key('zero'))
        # Assert the order acknowledges the promoter_cut.
        self.assertTrue(order.promoter_cut_amount > 0)
        try:
            AdRepAdvertiser.objects.get(ad_rep=ad_rep, advertiser=advertiser)
        except AdRepAdvertiser.DoesNotExist as error:
            self.fail(error)
        try:
            AdRepConsumer.objects.get(ad_rep=ad_rep,
                consumer=advertiser.consumer)
        except AdRepConsumer.DoesNotExist as error:
            self.fail(error)
        self.assertEqual(len(mail.outbox), 3 + prior_count)
        # Welcome aboard email 0 goes to ad rep, 
        # Email 1 is the web receipt, email 2 is admin sale announcement,
        # email 3 goes to the advertiser (1st time purchase) containing a
        # link to their window display. 
        self.assertTrue(' href="mailto:%s">%s</a>' %
            ('consumer@10Coupons.com', 'consumer@10Coupons.com') 
            in mail.outbox[2].alternatives[0][0])
    
    def test_create_order_rep_promo(self):
        """ Assert a non-default promo is preserved. """
        advertiser = Advertiser.objects.get(id=605)
        build_advertiser_session(self, advertiser)
        self.session['add_annual_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        data = self.test_credit_card_data_complete.copy()
        data.update({'code': 'A399'})
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout-success/')
        order = advertiser.businesses.all(
            )[0].order_items.order_by('-id')[0].order
        try:
            AdRepOrder.objects.get(ad_rep=ad_rep, order=order)
        except AdRepOrder.DoesNotExist as error:
            self.fail(error)
        # Assert order is created with this custom promotion of the promoter
        # 'Firestorm Ad Reps'.
        self.assertEqual(order.promotion_code,
            PromotionCode.objects.get_by_natural_key('A399'))

    def test_create_order_rep_bad_promo(self):
        """ Assert a promo not related to Firestorm Ad Rep is not valid. """
        advertiser = Advertiser.objects.get(id=605)
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        data = self.test_credit_card_data_complete.copy()
        data.update({'code': '25% off multiple products'})
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.assertEqual(
            response.context_data['promo_code_form'].errors['code'],
            [u'Tracking Code not valid'])
    
    def test_update_advertiser_rep(self):
        """ Assert a different AdRepAdvertiser gets associated with this
        advertiser. Make sure this different ad_rep gets associated with the 
        AdRepOrder.  Also, make sure the AdRepConsumer does not get
        updated.
        """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        [ad_rep1, ad_rep2] = AD_REP_FACTORY.create_ad_reps(create_count=2)
        self.session['ad_rep_id'] = ad_rep1.id
        self.assemble_session(self.session)
        factory = RequestFactory() 
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        AdRepAdvertiser.objects.create_update_rep(request, advertiser)
        ad_rep_advertiser = AdRepAdvertiser.objects.get(ad_rep=ad_rep1,
            advertiser=advertiser)
        self.assertEqual(ad_rep_advertiser.ad_rep_id, ad_rep1.id)
        self.session['ad_rep_id'] = ad_rep2.id
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/') 
        order = advertiser.businesses.all(
            )[0].order_items.order_by('-id')[0].order
        try:
            AdRepOrder.objects.get(ad_rep=ad_rep2, order=order)
        except AdRepOrder.DoesNotExist as error:
            self.fail(error)
        try:
            AdRepAdvertiser.objects.get(ad_rep=ad_rep2, advertiser=advertiser)
        except AdRepAdvertiser.DoesNotExist as error:
            self.fail(error)
        try:
            AdRepConsumer.objects.get(ad_rep=ad_rep1,
                consumer=advertiser.consumer)
        except AdRepConsumer.DoesNotExist as error:
            self.fail(error)
    
    def test_no_ses_rep_use_con_rep(self):
        """ No rep in session, check if this user has an AdRepConsumer and 
        use this rep as the AdRepAdvertiser and AdRepOrder for this user.
        """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['add_slot_choice'] = '1'
        self.session['ad_rep_id'] = ad_rep.id
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        factory = RequestFactory() 
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        AdRepConsumer.objects.create_update_rep(request, advertiser.consumer)
        ad_rep_consumer = AdRepConsumer.objects.get(ad_rep=ad_rep,
            consumer=advertiser.consumer)
        self.assertEqual(ad_rep_consumer.ad_rep_id, ad_rep.id)
        del request.session['ad_rep_id']
        self.assemble_session(self.session)
        response = self.client.post(reverse('checkout-coupon-purchase'),
            data=self.test_credit_card_data_complete, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout-success/') 
        order = advertiser.businesses.all(
            )[0].order_items.order_by('-id')[0].order
        try:
            AdRepOrder.objects.get(ad_rep=ad_rep, order=order)
        except AdRepOrder.DoesNotExist as error:
            self.fail(error)
        try:
            AdRepAdvertiser.objects.get(ad_rep=ad_rep, advertiser=advertiser)
        except AdRepAdvertiser.DoesNotExist as error:
            self.fail(error)
        try:
            AdRepConsumer.objects.get(ad_rep=ad_rep,
                consumer=advertiser.consumer)
        except AdRepConsumer.DoesNotExist as error:
            self.fail(error)
