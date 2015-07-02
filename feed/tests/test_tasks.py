""" Tests for feed tasks """

import datetime
import logging
from urllib2 import URLError

from django.core.urlresolvers import reverse

from advertiser.models import Advertiser, Business, Location, BillingRecord
from common.test_utils import EnhancedTestCase
from consumer.models import Consumer
from coupon.models import Coupon, CouponType, Offer
from ecommerce.models import Order, CreditCard, Payment
from feed import config
from feed.models import FeedProvider, FeedCoupon, FeedRelationship
from feed.tasks.tasks import (import_nashville_deals, scrape_incentrev_coupons,
    sync_business_to_sugar, sync_business_from_sugar, 
    create_sugar_coupon_expire_task, create_sugar_cc_expire_task,
    sync_all_to_sugar)
from feed.tests.feed_test_case import FeedTestCase
from feed.tests.test_sugar import MockSugar
from feed.sugar import Sugar, dict_to_name_value
from feed.sugar_in import create_sugar_reminder_task
from feed.sugar_out import get_sugar_relationship, build_recent_entry_query

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestTasks(FeedTestCase): 
    """ Test tasks """
    fixtures = ['test_advertiser', 'test_coupon', 'test_slot']
    
    def test_nash_half_off_feed(self):
        """ Test import of nashville half off coupons from feed xml """
        feed_provider_name = "Nashville Half Off Deals"
        advertiser = Advertiser.objects.get(id=114)
        advertiser.is_emailable = False
        advertiser.unemailablereason = 2 # do not email this advertiser
        advertiser.save()
        coupon_count = 2
        feed_url = "http://nash.halfoffdeals.com/inline/promos_xml.php" \
            "?num=%s&link=Yes&logo=Yes" % coupon_count 
        FeedProvider.objects.create(name=feed_provider_name,
            advertiser=advertiser, feed_url=feed_url)
        self.assertEqual(FeedProvider.objects.all().count(), 1)
        import_nashville_deals()
        self.assertEqual(FeedCoupon.objects.all().count(), coupon_count)
        self.assertEqual(FeedRelationship.objects.all().count(), coupon_count)
        self.assertEqual(FeedCoupon.objects.all()[0].feed_provider.advertiser, 
            advertiser)
        self.assertEqual(FeedRelationship.objects.all()[0].coupon.coupon_type, 
            CouponType.objects.get(coupon_type_name='MediaPartner'))
    
    def test_incentrev_scrape_coupons(self):
        """ Test scrape of IncentRev website """
        feed_provider_name = "IncentRev Coupon Scrape"
        advertiser = Advertiser.objects.get(id=114)
        feed_url = "http://bmlnm.incentrev.com/"
        FeedProvider.objects.create(name=feed_provider_name,
            advertiser=advertiser, feed_url=feed_url)
        self.assertEqual(FeedProvider.objects.all().count(), 1)
        self.assertEqual(FeedCoupon.objects.all().count(), 0)
        scrape_incentrev_coupons()
        feed_coupons = FeedCoupon.objects.all()
        if feed_coupons:
            self.assertTrue(feed_coupons.count() > 0)
            for feed_coupon in feed_coupons:
                self.assertTrue(feed_coupon.city != None)
                self.assertTrue(feed_coupon.state_province != None)
            self.assertTrue(FeedRelationship.objects.all().count() > 0)
    
    def test_fake_sync_biz_to_sugar(self):
        """ test sugar sync in TEST_MODE """
        LOG.debug('config.TEST_MODE: %s' % str(config.TEST_MODE))
        if config.TEST_MODE:
            coupon = Coupon.objects.get(id=300)
            sync_business_to_sugar(coupon=coupon)
        self.assertTrue(True)


