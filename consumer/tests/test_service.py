""" Unit tests for service functions of consumer app. """
#pylint: disable=C0103
from django.test import TestCase

from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer, ConsumerHistoryEvent, EmailSubscription
from consumer.service import (build_consumer_count_list,
    create_subscriber_for_consumer, get_consumer_instance_type, get_site_rep,
    process_consumer_opt_out, update_default_site_consumers,
    update_subscriber_of_consumer, qry_qualified_consumers)
from geolocation.models import USZip
from market.models import Site
from subscriber.models import MobilePhone, Subscriber

class FakeRequest(object):
    """ Fake request object. """
    pass

class TestService(TestCase):
    """ Test case for service functions of consumer app. """
    
    fixtures = ['test_consumer', 'test_sales_rep']
    
    @classmethod
    def setUpClass(cls):
        """ Build fake request for testing process_consumer_opt_out. """
        super(TestService, cls).setUpClass()
        cls.request = FakeRequest()
        cls.request.META = {'REMOTE_ADDR': '127.0.0.1'}

    def common_assertions_history(self, consumer):
        """ Assert ConsumerHistoryEvent log record. """
        log_history = ConsumerHistoryEvent.objects.latest('id')
        self.assertEqual(int(log_history.event_type), 1)
        self.assertEqual(log_history.ip, '127.0.0.1')
        self.assertEqual(log_history.consumer_id, consumer.id)
        data_dict = eval(log_history.data)
        return data_dict

    def test_update_default_site_cons(self):
        """ Assert consumers on site 1 having a zip code for site 2 are moved.
        """
        self.assertEqual(Consumer.objects.filter(site=1).count(), 3)
        update_default_site_consumers()
        self.assertEqual(Consumer.objects.filter(site=1).count(), 0)

    def test_get_site_rep_default(self):
        """ Assert that if site rep does not exist for this site, it will use 
        default (site 1's).
        """
        site = Site.objects.get(id=2)
        rep = get_site_rep(site)
        self.assertEqual(rep.email_domain, '10Coupons.com')
        self.assertEqual(rep.consumer_id, 300)
    
    def test_get_site_rep_28(self):
        """ Assert that if site rep does exist, it will be selected. This test
        is for the North Jersey market.
        """
        site = Site.objects.get(id=28)
        rep = get_site_rep(site)
        self.assertEqual(rep.email_domain, '10NorthJerseyCoupons.com')
        self.assertEqual(rep.consumer_id, 301)
        
    def test_single_opt_out_current(self):
        """ Assert a single consumer opt out works with subscription_list 
        param in current supported format.
        """
        subscription = [5]
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.email_subscription.add(subscription[0])
        self.assertTrue(consumer.email_subscription.get(id=1))
        self.assertTrue(consumer.email_subscription.get(id=subscription[0]))
        process_consumer_opt_out(self.request, consumer, subscription)
        self.assertTrue(consumer.email_subscription.get(id=1))
        with self.assertRaises(EmailSubscription.DoesNotExist):
            subscription = consumer.email_subscription.get(id=subscription[0])
        log_history_data = self.common_assertions_history(consumer)
        self.assertEqual(log_history_data['requested_list'], subscription)
        self.assertEqual(log_history_data['unsubscribed_list'], [5, 6])
        
    def test_flyer_opt_out_current(self):
        """ Assert consumer opt out of flye remail works with subscription_list 
        param in current supported format.
        """
        subscription = [1]
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.email_subscription.add(2, 3, 4, 5, 6)
        self.assertTrue(consumer.email_subscription.get(id=1))
        process_consumer_opt_out(self.request, consumer, subscription)
        self.assertEqual(consumer.email_subscription.count(), 0)
        log_history_data = self.common_assertions_history(consumer)
        self.assertEqual(log_history_data['requested_list'], subscription)
        self.assertEqual(log_history_data['unsubscribed_list'], ['ALL'])

    def test_multi_opt_out_current(self):
        """ Assert consumer opt out works with multiple items in the 
        subscription_list param in current supported format.
        """
        subscription = [2, 5]
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.email_subscription.add(2, 5, 6)
        self.assertTrue(consumer.email_subscription.get(id=1))
        self.assertTrue(consumer.email_subscription.get(id=2))
        self.assertTrue(consumer.email_subscription.get(id=5))
        self.assertTrue(consumer.email_subscription.get(id=6))
        process_consumer_opt_out(self.request, consumer, subscription)
        self.assertTrue(consumer.email_subscription.get(id=1))
        with self.assertRaises(EmailSubscription.DoesNotExist):
            subscription = consumer.email_subscription.get(id=2)
        with self.assertRaises(EmailSubscription.DoesNotExist):
            subscription = consumer.email_subscription.get(id=5)
        with self.assertRaises(EmailSubscription.DoesNotExist):
            subscription = consumer.email_subscription.get(id=6)
        log_history_data = self.common_assertions_history(consumer)
        self.assertEqual(log_history_data['requested_list'], subscription)
        self.assertEqual(log_history_data['unsubscribed_list'], [2, 5, 6])

    def test_flyer_opt_out_deprecated(self):
        """ Assert consumer opt out of flye remail works with subscription_list 
        param in current supported format.
        """
        subscription = '01343'
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assertTrue(consumer.email_subscription.get(id=1))
        consumer.email_subscription.add(2)
        process_consumer_opt_out(self.request, consumer, subscription)
        self.assertEqual(consumer.email_subscription.count(), 0)
        log_history_data = self.common_assertions_history(consumer)
        self.assertEqual(log_history_data['requested_list'], [1])
        self.assertEqual(log_history_data['unsubscribed_list'], ['ALL'])

    def test_opt_out_deprecated(self):
        """ Assert a single consumer opt out works with subscription_list 
        param in deprecated format (as 5 character string).
        """
        subscription = '03343'
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.email_subscription.add(3)
        self.assertTrue(consumer.email_subscription.get(id=1))
        self.assertTrue(consumer.email_subscription.get(id=3))
        process_consumer_opt_out(self.request, consumer, subscription)
        self.assertTrue(consumer.email_subscription.get(id=1))
        with self.assertRaises(EmailSubscription.DoesNotExist):
            subscription = consumer.email_subscription.get(id=3)
        log_history_data = self.common_assertions_history(consumer)
        self.assertEqual(log_history_data['requested_list'], [3])
        self.assertEqual(log_history_data['unsubscribed_list'], [3])


