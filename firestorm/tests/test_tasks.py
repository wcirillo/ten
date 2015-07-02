""" Test cases for Celery tasks of firestorm app of project ten. """

import datetime
from decimal import Decimal
import os

from django.db.models import Sum
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from BeautifulSoup import BeautifulStoneSoup
from advertiser.models import BillingRecord
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from coupon.models import Flyer
from ecommerce.factories.order_factory import ORDER_FACTORY
from ecommerce.models import Order, OrderItem, Promotion, PromotionCode
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.factories.ad_rep_lead_factory import AD_REP_LEAD_FACTORY
from firestorm.models import (AdRep, AdRepConsumer, AdRepOrder,
    AdRepWebGreeting, AdRepLead, AdRepCompensation, BonusPoolAllocation,
    BonusPoolFlyer, BONUS_POOL_MIN_SHARERS, BONUS_POOL_PERCENT)
from firestorm.soap import (MockSoap, create_order_detail_xml, 
    find_web_photo_match, process_downline_by_dealer_id, 
    process_enrollment, process_save_order_response, set_ad_rep_parent, 
    validate_order_data)
from firestorm.tests.firestorm_test_case import FirestormTestCase
from firestorm.tasks import (AD_REP_COMPENSATION_TASK, ALLOCATE_BONUS_POOL,
    CREATE_OR_UPDATE_AD_REP, UPDATE_CONSUMER_BONUS_POOL)