class TestSugarTasks(EnhancedTestCase): 
    """ Test tasks against the SugarCRM server """
    fixtures = ['test_advertiser', 'test_coupon', 'test_slot', 'test_sales_rep']
    
    try:
        sugar = Sugar(web_service_url=config.SUGAR_SANDBOX_OFFICE_URL)
    except URLError:
        sugar = Sugar(web_service_url=config.SUGAR_SANDBOX_REMOTE_URL)
    
    def test_sync_biz_to_sugar_coupon(self):
        """ Assert sync of coupon business to SugarCRM """
        LOG.debug('test_sync_biz_to_sugar_coupon')
        consumer = Consumer.objects.get(id=300)
        consumer.first_name = 'Danielle'
        consumer.last_name = 'Dongo'
        consumer.save()
        coupon = Coupon.objects.get(id=300)
        location = Location.objects.create(
            business=coupon.offer.business, location_address1='addr1',
            location_address2='addr2', location_city='city',
            location_state_province='st', location_zip_postal='00000',
            location_area_code='800', location_exchange='555', 
            location_number='1234', location_url='http://www.web.com')
            # add phone number fields here
        coupon.location = [location]
        coupon.save()
        advertiser = coupon.offer.business.advertiser
        advertiser.advertiser_name = "FirstName LastName"
        advertiser.save()
        sync_business_to_sugar(coupon=coupon, sugar=self.sugar)
        module = "Accounts"
        query = build_recent_entry_query(module=module, test_mode=True, 
            get_modified=False, start=None)
        # should return list of dict values not account_id
        sugar_list = self.sugar.get_entry_list(module, query)
        self.assertTrue(sugar_list[0]['id'] != -1)
        self.assertEquals(sugar_list[0]['biz_admin_url_c'], 
            ('https://10coupons.com' + reverse('admin:index') + 
             'advertiser/business/114/'))
        # business web url is synced not coupon location url
        self.assertEquals(sugar_list[0]['website'], None)
        self.assertEquals(sugar_list[0]['phone_office'], '(800) 555-1234')
        self.assertEquals(sugar_list[0]['email1'], advertiser.email)

    def test_sync_biz_to_sugar_offer(self):
        """ Assert sync of offer business to SugarCRM """
        LOG.debug('test_sync_biz_to_sugar_offer')
        #business = Business.objects.get(id=114)
        consumer = Consumer.objects.get(id=300)
        consumer.first_name = 'Danielle'
        consumer.last_name = 'Dongo'
        consumer.save()
        offer = Offer.objects.get(id=300)
        offer.create_datetime = datetime.datetime.now()
        offer.save()
        sync_business_to_sugar(offer=offer, sugar=self.sugar)
        module = "Accounts"
        query = build_recent_entry_query(module=module, test_mode=True, 
            get_modified=False, start=None)
        sugar_list = self.sugar.get_entry_list(module, query)
        self.assertTrue(sugar_list[0]['id'] != -1)
        self.assertEquals(sugar_list[0]['email1'], 
            offer.business.advertiser.email)

    def test_sync_biz_to_sugar(self):
        """ Assert business synched to SugarCRM and get_sugar_relationship.
        """
        LOG.debug('test_sync_biz_to_sugar')
        consumer = Consumer.objects.get(id=300)
        consumer.first_name = 'Danielle'
        consumer.last_name = 'Dongo'
        consumer.save()
        business = Business.objects.get(id=114)
        business.business_name = 'test14 biz' # case insensitive business name
        business.save()
        advertiser = business.advertiser
        advertiser.advertiser_name = u"FirstName Lastname"
        advertiser.save()
        sync_business_to_sugar(business=business, sugar=self.sugar)
        module = "Accounts"
        query = build_recent_entry_query(module=module, test_mode=True, 
            get_modified=False, start=None)
        sugar_list = self.sugar.get_entry_list(module, query)
        self.assertTrue(sugar_list[0]['id'] != -1)
        self.assertEquals(sugar_list[0]['email1'], advertiser.email)
        # test if relationship is set to Contacts
        contact_id = get_sugar_relationship(self.sugar, module1=module, 
            module1_id=sugar_list[0]['id'], module2='Contacts')
        self.assertTrue(contact_id is not None)
    
    def test_sync_biz_from_sugar_acct(self):
        """ Assert create of coupon business from SugarCRM account. """
        LOG.debug('test_sync_biz_from_sugar_acct')
        business = Business.objects.get(id=114)
        advertiser = business.advertiser
        module = "Accounts"
        query = build_recent_entry_query(module=module, test_mode=True, 
            get_modified=False, start=None)
        sugar_list = self.sugar.get_entry_list(module, query)
        sugar_dict = sugar_list[0]
        sugar_dict['business_id_c'] = ''
        self.sugar.set_entry(module, dict_to_name_value(sugar_dict))
        billing_record = BillingRecord.objects.get(id=114)
        order = billing_record.orders.all()[0]
        order.delete()
        billing_record.delete()
        business.delete()
        sync_business_from_sugar(test_mode=True, sugar=self.sugar)
        # business is not created since zip is not valid
        try:
            business = Business.objects.get(advertiser=advertiser)
            self.assertTrue(False)
        except business.DoesNotExist:
            self.assertTrue(True)

    def test_sync_from_sugar_contact(self):
        """ Assert create of coupon business from SugarCRM contact. """
        LOG.debug('test_sync_from_sugar_contact')
        business = Business.objects.get(id=114)
        advertiser = Advertiser.objects.get(id=114)
        email = advertiser.email
        module = "Contacts"
        query = build_recent_entry_query(module=module, test_mode=True, 
            get_modified=False, start=None)
        sugar_list = self.sugar.get_entry_list(module, query)
        sugar_dict = sugar_list[0]
        sugar_dict['advertiser_id_c'] = ''
        self.sugar.set_entry(module, dict_to_name_value(sugar_dict))
        billing_record = BillingRecord.objects.get(id=114)
        order = billing_record.orders.all()[0]
        order.delete()
        billing_record.delete()
        business.delete()
        consumer = Consumer.objects.get(email=email)
        consumer.delete()
        advertiser.delete()
        sync_business_from_sugar(test_mode=True, sugar=self.sugar)
        # business is not created since Sugar record modified by 10Coupons user
        try:
            business = Business.objects.get(advertiser=advertiser)
            self.assertTrue(False)
        except business.DoesNotExist:
            self.assertTrue(True)

    def test_sync_modify_biz_from_sugar(self):
        """ 
        Test task that will sync recently modified and created 
        SugarCRM accounts and contacts data to coupon website. 
        """
        LOG.debug('test_sync_modify_biz_from_sugar')
        sync_business_from_sugar(get_modified=True, sugar=self.sugar)
        self.assertTrue(True)
    
    def test_create_sugar_reminder_task(self):
        """ Assert that a SugarCRM task will be created for this business. """
        LOG.debug('test_create_sugar_reminder_task')
        business = Business.objects.get(id=114)
        subject = 'Test task'
        offset_days = 120
        create_sugar_reminder_task(self.sugar, business, subject, offset_days)
        # get parent_id from get_entry_list email = 
        module = "Accounts"
        query = build_recent_entry_query(module=module, test_mode=True, 
            get_modified=False, start=None)
        sugar_list = self.sugar.get_entry_list(module, query)
        query = "tasks.name = '%s' and tasks.parent_id = '%s'" % (subject, 
            sugar_list[0]['id'])
        sugar_list = self.sugar.get_entry_list(module='Tasks', query=query)
        if sugar_list and len(sugar_list) == 1:
            self.assertTrue(True)
        else:
            self.assertTrue(False)