class TestConsumerInstance(TestCase):
    """ Test identification of Consumer instances. """
    fixtures = ['test_consumer', 'test_advertiser', 'test_ad_rep', 
        'test_media_partner']
    
    def test_unidentifiable(self):
        """ Test when no Consumer found with email. """
        user_type, is_ad_rep = \
            get_consumer_instance_type('unidentifiable@10coupons.com')
        self.assertEqual(user_type, None)
        self.assertEqual(is_ad_rep, False)
        
    def test_identify_consumer(self):
        """ Test when only Consumer instance. """
        user_type, is_ad_rep = get_consumer_instance_type('101@example.com')
        self.assertEqual(user_type, 'consumer')
        self.assertEqual(is_ad_rep, False)
        
    def test_identify_advertiser(self):
        """ Test when Advertiser instance. """
        user_type, is_ad_rep = \
            get_consumer_instance_type('113_user@example.com')
        self.assertEqual(user_type, 'advertiser')
        self.assertEqual(is_ad_rep, False)
        
    def test_identify_affiliate(self):
        """ Test when Affiliate instance. """
        user_type, is_ad_rep = \
            get_consumer_instance_type('test_affiliate@example.com')
        self.assertEqual(user_type, 'affiliate_partner')
        self.assertEqual(is_ad_rep, False)
        
    def test_identify_media_partner(self):
        """ Test when MediaPartner instance. """
        user_type, is_ad_rep = \
            get_consumer_instance_type('test_media_group@example.com')
        self.assertEqual(user_type, 'media_group_partner')
        self.assertEqual(is_ad_rep, False)
        
    def test_identify_consumer_ad_rep(self):
        """ Test when AdRep Consumer instance. """
        user_type, is_ad_rep = \
            get_consumer_instance_type('test-ad-rep@example.com')
        self.assertEqual(user_type, 'consumer')
        self.assertEqual(is_ad_rep, True)
        
    def test_identify_adv_ad_rep(self):
        """ Test when AdRep Advertiser instance. """
        user_type, is_ad_rep = \
            get_consumer_instance_type('test-ad-rep2@example.com')
        self.assertEqual(user_type, 'advertiser')
        self.assertEqual(is_ad_rep, True)