class TestCreateUpdateAdRep(FirestormTestCase):
    """ Test case for CreateOrUpdateAdRep task. """

    def test_create_ad_rep(self):
        """ Assert an existing ad_rep is created with replicated website 
        details.
        """
        email = 'test_create_ad_rep@example.com'
        ad_rep_dict = {'email': email, 'firestorm_id': 10,}
        for field in ['url'] + self.ad_rep_repl_website_fields:
            ad_rep_dict[field] = 'test-create-ad-rep'
        CREATE_OR_UPDATE_AD_REP.run(ad_rep_dict)
        ad_rep = AdRep.objects.get(email=email)
        self.assertEqual(ad_rep.url, 'test-create-ad-rep')
        self.assertEqual(ad_rep.first_name, 'test-create-ad-rep')
        self.assertEqual(ad_rep.last_name, 'test-create-ad-rep')
        self.assertEqual(ad_rep.company, 'test-create-ad-rep')
        self.assertEqual(ad_rep.home_phone_number, '')
        self.assertEqual(ad_rep.primary_phone_number, '')
        web_greeting = AdRepWebGreeting.objects.get(ad_rep=ad_rep)
        self.assertEqual(web_greeting.web_greeting, 'test-create-ad-rep')

    def test_update_ad_rep(self):
        """ Assert an existing ad_rep is updated with replicated website 
        details.
        """
        email = 'test_update_ad_rep@example.com'
        ad_rep = AdRep.objects.create(username=email, email=email,
            firestorm_id=11, url='test_update_ad_rep')
        AdRepWebGreeting.objects.create(ad_rep=ad_rep, web_greeting=email)
        ad_rep_dict = {'email': email, 'firestorm_id': 11}
        for field in ['url'] + self.ad_rep_repl_website_fields:
            ad_rep_dict[field] = 'test-update-ad-rep'
        CREATE_OR_UPDATE_AD_REP.run(ad_rep_dict)
        ad_rep = AdRep.objects.get(email=email)
        self.assertEqual(ad_rep.url, 'test-update-ad-rep')
        self.assertEqual(ad_rep.first_name, 'test-update-ad-rep')
        self.assertEqual(ad_rep.last_name, 'test-update-ad-rep')
        self.assertEqual(ad_rep.company, 'test-update-ad-rep')
        self.assertEqual(ad_rep.home_phone_number, '')
        self.assertEqual(ad_rep.primary_phone_number, '')
        self.assertEqual(ad_rep.rank, 'test-update-ad-rep')
        web_greeting = AdRepWebGreeting.objects.get(ad_rep=ad_rep)
        self.assertEqual(web_greeting.web_greeting, 'test-update-ad-rep')
        
    def test_preexisting_consumer(self):
        """ Assert if firestorm provides the email address of a registered 
        consumer, an ad_rep is created from the consumer. Plus check for 
        ad_rep rank and enrollment promo codes.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        ad_rep_dict = {'status': 'Success', 'first_name': consumer.first_name, 
            'last_name': consumer.last_name, 'firestorm_id': '12', 
            'url': 'test-preexisting-consumer', 'company': '', 'rank': 'ADREP',
            'primary_phone_number': '8005551017', 'web_greeting': '', 
            'email': consumer.email, 'home_phone_number': ''}
        CREATE_OR_UPDATE_AD_REP.run(ad_rep_dict)
        ad_rep = AdRep.objects.filter(email=consumer.email)
        self.assertTrue(ad_rep.count())
        self.assertTrue(ad_rep[0].rank)
        promotion = Promotion.objects.all().order_by('-id')[0]
        self.assertTrue('%s %s' % (consumer.first_name, consumer.last_name) 
            in promotion.name)

    def test_preexisting_ad_rep_lead(self):
        """ Assert an ad_rep_lead converts to an ad_rep.
        """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        ad_rep_dict = {'status': 'Success',
            'first_name': ad_rep_lead.first_name,
            'last_name': ad_rep_lead.last_name, 'firestorm_id': '12',
            'url': 'preexisting-lead', 'company': '', 'rank': 'ADREP',
            'primary_phone_number': '8005551017', 'web_greeting': '',
            'email': ad_rep_lead.email, 'home_phone_number': ''}
        CREATE_OR_UPDATE_AD_REP.run(ad_rep_dict)
        ad_rep = AdRep.objects.filter(email=ad_rep_lead.email)
        self.assertTrue(ad_rep.count())
        self.assertTrue(ad_rep[0].rank)
        with self.assertRaises(AdRepLead.DoesNotExist):
            AdRepLead.objects.get(id=ad_rep_lead.id)

    def test_consumer_case_mismatch(self):
        """ Assert case is ignored when checking for preexisting consumer. """
        consumer = CONSUMER_FACTORY.create_consumer()
        ad_rep_dict = {'email': consumer.email.upper(), 'firestorm_id': 13,
            'url': 'upper-cased'}
        for field in self.ad_rep_repl_website_fields:
            ad_rep_dict[field] = ''
        CREATE_OR_UPDATE_AD_REP.run(ad_rep_dict)
        self.assertTrue(AdRep.objects.filter(email=consumer.email).count())

    def test_ad_rep_no_email(self):
        """ Assert an ad_rep_dict with a blank email results in no new AdRep.
        """
        ad_rep_dict = {'email': '', 'firestorm_id': 14,}
        for field in ['url'] + self.ad_rep_repl_website_fields:
            ad_rep_dict[field] = 'ad-rep-no-email'
        CREATE_OR_UPDATE_AD_REP.run(ad_rep_dict)
        try:
            ad_rep = AdRep.objects.get(firestorm_id=14)
            self.fail('AdRep %s created with blank email.' % ad_rep.id)
        except AdRep.DoesNotExist:
            pass


class TestAdRepCompensation(TestCase):
    """ Test case for celery task AdRepCompensationTask. """

    def test_compensation_good(self):
        """ Assert ad_rep_compensations are created for an ad_rep_order. """
        ad_reps = AD_REP_FACTORY.create_generations(create_count=5)
        order = ORDER_FACTORY.create_order()
        AdRepOrder.objects.create(ad_rep=ad_reps[0], order=order)
        ad_rep_compensation = AdRepCompensation.objects.get(ad_rep=ad_reps[0])
        self.assertTrue(ad_rep_compensation.amount, Decimal('79.6'))
        self.assertFalse(ad_rep_compensation.child_ad_rep)
        ad_rep_compensation = AdRepCompensation.objects.get(ad_rep=ad_reps[1])
        self.assertTrue(ad_rep_compensation.amount, Decimal('19.9'))
        self.assertEqual(ad_rep_compensation.child_ad_rep, ad_reps[0])
        ad_rep_compensation = AdRepCompensation.objects.get(ad_rep=ad_reps[2])
        self.assertTrue(ad_rep_compensation.amount, Decimal('4.98'))
        self.assertEqual(ad_rep_compensation.child_ad_rep, ad_reps[1])
        ad_rep_compensation = AdRepCompensation.objects.get(ad_rep=ad_reps[3])
        self.assertTrue(ad_rep_compensation.amount, Decimal('1.24'))
        self.assertEqual(ad_rep_compensation.child_ad_rep, ad_reps[2])
        with self.assertRaises(AdRepCompensation.DoesNotExist):
            AdRepCompensation.objects.get(ad_rep=ad_reps[4])

    def test_redo_invalid(self):
        """ Assert an ad_rep_order that already has compensations will not be
        re-processed.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        order = ORDER_FACTORY.create_order()
        ad_rep_order = AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
        count_after_once = AdRepCompensation.objects.filter(
            ad_rep_order=ad_rep_order).count()
        AD_REP_COMPENSATION_TASK(ad_rep_order.id)
        self.assertEqual(AdRepCompensation.objects.filter(
            ad_rep_order=ad_rep_order).count(), count_after_once)


