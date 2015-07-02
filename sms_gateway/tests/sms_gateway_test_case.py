""" A TestCase for many unit tests of the sms_gateway app. """

from django.test import TestCase

from common.contest import check_contest_is_running
from sms_gateway import config

class SMSGatewayTestCase(TestCase):
    """ Centralize common methods. """
    
    def setUp(self):
        self.original_mode = config.TEST_MODE
        config.TEST_MODE = True
        
        # A relevant chuck from the middle of these sms messages ([15:65]).
        self.good_sms = {
            'check': ": See the Email Message from 10LocalCoupons.com Re",
            'hv_email': ": See the Email Message from 10HudsonValleyCoupons",
            'reply_email': ": Reply with your EMAIL ADDRESS, to get 10Coupons ",
            'double': ": Reply YES to get text coupons (4msg/mo) Reply NO",
            'no': "erified. You won't get automatic text coupons. Txt",
            }
        if check_contest_is_running():
            self.good_sms.update({
            'success': ": Sending Local Alerts (4msg/mo)Learn More About $",
            'hv_success': ": Sending H.V. Alerts (4msg/mo)Learn More About $1",
            'hv_consumer': ": Sending H.V. Alerts (4msg/mo)Txt EmailAddress fo",
            'reply_zip': ": Reply w/ZipCode for Coupons& Alrts (4msg/mo) See",
            'opt_out': "t of 10Coupons Alrts You won't get messages & You ",
            })
        else:
            self.good_sms.update({
            'success': ": You'll now get Local Alerts (4msg/mo)Email Coupo",
            'hv_success': ": You'll now get H.V. Alerts (4msg/mo)Email Coupon",
            'hv_consumer': ": You'll now get H.V. Alerts (4msg/mo)Txt EmailAdd",
            'reply_zip': ": Reply w/ZipCode for Text Coupons& Alrts (4msg/mo",
            'opt_out': "t of 10Coupons Alrts You'll no longer receive mess",
            })
    
    def tearDown(self):
        config.TEST_MODE = self.original_mode
