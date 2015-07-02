""" Unit tests of coupon app. """

# Coupon Tests
from coupon.tests.test_coupon_code import TestCouponCode
from coupon.tests.test_coupon_models import (TestCouponModels,
    TestCurrentCouponManager)
from coupon.tests.test_edit_preview_edit import (
    TestEditModePreviewEdit)
from coupon.tests.test_flyer import (TestAppendCouponToFlyer,
    TestConditionallyAppendCoupon, TestGetNationalText, TestFlyerPhase2,
    TestFlyer, TestGetCouponsForFlyer, TestSetPriorWeeks,
    TestAddFlyerSubdivision, TestGetAvailableFlyerDates)
from coupon.tests.test_flyer_models import (TestFlyerModel,
    TestFlyerSubdivisionModel, TestFlyerPlacementModel,
    TestFlyerPlacementSubdivisionModel, TestFlyerSubjectModel)
from coupon.tests.test_publish_preview_edit import (
    TestPublishModePreviewEdit)
from coupon.tests.test_restrictions_views import (TestCouponRestrictions,
    TestValidDays)
from coupon.tests.test_search_coupons import (TestSearchNothing,
    TestSearchCategoryAndQuery, TestSearchCategory, TestSearchQuery,
    TestSpellingSuggestion)
from coupon.tests.test_service import (TestGetScheduledFlyer, TestService, 
    TestCouponPerformance, TestSortCoupons)
from coupon.tests.test_slot_models import (TestSlotModels,
    TestSlotModelFlyerPlacement, TestCalculateNextEndDate)
from coupon.tests.test_slot_service import (TestGetSlotCoupons,
    TestPublishBusinessCoupon)
from coupon.tests.test_tasks import (TestCreateWidget, TestRecordAction,
    TestTransactionRecordAction, TestCreateFlyers,
    TestCreateFlyersPhase2, TestExtendCouponExpirationDate,
    TestExpireSlotTimeFrames, TestTweetApprovedCoupon, TestFBShareCouponAction)
from coupon.tests.test_views import (TestBusinessUrlClick,
    TestCouponRedirect, TestSendSMSSingleCoupon, TestScanQRCode,
    TestTweetCoupon, TestFlyerClickShowCoupon, TestFacebookCoupon,
    TestWindowDisplay, TestEmailCoupon, TestExternalClickCoupon,
    TestFlyerClickCoupon)
from coupon.tests.test_view_coupon import (TestShowAllCouponsThisBiz,
    TestAllCouponsView, TestAllCouponsFacebookView, TestViewSingleCoupon,
    TestPrintCoupon, TestGenericAllCouponsView)
from coupon.tests.test_views_preview_edit import (TestPreviewEdit,
    TestPreviewEditExpirationDate, TestPreviewEditOffer, TestPreviewEditCoupon,
    TestPreviewEditLocation)
from coupon.tests.test_views_preview_edit_biz import (TestPreviewEditBusiness)
from coupon.tests.test_widget_views import TestWidgetViews

# Offer Tests
from coupon.offer.tests.test_views import TestCreateOffer
