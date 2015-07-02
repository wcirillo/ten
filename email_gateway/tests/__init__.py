""" Testing init for email_gateway app of project ten. """

from email_gateway.tests.test_context_processors import TestGetRepContext
from email_gateway.tests.test_email_model import TestEmailModel
from email_gateway.tests.test_process import TestProcess
from email_gateway.tests.test_send import (TestEmailFilterSettings,
    TestEmailDisplayHeaders)
from email_gateway.tests.test_service import TestService
from email_gateway.tests.test_views import (TestViews, TestRemoteBounceReport,
    TestResetPasswordFromEmail, TestSaleRedirectWithSession)

# Tests for tasks
from email_gateway.tests.test_abandoned_coupon_follow_up_task import (
    TestSendAbandonedCouponEmail)
from email_gateway.tests.test_ad_rep_reminder_email_task import (
    TestAdRepMtgReminder)
from email_gateway.tests.test_consumer_prospect_emails_task import (
    TestSendConsumerProspectEmails)
from email_gateway.tests.test_email_task import TestEmailTask
from email_gateway.tests.test_expiring_coupon import TestExpiringCouponTask
from email_gateway.tests.test_initial_inactive_emails_task import (
    TestSendInitialInactiveEmail)
from email_gateway.tests.test_sale_sends import TestSaleSends
from email_gateway.tests.test_unqualified_consumer_emails_task import (
    TestUnqualifiedEmail)
from email_gateway.tests.test_warm_leads_email_task import (
    TestSendWarmLeadsEmail, TestSendWarmLeadsEmailOld)
