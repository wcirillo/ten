""" Tests of ecommerce tasks. """

import datetime
from decimal import Decimal
import logging

from django.core import mail
from django.core.exceptions import ValidationError

from advertiser.models import BillingRecord
from common.test_utils import EnhancedTestCase
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import Slot
from ecommerce.models import Order, CreditCard, Payment
from ecommerce.tasks import AutoRenewSlotsTask
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRepAdvertiser, AdRepOrder

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestAutoRenewSlotsTask(EnhancedTestCase):
    """ Test processing of a slot payment. """

    @staticmethod
    def create_credit_card(slot):
        """ Create a credit card to this slot for testing. """
        credit_card = CreditCard.objects.create(
            business=slot.business,
            is_storage_opt_in=True,
            exp_year=30,
            exp_month=12)
        cc_number = '4111111111111111'
        credit_card.encrypt_cc(cc_number)
        credit_card.save() # Gets cc_type from cc_number.
        return credit_card

    def test_process_slot_payment_good(self):
        """ Asserts a slot payment is processed. """
        slot = SLOT_FACTORY.create_slot()
        slot.is_autorenew = True
        slot.save()
        BillingRecord.objects.create(business=slot.business)
        self.create_credit_card(slot)
        task = AutoRenewSlotsTask()
        task.test_mode = True
        payment = task.process_slot_payment(slot)[0]
        self.assertTrue(payment)
        self.assertEquals(payment.amount, Decimal('10'))
        self.assertEquals(payment.status, 'A')
        
    def test_no_auto_renew(self):
        """ Asserts a slot with auto-renew False does not renew. """
        slot = SLOT_FACTORY.create_slot()
        task = AutoRenewSlotsTask()
        task.test_mode = True
        with self.assertRaises(ValidationError):
            task.process_slot_payment(slot)

    def test_ad_rep_order_created(self):
        """ Assert an ad_rep_order is created for the renewal of a slot of an
        advertiser who is related to an ad_rep.
        """
        slot = SLOT_FACTORY.create_slot()
        slot.is_autorenew = True
        slot.save()
        self.create_credit_card(slot)
        BillingRecord.objects.create(business=slot.business)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create(ad_rep=ad_rep,
            advertiser=slot.business.advertiser)
        task = AutoRenewSlotsTask()
        task.test_mode = True
        payment, result_ad_rep = task.process_slot_payment(slot)
        self.assertEqual(ad_rep, result_ad_rep)
        try:
            AdRepOrder.objects.get(order=payment.order)
        except AdRepOrder.DoesNotExist:
            self.fail('AdRepOrder not created.')
        self.assertEqual(payment.order.promotion_code_id, 99)
        self.assertTrue(float(payment.order.promoter_cut_amount) > 0)

    def test_process_auto_renew_slots(self):
        """ Assert slots are auto-renewed creating payments and extending end
        date.
        """
        today = datetime.date.today()
        slots = SLOT_FACTORY.create_slots(create_count=5)
        for index, slot in enumerate(slots):
            slot.start_date = datetime.date(2011, 1, 1)
            slot.end_date = today
            slot.save()
            credit_card = self.create_credit_card(slot)
            if index == 1:
                ad_rep = AD_REP_FACTORY.create_ad_rep()
                AdRepAdvertiser.objects.create(ad_rep=ad_rep,
                    advertiser=slot.business.advertiser)
            if index != 3:
                billing_record = BillingRecord.objects.create(
                    business=slot.business)
                if index == 0:
                    credit_card_0 = credit_card
                    billing_record_0 = billing_record
            if index != 4:
                slot.is_autorenew = True
                slot.save()
        old_payment_count = Payment.objects.count()
        task = AutoRenewSlotsTask()
        task.test_mode = True
        task.run(test_recipients=['auto_renew_slots@example.com'])
        new_payment_count = Payment.objects.count()
        self.assertTrue(new_payment_count > old_payment_count)
        # A good renewal; get updated slot end_date:
        slot = Slot.objects.get(id=slots[0].id)
        try:
            order = Order.objects.get(billing_record=billing_record_0)
        except Order.DoesNotExist:
            self.fail('No payment for a valid auto-renewal')
        self.assertEqual(order.total, slot.renewal_rate) 
        try:
            payment = Payment.objects.get(order__id=order.id)
        except Payment.DoesNotExist:
            self.fail('No payment for a valid auto-renewal')
        self.assertEqual(payment.amount, slot.renewal_rate)
        self.assertEqual(payment.status, 'A')
        self.assertEqual(payment.credit_card, credit_card_0)
        try:
            order_item = order.order_items.all()[0]
        except IndexError:
            self.fail('Order has no order items.')
        self.assertEqual(order_item.product.id, 2)
        self.assertEqual(order_item.ordered_object, slot)
        self.assertEqual(order_item.amount, slot.renewal_rate)
        self.assertEqual(order_item.end_datetime, datetime.datetime.combine(
            slot.end_date, datetime.time()))
        self.assertTrue(slot.end_date > today)
        self.assertTrue(Slot.objects.get(id=slots[1].id).end_date > today)
        self.assertTrue(Slot.objects.get(id=slots[2].id).end_date > today)
        # No renewal because business has no billing record:
        self.assertEqual(Slot.objects.get(id=slots[3].id).end_date, today)
        # No renewal because is_autorenew is False:
        self.assertEqual(Slot.objects.get(id=slots[4].id).end_date, today)
        for email in mail.outbox:
            self.assertNotEqual(email.subject, 'Auto-renew not approved')
        self.assertTrue(ad_rep.first_name in mail.outbox[0].alternatives[0][0])
