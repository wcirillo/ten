""" Views for ecommerce app. """

import datetime
from dateutil import relativedelta
import logging
import os

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.forms.util import ErrorList
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.defaultfilters import date as date_filter
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin

from advertiser.models import Advertiser, BillingRecord
from consumer.service import get_opted_in_count_by_site
from common.session import (delete_all_session_keys_in_list,
    delete_key_from_session, parse_curr_session_keys,
    update_session_by_dictionary)
from coupon.config import TEN_COUPON_RESTRICTIONS
from coupon.models import Coupon, Slot, SlotTimeFrame, FlyerPlacement
from coupon.service.flyer_service import (next_flyer_date,
    add_flyer_subdivision)
from coupon.service.single_coupon_service import SINGLE_COUPON
from coupon.service.slot_service import create_business_families_list
from coupon.service.valid_days_service import VALID_DAYS
from ecommerce.connector import USAePayConnector, ProPayConnector
from ecommerce.forms import (CheckoutCouponCreditCardForm, 
    CheckoutCouponBillingRecordForm, CheckoutCouponPromoCodeForm, 
    CheckoutProductSelection)
from ecommerce.models import (Order, OrderItem, Payment,
    PromotionCode)
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.product_list import (calc_total_of_all_products,
    get_product_quantity, get_slot_renewal_rate, set_selected_product)
from ecommerce.service.promotion_preapproval import check_promotion_preapproval
from ecommerce.service.purchase_service import (prep_vars_for_purchase, 
    reinitialize_credit_card_form, send_purchase_emails, sync_sugar_order)
from ecommerce.tests.test_connector import MockProPayConnector
from firestorm.models import AdRepOrder
from market.service import get_current_site


LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)
LOG.info('Logging Started')

