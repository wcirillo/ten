""" Tests for tasks of email_gateway app. """
from datetime import datetime, timedelta
import logging

from django.core import mail

from advertiser.models import Business
from common.test_utils import EnhancedTestCase
from coupon.models import Slot
from email_gateway.tasks.initial_inactive_emails import InitialInactiveEmail

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class TestSendInitialInactiveEmail(EnhancedTestCase):
    """ Test send_initial_inactive_email task. """
    fixtures = ['test_advertiser', 'test_coupon', 'test_sales_rep',
        'test_auth_group', 'test_slot', 'test_coupon_views']
    
    def setUp(self):
        super(TestSendInitialInactiveEmail, self).setUp()
        self.yesterday = datetime.now().date()- timedelta(days=1)
        self.initial_inactive_email = InitialInactiveEmail()
        
    def test_active_slot_w_exp_slot(self):
        """ Assert biz with active slot will not process even if other slot
        expired.
        """
        business = Business.objects.get(id=114)
        slot = Slot.objects.get(id=4)
        slot.end_date = self.yesterday
        slot.save()
        self.initial_inactive_email.run(business=business)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_couponless_business(self):
        """Test biz without paid coupons in history will not process email. """
        business = Business.objects.get(id=118)
        business.advertiser.auth_groups = []
        business.save()
        self.initial_inactive_email.run(business=business)
        self.assertEqual(len(mail.outbox), 0)
        
    def test_business_do_not_market(self):
        """Test biz in advertiser_do_not_market authgroup. """
        business = Business.objects.get(id=119)
        business.advertiser.auth_groups = [2]
        business.save()
        self.initial_inactive_email.run(business=business)
        self.assertEqual(len(mail.outbox), 0)
        
    def test_inactive_email_success(self):
        """Test content or valid expired/inactive slot for business account. """
        business = Business.objects.get(id=119)
        slot = Slot.objects.get(id=10)
        slot.business = business
        slot.end_date = self.yesterday
        slot.save()
        self.initial_inactive_email.run(business=business)
        businesses = Business.objects.filter(
            slots__end_date=self.yesterday, 
            offers__coupons__coupon_type=3
            ).exclude(slots__end_date__gt=self.yesterday)
        self.assertTrue(len(mail.outbox) > 0)
        biz_name = businesses[0].business_name
        self.assertTrue(biz_name in mail.outbox[0].subject)
        self.assertTrue('Potential Customers are look' in
            mail.outbox[0].subject)
        self.assertTrue('Put your business back on the website'
            in mail.outbox[0].body)
        self.assertTrue('This is how the coupon looked last time'
            in mail.outbox[0].alternatives[0][0])
        self.assertTrue('Reputable Salesperon' in mail.outbox[0].body)
