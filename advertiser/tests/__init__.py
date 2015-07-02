""" Unit tests of advertiser app. """

# Advertiser Tests
from advertiser.tests.test_model import (TestLocationModel,
    TestBusinessProfileModel)
from advertiser.tests.test_views import (TestAdvertiserViews, 
    TestAdvertiserViewsNoMarket, TestAdRepAdvertiser, TestCouponStats, 
    TestRegParentRedirect)
from advertiser.tests.test_account_view import TestAdvertiserAccount

# Business Tests
from advertiser.business.tests.test_service import TestBusinessService
from advertiser.business.tests.test_tasks import TestWebSnap
from advertiser.business.tests.test_views import TestBusinessProfile

# Location Tests
from advertiser.business.location.tests.test_location_services import (
    TestLocationServices)
from advertiser.business.location.tests.test_location_views import (
    TestBusinessLocations, TestCreateLocation)
from advertiser.business.location.tests.test_tasks import TestLocationTasks

