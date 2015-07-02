""" Unit tests of sms_gateway app of project ten. """

from sms_gateway.tests.test_api import TestApi
from sms_gateway.tests.test_service import TestService
from sms_gateway.tests.test_tasks import (TestTasks, TestTasksNo, TestTasksYes,
    TestTasksZip)
from sms_gateway.tests.test_tasks_email import (TestTasksWordEmail,
    TestTasksEmailAddress)
from sms_gateway.tests.test_task_text_blast_coupon import TestTextBlast
from sms_gateway.tests.test_views import TestReceiveSMS, TestReceiveReport