class TestMockSugarTasks(EnhancedTestCase):
    """ This class has the tests for the Sugar tasks. It will not connect to 
    any Sugar instance. """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_slot', 'test_flyer',
        'test_ecommerce']
            
    def test_create_sugar_cpn_exp_task(self):
        """ Assert that sugar create coupon expires task completes """
        offset_days = 2
        coupon = Coupon.objects.get(id=416)
        coupon.expiration_date = (datetime.date.today() + 
            datetime.timedelta(days=offset_days))
        coupon.save()
        self.assertEqual(create_sugar_coupon_expire_task(MockSugar(), 
            offset_days=offset_days), None)
    
    def test_create_sugar_cc_exp_task(self):
        """ Assert that sugar create cc expire task completes. """
        current_date = datetime.datetime.now()
        order = Order.objects.create(billing_record_id=114)
        credit_card = CreditCard.objects.get(id=500)
        credit_card.exp_month = int(current_date.strftime("%m"))
        credit_card.exp_year = int(current_date.strftime("%y"))
        credit_card.encrypt_cc('4111111111111111')
        credit_card.clean()
        credit_card.save()
        Payment.objects.create(order=order, credit_card=credit_card,
            amount='50.00', method='C', status='p')
        self.assertEqual(create_sugar_cc_expire_task(MockSugar(), 
            test_mode=True), None)
    
    def test_sync_all_to_sugar(self):
        """ Assert that sugar sync all businesses task completes. """
        self.assertEqual(sync_all_to_sugar(sugar=MockSugar()), None)
