""" Test forms of common app. """

from advertiser.models import BillingRecord
from ecommerce.forms import (CheckoutCouponBillingRecordForm, 
    CheckoutCouponCreditCardForm)
from ecommerce.models import CreditCard
from ecommerce.tests.ecommerce_test_case import EcommerceTestCase

class TestCreditCardCheckoutForm(EcommerceTestCase):
    """ Assert form method functionality. """
    fixtures = ['test_ecommerce_views', 'test_promotion']

    def build_credit_card(self):
        """ Prepare the form submit for a payment submittal. """
        data = self.test_credit_card_data.copy()
        self.credit_card_form = CheckoutCouponCreditCardForm(data=data)
        self.assertTrue(self.credit_card_form.is_valid(), True)

    def common_assertions(self, credit_card):
        """ Assert common results. """
        self.assertEqual(credit_card.business_id, 600)
        self.assertEqual(credit_card.card_holder, 'Adam Eve')
        self.assertEqual(credit_card.cc_type, 'visa')
        self.assertEqual(credit_card.cvv2, '6671')
        self.assertTrue(credit_card.encrypted_number)
        self.assertEqual(credit_card.exp_year, 20)
        self.assertEqual(credit_card.exp_month, 11)
        self.assertEqual(credit_card.is_storage_opt_in, True)
        self.assertEqual(credit_card.last_4, '1111')
        

    def test_new_credit_card(self):
        """ Test creation of new credit card. """
        oldest_card_id = CreditCard.objects.latest('id').id
        self.build_credit_card()
        credit_card = self.credit_card_form.create_or_update(business_id=600)
        self.assertTrue(credit_card.id > oldest_card_id)
        self.common_assertions(credit_card)

    def test_update_existing(self):
        """ Test credit card found and updated. """
        self.build_credit_card()
        credit_card = self.credit_card_form.create_or_update(
            business_id=600, credit_card_id=602)
        self.assertEqual(credit_card.id, 602)
        self.common_assertions(credit_card)
        
    def test_update_non_existing(self):
        """ Test credit card not found to assert new record created. """
        self.build_credit_card()
        oldest_card_id = CreditCard.objects.latest('id').id
        # Credit card record 600 belongs to business 602.
        credit_card = self.credit_card_form.create_or_update(
            business_id=600, credit_card_id=600)
        self.assertTrue(credit_card.id > oldest_card_id)
        self.common_assertions(credit_card)


class TestBillingRecordForm(EcommerceTestCase):
    """ Assert form method functionality. """
    fixtures = ['test_ecommerce_views', 'test_promotion']

    def build_billing_record(self):
        """ Prepare the form post for the checkout submittal. """
        data = self.test_credit_card_data.copy()
        self.billing_record_form = CheckoutCouponBillingRecordForm(data=data)
        self.assertTrue(self.billing_record_form.is_valid(), True)

    def common_assertions(self, billing_record):
        """ Assert common results. """
        self.assertEqual(billing_record.business_id, 600)
        self.assertEqual(billing_record.billing_address1, '1000 Main Street')
        self.assertEqual(billing_record.billing_address2, 'Suite 2332')
        self.assertEqual(billing_record.billing_city, 'Fort Lauderdale')
        self.assertEqual(billing_record.billing_zip_postal, '55555')
        self.assertEqual(billing_record.billing_state_province, 'FL')
    
    def test_new_billing(self):
        """ Test creation of new billing record. """
        oldest_billing_record_id = BillingRecord.objects.latest('id').id
        self.build_billing_record()
        billing_record = self.billing_record_form.create_or_update(
            business_id=600)
        self.assertTrue(billing_record.id > oldest_billing_record_id)
        self.common_assertions(billing_record)

    def test_update_existing(self):
        """ Test billing record found and updated. """
        self.build_billing_record()
        billing_record = self.billing_record_form.create_or_update(
            business_id=600, billing_record_id=603)
        self.assertEqual(billing_record.id, 603)
        self.common_assertions(billing_record)
        
    def test_update_non_existing(self):
        """ Test billing record not found to assert new record created. """
        self.build_billing_record()
        oldest_billing_record_id = BillingRecord.objects.latest('id').id
        # Billing record 602 belongs to business 603.
        billing_record = self.billing_record_form.create_or_update(
            business_id=600, billing_record_id=602)
        self.assertTrue(billing_record.id > oldest_billing_record_id)
        self.common_assertions(billing_record)