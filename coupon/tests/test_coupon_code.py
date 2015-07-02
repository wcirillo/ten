""" Test of coupon_code module. """

from django.test import TestCase

from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.models import CouponCode
from coupon.service.coupon_code_service import (check_coupon_code, 
    create_coupon_code, create_multiple_coupon_codes)


class TestCouponCode(TestCase):
    """ Test case for coupon_code_service functions. """

    def test_check_coupon_code_good(self):
        """ Assert a valid code for a coupon is created, checked and not used.
        """
        coupon = COUPON_FACTORY.create_coupon()
        coupon_code = create_coupon_code(coupon)
        used_count = check_coupon_code(coupon, coupon_code.code)
        self.assertEqual(used_count, 0)
                
    def test_check_coupon_code_bad(self):
        """ Assert an invalid code for a coupon fails checking. """
        coupons = COUPON_FACTORY.create_coupons(create_count=2)
        coupon_code = create_coupon_code(coupons[0])
        used_count = check_coupon_code(coupons[1], coupon_code.code)
        self.assertEqual(used_count, -1)

    def test_create_coupon_code(self):
        """ Assert create_coupon_code works with various inputs. """
        coupon = COUPON_FACTORY.create_coupon()
        coupon_code = create_coupon_code(coupon)
        another_coupon_code = create_coupon_code(coupon)
        self.assertTrue(coupon_code != another_coupon_code)
        coupon_code = create_coupon_code(coupon, 12)
        self.assertEqual(len(coupon_code.code), 12)
        coupon_code = create_coupon_code(coupon, 8, 4, '-')
        self.assertEqual(len(coupon_code.code), 11)
        coupon_code_set = create_multiple_coupon_codes(coupon, 6)
        self.assertEqual(len(coupon_code_set), 6)
        coupon_code_set = create_multiple_coupon_codes(coupon, 6, 3, '-')
        self.assertEqual(len(coupon_code_set), 6)
        self.assertEqual(len(coupon_code_set[0].code), 3)
        
    def test_create_mult_coupon_codes(self):
        """ Assert multiple codes are created for a coupon. """
        coupon = COUPON_FACTORY.create_coupon()
        preexisting_count = CouponCode.objects.filter(coupon=coupon).count()
        create_multiple_coupon_codes(coupon, 6)
        new_count = CouponCode.objects.filter(coupon=coupon).count()
        self.assertEqual(preexisting_count + 6, new_count)
