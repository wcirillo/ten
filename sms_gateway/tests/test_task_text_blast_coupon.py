"""
Tests of sms_gateway app tasks.
"""
from django.conf import settings

from coupon.models import Action, Coupon, CouponAction, SubscriberAction
from sms_gateway.tasks import text_blast_coupon
from sms_gateway.tests.sms_gateway_test_case import SMSGatewayTestCase

settings.CELERY_ALWAYS_EAGER = True

class TestTextBlast(SMSGatewayTestCase):
    """ Unit tests for text blasting. """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_subscriber', ]
   
    def setUp(self):
        """
        Tests need eager queue. Tests needs access to the request factory.
        """
        super(TestTextBlast, self).setUp()     
        self.action = Action.objects.get(id=11)
        
    def test_text_blast_coupon(self):
        """ 
        Asserts that a valid coupon is blasted.
        """
        coupon = Coupon.objects.get(id=1)
        print(coupon)
        coupon.sms = coupon.get_default_sms()
        print(coupon.sms)
        coupon.save()
        self.assertEquals(CouponAction.objects.filter(
                coupon=coupon,
                action=self.action
            ).count(), 0)
        self.assertEquals(SubscriberAction.objects.filter(
                coupon=coupon,
                action=self.action
            ).count(), 0)
        text_blast_coupon(coupon)
        # Check for subscriber action recorded for this coupon
        self.assertEquals(str(coupon.subscriber_actions.all()[0].action), 
            'Text Blasted')
        try:
            coupon_action = CouponAction.objects.get(
                coupon=coupon,
                action=self.action
                )
            self.assertEquals(coupon_action.count, 1)
        except CouponAction.DoesNotExist:
            self.fail('CouponAction was not created.')
        # Try blasting it again. This is not allowed.
        text_blast_coupon(coupon)
        try:
            coupon_action = CouponAction.objects.get(
                coupon=coupon,
                action=self.action
                )
            self.assertEquals(coupon_action.count, 1)
        except CouponAction.DoesNotExist:
            self.fail('CouponAction was not created.')
        # Try blasting a different coupon of same business now.
        coupon = Coupon.objects.get(id=5)
        text_blast_coupon(coupon)
        self.assertEquals(CouponAction.objects.filter(
                coupon=coupon,
                action=self.action
            ).count(), 0)
               
    def test_blast_not_sms(self):
        """ 
        Assert a coupon that has is_redeemed_by_sms False does not blast. 
        """
        coupon = Coupon.objects.get(id=2)
        text_blast_coupon(coupon)
        self.assertEquals(CouponAction.objects.filter(
                coupon=coupon,
                action=self.action
            ).count(), 0)
        
    def test_blast_not_approved(self):
        """
        Assert a coupon that is not approved does not blast.
        """
        coupon = Coupon.objects.get(id=3)
        text_blast_coupon(coupon)
        self.assertEquals(CouponAction.objects.filter(
                coupon=coupon,
                action=self.action
            ).count(), 0)
        
    def test_blast_no_zip(self):
        """
        Assert a coupon that has no zip code does not blast.
        """
        coupon = Coupon.objects.get(id=4)
        text_blast_coupon(coupon)
        self.assertEquals(CouponAction.objects.filter(
                coupon=coupon,
                action=self.action
            ).count(), 0)
