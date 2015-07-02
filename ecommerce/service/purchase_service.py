""" Functions that aid the purchase process. """

from django.conf import settings
from django.core.urlresolvers import reverse

from common.session import parse_curr_session_keys
from coupon.models import Coupon, Slot
from coupon.service.flyer_service import (next_flyer_date)
from ecommerce.forms import CheckoutCouponCreditCardForm
from ecommerce.models import Order
from email_gateway.context_processors import get_rep_context
from email_gateway.send import send_email
from feed.tasks.tasks import sync_business_to_sugar
from firestorm.service import build_adv_url_with_ad_rep
from market.service import get_current_site

def prep_vars_for_purchase(request, _keys=None):
    """ Share variable assignment for purchase process and free purchase
    process. """
    _keys_list = ['product_list', 'this_business'] + (_keys or [])
    current_slot_id = request.session.get('current_slot_id', None)
    if not current_slot_id:
        _keys_list.extend(['this_offer', 'this_coupon'])
    session_dict = parse_curr_session_keys(request.session, _keys_list)
    session_dict.update({'site': get_current_site(request),
        'current_slot_id': current_slot_id})
    return session_dict

def reinitialize_credit_card_form(_post):
    """ Reinitialize_credit_card_form the credit_card_form without validating 
    any fields so we can post the entered data back to the user when they 
    actually submit. (IE: if they enter a promo and hit "APPLY" this form is 
    not actually submitted.
    """
    credit_card_form = CheckoutCouponCreditCardForm()
    initial_data = {}
    for field in credit_card_form.fields:
        field_value_pair = _post.get(field, None)
        if field_value_pair:
            initial_data.update({field: field_value_pair})
    credit_card_form = CheckoutCouponCreditCardForm(initial=initial_data)
    return credit_card_form

def send_purchase_emails(request, product_id, order_id, coupon, renewal_rate=None):
    """ Send purchase emails to advertiser and if applicable, to ad rep.
    Potential emails sent:
        advertiser email receipt: always
        notify email receipt: always (when not demo depending on settings)
        welcome advertiser window display (first slot purchase)
        welcome business ad rep window display (first business' slot purchase)
    """
    order = Order.objects.get(id=order_id)
    session_dict = prep_vars_for_purchase(request)
    business = order.order_items.all()[0].business
    prev_orders = business.billing_records.count()
    try:
        payment = order.payments.filter(status='A')[0]
    except IndexError:
        payment = None
    if not coupon:
        # Get latest coupon to create back button to coupon when page loads 
        # from window display link.
        coupon = business.offers.latest('id').coupons.latest('id')
    shared_context = {
        'to_email': request.session['consumer']['email'],
        'subject': '%s receipt: %s' % (business.business_name, order.invoice), 
        'show_unsubscribe': False,
        'business': business, 
        'product_id': product_id,
        'display_all_recipients': True,
        'open_slot_count': Slot.current_slots.get_current_business_slots(
            business_id=session_dict['this_business']['business_id']).count(),
        'window_display_url': build_adv_url_with_ad_rep(
                business.advertiser, 
                reverse('window-display', kwargs={'coupon_id': coupon.id}))}
    if payment:
        shared_context.update({
            'payment': payment,
            'cc_type': payment.credit_card.get_cc_type_display(),              
            })
    email_context = shared_context.copy()
    email_context.update({
        'prev_orders': prev_orders,
        'order': order, 
        'renewal_rate':renewal_rate,
        'next_flyer_date': next_flyer_date(),
        'num_consumers': 
            session_dict['site'].get_or_set_consumer_count(),
        'num_flyers': Order.objects.latest().order_items.filter(
            product__name__icontains='flyer').count(),
        'coupon_count': Coupon.objects.filter(
            offer__business__advertiser__id=
                business.advertiser.id).count()})
    if not session_dict['current_slot_id']:
        # We are buying a slot with a coupon association.
        shared_context.update({'coupon': coupon})
    cc_ad_rep_if_exists = False
    if prev_orders < 2:
        email_context['subject'] += ' Welcome to %s' % \
            session_dict['site'].domain
    if product_id == 1 or prev_orders > 1:
        cc_ad_rep_if_exists = True
    if not session_dict['current_slot_id']:
        # We are buying a slot with a coupon association.
        email_context['coupon'] = coupon 
    rep_context = get_rep_context(session_dict['site'], 
        request.session['consumer']['email'], cc_rep=cc_ad_rep_if_exists)
    email_context.update(rep_context)
    send_email(template='ecommerce_welcome_receipt', 
        site=session_dict['site'], context=email_context)
    # Send admin notifications if set but not if free and demo.
    email_context['cc_signature_flag'] = False
    if settings.SEND_SALE_NOTIFICATIONS is True \
    and (payment or order.promotion_code.code != 'demo330'):
        if session_dict['current_slot_id']:
            # Just purchasing Flyers.
            sale_type = 'FLYERS PURCHASED'
        else:
            # We are buying a slot with a coupon association.
            sale_type = 'WEB SALE'
        email_context['to_email'] = settings.NOTIFY_COMPLETED_SALE_LIST
        email_context['subject'] = '%s on %s -- %s' % (sale_type,
            session_dict['site'], email_context['subject'])
        send_email(template='ecommerce_welcome_receipt',
            site=session_dict['site'], context=email_context)
    # Send window display to ad rep if they did not receive copy of receipt.
    if email_context.get('has_ad_rep', False) and prev_orders < 2 \
    and product_id in [2, 3]:
        email_context = shared_context.copy()
        email_context.update(get_rep_context(
            session_dict['site'], 
            request.session['consumer']['email'], 
            instance_filter='ad_rep')) # Instance filter prevents ad rep CC.
        # Send email to ad_rep.
        email_context['to_email'] = rep_context.get('signature_email')
        email_context['subject'] = 'Help %s Succeed' % business.business_name
        email_context.update(rep_context)
        send_email(template='ecommerce_ad_rep_window_display',
            site=session_dict['site'], context=email_context)

def sync_sugar_order(current_slot_id, coupon=None, business=None):
    """ Sync business or coupon to sugar, for each order. If buying a coupon 
    slot, sync coupon (based on sync_mode).
    """
    if current_slot_id and business:
        sync_business_to_sugar.delay(business=business)
    else:
        sync_business_to_sugar.delay(coupon=coupon)

