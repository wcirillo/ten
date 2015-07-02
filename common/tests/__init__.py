""" Unit tests for common modules of project ten. """

from common.tests.test_admin_views import TestAdminViews
from common.tests.test_cleaning import TestCustomCleans
from common.tests.test_contest import TestContestEligibility
from common.tests.test_context_processors import (TestCurrentURLNoSubdomain,
    TestSafeUrls)
from common.tests.test_custom_format_for_display import (
    TestCustomDisplayFormatter)
from common.tests.test_custom_validation import TestCustomValidator
from common.tests.test_form import TestSignInForm
from common.tests.test_home import TestShowMarketHome
from common.tests.test_payload_signing import TestPayloadSigning
from common.tests.test_qr_image_cache import TestQRImageCache
from common.tests.test_service import TestService, TestGetHomeData
from common.tests.test_session import TestSessionKeyParser
from common.tests.test_sitemap import TestSitemap
from common.tests.test_blog import TestBlog
from common.tests.test_utils import TestFacebookMetaBuilder, TestUtils
from common.tests.test_views import (TestAdRepSignIn, TestConsumerMap, 
    TestCrossSiteSignIn, TestGenericHomeView, TestGenericLinkRedirects,
    TestGenericViews, TestLocalHomeView, TestLocalView, TestMapViews, 
    TestMarketSearchViews, TestNextFunctionality, TestOptInOptOutView,
    TestPasswordReset, TestShowSampleFlyer, TestSignIn, TestLoader)