class TestUpdateConsumerBonusPool(TestCase):
    """ Test case for celery tasks update_consumer_bonus_pool. """

    def test_update_bonus_pool_good(self):
        """ Assert the consumer bonus pool count is accumulated for an ad_rep
        with consumers in the recipient list.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.assertEqual(ad_rep.consumer_points, 0)
        flyer = Flyer.objects.create(site_id=2, is_approved=True)
        consumer_ids = []
        consumer_emails = []
        for consumer_x in range(5):
            email = 'test_update_bonus_pool_%s@example.com' % consumer_x
            consumer = Consumer.objects.create(site_id=2, email=email,
                username=email)
            consumer_ids.append(consumer.id)
            consumer_emails.append(email)
        # Five consumers to receive this flyer
        # Two who receive this flyer will be related to this ad_rep.
        # A third consumer of this ad rep does not receive the flyer.
        for consumer_id in consumer_ids[3:6]:
            AdRepConsumer.objects.create(ad_rep=ad_rep, consumer_id=consumer_id)
        UPDATE_CONSUMER_BONUS_POOL(flyer.id, consumer_emails)
        try:
            bonus_pool_flyer = BonusPoolFlyer.objects.get(flyer__id=flyer.id)
        except BonusPoolFlyer.DoesNotExist:
            self.fail("Bonus pool flyer not created.")
        # Bonus pool accumulates two point for his consumers that receive this 
        # flyer.
        self.assertEqual(bonus_pool_flyer.calculate_status, '2')
        ad_rep = AdRep.objects.get(id=ad_rep.id)
        self.assertNotEqual(ad_rep.consumer_points, 0)

    def test_redo_update(self):
        """ Assert a flyer that has already been calculated into the consumer 
        bonus pool is not calculated again.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.assertEqual(ad_rep.consumer_points, 0)
        flyer = Flyer.objects.create(site_id=2, is_approved=True)
        flyer_recipients = CONSUMER_FACTORY.create_consumers(create_count=5)
        for consumer in flyer_recipients:
            AdRepConsumer.objects.create(ad_rep=ad_rep, consumer_id=consumer.id)
        BonusPoolFlyer.objects.create(flyer_id=flyer.id, calculate_status='2')
        UPDATE_CONSUMER_BONUS_POOL(flyer.id, [])
        ad_rep = AdRep.objects.get(id=ad_rep.id)
        self.assertEqual(ad_rep.consumer_points, 0)


class TestGetDownlineByDealerID(FirestormTestCase):
    """ Test firestorm get_downline_by_dealer_id web service """
    fixtures = ['test_ad_rep']

    def test_get_dealer_downline(self):
        """ Assert downline_by_dealer_id web service processed successfully. """
        mock_soap = MockSoap()
        self.assertEqual(mock_soap.get_downline_by_dealer_id(), [55])
    
    def test_process_dealer_downline(self):
        """ Assert functions in the downline_by_dealer_id web service. """
        mock_soap = MockSoap()
        response = mock_soap.call_get_downline_by_dealer_id(1, 1)
        ad_rep_parent_dict = process_downline_by_dealer_id(response)
        self.assertEqual(ad_rep_parent_dict, {2: 1, 55: 2})
        firestorm_id_list = set_ad_rep_parent(ad_rep_parent_dict)
        self.assertEqual(firestorm_id_list, [55])
        # check if parent ad rep is set
        parent_ad_rep = AdRep.objects.get(firestorm_id=1)
        ad_rep = AdRep.objects.get(firestorm_id=2)
        self.assertEqual(ad_rep.parent_ad_rep, parent_ad_rep)
        self.assertEqual(len(AdRep.objects.filter(firestorm_id=55)), 0)


