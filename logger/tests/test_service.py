""" Test services in logger app. """
from datetime import datetime, timedelta
from django.test import TestCase 

from logger.models import LogHistory
from logger.service import log_db_entry, get_last_db_log

class TestService(TestCase):
    """ Tests for service functions of logger app. """    
    
    fixtures = ['test_log_history']
        
    def test_log_entry(self):
        """ Test the service that creates new log entries. """
        yesterday = datetime.now() - timedelta(days=1)
        details = {'msg':'my test log entry'}
        log_db_entry('test_task1', 'ACTION', details,
                     yesterday)
        try:
            log1 = LogHistory.objects.get(
                logger='test_task1', status='ACTION',
                detail_dict=details, execution_date_time=yesterday)
        except LogHistory.DoesNotExist:
            self.fail('Failed saving new log entry.')
        # Add a log entry missing a date (will default).
        self.assertEqual(log1.status, 'ACTION')
        log_db_entry('test_task2', 'ACTION', '')
        try:
            log2 = LogHistory.objects.get(
                logger='test_task2', status='ACTION')
        except LogHistory.DoesNotExist:
            self.fail('Failed saving new log entry with defaulted date.')
        self.assertTrue(log2.execution_date_time > yesterday)
    
    def test_get_last_log(self):
        """ Test service to retrieve last log entry. """
        log1 = get_last_db_log('my_task')
        self.assertEqual(log1.id, 4)
        log2 = get_last_db_log('another_task')
        self.assertEqual(log2.id, 3)
        # Test retrieval of last log of specific status.
        log3 = get_last_db_log('my_task', 'FAIL')
        self.assertEqual(log3.id, 1)        