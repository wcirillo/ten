""" Unit tests for firestorm app of project ten. """
from firestorm.tests.test_ad_rep_account_views import (TestAdRepAccountViews,
    TestAdRepConsumers, TestDownlineConsumers, TestRecruitmentAd,
    TestWebAddresses, TestAdvertiserStats, TestAdminViews)
from firestorm.tests.test_ad_rep_photo_upload import TestAdRepPhotoUpload
from firestorm.tests.test_become_ad_rep_views import (TestBecomeAdRepPitch,
    TestBecomeAdRepGeneric, TestApplyReview)
from firestorm.tests.test_models import (TestAdRepModel, TestAdRepOrderModel,
    TestBonusPoolAllocation, TestAdRepLeadModel, TestAdRepLeadAdmin,
    TestAdRepUSState)
from firestorm.tests.test_print_views import TestPrintViews
from firestorm.tests.test_service import (TestBuildURLForAdRepLoading, 
    TestGetConsumerBonusPool)
from firestorm.tests.test_views import (TestAdRepEnrollment, TestAdRepRecommend,
    TestAdRepHomeActive, TestAdRepSignIn, TestAdRepViews, TestContextProcessors,  
    TestRedirectForAdRep, TestStaticAdRepViews, TestVirtualOfficeLink)

# Task tests:
from firestorm.tests.test_ad_rep_invite import TestAdRepInviteTask
from firestorm.tests.test_email_tasks import (TestAdRepLeadEmails,
    TestAdRepLeadMarketMgrPitch, TestCeleryTaskDelay, TestSendEnrollmentEmail,
    TestAdRepLeadPromoTask, TestNotifyNewRecruit)
from firestorm.tests.test_tasks import (TestCreateUpdateAdRep,
    TestUpdateConsumerBonusPool, TestSaveOrder, TestGetDealerDetail, 
    TestEnrollment, TestGetDownlineByDealerID, TestAdRepCompensation,
    TestAllocateBonusPool)
