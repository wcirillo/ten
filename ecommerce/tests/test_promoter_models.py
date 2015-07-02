""" Tests for promoter models of the ecommerce app """

import datetime
import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase 

from ecommerce.models import Promoter, Promotion, PromotionCode, Order

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestPromoterModels(TestCase):
    """ Tests for ecommerce models. """
    fixtures = ['test_advertiser', 'test_ecommerce', 'test_promotion']
    
    def test_promoter_natural_key(self):
        """ Assert getting a promoter by natural key works. """
        try:
            promoter = Promoter.objects.get_by_natural_key('Firestorm Ad Reps')
        except (Promoter.DoesNotExist, AttributeError) as error:
            self.fail(error)
        self.assertTrue(getattr(promoter, 'natural_key', False))

    def test_promoter_clean_good(self):
        """
        Tests the clean method of Promoter.
        """
        promoter = Promoter()
        try:
            promoter.clean()
        except ValidationError:
            self.fail('Promoter clean failed.')
            
    def test_promoter_clean_bad(self):
        """
        Tests the clean method of Promoter with bad parameters.
        """
        promoter = Promoter()
        promoter.start_date = None
        promoter.end_date = datetime.date(2000, 1, 1)
        try:
            promoter.clean()
            self.fail('Promoter clean passed with expired end date.')
        except ValidationError:
            pass
            
    def test_promoter_delete_good(self):
        """
        Tests deleting a brand new promoter.
        """
        promoter = Promoter()
        promoter.save()
        try:
            promoter.delete()
        except ValidationError:
            self.fail('Deleting a new promoter failed.')
    
    def test_promoter_delete_bad(self):
        """
        Tests deleting a promoter with a used promotion.
        """
        promoter = Promoter.objects.get(id=1)
        try:
            promoter.delete()
            self.fail('Deleted a promoter with used promotion.')
        except ValidationError as error:
            LOG.debug(error)
            
    def test_promotion_natural_key(self):
        """ Assert getting a promotion by natural key works. """
        try:
            promotion = Promotion.objects.get_by_natural_key(
                'Ad Rep No Discount')
        except (Promotion.DoesNotExist, AttributeError) as error:
            self.fail(error)
        self.assertTrue(getattr(promotion, 'natural_key', False))

    def test_promotion_clean_good(self):
        """
        Tests the clean method of Promotion, before and after a save.
        """
        promotion = Promotion()
        promotion.promoter = Promoter.objects.get(id=1)
        try:
            promotion.clean()
        except ValidationError:
            self.fail('Promotion clean failed.')
        self.assertEqual(promotion.monthly_usages_allowed, 0)
        promotion.save()
        print(promotion)
        try:
            promotion.clean()
        except ValidationError:
            self.fail('Promotion clean failed.')
        
    def test_promotion_change_promoter(self):
        """
        Don't allow a used promotion to be switched to a different promoter.
        """
        promotion = Promotion.objects.get(id=201)
        promotion.promoter = Promoter.objects.get(id=2)
        try:
            promotion.clean()
            self.fail('Used promotion cleaned to change promoter.')
        except ValidationError as error:
            LOG.debug(error)
            
    def test_promotion_change_type(self):
        """
        Don't allow a used promotion to change type.
        """
        promotion = Promotion.objects.get(id=201)
        promotion.promo_type = 2
        try:
            promotion.clean()
            self.fail('Used promotion cleaned to change type.')
        except ValidationError as error:
            LOG.debug(error)
        
    def test_promotion_change_amount(self):
        """
        Don't allow a used promotion to change amount.
        """
        promotion = Promotion.objects.get(id=201)
        promotion.promo_amount = 1
        try:
            promotion.clean()
            self.fail('Used promotion cleaned to change amount.')
        except ValidationError as error:
            LOG.debug(error)
        
    def test_change_use_method(self):
        """
        Don't allow a used promotion to change use_method.
        """
        promotion = Promotion.objects.get(id=201)
        promotion.use_method = 2
        try:
            promotion.clean()
            self.fail('Used promotion cleaned to change use_method.')
        except ValidationError as error:
            LOG.debug(error)
        
    def test_change_code_method(self):
        """
        Don't allow a used promotion to change code_method.
        """
        promotion = Promotion.objects.get(id=201)
        promotion.code_method = 'unique'
        try:
            promotion.clean()
            self.fail('Used promotion cleaned to change code_method.')
        except ValidationError as error:
            LOG.debug(error)
             
    def test_promotion_end_date_bad(self):
        """
        Don't allow a promotion to have an end date before start date.
        """
        promotion = Promotion.objects.get(id=201)
        promotion.end_date = datetime.date(2000, 1, 1)
        try:
            promotion.clean()
            self.fail('Promotion cleaned with end date before start date.')
        except ValidationError as error:
            LOG.debug(error)
             
    def test_promotion_unique_once(self):
        """
        Tests cleaning a promotion with use_method "only ever used once" with
        the code_method "everyone gets a unique code."
        """
        promotion = Promotion()
        promotion.promoter = Promoter.objects.get(id=1)
        promotion.use_method = '3'
        promotion.code_method = 'unique'
        try:
            promotion.clean()
            self.fail('Promotion allowed once ever and unique codes.')
        except ValidationError as error:
            LOG.debug(error)
        
    def test_forgot_monthly_uses(self):
        """
        Tests cleaning a promotion with monthly usage, and not specifying
        how many.
        """
        promotion = Promotion()
        promotion.promoter = Promoter.objects.get(id=1)
        promotion.use_method = '4'
        try:
            promotion.clean()
            self.fail('Promotion allowed monthly usage with 0 uses.')
        except ValidationError as error:
            LOG.debug(error)
        
    def test_promotion_normalize(self):
        """
        Test 0% off = $0 off, normalized to the former.
        """
        promotion = Promotion()
        promotion.promoter = Promoter.objects.get(id=1)
        promotion.promo_amount = 0
        promotion.promo_type = '2'
        promotion.clean()
        self.assertEqual(promotion.promo_type, '1')
        
    def test_promotion_delete_good(self):
        """
        Tests deleting a new promotion.
        """
        promotion = Promotion()
        promotion.promoter = Promoter.objects.get(id=1)
        promotion.promo_amount = 0
        promotion.promo_type = '2'
        promotion.save()
        try:
            promotion.delete()
        except ValidationError:
            self.fail('Failed Deleting a new promotion.')
            
    def test_promotion_delete_bad(self):
        """
        Tests deleting a used promotion.
        """
        promotion = Promotion.objects.get(id=201)
        try:
            promotion.delete()
            self.fail('Deleted a used promotion.')
        except ValidationError as error:
            LOG.debug(error)
            
    def test_can_be_used_inactive(self):
        """
        Tests to see if an inactive promotion can be used.
        """
        promotion = Promotion.objects.get(id=211)
        try:
            promotion.can_be_used()
            self.fail('Inactive promotion can be used.')
        except ValidationError as error:
            LOG.debug(error)
            
    def test_promoter_inactive(self):
        """
        Tests to see if a promotion of an inactive promoter can be used.
        """
        promotion = Promotion.objects.get(id=207)
        try:
            promotion.can_be_used()
            self.fail('Inactive promoter has promotion that can be used.')
        except ValidationError as error:
            LOG.debug(error)
            
    def test_promoter_not_approved(self):
        """
        Tests to see if a promotion of promoter not approved can be used.
        """
        promotion = Promotion.objects.get(id=206)
        try:
            promotion.can_be_used()
            self.fail('Not approved promoter has promotion that can be used.')
        except ValidationError as error:
            LOG.debug(error)
            
    def test_promotion_not_started(self):
        """
        Tests to see if a promotion with future start date can be used.
        """
        promotion = Promotion.objects.get(id=212)
        try:
            promotion.can_be_used()
            self.fail('Not started yet promotion can be used.')
        except ValidationError as error:
            LOG.debug(error)
    
    def test_promotion_already_ended(self):
        """
        Tests to see if a promotion with past end date can be used.
        """
        promotion = Promotion.objects.get(id=213)
        try:
            promotion.can_be_used()
            self.fail('Already promotion can be used.')
        except ValidationError as error:
            LOG.debug(error)

    def test_promoter_not_started(self):
        """
        Tests to see if a promotion of a promoter with future start date can be 
        used.
        """
        promotion = Promotion.objects.get(id=214)
        try:
            promotion.can_be_used()
            self.fail('Not started yet promoter has promotion can be used.')
        except ValidationError as error:
            LOG.debug(error)
    
    def test_promoter_already_ended(self):
        """
        Tests to see if a promotion of a promoter with past end date can be 
        used.
        """
        promotion = Promotion.objects.get(id=215)
        try:
            promotion.can_be_used()
            self.fail('Not started yet promoter has promotion can be used.')
        except ValidationError as error:
            LOG.debug(error)
     
    def test_product_inactive(self):
        """
        Tests to see if a promotion of an inactive product can be used.
        """
        promotion = Promotion.objects.get(id=202)
        try:
            promotion.can_be_used()
            self.fail('Inactive product has promotion that can be used.')
        except ValidationError as error:
            LOG.debug(error)
       
    def test_gift_certificate_used(self):
        """
        Tests to see if a promotion that can only be used once, and has been
        used once already, can be used now.
        """
        promotion = Promotion.objects.get(id=210)
        try:
            promotion.can_be_used()
            self.fail('Gift certificate can be reused.')
        except ValidationError as error:
            LOG.debug(error)
     
    def test_once_per_month_used(self):
        """
        Tests to see if a promotion that can only be used once per month, and 
        has been used once already this month, can be used now.
        """
        promotion = Promotion.objects.get(id=208)
        Order.objects.create(billing_record_id=114, promotion_code_id=208)
        # Now check to see if it can be used again...
        try:
            promotion.can_be_used()
            self.fail('Once per month promo cleaned for 2nd use.')
        except ValidationError as error:
            LOG.debug(error)
    
    def test_promotion_code_natrl_key(self):
        """ Assert getting a promotion code by natural key works. """
        try:
            promotion_code = PromotionCode.objects.get_by_natural_key('zero')
        except (PromotionCode.DoesNotExist, AttributeError) as error:
            self.fail(error)
        self.assertTrue(getattr(promotion_code, 'natural_key', False))

    def test_increment_decrement_code(self):
        """
        Tests that a promotion_code.used_count is incremented and decremented
        correctly.
        """
        code = 'incrementer decrementer test'
        promotion_code = PromotionCode.objects.create(promotion_id=201,
            code=code)
        self.assertEqual(PromotionCode.objects.get(code=code).used_count, 0)
        promotion_code.increment_used_count()
        self.assertEqual(PromotionCode.objects.get(code=code).used_count, 1)
        promotion_code.increment_used_count()
        self.assertEqual(PromotionCode.objects.get(code=code).used_count, 2)
        promotion_code.decrement_used_count()
        self.assertEqual(PromotionCode.objects.get(code=code).used_count, 1)
        promotion_code.decrement_used_count()
        self.assertEqual(PromotionCode.objects.get(code=code).used_count, 0)
            
    def test_del_promotion_code(self):
        """
        Tests delete method of PromotionCode.
        """
        code = 'delete method test'
        promotion_code = PromotionCode.objects.create(promotion_id=201,
            code=code)
        promotion_code.increment_used_count()
        try:
            promotion_code.delete()
            self.fail('PromtionCode with used_count > 0 was deleted!')
        except ValidationError:
            pass
        promotion_code.decrement_used_count()
        promotion_code = PromotionCode.objects.get(code=code)
        LOG.debug('used_count: %s' % promotion_code.used_count)
        try:
            promotion_code.delete()
        except ValidationError:
            self.fail('PromotionCode with used_count = 0 was not deleted!')
    
    def test_promotion_code_unicity(self):
        """
        Tests code of CouponCode must be unique. 
        """
        code = 'clean method test'
        PromotionCode.objects.create(promotion_id=201, code=code)
        another_promotion_code = PromotionCode(promotion_id=201, code=code)
        try: 
            another_promotion_code.save()
            self.fail('duplicate code PromotionCode was saved.')
        except IntegrityError:
            pass

