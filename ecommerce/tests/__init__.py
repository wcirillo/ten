""" Unit tests of ecommerce app. """

from ecommerce.tests.test_admin_views import TestEcommerceAdminViews
from ecommerce.tests.test_add_flyer_views import (TestAddFlyerByMap,
    TestAddFlyerDates, TestAddFlyerEntireMarket)
from ecommerce.tests.test_add_slot_views import (TestAddNewDisplay,
    TestAddNewDisplayOpenSlots)
from ecommerce.tests.test_form import (TestCreditCardCheckoutForm,
    TestBillingRecordForm)
from ecommerce.tests.test_promoter_models import TestPromoterModels
from ecommerce.tests.test_order_models import TestOrderModels
from ecommerce.tests.test_payment_models import TestPaymentModels
from ecommerce.tests.test_connector import (TestUSAePayConnector, 
    TestProPayConnector, TestMockProPayConnector)
from ecommerce.tests.test_service import (TestCreditCardService,
    TestCalculateCurrentPrice, TestCheckOrderPaid)
from ecommerce.tests.test_product_list import (TestProductService, 
    TestProductList)
from ecommerce.tests.test_tasks import TestAutoRenewSlotsTask
from ecommerce.tests.test_posted_checkout_views import (TestFlyerPurchase,
    TestCouponPurchaseRequest, TestAdRepOrder)
from ecommerce.tests.test_show_checkout_views import (TestShowCouponCheckout,
    TestShowReceipt)
from ecommerce.tests.test_template_tag import TestCurrencyTag
from ecommerce.tests.test_views_promotion import TestPromotion