class TestEnrollment(FirestormTestCase):
    """ Test enroll of firestorm dealers with the soap api: enroll customer
    and enroll member. """

    def setUp(self):
        super(TestEnrollment, self).setUp()
        self.ad_rep_dict = {'first_name' : 'first', 'last_name' : 'last', 
            'email': 'test@example.com', 'url' : 'u', 'ad_rep_url' : 'url',
            'tax_payer_number': 1, 'address1': 'addr', 'city': 'mycity', 
            'state_province': 'ny',  
            'ad_rep_id': 100, 'password' : 'pw1234',    
            'zip_postal': '10950'}

         
    def test_enroll_customer_call(self):
        """ Assert firestorm soap connector returns a firestorm id of a 
        created firestorm dealer. 
        """
        mock_soap = MockSoap()
        response_dict = mock_soap.enroll_customer(ad_rep_dict=self.ad_rep_dict)
        # New firestorm member enrolled
        self.assertEqual(response_dict['firestorm_id'], 10)

    def test_enroll_member_call(self):
        """ Assert firestorm soap connector returns a firestorm id of a 
        created firestorm dealer. 
        """
        mock_soap = MockSoap()
        response_dict = mock_soap.enroll_member(ad_rep_dict=self.ad_rep_dict)
        # New firestorm member enrolled
        self.assertEqual(response_dict['firestorm_id'], 10)

    def test_process_enrollment(self):
        """ Assert process enroll customer returns error message(s) when a user 
        tries to enroll with the same url of an existing firestorm user. 
        """
        soap_response = """<?xml version='1.0' encoding='utf-8' ?>
            <FIRESTORMRESULT><STATUS>FAIL</STATUS><ID>-1</ID>
            <ORDERID>-1</ORDERID><ERRORS errorcount='1'>
            <ERRORMSG>The username supplied is not available for use</ERRORMSG>
            </ERRORS></FIRESTORMRESULT>"""
        response_dict = process_enrollment(soap_response)
        self.assertTrue('url' in response_dict['error_list'])

