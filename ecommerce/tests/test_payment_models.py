""" Tests for payment models of the ecommerce app """

import datetime
from esapi.exceptions import EncryptionException

from django.core.exceptions import ValidationError
from django.test import TestCase

from advertiser.factories.business_factory import BUSINESS_FACTORY
from ecommerce.factories.order_factory import ORDER_FACTORY
from ecommerce.models import CreditCard, Payment, PaymentResponse


class TestPaymentModels(TestCase):
    """ Tests for ecommerce models. """

    def test_save_credit_card(self):
        """ Assert a credit card is saved and encryption and decryption work.
        """
        business = BUSINESS_FACTORY.create_business()
        cc_number = '4111111111111111'
        credit_card = CreditCard(exp_month=5, exp_year=31, 
            card_holder='Testy Test', business= business)
        credit_card.cvv2 = '1234' # Saved on the instance but not the model
        credit_card.encrypt_cc(cc_number)
        credit_card.clean() # Gets cc_type from cc_number
        credit_card.save()
        decrypted = credit_card.decrypt_cc()
        self.assertEquals(cc_number, decrypted)
    
    def test_clean_cc_alpha_dates(self):
        """ Assert a credit card fails cleaning with alpha chars in date fields.
        """
        business = BUSINESS_FACTORY.create_business()
        cc_number = '4111111111111111'
        credit_card = CreditCard()
        credit_card.exp_month = 5
        credit_card.exp_year = '12' # String, not int.
        credit_card.card_holder = 'Testy Test'
        credit_card.business = business
        credit_card.cvv2 = '1234'
        credit_card.encrypt_cc(cc_number)
        with self.assertRaises(ValidationError):
            credit_card.clean()
    
    def test_clean_cc_bad_dates(self):
        """ Assert a credit card fails cleaning with bad dates in date fields.
        """
        business = BUSINESS_FACTORY.create_business()
        cc_number = '4111111111111111'
        credit_card = CreditCard()
        credit_card.exp_month = 0
        credit_card.exp_year = 31
        credit_card.card_holder = 'Testy Test'
        credit_card.business = business
        credit_card.cvv2 = '1234'
        credit_card.encrypt_cc(cc_number)
        with self.assertRaises(ValidationError):
            credit_card.clean()
    
    def test_card_exp_this_month(self):
        """ Assert a credit card passes cleaning if it is expiring this month.
        """
        today = datetime.datetime.today()
        business = BUSINESS_FACTORY.create_business()
        cc_number = '4111111111111111'
        credit_card = CreditCard()
        credit_card.exp_month = today.month
        credit_card.exp_year = int(str(datetime.datetime.today().year)[-2:])
        credit_card.card_holder = 'Testy Test'
        credit_card.business = business
        credit_card.cvv2 = '1234'
        credit_card.encrypt_cc(cc_number)
        try:
            credit_card.clean()
        except ValidationError:
            self.fail('Credit card exp this month failed cleaning.')
    
    def test_card_expired(self):
        """ Assert a credit card fails cleaning if it is expired. """
        business = BUSINESS_FACTORY.create_business()
        cc_number = '4111111111111111'
        credit_card = CreditCard()
        credit_card.exp_month = 1
        credit_card.exp_year = 1
        credit_card.card_holder = 'Testy Test'
        credit_card.business = business
        credit_card.cvv2 = '1234'
        credit_card.encrypt_cc(cc_number)
        with self.assertRaises(ValidationError):
            credit_card.clean()
    
    def test_card_far_future(self):
        """ Assert a credit card with a far future year fails cleaning. """
        business = BUSINESS_FACTORY.create_business()
        cc_number = '4111111111111111'
        credit_card = CreditCard()
        credit_card.exp_month = 1
        credit_card.exp_year = 99
        credit_card.card_holder = 'Testy Test'
        credit_card.business = business
        credit_card.cvv2 = '1234'
        credit_card.encrypt_cc(cc_number)
        with self.assertRaises(ValidationError):
            credit_card.clean()
    
    def test_delete_credit_card(self):
        """ Assert when a credit card is deleted, private info set to none and
        data for audit trail is left intact.
        """
        business = BUSINESS_FACTORY.create_business()
        cc_number = '4111111111111111'
        credit_card = CreditCard(exp_month=5, exp_year=31, 
            card_holder='Deleter Test', business=business)
        credit_card.cvv2 = '4321' # Saved on the instance but not the model
        credit_card.encrypt_cc(cc_number)
        credit_card.clean() # Gets cc_type from cc_number
        credit_card.save()
        credit_card.delete()
        self.assertEquals(credit_card.exp_month, None)
        self.assertEquals(credit_card.exp_year, None)
        self.assertEquals(credit_card.encrypted_number, None)
        self.assertEquals(credit_card.card_holder, None)
        self.assertEquals(credit_card.last_4, '1111')
        self.assertEquals(credit_card.cc_type, 'visa')
    
    def test_bad_decrypt_credit_card(self):
        """ Assert a bogus cipher text failed decryption. """
        business = BUSINESS_FACTORY.create_business()
        credit_card = CreditCard.objects.create(business=business,
            cc_type='visa', last_4='1111')
        credit_card.encrypted_number = 'foo'
        with self.assertRaises(EncryptionException):
            credit_card.decrypt_cc()

    def test_modify_locked_payment(self):
        """ Assert a locked payment cannot be modified. """
        order = ORDER_FACTORY.create_order()
        payment = Payment.objects.create(order=order, is_locked=True)
        payment.is_void = True
        with self.assertRaises(ValidationError):
            payment.save()
    
    def test_delete_locked_payment(self):
        """ Assert a locked payment cannot be deleted. """
        order = ORDER_FACTORY.create_order()
        payment = Payment.objects.create(order=order, is_locked=True)
        with self.assertRaises(ValidationError):
            payment.delete()
    
    def test_save_payment_response(self):
        """ Assert a payment response is cleaned and saved. """
        order = ORDER_FACTORY.create_order()
        payment = Payment.objects.create(order=order)
        payment_response = PaymentResponse(payment=payment, status='A',
            avs_result_code='Y')
        payment_response.clean()
        payment_response.save()
        self.assertEquals(payment_response.avs_result_code, 'YYY')
            
    def test_delete_locked_response(self):
        """ Assert a payment response of a locked payment cannot be deleted. """
        order = ORDER_FACTORY.create_order()
        payment = Payment.objects.create(order=order, is_locked=True)
        payment_response = PaymentResponse.objects.create(payment=payment,
            status='A')
        with self.assertRaises(ValidationError):
            payment_response.delete()