class CouponPurchase(FormMixin, TemplateResponseMixin, View):
    """ Class based view for coupon purchase. """
    template_name = 'ecommerce/display_checkout_coupon_purchase.html'
    context = {}

    def get_success_url(self):
        """ Return the success confirmation page for coupon purchased. """
        return reverse('coupon-purchased')

    def add_order_items(self, order, business_id):
        """ Add items in product list to order. """
        for product in self.session_dict['product_list']:
            order.order_items.add(OrderItem(
                site_id=self.session_dict['site'].id,
                order_id = order.id,
                item_id=None,
                product_id=product[0],
                business_id=business_id,
                amount=product[1],
                description=_('%s') % (product[2]),
                start_datetime=product[3],
                end_datetime=product[4]))

    @staticmethod
    def annual_savings(annual_price, monthly_price):
        """ Return annual savings ( (monthly_price X 12) - annual_price) """
        if annual_price and monthly_price:
            return monthly_price * 12 - annual_price

    def get_slot_and_coupon(self, request, business_id):
        """ Return the slot for this purchased coupon. """
        coupon = None
        if not self.session_dict['current_slot_id']:
            # We are buying a slot with a coupon association
            # Set coupon_type = 3 is set for "Paid" and re-save the coupon
            # with the new coupon_type after payment was successfully
            # processed.
            coupon = Coupon.objects.get(
                id=self.session_dict['this_coupon']['coupon_id'])
            self.session_dict['this_coupon']['coupon_type_id'] = 3
            request.session.modified = True
            coupon.coupon_type_id = 3
            coupon.save()
            slot_renewal_rate = \
                get_slot_renewal_rate(self.session_dict['product_list'])[0]
            if self.selected_product_id == 3:
                auto_renew = False
                slot_end_date = datetime.date.today() + \
                    relativedelta.relativedelta(years=1)
            else:
                auto_renew = True
                slot_end_date = datetime.date.today() + \
                    relativedelta.relativedelta(months=1)
            slot = Slot.objects.create(site_id=self.session_dict['site'].id,
                business_id=business_id,
                renewal_rate=slot_renewal_rate, is_autorenew=auto_renew,
                end_date=slot_end_date)
            SlotTimeFrame.objects.create(slot_id=slot.id,
                coupon_id=coupon.id)
        else:
            slot = Slot.objects.get(id=self.session_dict['current_slot_id'])
        return slot, coupon

    def process_coupon_free_purchase(self, request):
        """ Alternative process for when a coupon is free, ex: tracking code.
        """
        self.session_dict = prep_vars_for_purchase(request)
        business_id = self.session_dict['this_business']['business_id']
        # Get product Flyer Placement.
        promo_code = request.session.get('promo_code', None)
        # BillingRecord Instance.
        billing_record = BillingRecord.objects.create(business_id=business_id)
        order = Order.objects.create(billing_record=billing_record,
            promotion_code=PromotionCode.objects.get(code__iexact=promo_code),
            method = 'V')
        self.add_order_items(order, business_id)
        slot, coupon = self.get_slot_and_coupon(request, business_id)
        # Update all order_item.item_id's with the slot id now that we have
        # created the slot.
        for order_item in order.order_items.order_by('start_datetime'):
            order_item.item_id = slot.id
            order_item.save()
            if order_item.product_id == 1:
                flyer_placement = FlyerPlacement.objects.create(
                    site_id=slot.site_id,
                    slot=slot,
                    send_date=order_item.start_datetime)
                add_flyer_subdivision(request, flyer_placement)
        request.session['order_id'] = order.id
        send_purchase_emails(
            request, self.selected_product_id, order.id, coupon)
        if settings.SUGAR_SYNC_MODE:
            # Sync this coupon business to SugarCRM
            sync_sugar_order(current_slot_id=True, coupon=coupon)
        return HttpResponseRedirect(reverse('coupon-purchased'))

    def process_promo_code(self, request, site):
        """ Process the promo code.

        Preconditions: only a valid promotion_code is placed in the session.
        """
        product_list = request.session['product_list']
        total = subtotal = calc_total_of_all_products(product_list)
        self.promotion_code = False
        self.context.update({
            'subtotal': subtotal,
            'amount_discounted': False,
            'total': total,
            })
        if not self.promo_code:
            if 'hsdemo' in os.uname()[1]:
                self.promo_code = 'demo'
                request.session['promo_code'] = 'demo'
        if self.promo_code:
            self.promotion_code = PromotionCode.objects.get(
                code__iexact=self.promo_code)
            try:
                subtotal, amount_discounted, total = \
                    check_promotion_preapproval(self.promotion_code,
                        Advertiser.objects.get(id=parse_curr_session_keys(
                                request.session, ['advertiser_id']
                            )['advertiser_id']),
                    product_list, request)
                self.context.update({
                    'subtotal': subtotal,
                    'amount_discounted': amount_discounted,
                    'total': total,
                    })
            except ValidationError as e:
                # This promo is not valid for this advertiser anymore, reload.
                self.context.update({
                    'js_checkout_coupon_purchase': 1,
                    'next_flyer_date': next_flyer_date(),
                    'opted_in_count': get_opted_in_count_by_site(site)})
                promo_code_form = CheckoutCouponPromoCodeForm(initial=
                    {'code': request.session['promo_code']})
                promo_code_form.errors.update({
                    'code':ErrorList([e.messages[0]])})
                delete_all_session_keys_in_list(request, ['promo_code'])
                # Hook the validation error message to the ErrorList so it
                # can get printed above the form field when we reload.
                self.context.update({
                    'product_form': CheckoutProductSelection(initial={
                        'selected_product_id': self.selected_product_id}),
                    'credit_card_form': CheckoutCouponCreditCardForm(),
                    'billing_record_form': CheckoutCouponBillingRecordForm(),
                    'promo_code_form': promo_code_form})
                if request.session.get('current_slot_id', None):
                    # We are just buying Flyers
                    self.context.update({
                        'flyer_count': get_product_quantity(product_list, 1)})
                return self.render_to_response(
                    RequestContext(request, self.context))
            if (total == 0 and request.method == "POST"
                    and request.POST.get('submit_frm_free_coupon')):
                return self.process_coupon_free_purchase(request)
        return False

    def prepare(self, request):
        """ Prepare to handle a GET or a POST request. Returns a response
        objects or False if processing should be continued.
        """
        try:
            product_list = request.session['product_list']
            site = get_current_site(request)
            renewal_rate = False
            annual_slot_price = get_product_price(3, site)
            slot_price = get_product_price(2, site)
            self.session_dict = parse_curr_session_keys(request.session,
                ['advertiser_id', 'coupon_id', 'this_business'])
            # Current_slot_id will exist if we are just purchasing flyers.
            if not request.session.get('current_slot_id', None):
                # We are buying coupon placement.
                # Get the locked in renewal rate for this slot.
                renewal_rate, self.selected_product_id = \
                    get_slot_renewal_rate(product_list)
            else:
                self.selected_product_id = 1
            # Calculate total of all products without promos applied.
            # Only Valid Promo Codes will be placed in session.
            self.promo_code = request.session.get('promo_code', None)
            response = self.process_promo_code(request, site)
            if response:
                return response
            self.context.update({
                'promotion_code': self.promotion_code,
                'business_families_count':len(
                    create_business_families_list(business_id=
                        self.session_dict['this_business']['business_id'])),
                'js_checkout_coupon_purchase': 1,
                'next_flyer_date': next_flyer_date(),
                'opted_in_count': get_opted_in_count_by_site(site),
                'renewal_rate': renewal_rate,
                'selected_product_id': self.selected_product_id})
            if not request.session.get('current_slot_id', None):
                # We are buying a slot with a coupon association.
                coupon = (Coupon.objects.all()
                    .select_related('offer', 'offer__business')
                    .get(id=self.session_dict['coupon_id']))
                self.context.update(
                    SINGLE_COUPON.set_single_coupon_dict(request, coupon))
                self.context.update({
                    'business_name':
                        self.session_dict['this_business']['business_name'],
                    'annual_slot_price': annual_slot_price,
                    'slot_price': slot_price,
                    'annual_savings': 
                        self.annual_savings(annual_slot_price, slot_price)
                    })
            if not self.context['total']:
                # Check if total == 0. This will get hit if a FREE Slot is being
                # published. A user must enter a FreeAll promo code on
                # Advertiser Registration to hit this situation.
                return render_to_response('ecommerce/display_free_coupon.html',
                    RequestContext(request, self.context))
        except KeyError as error:
            LOG.error('Key Error: %s' % error)
            return HttpResponseRedirect(reverse('all-coupons'))
        return False

    def process_promotion_form(self, request):
        """ Process the promotion form for the coupon purchase process.
        Returns a response object or False if processing should continue. """
        # Set default order total; will override if promo.
        total = subtotal = calc_total_of_all_products(
            self.session_dict['product_list'])
        promo_code_form = self.context['promo_code_form']
        promotion_code = self.amount_discounted = False
        self.context.update({
            'subtotal': subtotal,
            'total': total})
        if promo_code_form.is_valid():
            promo_code = promo_code_form.cleaned_data.get('code', None)
            if promo_code:
                promotion_code = PromotionCode.objects.get(
                    code__iexact=promo_code)
                advertiser = Advertiser.objects.get(id=
                        self.session_dict['this_advertiser']['advertiser_id'])
                try:
                    subtotal, amount_discounted, total = \
                        check_promotion_preapproval(promotion_code, advertiser,
                            self.session_dict['product_list'], request)
                    session_key_value_dictionary = {'promo_code':promo_code}
                    update_session_by_dictionary(request,
                        session_key_value_dictionary)
                    self.context.update({
                        'subtotal': subtotal,
                        'amount_discounted': amount_discounted,
                        'total': total})
                    if eval(request.POST.get('post_reload', '0')):
                        self.context.update({
                            'promotion_code': promotion_code})
                        # post_reload will be true if the
                        # recalculate button got clicked instead of the
                        # process_credit_card_button.
                        if not total:
                            # Free coupon!
                            # Note: this does *not* use the class method
                            # render_to_response but uses the django shortcut!
                            # TODO: Check for duplicate order w/i the last 3
                            # hours.
                            return render_to_response(
                                'ecommerce/display_free_coupon.html',
                                RequestContext(request, self.context)
                                )
                        return self.render_to_response(
                            RequestContext(request, self.context))
                except ValidationError as e:
                    # This promo is not valid for this advertiser anymore.
                    delete_all_session_keys_in_list(request, ['promo_code'])
                    # Hook the validation error message to the ErrorList so it
                    # can get printed above the form field when we return back
                    # to the client.
                    promo_code_form.errors.update({
                        'code': ErrorList([e.messages[0]])})
                    return self.render_to_response(
                        RequestContext(request, self.context))
            else:
                # Remove the following keys from session if they exist. They are
                # no longer needed at this point. A promo code may have been
                # entered and validated. Then the user may have wiped out the
                # promo code field before they submitted the form again. Wipe
                # this key out so the promo does not get applied.
                delete_all_session_keys_in_list(request, ['promo_code'])
                # If this user applied a promo and wiped it out, then hit
                # recalculate. We want to POST all data back to the form that
                # was filled out and show the original 'Full Price' back to the
                # order summary display.
                if eval(request.POST.get('post_reload', '0')):
                    return self.render_to_response(
                        RequestContext(request, self.context))
        else:
            # Promo code doesn't exist and the user hit recalculate.
            promo_code = None
            if eval(request.POST.get('post_reload', '0')):
                return self.render_to_response(
                    RequestContext(request, self.context))
        if promo_code:
            self.context['promotion_code'] = promotion_code
        return False

    def get_order_card_billing(self, request, business_id, promotion_code):
        """ Return an order, a credit card, and a billing record for this
        purchase process.

        Credit_card_id and billing_record_id will only exist if payment did not
        go through and we need to rerun the payment. These keys get placed into
        session at the end of 'process_coupon_purchase' so that these records
        will be updated instead of new inserts upon rerun of the
        process.
        """
        billing_record_form = self.context['billing_record_form']
        credit_card_form = self.context['credit_card_form']
        credit_card_id = request.session.get('credit_card_id', None)
        credit_card = credit_card_form.create_or_update(
            business_id, credit_card_id)
        billing_record_id = request.session.get('billing_record_id', None)
        billing_record = billing_record_form.create_or_update(
            business_id=business_id, billing_record_id=billing_record_id)
        order_id = request.session.get('order_id', None)
        process_payment_again = \
            request.session.get('process_payment_again', None)
        # TODO: Check for duplicate order within the last 3 hours.
        if process_payment_again and order_id and self.context['total']:
            order = Order.objects.get(id=order_id)
        else:
            order = Order.objects.create(
                billing_record=billing_record,
                promotion_code=promotion_code or None,
                method = 'C')
            request.session['order_id'] = order.id
            self.add_order_items(order, business_id)
        return order, credit_card, billing_record

    def process_valid_payment_form(self, request, promotion_code):
        """ Process these valid forms.

        Precondition: billing_credit_form, billing_record_form and
        promo_card_form have all passed is_valid().
        """
        business_id = self.session_dict['this_business']['business_id']
        credit_card_form = self.context['credit_card_form']
        # Ensure that there is not a payment already in progress
        if request.session.has_key('payment_in_progress'):
            # Check for a completed duplicate payment.
            # Move the next 9 lines over under the else clause when dup check
            # comes back into play.
            credit_card_form.errors.update({'cc_number':
            ErrorList(
            [u'There was an error processing your request. Please resubmit'])})
            self.context.update({
                'credit_card_form': credit_card_form})
            if not self.session_dict['current_slot_id']:
                LOG.info("%s%s %s %s" % (
                    '004 Duplicate Payment Caught, posted back',
                    ' ( coupon id: %s offer id: %s).',
                    str(self.session_dict['this_coupon']['coupon_id']),
                        self.session_dict['this_offer']['offer_id']))
            delete_key_from_session(request, 'payment_in_progress')
            return self.render_to_response(
                RequestContext(request, self.context))
        else:
            request.session['payment_in_progress'] = True
        order, credit_card, billing_record = self.get_order_card_billing(
            request, business_id, promotion_code)
        try:
            connector = USAePayConnector()
            if order.order_items.all()[0].product_id == 3:
                connector = ProPayConnector()
                if request.session.get('tlc_sandbox_testing', False):
                    connector = MockProPayConnector()
            connector.test_mode = request.session.get(
                'tlc_sandbox_testing', False)
            connector.process_payment(order, order.total,
                credit_card, billing_record)
            # Payment went through successfully!
            slot, coupon = self.get_slot_and_coupon(request, business_id)
            # Update all order_item.item_id's with the slot id now that we have
            # created the slot.
            for order_item in order.order_items.order_by('start_datetime'):
                order_item.item_id = slot.id
                order_item.save()
                if order_item.product_id == 1:
                    flyer_placement = FlyerPlacement(
                        site_id=slot.site_id,
                        slot=slot,
                        send_date=order_item.start_datetime)
                    flyer_placement.save()
                    add_flyer_subdivision(request, flyer_placement)
            send_purchase_emails(request, self.selected_product_id, order.id,
                coupon, self.context['renewal_rate'])
            if settings.SUGAR_SYNC_MODE:
                # Sync this coupon business to SugarCRM
                sync_sugar_order(self.session_dict['current_slot_id'],
                    coupon=coupon,
                    business=order.order_items.all()[0].business)
            delete_key_from_session(request, 'payment_in_progress')
            return HttpResponseRedirect(self.get_success_url())
        except ValidationError as e:
            session_key_value_dictionary = {
                'process_payment_again': True,
                'credit_card_id': credit_card.id,
                'billing_record_id': billing_record.id,
                'order_id': order.id}
            update_session_by_dictionary(request, session_key_value_dictionary)
            if promotion_code:
                self.context.update({
                    'promotion_code': promotion_code,
                    'amount_discounted': self.amount_discounted})
            self.context.update({
                'msg_credit_card_problem': e.messages[0]})
            # Payment did not go through.
            delete_key_from_session(request, 'payment_in_progress')
            return self.render_to_response(
                RequestContext(request, self.context))

    def process_coupon_purchase(self, request):
        """ Takes the form POST, processes it, and either re-displays the form
        or the success confirmation page.
        """
        # Current_slot_id will exist if we are just purchasing flyers
        # Get vars needed from session (product_list, site, this_coupon,
        # this_offer, this_business and current_slot_id
        self.session_dict = prep_vars_for_purchase(request, ['this_advertiser'])
        # Populate the Forms.
        promo_code_form = CheckoutCouponPromoCodeForm(request.POST)
        billing_record_form = CheckoutCouponBillingRecordForm(request.POST)
        product_form =  CheckoutProductSelection(request.POST)
        credit_card_form = reinitialize_credit_card_form(request.POST)
        self.context.update({
            'credit_card_form': credit_card_form,
            'billing_record_form': billing_record_form,
            'promo_code_form': promo_code_form,
            'product_form': product_form})
        # Get product Flyer Placement.
        renewal_rate = False
        self.selected_product_id = None
        if not self.session_dict['current_slot_id']:
            # We are buying a slot with a coupon association
            # Get the renewal rate for this slot
            renewal_rate, self.selected_product_id = \
                get_slot_renewal_rate(self.session_dict['product_list'])
            if product_form.is_valid() and self.selected_product_id != \
                    product_form.cleaned_data['selected_product_id']:
                self.selected_product_id = \
                    int(product_form.cleaned_data['selected_product_id'])
                # Update product_list, update add_choice key in session.
                self.session_dict['product_list'] = set_selected_product(
                    request, self.selected_product_id)
                renewal_rate = get_slot_renewal_rate(
                    self.session_dict['product_list'])[0]
                delete_all_session_keys_in_list(request, ['charge_amount',
                    'order_id', 'process_payment_again'])
        # Expiration date is stored as unicode, needs to be datetime for check.
        self.context.update({
            'product_list': self.session_dict['product_list'],
            'renewal_rate': renewal_rate,
            'selected_product_id': self.selected_product_id})
        response = self.process_promotion_form(request)
        if response:
            return response
        # Check all required fields are filled out. Even though we checked the
        # promo_code_form.is_valid() already in the 'promo code' code. We should
        # check it again, because there is a possibility it could still fall in
        # this without being valid. This case would occur if a user submitted
        # the form to process the credit card and the promo code wasn't valid.
        credit_card_form = CheckoutCouponCreditCardForm(request.POST)
        if (credit_card_form.is_valid() and billing_record_form.is_valid()
                and promo_code_form.is_valid()):
            self.context.update(
                {'credit_card_form': credit_card_form,
                'billing_record_form': billing_record_form,
                'promo_code_form': promo_code_form})
            return self.process_valid_payment_form(request,
                self.context['promotion_code'])
        else:
            # Required fields are not filled out. Return to page with form data.
            self.context.update({
                'credit_card_form': credit_card_form})
            return self.render_to_response(
                RequestContext(request, self.context))

    def get(self, request):
        """ Handle a GET request of this view. """
        response = self.prepare(request)
        if response:
            return response
        site = get_current_site(request)
        self.context.update({
            'product_list': request.session['product_list'],
            'credit_card_form': CheckoutCouponCreditCardForm(),
            'billing_record_form': CheckoutCouponBillingRecordForm(
                initial={'billing_state_province':
                    site.get_abbreviated_state_province()}),
            'product_form': CheckoutProductSelection(initial={
                'selected_product_id': self.selected_product_id}),
            'promo_code_form': CheckoutCouponPromoCodeForm(
                initial={'code':self.promo_code or None})})
        return self.render_to_response(RequestContext(request, self.context))

    def post(self, request):
        """ Handle a POST request of this view. """
        response = self.prepare(request)
        if response:
            return response
        return self.process_coupon_purchase(request)


