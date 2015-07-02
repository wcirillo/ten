""" Test cases for unit tests of the ecommerce app of project ten. """

import datetime

from django.template.defaultfilters import date as date_filter

from advertiser.models import Advertiser
from common.session import build_advertiser_session
from common.test_utils import EnhancedTestCase
from coupon.models import Slot
from coupon.factories.slot_factory import SLOT_FACTORY


class EcommerceTestCase(EnhancedTestCase):
    """ Generic test case for unit test in ecommerce app. """
    test_credit_card_data = {
        "cc_number" : "4111111111111111",
        "exp_month" : "11",
        "exp_year" : "20",
        "cvv_number" : "6671",
        "card_holder" : "Adam Eve",
        "billing_address1": '1000 Main Street',
        "billing_address2": 'Suite 2332',
        "billing_city" : "Fort Lauderdale",
        "billing_zip_postal" : "55555",
        "billing_state_province" : "FL",
        "post_reload":"0"}
    test_credit_card_data_complete = test_credit_card_data.copy()

    def prep_for_flyer_purchase(self):
        """ Create advertiser and slot time frame for flyer date selection. """
        self.slot = SLOT_FACTORY.create_slot()
        self.advertiser = self.slot.business.advertiser
        self.login_build_set_assemble(self.advertiser)

    def common_ecommerce_asserts(self, response):
        """ Common asserts for ecommerce checkout page. """
        self.assertEqual(response.status_code, 200)
        # Page contains our headline.
        self.assertContains(response, str(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer']\
            [self.client.session['current_offer']]['headline']))
        # Page contains our qualifier.
        self.assertContains(response, str(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer']\
            [self.client.session['current_offer']]['qualifier']))

    def credit_card_asserts(self, response, data):
        """ Make assertions that are common to credit card pages. """
        self.common_ecommerce_asserts(response)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, data['billing_state_province'])
        self.assertContains(response, data['billing_zip_postal'])
        self.assertContains(response, data['billing_city'])
        self.assertContains(response, data['cvv_number'])
        self.assertContains(response, data['cc_number'])

    def prep_advertiser_slot_choice_0(self, advertiser_id=602):
        """ Set advertiser session with annual slot choice added. """
        advertiser = Advertiser.objects.get(id=advertiser_id)
        build_advertiser_session(self, advertiser)
        self.session['add_annual_slot_choice'] = '0'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        return advertiser

    def prep_advertiser_slot_choice_1(self):
        """ Set advertiser session with slot choice added. """
        advertiser = Advertiser.objects.get(id=602)
        build_advertiser_session(self, advertiser)
        self.session['add_slot_choice'] = '1'
        self.create_product_list(advertiser.site)
        self.assemble_session(self.session)
        return advertiser

    def make_advertiser_with_slot(self, **kwargs):
        """ Make an advertiser and a slot for his business. """
        self.advertiser = self.make_advrt_with_coupon(**kwargs)
        self.slot = Slot.objects.create(site_id=2,
            business_id=self.advertiser.businesses.all()[0].id,
            renewal_rate=99,
            is_autorenew=True,
            end_date=datetime.date.today() + datetime.timedelta(days=100))

    def common_flyer_purchase_asserts(self, response, first_purchase_date,
            second_purchase_date):
        """ Make assertions common to displaying results of flyer purchase. """
        self.assertContains(response, 'Email Flyer scheduled for %s.' %
            date_filter(first_purchase_date, "M j, Y"))
        self.assertContains(response, 'Email Flyer scheduled for %s.' %
            date_filter(second_purchase_date, "M j, Y"))