class TestSaveOrder(FirestormTestCase):
    """ Test for save of firestorm orders with soap api. """
    fixtures = ['test_advertiser', 'test_ecommerce', 'test_promotion',
        'test_ad_rep']
        
    def test_save_order_call(self):
        """ Assert firestorm soap connector returns a firestorm order id. """
        order = ORDER_FACTORY.create_order()
        # On create of an AdRepOrder, FirestormSoap.save_order will be called.
        ad_rep_order = AdRepOrder.objects.create(ad_rep_id=1000, order=order)
        mock_soap = MockSoap()
        mock_soap.save_order(ad_rep_order=ad_rep_order)
        ad_rep_order2 = AdRepOrder.objects.get(id=ad_rep_order.id)
        self.assertEqual(ad_rep_order2.firestorm_order_id, 1)

    def test_create_order_ann_promo(self):
        """ Assert order with promo returns discounted amount in save order 
        xml. For annual and monthly discounted product purchase, 
        the orderdetail priceeach should equal the order total. 
        """
        promo = 'A399' # discount an annual purchase
        promotion_code = PromotionCode.objects.get_by_natural_key(promo)
        order = Order.objects.create(billing_record_id=114,
            promotion_code_id=promotion_code.id)
        order_item = OrderItem(product_id=3, site_id=2, business_id=114,
            end_datetime=datetime.datetime.now())
        order.order_items.add(order_item)
        orders_xml = create_order_detail_xml(order=order)
        soup = BeautifulStoneSoup(orders_xml)
        self.assertEqual(len(soup.findAll('orderdetail')), 1)
        self.assertEqual(soup.find('productnumber').string, '3')
        self.assertEqual(soup.find('priceeach').string, str(order.total))
        self.assertEqual(soup.find('retailpriceeach').string, str(order.total))
        self.assertEqual(soup.find('wholesalepriceeach').string, 
            str(order.total))
        self.assertEqual(soup.find('uplinevolumepriceeach').string, 
            str(order.total))

    def test_create_order_free_flyer(self):
        """ Assert order with promo returns discounted amount in save order 
        xml. The orderdetail: retail, wholesale, line total, upline and 
        price each - should equal the order total. 
        """
        promo = 'free flyer' # flyer with zero cost
        promotion_code = PromotionCode.objects.get_by_natural_key(promo)
        order = Order.objects.create(billing_record_id=114,
            promotion_code_id=promotion_code.id)
        order_item = OrderItem(product_id=1, site_id=2, business_id=114,
            end_datetime=datetime.datetime.now())
        order.order_items.add(order_item)
        orders_xml = create_order_detail_xml(order=order)
        soup = BeautifulStoneSoup(orders_xml)
        self.assertEqual(len(soup.findAll('orderdetail')), 1)
        self.assertEqual(soup.find('productnumber').string, '1')
        self.assertEqual(soup.find('priceeach').string, str(order.total))
        self.assertEqual(soup.find('retailpriceeach').string, str(order.total))
        self.assertEqual(soup.find('wholesalepriceeach').string, 
            str(order.total))
        self.assertEqual(soup.find('uplinevolumepriceeach').string, 
            str(order.total))

    def test_create_order_detail_month(self):
        """ Assert order returns amount for monthly coupon purchase in save 
        order xml. 
        """
        order = Order.objects.create(billing_record_id=114)
        order_item = OrderItem(product_id=2, site_id=2, business_id=114,
            end_datetime=datetime.datetime.now())
        order.order_items.add(order_item)
        orders_xml = create_order_detail_xml(order=order)
        soup = BeautifulStoneSoup(orders_xml)
        self.assertEqual(len(soup.findAll('orderdetail')), 1)
        self.assertEqual(soup.find('productnumber').string, '2')
        self.assertEqual(soup.find('priceeach').string, str(order.total))

    def test_create_order_detail_flyer(self):
        """ Assert order with promo returns discounted amount in save order 
        xml. In the xml, the OrderDetail PriceEach should equal the order total. 
        """
        order = Order.objects.create(billing_record_id=114)
        order_item = OrderItem(product_id=1, site_id=2, business_id=114,
            end_datetime=datetime.datetime.now(), amount='10.00')
        order.order_items.add(order_item)
        order_item = OrderItem(product_id=1, site_id=2, business_id=114,
            end_datetime=(datetime.datetime.now() + 
            datetime.timedelta(days=7)), amount='10.00')
        order.order_items.add(order_item)
        orders_xml = create_order_detail_xml(order=order)
        soup = BeautifulStoneSoup(orders_xml)
        self.assertEqual(len(soup.findAll('orderdetail')), 2)
        self.assertEqual(soup.find('productnumber').string, '1')
        self.assertEqual(soup.find('priceeach').string, 
            str(order.order_items.all()[0].amount))
        
    def test_process_save_order(self):
        """ Assert process save order response doesn't add a firestorm order to
        this ad rep order since error messages are returned. 
        """
        order = Order.objects.create(billing_record_id=114)
        # On create of an AdRepOrder, FirestormSoap.save_order will be called.
        ad_rep_order = AdRepOrder.objects.create(ad_rep_id=1000, order=order)
        order_dict = {'billing_city': ' '}
        response = """<FIRESTORMRESULT><STATUS>FAIL</STATUS>
            <ERRORS errorcount='2'>
            <ERRORMSG>Ship address line 1 must be provided</ERRORMSG>
            <ERRORMSG>Ship city must be provided</ERRORMSG>
            </ERRORS></FIRESTORMRESULT>"""
        try:
            process_save_order_response(response, ad_rep_order, order_dict)
            self.assertTrue(False)
        except ValidationError:
            self.assertTrue(True)

    def test_validate_order_data(self):
        """ Assert order billing record values of '' are changed to ' '. """
        billing_record = BillingRecord.objects.get(id=114)
        billing_record.billing_city = None
        billing_record.save()
        order = Order.objects.create(billing_record_id=billing_record.id)
        order_dict = validate_order_data(order)
        self.assertEquals(order_dict['billing_city'], ' ')
        self.assertEquals(order_dict['billing_address1'], ' ')