class TestConsumerSiteCountList(TestCase):
    """ Test case for service function build_consumer_count_list. """
    fixtures = ['test_advertiser', 'test_consumer', 'test_coupon',
        'test_coupon_views', 'test_flyer']
    
    def setUp(self):
        """ Build comparison of current before adding a consumer. """
        super(TestConsumerSiteCountList, self).setUp()
        self.hv_list = build_consumer_count_list(2)
        self.hv_count = self.hv_list[0]['county_count']
        self.hv_zip = self.hv_list[0]['cities'][0]['zips'][0]['zip']
        self.hv_site = Site.objects.get(id=2)
        self.consumer = Consumer.objects.create_consumer(
            username='illegit_consumer@site.com', 
            email='illegit_consumer@site.com',
            consumer_zip_postal=self.hv_zip,
            site = self.hv_site
            )
        self.consumer.is_email_verified = True
        self.consumer.save()
    
    def test_orange_county_count(self):
        """ Assert the consumer count site list is built accurately. """
        oc_count = Consumer.objects.filter(site__id=2, is_email_verified=True,
            is_emailable=True,
            email_subscription=1, consumer_zip_postal__in=
            USZip.objects.filter(us_county__name='Orange'
            ).values_list('code', flat=True)).count()
        test_list = build_consumer_count_list(2)
        # Only one county is currently configured for site 2 (Orange).
        self.assertEqual(oc_count, test_list[0]['county_count'])
        self.assertEqual('Orange', test_list[0]['county'])
        self.assertEqual('12550', test_list[0]['cities'][0]['zips'][0]['zip'])
        self.assertEqual(oc_count,
            test_list[0]['cities'][0]['zips'][0]['zip_count'])
        
    def test_valid_count_site(self):
        """ Assert the consumers included in these counts are on the right site.
        """
        site = Site.objects.get(id=3)
        self.consumer.site = site
        self.consumer.save()
        test_list1 = build_consumer_count_list(2)
        self.assertEqual(self.hv_list[0]['county_count'], 
            test_list1[0]['county_count'])
        self.consumer.site = self.hv_site
        self.consumer.save()
        test_list2 = build_consumer_count_list(2)
        self.assertEqual(self.hv_list[0]['county_count'] + 1, 
            test_list2[0]['county_count'])
        
    def test_valid_count_subscription(self):
        """ Assert the consumers included in these counts have an email
        subscription.
        """
        self.consumer.email_subscription = []
        self.consumer.save()
        test_list6 = build_consumer_count_list(2)
        self.assertEqual(self.hv_list[0]['county_count'], 
            test_list6[0]['county_count'])
        self.consumer.email_subscription = [1]
        self.consumer.save()
        test_list7 = build_consumer_count_list(2)
        self.assertEqual(self.hv_list[0]['county_count'] + 1, 
            test_list7[0]['county_count'])


class TestQualifiedConsumers(TestCase):
    """ Assert result of queryset returned by qry_qualified_consumers abides by
    rules that exclude eligilbity.
    """
    fixtures = ['test_consumer', 'test_advertiser', 'test_coupon_views', 
        'test_subscriber']

    def prep_consumer(self):
        """ Prepare consumer for tests. """
        mobile_phone = MobilePhone.objects.get(mobile_phone_number='8455550000')
        mobile_phone.is_verified = True
        mobile_phone.save()
        self.good_subscriber = Subscriber.objects.get(id=2)
        self.good_consumer = Consumer.objects.get(id=115)
        self.good_consumer.is_email_verified = True
        self.good_consumer.save()

    def common_asserts(self, consumer, test_name, test_msg):
        """ Common shared assertions for this test case. """
        result = qry_qualified_consumers()
        if result.filter(id=consumer.id).exists():
            self.fail('%s: %s' % (test_name, test_msg))
    
    def test_consumer_is_verified(self):
        """ Assert consumer has to be verified to be qualified. """
        self.prep_consumer()
        unverified_consumer = self.good_consumer
        unverified_consumer.is_email_verified = False
        unverified_consumer.subscriber = self.good_subscriber
        unverified_consumer.save()
        self.common_asserts(unverified_consumer, 'test_consumer_is_verified',
            'Unverified consumer email is identified as qualifying')

    def test_consumer_w_subscription(self):
        """ Assert consumer has to have Email Flyer subscription to qualify. """
        self.prep_consumer()
        unsubscribed_consumer = Consumer.objects.get(id=122)
        unsubscribed_consumer.subscriber = self.good_subscriber
        unsubscribed_consumer.save()
        self.common_asserts(unsubscribed_consumer, 'test_consumer_w_subscription',
            'Consumer without subscription is identified as qualifying')

    def test_consumer_no_subscriber(self):
        """ Assert consumer must have subscriber. """
        self.prep_consumer()
        self.common_asserts(self.good_consumer, 'test_consumer_no_subscriber',
            'Consumer without subscriber is identified as qualifying')

    def test_subscriber_no_phone(self):
        """ Assert consumer must have subscriber with mobile. """
        self.prep_consumer()
        subscriber = Subscriber.objects.get(id=3)
        self.good_consumer.subscriber = subscriber
        self.good_consumer.save()
        self.common_asserts(self.good_consumer, 'test_consumer_no_subscriber',
            'Consumer with subscriber with no mobile is qualifying.')

    def test_unverified_phone(self):
        """ Assert consumer must have subscriber with verified mobile. """
        self.prep_consumer()
        subscriber = Subscriber.objects.get(id=7)
        self.good_consumer.subscriber = subscriber
        self.good_consumer.save()
        self.common_asserts(self.good_consumer, 'test_consumer_no_subscriber',
            'Consumer with subscriber with no mobile is qualifying.')

    def test_qualified_consumer(self):
        """ Assert qualified consumer is selectable. """
        self.prep_consumer()
        self.good_consumer.subscriber = self.good_subscriber
        self.good_consumer.save()
        result = qry_qualified_consumers()
        self.assertEqual(result.filter(id=self.good_consumer.id).count(), 1)


