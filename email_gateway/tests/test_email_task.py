""" Tests for tasks of email_gateway app. """
# pylint: disable=C0103
from datetime import datetime, timedelta
import logging

from common.test_utils import EnhancedTestCase
from email_gateway.tasks.email_task import EmailTask
from logger.service import log_db_entry

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

class MockEmailTask(EmailTask):
    """ A mock EmailTask with a name, for testing. """
    @classmethod
    def get_task_name(cls):
        """ Return custom task name. """
        return 'task name'

class TestEmailTask(EnhancedTestCase):
    """ This class has the tests for the EmailTask Class """

    @classmethod
    def setUpClass(cls):
        super(TestEmailTask, cls).setUpClass()
        cls.email_task = MockEmailTask()
    
    def test_get_task_date_range(self):
        """ Assert get_task_date_range returns from_date of today and 
        to_date of tomorrow.
        """
        from_date, to_date = self.email_task.get_task_date_range(
            days_past=0, get_missed_days=False)
        today = datetime.now().date()
        self.assertEqual(from_date, today)
        self.assertEqual(to_date, today + timedelta(days=1))

    def test_get_task_date_past_days(self):
        """ Assert get_task_date_range returns from_date 5 days ago. """
        days_past = 5
        from_date, to_date = self.email_task.get_task_date_range(
            days_past=days_past, get_missed_days=False)
        today = datetime.now().date()
        from_date2 = today - timedelta(days=days_past)
        self.assertEqual(from_date, from_date2)
        self.assertEqual(to_date, from_date2 + timedelta(days=1))

    def test_get_task_date_missed(self):
        """ Assert get_task_date_range returns from_date 5 days ago. There are 
        2 missed days. Task from_date is 5 days ago.
        """
        log_db_entry(self.email_task.get_task_name(), 'EMAIL', '{}',
            datetime.now().date() - timedelta(days=2))
        days_past = 5
        from_date, to_date = self.email_task.get_task_date_range(
            days_past=days_past)
        today = datetime.now().date()
        from_date2 = today - timedelta(days=days_past)
        self.assertEqual(from_date, from_date2 - timedelta(days=2))
        self.assertEqual(to_date, from_date2 + timedelta(days=1))
   
    def test_get_task_date_missed_max(self):
        """ Assert get_task_date_range returns accurate from_date. There are 5 
        missed days. Task from_date is 7 days ago.
        """
        log_db_entry('task name', 'EMAIL', '{}',
            datetime.now().date() - timedelta(days=10)) # > 5 missed days
        days_past = 7
        from_date, to_date = self.email_task.get_task_date_range(
            days_past=days_past)
        today = datetime.now().date()
        from_date2 = today - timedelta(days=days_past)
        # 5 days is default max missed days
        self.assertEqual(from_date, from_date2 - timedelta(days=5))
        self.assertEqual(to_date, from_date2 + timedelta(days=1))

    def test_get_task_date_default_max(self):
        """ Assert get_task_date_range returns accurate from_date. If log not 
        found for this task, set to max days to 0 days, not max.
        """
        days_past = 7
        from_date = self.email_task.get_task_date_range(
            days_past=days_past, max_days=30)[0]
        today = datetime.now().date()
        self.assertEqual(from_date, today - timedelta(days_past))

    def test_has_task_run_today(self):
        """ Assert has_task_run_today returns True only when task has run 
        today with status = EMAIL.
        """
        self.assertFalse(self.email_task.has_task_run_today())
        log_db_entry(self.email_task.get_task_name(), 'EMAIL', {})
        self.assertTrue(self.email_task.has_task_run_today())
        self.assertFalse(self.email_task.has_task_run_today(rerun=True))