class TestGetDealerDetail(TestCase):
    """ Test case for save of firestorm orders with soap api. """
    fixtures = ['test_advertiser', 'test_ecommerce', 'test_promotion',
        'test_ad_rep']

    def test_dealer_detail_call(self):
        """ Assert mock soap connector returns firestorm dealer information. """
        ad_rep = AdRep.objects.get(id=1000)
        parent_ad_rep = AdRep.objects.get(firestorm_id=2)
        parent_ad_rep.firestorm_id = 20
        parent_ad_rep.save()
        mock_soap = MockSoap()
        mock_soap.get_dealer_detail(firestorm_id=ad_rep.firestorm_id)
        ad_rep = AdRep.objects.get(id=1000)
        self.assertEqual(ad_rep.first_name, 'John')
        self.assertEqual(ad_rep.last_name, 'Smith')
        self.assertEqual(ad_rep.company, 'Test Inc')
        self.assertEqual(ad_rep.fax_phone_number, '')
        self.assertEqual(ad_rep.cell_phone_number, '4165551788')
        self.assertEqual(ad_rep.primary_phone_number, '123-555-1111')
        self.assertEqual(ad_rep.mailing_address1, '57 Test Ave')
        self.assertEqual(ad_rep.mailing_city, 'Bronx')
        self.assertEqual(ad_rep.mailing_state_province, 'NY')
        self.assertEqual(ad_rep.mailing_zip_postal, '10940')
        self.assertEqual(ad_rep.consumer_zip_postal, '10940')
        self.assertTrue(ad_rep.check_password('test'))
        self.assertEqual(ad_rep.parent_ad_rep, parent_ad_rep)
        self.assertTrue(os.listdir(mock_soap.WEB_PHOTO_PATH))
        self.assertTrue(str(ad_rep.firestorm_id) in ad_rep.web_photo_path)
        self.assertTrue(os.path.isfile(ad_rep.web_photo_path))
        if os.path.isfile(ad_rep.web_photo_path):
            os.remove(ad_rep.web_photo_path)

    def test_dealer_detail_customer(self):
        """ Assert mock soap connector returns firestorm dealer information
        for a referring consumer with valid sponsor (parent) id. """
        ad_rep = AdRep.objects.get(id=1002)
        parent_ad_rep = AdRep.objects.get(firestorm_id=2)
        parent_ad_rep.firestorm_id = 20
        parent_ad_rep.save()
        mock_soap = MockSoap()
        mock_soap.get_dealer_detail(firestorm_id=ad_rep.firestorm_id)
        ad_rep = AdRep.objects.get(id=1002)
        self.assertEqual(ad_rep.parent_ad_rep, parent_ad_rep)
        
    def test_new_ad_rep(self):
        """ Assert get dealer details returns ad_rep_dict when ad rep is not 
        in db but exists in firestorm. Also new ad rep will not be created. """
        mock_soap = MockSoap()
        ad_rep_count = AdRep.objects.count()
        ad_rep = AdRep.objects.all().order_by('-firestorm_id')[0]
        new_firestorm_id = int(ad_rep.firestorm_id) + 1
        ad_rep_dict = mock_soap.get_dealer_detail(firestorm_id=new_firestorm_id)
        self.assertEqual(ad_rep_dict['firestorm_id'], str(new_firestorm_id))
        ad_rep_count_after = AdRep.objects.count()
        self.assertEqual(ad_rep_count, ad_rep_count_after)
        
    def test_dealer_details_cache(self):
        """ Assert ad rep details are updated due to refresh minutes argument. 
        """
        ad_rep = AdRep.objects.get(id=1000)
        ad_rep.mailing_address1 = None
        ad_rep.save()
        mock_soap = MockSoap()
        mock_soap.get_dealer_detail(firestorm_id=ad_rep.firestorm_id,
            refresh_minutes=10)
        ad_rep = AdRep.objects.get(id=1000)
        # since ad_rep mailing address is None, update ad rep details 
        self.assertEqual(ad_rep.mailing_address1, '57 Test Ave')
        ad_rep = AdRep.objects.get(id=1000)
        ad_rep.mailing_address1 = 'address'
        ad_rep.save()
        mock_soap.get_dealer_detail(firestorm_id=ad_rep.firestorm_id,
            refresh_minutes=10)
        ad_rep = AdRep.objects.get(id=1000)
        # since ad rep modified recently, do not update ad rep details
        self.assertEqual(ad_rep.mailing_address1, 'address')
        
    def test_ad_rep_dict_response(self):
        """ Assert new ad rep causes GetDealerDetail to return ad_rep_dict """
        ad_rep = AdRep.objects.get(id=1000)
        user = User.objects.get(id=ad_rep.id)
        user.delete()
        mock_soap = MockSoap()
        response = mock_soap.get_dealer_detail(firestorm_id=1)
        self.assertEqual(response, {'first_name': u'John',
            'last_name': u'Smith', 'firestorm_id': u'1',
            'cell_phone_number': u'4165551788', 'url': u'joeshmoe',
            'web_greeting': '', 'company': u'Test Inc',
            'mailing_address1': u'57 Test Ave',
            'mailing_state_province': u'NY',
            'work_phone_number': u'1235551800',
            'home_phone_number': u'1235551786',
            'mailing_address2': u'',
            'mailing_city': u'Bronx', 'fax_phone_number': '', 
            'mailing_zip_postal': u'10940', 'password': u'test', 
            'email': u'newadrep@deleardetail.org',
            'sponsor_id': u'20'})

    def test_get_ad_rep_web_photo(self):
        """ Assert that new web photo file of same contents is not created if 
        file is already in folder.
        """
        mock_soap = MockSoap()
        web_photo_path = mock_soap.WEB_PHOTO_PATH + '1.jpg'
        f = open(web_photo_path, 'rb')
        binary_string = f.read()
        f.close()
        web_photo_path_match = find_web_photo_match(1, binary_string)
        self.assertEqual(web_photo_path_match, web_photo_path)
        # check if file is added again
        file_count = 0
        for image_filename in os.listdir(mock_soap.WEB_PHOTO_PATH):
            if image_filename == '1.jpg':
                file_count += 1
                if file_count > 1:
                    self.assertTrue(False)
        self.assertTrue(True)


