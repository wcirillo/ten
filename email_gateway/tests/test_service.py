""" Test module for email_gateway services. """
from datetime import datetime, timedelta

from django.test import TestCase

from advertiser.models import Advertiser
from coupon.models import Slot
from email_gateway.config import ABANDONED_COUPON_SCHED_DICT
from email_gateway.service.task_service import (check_email_schedule,
    qry_inactive_email)
from logger.models import LogHistory

class TestService(TestCase):
    """ Test case for service functions of consumer app. """
    
    fixtures = ['test_consumer', 'test_advertiser', 'test_coupon', 
        'test_advertiser_views', 'test_auth_group', 'test_ecommerce', 
        'test_ecommerce_views', 'test_slot', 'test_log_history', 
        'test_subscriber']
        
    def prep_schedule(self):
        """ Prepare the schedule for tests (remove today from the schedule if
        it is exists. 
        """
        self.today = datetime.now().strftime('%Y%m%d')
        self.current_month = datetime.now().strftime('%B')
        try:
            for key in ABANDONED_COUPON_SCHED_DICT[self.current_month]:
                if self.today in ABANDONED_COUPON_SCHED_DICT[
                self.current_month][key]:
                    ABANDONED_COUPON_SCHED_DICT[self.current_month][key].remove(
                    self.today)
        except KeyError:
            self.fail('Current schedule obsolete.')
        self.task_name = 'task_not_found'
        self.today_date_time = datetime.now()

    def test_check_no_schedule(self):
        """ Test to ensure the check_email_schedule service adheres to parameters
        supplied when there is no history or no schedule.
        """
        self.prep_schedule()
        schedule = None
        status = 'EMAIL'
        days = 5
        last_run, process_state, is_odd = check_email_schedule(self.task_name, 
                schedule, status=status, test_mode=False, default_days=days)
        self.assertTrue(last_run < self.today_date_time - timedelta(days=days))
        self.assertEqual(process_state, 'EMAIL')
        self.assertEqual(is_odd, None)
        # Check process_state for interpreted status of log entry to be test.
        last_run, process_state, is_odd = check_email_schedule(self.task_name, 
                schedule, status=status, default_days=days, test_mode=True)
        self.assertTrue(last_run < self.today_date_time - timedelta(days=days))
        self.assertEqual(process_state, 'TESTMODE')
        self.assertEqual(is_odd, None)

    def test_check_email_schedule(self):
        """ Test to ensure the check_email_schedule service adheres to parameters
        supplied when there is a valid schedule.
        """
        self.prep_schedule()
        # Check when date is not in date_list
        schedule = ABANDONED_COUPON_SCHED_DICT
        status = 'EMAIL'
        days = 5
        # With TestMode should return TESTMODE.
        last_run, process_state, is_odd = check_email_schedule(self.task_name, 
                schedule, status=status, default_days=days, test_mode=True)
        self.assertEqual(process_state, 'TESTMODE') 
        self.assertEqual(is_odd, None)
        # When test_mode is False, should abort when not in schedule.
        last_run, process_state, is_odd = check_email_schedule(self.task_name, 
                schedule, status=status, default_days=days, test_mode=False)
        self.assertEqual(process_state, 'ABORT')
        self.assertEqual(is_odd, None)
        # Check task that was run recently.
        log_history = LogHistory.objects.get(id=3)
        log_history.execution_date_time = self.today_date_time
        log_history.save()
        self.task_name = 'another_task'
        status = 'SUCCESS'
        schedule = None
        last_run, process_state = check_email_schedule(self.task_name, 
                schedule, status=status, test_mode=False, default_days=days)[:2]
        self.assertEqual(last_run, self.today_date_time)
        self.assertEqual(process_state, 'ABORT')
        # If it would abort, but test_mode is true, process_state = TESTMODE.
        last_run, process_state = check_email_schedule(self.task_name, 
                schedule, status=status, test_mode=True, default_days=days)[:2]
        self.assertEqual(process_state, 'TESTMODE')
        
        schedule = ABANDONED_COUPON_SCHED_DICT
        # Check when date is NOT in date_list.
        last_run, process_state = check_email_schedule(self.task_name, 
                schedule, status=status, test_mode=False)[:2]
        self.assertEqual(process_state, 'ABORT')
        # Add today to schedule in week 1 and test process_state again.
        ABANDONED_COUPON_SCHED_DICT[
            self.current_month]['week_1'].append(self.today)
        schedule = ABANDONED_COUPON_SCHED_DICT
        last_run, process_state, is_odd = check_email_schedule(self.task_name, 
                schedule, status=status, test_mode=False)
        self.assertEqual(process_state, 'ABORT')
        # Test with today in schedule and last_run acceptable.
        self.task_name = 'my_task'
        status = 'SUCCESS'
        process_state, is_odd = check_email_schedule(self.task_name, 
                schedule, status=status, test_mode=False, default_days=days)[1:]
        self.assertEqual(process_state, 'EMAIL')
        if datetime.now().month % 2 == 0:
            # Week 1 sends will be even numbered businesses only.
            odd_only = 1
        else:
            odd_only = 0
        self.assertEqual(is_odd, odd_only)
        # Try week 2.
        for key in ABANDONED_COUPON_SCHED_DICT[self.current_month]:
            if self.today in ABANDONED_COUPON_SCHED_DICT[self.current_month][key]:
                ABANDONED_COUPON_SCHED_DICT[
                self.current_month][key].remove(self.today)
        ABANDONED_COUPON_SCHED_DICT[
            self.current_month]['week_2'].append(self.today)
        process_state, is_odd = check_email_schedule(self.task_name, 
                schedule, status=status, test_mode=False, default_days=days)[1:]
        self.assertEqual(process_state, 'EMAIL')
        if datetime.now().month % 2 == 0:
            # Week 2 sends will be even numbered businesses only.
            odd_only = 0
        else:
            odd_only = 1
        self.assertEqual(is_odd, odd_only)
        self.assertEqual(process_state, 'EMAIL')
    
    def test_query_inactive_email(self):
        """ Test query filter used to pull businesses for initial_inactive and 
        perpetual_inactive task emails. 
        """
        test_end_date = datetime.now() - timedelta(days=15)
        test_start_date = datetime.now()-timedelta(days=200)
        today = datetime.now()
        yesterday = datetime.now() - timedelta(days=1)
        # Test advertiser cannot belong to advertisers__do_not_market.
        slot_118 = Slot()
        slot_118.end_date = test_end_date
        slot_118.site_id = 2
        slot_118.start_date = test_start_date
        slot_118.business_id = 118
        slot_118.save()
        result = qry_inactive_email(
            advertiser_id=118,
            perpetual=1,
            end_date=today)
        self.assertEqual(0, sum(1 for row in result))
        # Test advertiser with multiple inactive businesses.
        slot_118.business_id = 122
        slot_118.save()
        slot_121 = Slot()
        slot_121.end_date = datetime.now() - timedelta(days=25)
        slot_121.site_id = 2
        slot_121.start_date = test_start_date
        slot_121.business_id = 121
        slot_121.save()
        result = qry_inactive_email(advertiser_id=124, perpetual=1,
            end_date=today)
        self.assertEqual(1, sum(1 for row in result))
        # Test mod_filter.
        result = qry_inactive_email(advertiser_id=124, perpetual=1,
            end_date=today, mod_filter=0)
        self.assertEqual(1, sum(1 for row in result))
        result = qry_inactive_email(advertiser_id=124, perpetual=1,
            end_date=datetime.now(), mod_filter=1)
        self.assertEqual(0, sum(1 for row in result))
        # Exclude advertiser with active slot.
        slot_121.end_date = datetime.now() + timedelta(days=25)
        slot_121.save()
        result = qry_inactive_email(advertiser_id=124, perpetual=1,
            end_date=today)
        self.assertEqual(0, sum(1 for row in result))
        # Must have email subscription "Advertiser Marketing".
        Slot.objects.filter(business__id=113).update(end_date=test_end_date)
        advertiser = Advertiser.objects.get(id=113)
        advertiser.email_subscription = []
        advertiser.save()
        result = qry_inactive_email(advertiser_id=113, perpetual=1,
            end_date=today)
        self.assertEqual(0, sum(1 for row in result))
        # Must have had a slot.
        result = qry_inactive_email(advertiser_id=601, perpetual=1,
            end_date=today)
        self.assertEqual(0, sum(1 for row in result))
        # Test perpetual flag (end_date = vs end_date less then).
        result = qry_inactive_email(advertiser_id=124, perpetual=0,
            end_date=today)
        self.assertEqual(0, sum(1 for row in result))
        slot_121.end_date = yesterday
        slot_121.save()
        result = qry_inactive_email(advertiser_id=124, perpetual=0,
            end_date=datetime.now().date() - timedelta(days=1))
        self.assertEqual(1, sum(1 for row in result))