class TestCreateSubForConsumer(TestCase):
    """ Test case for service function create_subscriber_for_consumer. """
    fixtures = ['test_consumer']
    
    def test_consumer_has_sub_no_phone(self):
        """ Assert a consumer having a subscriber who has no phone, a phone is
        created.
        """
        site = Site.objects.get(id=2)
        consumer = Consumer.objects.get(id=105)
        self.assertEqual(create_subscriber_for_consumer(consumer, 1,
            '2225550000', '12550', site), 0)
        try:
            mobile_phone = MobilePhone.objects.get(
                mobile_phone_number='2225550000')
        except MobilePhone.DoesNotExist:
            self.fail('Mobile phone not created.')
        self.assertEqual(mobile_phone.subscriber.consumer(), consumer)

    def test_consumer_has_subscriber(self): 
        """ Assert when a consumer already has a subscriber who has a phone, 
        0 is returned. 
        """ 
        site = Site.objects.get(id=2) 
        consumer = Consumer.objects.get(id=105) 
        MobilePhone.objects.create(subscriber_id=30, carrier_id='2', 
            mobile_phone_number='2225550001') 
        self.assertEqual(create_subscriber_for_consumer(consumer, 1, 
            '2225550001', '12550', site), 0) 
 
    def test_con_has_sub_diff_number(self): 
        """ Assert when this number belongs to a different subscriber, 0 is 
        returned. 
        """ 
        site = Site.objects.get(id=2) 
        consumer = Consumer.objects.get(id=105) 
        MobilePhone.objects.create(subscriber_id=31, carrier_id='2', 
            mobile_phone_number='2225550002') 
        self.assertEqual(create_subscriber_for_consumer(consumer, 1, 
            '2225550002', '12550', site), 1) 
 
 
class TestUpdateSubscriberOfConsumer(TestCase): 
    """ Test case for update_subscriber_of_consumer. """ 
    fixtures = ['test_consumer'] 
 
    def test_mobile_phone_in_use(self): 
        """ Assert if this mobile phone is already used, 1 is returned. """ 
        site = Site.objects.get(id=2) 
        consumer = Consumer.objects.get(id=105) 
        MobilePhone.objects.create(subscriber_id=31, carrier_id='2', 
            mobile_phone_number='2225550003') 
        self.assertEqual(update_subscriber_of_consumer(consumer, '2', 
            '2225550003', '12550', site), 1) 
 
    def test_subscriber_no_phone(self): 
        """ Assert a subscriber without a phone gets a phone. """ 
        site = Site.objects.get(id=2) 
        consumer = Consumer.objects.get(id=105) 
        self.assertEqual(update_subscriber_of_consumer(consumer, '2', 
            '2225550004', '12550', site), 0) 
        try: 
            mobile_phone = MobilePhone.objects.get( 
                mobile_phone_number='2225550004') 
        except MobilePhone.DoesNotExist: 
            self.fail("Mobile phone not created.") 
        self.assertEqual(list(consumer.subscriber.mobile_phones.all()), 
            [mobile_phone]) 
 
    def test_con_has_sub_diff_number(self): 
        """ Assert a consumer updates her phone number. """ 
        site = Site.objects.get(id=2) 
        consumer = Consumer.objects.get(id=105) 
        MobilePhone.objects.create(subscriber_id=30, carrier_id='2', 
            mobile_phone_number='2225550005') 
        # A different phone number: 
        self.assertEqual(update_subscriber_of_consumer(consumer, '2', 
            '2225550006', '12550', site), 0) 
        try: 
            mobile_phone = MobilePhone.objects.get( 
                mobile_phone_number='2225550006') 
        except MobilePhone.DoesNotExist: 
            self.fail('Mobile phone not created.') 
        self.assertEqual(mobile_phone.subscriber.consumer(), consumer)