class TestAllocateBonusPool(FirestormTestCase):
    """ Test case for AllocateBonusPool task. """

    def test_allocation_formula(self):
        """ Assert the consumer bonus pool is allocated by proximity and
        consumer counts.
        """
        ad_reps = AD_REP_FACTORY.create_ad_reps(create_count=6)
        # One of these will not be selected for allocation; selects 4 of 5.
        for counter in range(0, 5):
            ad_reps[counter].consumer_points = 100 + counter
            ad_reps[counter].save()
            AD_REP_FACTORY.qualify_ad_rep(ad_reps[counter])
        # This ad_rep is not close.
        ad_reps[5].site_id = 131
        ad_reps[5].consumer_zip_postal = '00927'
        ad_reps[5].consumer_points = 1000
        ad_reps[5].save()
        AD_REP_FACTORY.qualify_ad_rep(ad_reps[5])
        # Allocations are no longer created when the AdRepOrder is created.
        order = ORDER_FACTORY.create_order()
        ad_rep_order = AdRepOrder.objects.create(ad_rep=ad_reps[0], order=order)
        ALLOCATE_BONUS_POOL.run(ad_rep_order.id)
        bonus_pool_allocations = BonusPoolAllocation.objects.filter(
            ad_rep_order=ad_rep_order)
        self.assertEqual(len(bonus_pool_allocations), 5)
        self.assertEqual(
            bonus_pool_allocations.aggregate(Sum('amount'))['amount__sum'],
            Decimal(str(round(order.total * BONUS_POOL_PERCENT / 100, 2))))

    def test_more_than_min(self):
        """ Assert more than the minimum ad_reps can receive an allocation. """
        ad_reps = AD_REP_FACTORY.create_ad_reps(
            create_count=BONUS_POOL_MIN_SHARERS + 1)
        for ad_rep in ad_reps:
            ad_rep.consumer_points = 1
            ad_rep.save()
            AD_REP_FACTORY.qualify_ad_rep(ad_rep)
        order = ORDER_FACTORY.create_order()
        ad_rep_order = AdRepOrder.objects.create(ad_rep=ad_reps[0], order=order)
        ALLOCATE_BONUS_POOL.run(ad_rep_order.id)
        bonus_pool_allocations = BonusPoolAllocation.objects.filter(
            ad_rep_order=ad_rep_order)
        self.assertEqual(len(bonus_pool_allocations), len(ad_reps))

    def test_allocation_not_qualified(self):
        """ Assert an ad_rep not qualified does not receive an allocation. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        ad_rep.consumer_points = 100
        ad_rep.save()
        order = ORDER_FACTORY.create_order()
        ad_rep_order = AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
        self.assertEqual(BonusPoolAllocation.objects.filter(
            ad_rep_order=ad_rep_order).count(), 0)

    def test_already_allocated(self):
        """ Assert allocation task quits for an order already allocated. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        order = ORDER_FACTORY.create_order()
        ad_rep_order = AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
        BonusPoolAllocation.objects.create(ad_rep_order=ad_rep_order,
            ad_rep=ad_rep, consumer_points=1, amount=Decimal('1'))
        ALLOCATE_BONUS_POOL.run(ad_rep_order.id)
        self.assertEqual(BonusPoolAllocation.objects.filter(
            ad_rep_order=ad_rep_order).count(), 1)