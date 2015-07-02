""" Ecommerce Admin View Testing. """

from common.test_utils import EnhancedTestCase
from ecommerce.models import CreditCard

class TestEcommerceAdminViews(EnhancedTestCase):
    """ Class that tests ecommerce admin views. """
    fixtures = ['admin-views-users.xml', 'test_ecommerce', 'test_advertiser']
    
    def setUp(self):
        super(TestEcommerceAdminViews, self).setUp()
        self.client.login(username='super', password='secret')

    def test_show_credit_card_admin(self):
        """ View credit card in admin. """
        credit_card = CreditCard.objects.get(id=503)
        credit_card.encrypt_cc('371122223332233')
        credit_card.save()
        response = self.client.get('/captain/ecommerce/creditcard/%s/' % 
            credit_card.id)
        self.assertEquals(response.status_code, 200)
        # Next make sure user went to credit card
        self.assertContains(response, credit_card.card_holder)
        self.assertContains(response, credit_card.last_4)
        self.assertContains(response, credit_card.business)
        # Ensure decrypted nor encrypted cc number is displayed on page.
        self.assertNotContains(response, credit_card.encrypted_number)
        self.assertNotContains(response, credit_card.decrypt_cc())
        
    def test_post_cc_no_number(self):
        """ 
        Post credit card changes to form in admin missing credit card number.
        Should update all changed values that were populated, but preserve the
        credit card number, type and last_4 in the database. 
        """
        credit_card = CreditCard.objects.get(id=503)
        credit_card.encrypt_cc('6011222233332224')
        credit_card.cc_type = 'discover'
        credit_card.save()
        response = self.client.post(
            '/captain/ecommerce/creditcard/%s/' % credit_card.id,
            data={'card_holder' : 'King George VIII',
                'exp_month' : 11, 'exp_year' : 20, 
                'is_storage_opt_in' : True,
                'last_4': 2224,
                'cc_type' : 'amex', 'business' : 114}, follow=True)
        self.assertEquals(response.status_code, 200)
        # Next make sure our card number was not removed
        updated_cc = CreditCard.objects.get(id=503)
        self.assertEquals(credit_card.decrypt_cc(), updated_cc.decrypt_cc())
        self.assertEquals(credit_card.last_4, updated_cc.last_4)
        self.assertEquals(credit_card.cc_type, updated_cc.cc_type)
        # Check changed values were saved.
        self.assertEquals(updated_cc.card_holder, 'King George VIII')
        self.assertEquals(updated_cc.exp_month, 11)
        self.assertEquals(updated_cc.exp_year, 20)
        
    def test_post_store_without_card(self):
        """ 
        Post a credit card change that has no cc number in post nor in DB,
        but has the storage_opt_in flag set to True. This should not be allowed,
        and should reset the flag to False until a credit card number exists. 
        """
        credit_card = CreditCard.objects.get(id=504)
        response = self.client.post(
            '/captain/ecommerce/creditcard/%s/' % credit_card.id,
            data = { 'card_holder' : 'King Jesse Lear',
                    'exp_month' : 10, 'exp_year' : 21, 
                    'is_storage_opt_in' : True,
                    'last_4' : 4444,
                    'cc_type' : 'amex', 'business' : 114}, follow=True)
        self.assertEquals(response.status_code, 200)
        # Next make sure our card number was not removed
        updated_cc = CreditCard.objects.get(id=504)
        self.assertEquals(updated_cc.encrypted_number, 
            credit_card.encrypted_number)
        self.assertEquals(updated_cc.last_4, '4444')
        self.assertEquals(credit_card.cc_type, updated_cc.cc_type)
        self.assertEquals(updated_cc.is_storage_opt_in, False)
        # Check changed values were saved.
        self.assertEquals(updated_cc.card_holder, 'King Jesse Lear')
        self.assertEquals(updated_cc.exp_month, 10)
        self.assertEquals(updated_cc.exp_year, 21)
        
    def test_change_last4_stored_card(self):
        """ 
        Post a credit card edit of an existing card stored in the system but 
        only submit a change to the last_4. This change should be denied because
        the card number should always be used to determine the last_4 when it 
        exists. 
        """
        # Encrypt and store card number in database.
        credit_card = CreditCard.objects.get(id=504)
        credit_card.encrypt_cc('6011222233332224')
        credit_card.cc_type = 'discover'
        credit_card.last_4 = '2224'
        credit_card.save()
        response = self.client.post(
            '/captain/ecommerce/creditcard/%s/' % credit_card.id,
            data = {'card_holder' : 'Jim Collins',
                    'exp_month' : 10, 'exp_year' : 21, 
                    'is_storage_opt_in' : True,
                    'last_4' : 4444,
                    'cc_type' : 'amex', 'business' : 114}, follow=True)
        self.assertEquals(response.status_code, 200)
        # Next make sure our card number was not removed
        updated_cc = CreditCard.objects.get(id=504)
        self.assertEquals(updated_cc.encrypted_number, 
            credit_card.encrypted_number)
        self.assertEquals(updated_cc.last_4, credit_card.last_4)
        # Check user received an error msg.
        self.assertContains(response, "You must enter the full")
        self.assertContains(response, 
            "credit card number to change the last 4 of an existing")

