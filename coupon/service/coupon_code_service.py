""" Service functions for CouponCode model. """

from django.db import IntegrityError, transaction

from coupon.models import CouponCode
from common.utils import normalize_code, random_code_generator

def check_coupon_code(coupon, code):
    """ Returns -1 if this code is invalid for this coupon, or used_count."""
    code = normalize_code(code)
    try:
        coupon_code = CouponCode.objects.get(coupon=coupon, code=code)
    except CouponCode.DoesNotExist:
        return -1
    return coupon_code.used_count

@transaction.commit_manually
def create_coupon_code(coupon, *args, **kwargs):
    """ Create a coupon_code for this coupon. """
    coupon_code = CouponCode()
    coupon_code.coupon = coupon
    coupon_code.code = random_code_generator(*args, **kwargs)
    # Codes are required to be unique per coupon.
    # If they collide, try once more only.
    try:
        coupon_code.save()
    except IntegrityError:
        transaction.rollback()
        coupon_code.code = random_code_generator(*args, **kwargs)
        coupon_code.save()
    transaction.commit()
    return coupon_code
    
def create_multiple_coupon_codes(coupon, count, *args, **kwargs):
    """ For this coupon create n coupon_codes. """
    coupon_code_set = []
    x = 0
    while x < count:
        coupon_code = create_coupon_code(coupon, *args, **kwargs)
        coupon_code_set.append(coupon_code)
        x += 1
    return coupon_code_set

