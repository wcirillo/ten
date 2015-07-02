""" Tests for tasks of email_gateway app. """
from datetime import datetime, timedelta
import logging

from django.conf import settings
from django.core import mail

from advertiser.models import Advertiser, Business
from common.test_utils import EnhancedTestCase
from consumer.models import SalesRep
from email_gateway.config import ABANDONED_COUPON_SCHED_DICT
from email_gateway.tasks.abandoned_coupon_follow_up import (
    AbandonedCouponEmailTask)
from logger.models import LogHistory
from logger.service import get_last_db_log, log_db_entry

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class TestSendAbandonedCouponEmail(EnhancedTestCase):
    """ Test case for send_abandoned_coupon_followup email task. """
    fixtures = ['test_consumer', 'test_advertiser', 'test_coupon', 
        'test_advertiser_views', 'test_auth_group', 'test_ecommerce', 
        'test_ecommerce_views', 'test_slot', 'test_log_history', 
        'test_subscriber', 'test_sales_rep']

    def setUp(self):
        super(TestSendAbandonedCouponEmail, self).setUp()
        self.task_name = 'email_gateway.tasks.send_abandoned_coupon_followup'
        self.curr_month = datetime.now().strftime('%B')
        self.today = datetime.now().strftime('%Y%m%d')
        self.abandoned_coupon_email_task = AbandonedCouponEmailTask()

    def update_task_schedule(self, odd_even='clear'):
        """ Use as method for tests to update task schedule (param takes "odd"
        or "even") to permit or prohibit task run for a given business.
        """
        if odd_even == 'odd': # Week one will be the odd week.
            odd_month_week = "week_2"
            even_month_week = "week_1"
        else: # Week one will be even, week two will be odd.
            odd_month_week = "week_1"
            even_month_week = "week_2"
        if datetime.now().month % 2 == 0:
            week = odd_month_week
        else:
            week = even_month_week
        # Remove today's schedule if present.
        for key in ABANDONED_COUPON_SCHED_DICT[self.curr_month]:
            if self.today in ABANDONED_COUPON_SCHED_DICT[self.curr_month][key]:
                ABANDONED_COUPON_SCHED_DICT[
                    self.curr_month][key].remove(self.today)
        try:
            if odd_even != 'clear':
                # Update schedule for today.
                ABANDONED_COUPON_SCHED_DICT[
                    self.curr_month][week].append(self.today)
        except KeyError:
            self.fail("ABANDONED_COUPON_SCHED_DICT outdated; Add months.")
        
    def test_followup_bad_day(self):
        """ Assert abandoned followup not sent on a day that is not permitted.
        """
        # Try to execute task on wrong day
        self.update_task_schedule()
        self.abandoned_coupon_email_task.run()
        self.assertEqual(len(mail.outbox), 0)

    def test_min_sched_days(self):
        """ Assert that the abandoned coupon schedule has at least 2 days left.
        """
        future_dates = 0
        for month in ABANDONED_COUPON_SCHED_DICT:
            for week_key in ABANDONED_COUPON_SCHED_DICT[month]:
                for this_date in ABANDONED_COUPON_SCHED_DICT[month][week_key]:
                    if int(this_date) - int(self.today) > 0:
                        future_dates += 1
        if future_dates < 3:
            self.fail('Abandoned coupon task schedule needs more dates!')

    def test_multiple_times_5_days(self):
        """ Assert task fails to execute for second time within five day span.
        """
        log_db_entry(self.task_name, 'EMAIL', '{}',
            datetime.now().date() - timedelta(days=5))
        # Add today's date to task schedule.
        # One week odd business IDs are sent, the next even, control for tests.
        self.update_task_schedule('odd')
        business = Business.objects.get(id=113)
        self.abandoned_coupon_email_task.run(business)
        self.assertEqual(len(mail.outbox), 0)

    def test_even_business_id(self):
        """ Assert an even business id doesn't get this email (the abandoned_
        coupon_followup email task only processes even or odd business_ids at
        a given run to mimic randomness of perpetual emails within a month).
        """
        # Try to execute task with an (even-numbered business id).
        self.update_task_schedule('odd')
        business = Business.objects.get(id=114)
        business.advertiser.email = 'tasktesterA@10coupons.com'
        business.save()
        self.abandoned_coupon_email_task.run(business)
        self.assertEqual(len(mail.outbox), 0)
        
    def test_nonqualified_business(self):
        """ Assert a business not in advertiser_marketing doesn't get this
        email. """
        self.update_task_schedule('even')
        biz114 = Business.objects.get(id=114)
        biz114.advertiser.email_subscription = []
        biz114.advertiser.email = 'tasktesterA@10coupons.com'
        biz114.save()
        self.abandoned_coupon_email_task.run(biz114)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_task_success(self):
        """ Assert the abandoned coupon follow up email is generated to a
        qualifying advertiser, with the correct content on a day that is
        permitted.
        """
        self.update_task_schedule('odd')
        # Try a valid business
        business = Business.objects.get(id=113)
        business.advertiser.email = 'tasktesterA@10coupons.com'
        business.save()
        self.abandoned_coupon_email_task.run(business)
        self.assertEqual(len(mail.outbox), 1)
        last_log = get_last_db_log(self.task_name, 'EMAIL')
        self.assertEqual(
            last_log.execution_date_time.date(), datetime.now().date())
        biz_name1 = business.business_name
        self.assertTrue('Complete your coupon for' in mail.outbox[0].subject)
        self.assertTrue(biz_name1 in mail.outbox[0].subject)
        target_path = '%s/hudson-valley/sale-redirect/' % (
            settings.HTTP_PROTOCOL_HOST)
        self.assertTrue(target_path in mail.outbox[0].body)
        self.assertTrue(target_path in mail.outbox[0].alternatives[0][0])
        self.assertTrue(biz_name1 in mail.outbox[0].body)
        self.assertTrue(biz_name1 in mail.outbox[0].alternatives[0][0])
        rep = SalesRep.objects.get(sites=1)
        self.assertTrue(rep.consumer.first_name in mail.outbox[0].body)
        self.assertTrue(rep.consumer.first_name in 
            mail.outbox[0].alternatives[0][0])
        self.assertTrue('Display images to view' 
            in mail.outbox[0].alternatives[0][0])
        # Removed promo codes 6/8/11.
        self.assertTrue('10RTG' not in mail.outbox[0].body)
        self.assertTrue('10RTG' not in mail.outbox[0].alternatives[0][0])
        
    def test_send_task_coldcall_biz(self):
        """ Assert that abandoned_coupon_followup task will send to an 
        advertiser in the coldcall group with alternate subject.
        """
        # Test ColdCall-leads group biz.
        self.update_task_schedule('even')
        cold_call_biz = Business.objects.get(id=116)
        mail_count = len(mail.outbox)
        abandoned_coupon_email_task = AbandonedCouponEmailTask()
        abandoned_coupon_email_task.test_mode = 'test@10coupons.com'
        abandoned_coupon_email_task.run(cold_call_biz)
        self.assertTrue(len(mail.outbox) > mail_count)
        self.assertTrue('Publish a coupon for' 
            in mail.outbox[len(mail.outbox)-1].subject)
        self.assertTrue(cold_call_biz.business_name 
                in mail.outbox[len(mail.outbox)-1].subject)
        # Check if log entry has status TESTMODE.
        last_log = LogHistory.objects.get(logger=self.task_name,
            status='TESTMODE')
        self.assertEqual(
            last_log.execution_date_time.date(), datetime.now().date())

    def test_qry_abandon_coupon_email(self):
        """ Test query filter used to pull businesses for 
        abandoned_coupon_followup task emails.
        """
         # Test excluded advertiser that has made purchase.
        cut_off = datetime.now()-timedelta(10)
        result = self.abandoned_coupon_email_task.qry_abandoned_coupon_email(
            mod_filter=None, cut_off=cut_off, advertiser_id=114)
        self.assertEqual(0, sum(1 for row in result))
        # Test excluded advertiser when not subscribed to Advertiser_Marketing.
        advertiser = Advertiser.objects.get(id=113)
        advertiser.email_subscription = []
        advertiser.save()
        result = AbandonedCouponEmailTask().qry_abandoned_coupon_email(
            mod_filter=None, cut_off=cut_off, advertiser_id=113)
        self.assertEqual(0, sum(1 for row in result))
        # Test excluded advertiser when belongs to do_not_market group.
        result = AbandonedCouponEmailTask().qry_abandoned_coupon_email(
            mod_filter=None, cut_off=cut_off, advertiser_id=118)
        self.assertEqual(0, sum(1 for row in result))
        # Test qualified advertiser with multiple businesses.
        result = AbandonedCouponEmailTask().qry_abandoned_coupon_email(
            mod_filter=None, cut_off=cut_off, advertiser_id=124)
        self.assertEqual(1, sum(1 for row in result))
        # Test mod_filter.
        result = AbandonedCouponEmailTask().qry_abandoned_coupon_email(
            mod_filter=0, cut_off=cut_off, advertiser_id=124)
        self.assertEqual(122, result[0].id)
        result = AbandonedCouponEmailTask().qry_abandoned_coupon_email(
            mod_filter=1, cut_off=cut_off, advertiser_id=124)
        self.assertEqual(0, sum(1 for row in result))
        # Test cut_off date.
        business = Business.objects.get(id=122)
        business.business_modified_datetime = datetime.now()
        business.save()
        result = AbandonedCouponEmailTask().qry_abandoned_coupon_email(
            cut_off=cut_off, advertiser_id=124, mod_filter=None)
        self.assertEqual(0, sum(1 for row in result))
        tomorrow = datetime.now()+timedelta(days=1)
        result = AbandonedCouponEmailTask().qry_abandoned_coupon_email(
            cut_off=tomorrow, advertiser_id=124, mod_filter=None)
        self.assertEqual(1, sum(1 for row in result))
