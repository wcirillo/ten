""" Tasks for ecommerce app of project ten. """

import datetime
import logging

from celery.task import Task

from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import date as date_filter

from ecommerce.connector import USAePayConnector
from ecommerce.models import Product, Order, OrderItem, Payment
from email_gateway.send import send_email
from firestorm.models import AdRepAdvertiser, AdRepOrder
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class AutoRenewSlotsTask(Task):
    """ Auto-renew slots that are expiring soon. """
    test_mode = USAePayConnector().test_mode
    results_dict = {
        'good_payment_tuples': [], # A list of payment, ad_rep tuples.
        'bad_payment_tuples': []
    }

    def process_slot_payment(self, slot):
        """ Process the auto-renewing payment for a slot. """
        LOG.debug(slot)
        if not slot.is_autorenew:
            LOG.debug('This slot does not auto-renew')
            raise ValidationError("This slot does not auto-renew.")
        try:
            credit_card = slot.business.credit_cards.filter(
                is_storage_opt_in=True).order_by('id')[0]
        except IndexError as error:
            LOG.debug('Cannot auto-renew slot without credit card: %s' % slot)
            raise error
        try:
            billing_record = slot.business.billing_records.all()[0]
        except IndexError as error:
            LOG.debug('Cannot auto-renew slot without billing record: %s' % slot)
            raise error
        exp_date = datetime.date(credit_card.exp_year, credit_card.exp_month, 1)
        if datetime.date.today() > exp_date:
            credit_card.exp_year += 1
        service_start_date = slot.end_date + datetime.timedelta(1)
        end_date = slot.calculate_next_end_date()
        order = Order.objects.create(billing_record=billing_record, method='C')
        product = Product.objects.get(id=2)
        order_item = OrderItem(
            site=slot.site,
            product=product,
            item_id=slot.id,
            business=slot.business,
            description="%s on %s %s - %s. Price Locked on %s" % (
                product.name,
                slot.site.name,
                date_filter(service_start_date, "n/j/y"),
                date_filter(end_date, "n/j/y"),
                date_filter(slot.start_date, "M j, Y")),
            amount=slot.renewal_rate,
            start_datetime=service_start_date,
            end_datetime = datetime.datetime.combine(end_date, datetime.time()))
        order.order_items.add(order_item)
        LOG.debug(order_item.description)
        ad_rep = None
        try:
            connector = USAePayConnector()
            connector.test_mode = self.test_mode
            payment = connector.process_payment(order, order.total,
                credit_card, billing_record)
            # If this advertiser has an ad rep, relate this order.
            advertiser = slot.business.advertiser
            try:
                ad_rep = advertiser.ad_rep_advertiser.ad_rep
                AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
                # Default, no discount promotion code for ad_rep for tracking
                # promoter_cut_amount.
                order.promotion_code_id = 99
                order.save()
            except AdRepAdvertiser.DoesNotExist:
                pass
        except ValidationError:
            LOG.debug('Payment not approved.')
            # If the card failed, this order has a payment.
            payment = order.payments.all()[0]
        LOG.debug('payment: %s' % payment.__dict__)
        if payment.status == 'A':
            slot.end_date = end_date
            LOG.debug('%s extended to %s' % (slot, end_date))
            try:
                slot.save()
            except ValidationError as error:
                LOG.error('%s end date not extended to %s: %s' % (slot,
                    end_date, error))
        return payment, ad_rep

    def auto_renew_slots_by_site(self, site):
        """ Auto renew slots for this site, ignoring any that already have a
        payment (whether approved or not) within the past day.

        Send email for any payments not approved.
        """
        days_away = datetime.date.today() + datetime.timedelta(3)
        one_day_ago = datetime.date.today() - datetime.timedelta(1)
        slots = site.slots.filter(
                is_autorenew=True,
                end_date__lt=days_away,
                end_date__gt=one_day_ago,
                renewal_rate__gt=0
            ).exclude(id__in=
                Payment.objects.filter(
                    order__order_items__product__id__in=[2, 3],
                    create_datetime__gt=one_day_ago
                    ).exclude(order__order_items__item_id=None).values_list(
                        'order__order_items__item_id', flat=True)
            )
        LOG.debug('%s slots for auto-renewal on %s' % (len(slots), site))
        for slot in slots:
            try:
                payment, ad_rep = self.process_slot_payment(slot)
            except IndexError:
                continue
            if payment and payment.status == 'A':
                self.results_dict['good_payment_tuples'].append(
                    (payment, ad_rep))
            else:
                self.results_dict['bad_payment_tuples'].append(
                    (payment, ad_rep))
        return

    def run(self, test_recipients=False):
        """ Loop sites and auto-renew slots. """
        LOG.info('Starting auto-renew slots')
        for site in Site.objects.filter(id__gt=1):
            LOG.debug('Starting auto-renewal for %s' % site)
            self.auto_renew_slots_by_site(site)
        if len(self.results_dict['good_payment_tuples']) > 0:
            # Send notification email
            if settings.SEND_SALE_NOTIFICATIONS is True or test_recipients:
                LOG.debug('sending good payments announcement')
                # Calculate total renewal dollars.
                total = 0
                for payment in zip(*self.results_dict['good_payment_tuples'])[0]:
                    total += payment.order.total
                subject = 'Slot auto-renewal for %s' % (
                    datetime.datetime.today().strftime("%Y-%m-%d"))
                if test_recipients:
                    recipients = test_recipients
                else:
                    recipients = settings.NOTIFY_COMPLETED_SALE_LIST
                send_email(template='ecommerce_renew_notify',
                    site=Site.objects.get(id=1),
                    context={
                        'to_email': recipients,
                        'subject': subject,
                        'show_unsubscribe': False,
                        'payment_tuples':
                            self.results_dict['good_payment_tuples'],
                        'total': total})
        if len(self.results_dict['bad_payment_tuples']) > 0:
            LOG.debug('Bad payments: %s' %
                self.results_dict['bad_payment_tuples'])
            send_email(template='ecommerce_renew_notify',
                site=Site.objects.get(id=1),
                context={
                    'to_email': ['sbywater@10coupons.com',
                        'ckniffin@10coupons.com', 'alenec@10coupons.com'],
                    'subject': 'Auto-renew not approved',
                    'payment_tuples': self.results_dict['bad_payment_tuples'],
                    'total': 0})
        LOG.info('Finished auto-renew slots')