def show_coupon_purchase_success(request):
    """ Display the success confirmation page after coupon purchase. """
    try:
        session_dict = parse_curr_session_keys(request.session, 
            ['advertiser_id', 'this_business'])
        product_list = request.session['product_list']
        # current_slot_id will exist if we are just purchasing flyers.
        current_slot_id = request.session.get('current_slot_id', None)
        renewal_rate = False
        context_dict = {}
        if not current_slot_id:
            # We are buying a slot with a coupon association.
            session_dict.update(parse_curr_session_keys(
                request.session, ['coupon_id']))
            coupon = Coupon.objects.get(id=session_dict['coupon_id'])
            # Get the locked renewal rate for this slot
            for product in product_list:
                if product[0] == 2:
                    renewal_rate = product[1]
        advertiser = Advertiser.objects.get(id=session_dict['advertiser_id'])
        order = Order.objects.get(id=request.session['order_id'])
        AdRepOrder.objects.create_update_rep(request=request, order=order)
        try:
            payment = order.payments.filter(status='A')[0]
            cc_type = payment.credit_card.get_cc_type_display()
        except IndexError:
            payment = Payment(amount='0.00')
            cc_type = ''
        # Session was modified when we changed this_coupon['coupon_type_id'].
        request.session.modified = True
        site = get_current_site(request)
        context_dict.update({
            'js_checkout_coupon_purchase_success':1, 'order':order, 
            'advertiser': advertiser, 'payment': payment, 'cc_type': cc_type,
            'product_list':product_list, 'renewal_rate':renewal_rate,
            'promotion_code':order.promotion_code,
            'amount_discounted':order.amount_discounted,
            'subtotal':order.subtotal, 'total':order.total,
            'next_flyer_date': next_flyer_date(),
            'opted_in_count': get_opted_in_count_by_site(site)})
        if not current_slot_id:
            # We are buying a slot with a coupon association
            coupon.expiration_date = date_filter(coupon.expiration_date, 
                'n/j/y')
            valid_days = VALID_DAYS.create_valid_days_string(coupon)
            # Show Coupon.
            sample_phone_text = """<p><strong>71010:</strong><br />
            10Coupon Alrts: %s Details on Website.</p>""" % coupon.sms
            all_locations = coupon.location.all().order_by('id')
            # Get location coordinates for coupon map display
            location_coords = coupon.get_location_coords_list()
            if location_coords:
                context_dict.update({'location_coords': location_coords})
            context_dict.update(SINGLE_COUPON.set_single_coupon_dict(
                request, coupon))
            context_dict.update({'expiration_date': coupon.expiration_date, 
                'valid_days': valid_days, 
                'sample_phone_text': sample_phone_text,
                'all_locations':all_locations,
                'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS})
        context_dict.update({'renewal_rate': renewal_rate})
        # CLEAN UP, CLEAN UP, CLEAN UP!
        # Remove the following keys from session if they exist. They are no 
        # longer needed at this point.
        delete_all_session_keys_in_list(request, ['promo_code', 
            'process_payment_again', 'credit_card_id', 'billing_record_id', 
            'order_id', 'charge_amount', 'product_list', 'coupon_mode',
            'locked_flyer_price', 'locked_consumer_count', 'add_slot_choice', 
            'add_flyer_choice', 'current_slot_id', 'expiration_date', 
            'add_annual_slot_choice', 'flyer_dates_list'])
        # setup variables for success message
        coupons = Coupon.objects.select_related('offer').filter(
            offer__business__id=session_dict['this_business']['business_id'])
        coupon_count = coupons.count()
        if coupon_count == 1:
            offer = coupons[0].offer
            context_dict.update({'offer':offer})
        # All Open Slots for this business
        open_slots_this_business = Slot.current_slots.get_current_business_slots(
            business_id=session_dict['this_business']['business_id'])
        slot_content_type = ContentType.objects.get(
            app_label='coupon', model='slot')
        purchased_flyers_count = 0
        for slot in open_slots_this_business: 
            purchased_flyers_count += OrderItem.objects.filter(
                item_id=slot.id, product=1, 
                content_type=slot_content_type).count()
        context_dict.update({'purchased_flyers_count':purchased_flyers_count,
            'open_slots': open_slots_this_business.count(),
            'coupon_count':coupon_count,
            'business_name':session_dict['this_business']['business_name']})
        success_template = \
            'ecommerce/display_checkout_coupon_purchase_success.html'
        if current_slot_id:
            success_template = \
                'ecommerce/display_checkout_flyer_purchase_success.html'
        return render_to_response(success_template, context_dict, 
            context_instance=RequestContext(request))
    except KeyError:
        return HttpResponseRedirect(reverse('all-coupons'))

def show_receipt(request, order_id):
    """ Display the receipt associated with a coupon purchase. """
    try:
        # Check if we have an advertiser in session.
        advertiser_id = request.session['consumer']['advertiser']\
            ['advertiser_id']
        try:
            # Check the order_id coming in from the URL is a valid order_id.
            order = Order.objects.select_related().get(id=order_id)
            try:
                # Get the most recent order.
                coupon = Coupon.objects.get(
                    id=order.order_items.all()[0].item_id) 
                advertiser = coupon.offer.business.advertiser
                business = coupon.offer.business
                # If this advertiser in session is associated with the order, 
                # show the receipt.
                if advertiser.id == advertiser_id:
                    try:
                        payment = order.payments.filter(status='A')[0]
                        cc_type = payment.credit_card.get_cc_type_display()
                    except IndexError:
                        payment = Payment(amount='0.00')
                        cc_type = ''
                    context_dict = {'coupon':coupon, 'order':order, 
                        'payment': payment, 'cc_type': cc_type, 
                        'business':business}
                    return render_to_response(
                        'ecommerce/display_print_receipt.html', 
                        context_dict, context_instance=RequestContext(request))
                else:
                    return HttpResponseRedirect(reverse('all-coupons'))
            except IndexError:
                return HttpResponseRedirect(reverse('all-coupons'))
            except Coupon.DoesNotExist:
                # This order ID is not for purchasing a coupon.
                return HttpResponseRedirect(reverse('all-coupons'))
        except Order.DoesNotExist:
            # Order ID not valid.
            return HttpResponseRedirect(reverse('all-coupons'))
    except KeyError:
        # No advertiser in session.
        return HttpResponseRedirect(reverse('all-coupons'))
