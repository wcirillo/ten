""" Tests for tasks of email_gateway app. """
import datetime
from itertools import groupby
import logging

from django.conf import settings
from django.core import mail

from advertiser.factories.business_factory import BUSINESS_FACTORY
from advertiser.models import Business
from common.test_utils import EnhancedTestCase
from consumer.models import SalesRep
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.offer_factory import OFFER_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import Offer
from ecommerce.models import Order, OrderItem
from email_gateway.tasks.warm_lead_emails import WarmLeadEmailTask
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRepAdvertiser

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestSendWarmLeadsEmail(EnhancedTestCase):
    """ Test case for WarmLeadEmailTask. """
    fixtures = ['test_sales_rep']

    @staticmethod
    def prep_advertiser(advertiser, days):
        """ Make the advertiser record emailable, and n + 1 days old. """
        advertiser.advertiser_create_datetime -= datetime.timedelta(days + 1)
        LOG.debug('advertiser_create_datetime: %s' %
            advertiser.advertiser_create_datetime)
        advertiser.is_emailable = True
        advertiser.save()
        advertiser.email_subscription.add(4)

    def test_send_warm_lead_zero_days(self):
        """ Assert email not sent when last_run_days is 0. """
        WarmLeadEmailTask().run(last_run_days=0)
        for message in mail.outbox:
            if 'Warm leads Genie' not in message.extra_headers['From']:
                self.fail('No emails should have sent to advertisers.')

    def test_send_business_10(self):
        """ Assert email for a 10 day old advertiser acct without an offer. """
        business = BUSINESS_FACTORY.create_business()
        advertiser = business.advertiser
        self.prep_advertiser(advertiser, 10)
        WarmLeadEmailTask().run()
        LOG.debug(mail.outbox[0].to)
        LOG.debug(mail.outbox[0].alternatives[0][0])
        LOG.debug(mail.outbox[0].body)
        self.assertEqual(mail.outbox[0].subject,
            'Finish your first Coupon today')
        self.assertTrue('Hi,' in mail.outbox[0].body)
        self.assertTrue('/hudson-valley/create-coupon/' in mail.outbox[0].body)
        self.assertTrue('Hi,' in mail.outbox[0].alternatives[0][0])
        self.assertTrue('example we created' in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue('30% OFF' in
            mail.outbox[0].alternatives[0][0])
        self.assertEqual(mail.outbox[0].alternatives[0][0].count(
            business.business_name), 2)
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue("Publish this coupon! It's almost done already." in
            mail.outbox[0].alternatives[0][0])
        # Assert report email contains this advertiser.
        LOG.debug(mail.outbox[3].to)
        LOG.debug(mail.outbox[3].alternatives[0][0])
        LOG.debug(mail.outbox[3].body)
        self.assertTrue(advertiser.email in mail.outbox[3].body)
        self.assertTrue(business.business_name in mail.outbox[3].body)
        self.assertTrue(advertiser.email in mail.outbox[3].alternatives[0][0])
        self.assertTrue(business.business_name in
            mail.outbox[3].alternatives[0][0])

    def test_send_offer_10(self):
        """ Assert email for a 10 day old advertiser acct showing sample offer.
        """
        offer = OFFER_FACTORY.create_offer()
        advertiser = offer.business.advertiser
        self.prep_advertiser(advertiser, 10)
        WarmLeadEmailTask().run()
        self.assertEqual(mail.outbox[0].subject,
            'Publish your first coupon today')
        self.assertTrue('Hi,' in mail.outbox[0].body)
        self.assertTrue('/hudson-valley/create-coupon/' in mail.outbox[0].body)
        self.assertTrue('Hi,' in mail.outbox[0].alternatives[0][0])
        self.assertTrue('example we created' in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue('30% OFF' in
            mail.outbox[0].alternatives[0][0])
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue("Publish this coupon! It's almost done already." in
            mail.outbox[0].alternatives[0][0])

    def test_lead_for_ad_rep(self):
        """ Assert the email is 'from' an ad_rep and the ad_rep gets a copy.
        """
        # This first ad_rep on the site will get this lead.
        ad_rep = AD_REP_FACTORY.create_ad_reps(create_count=2)[0]
        mail_prior = len(mail.outbox)
        offer = OFFER_FACTORY.create_offer()
        advertiser = offer.business.advertiser
        self.prep_advertiser(advertiser, 1)
        WarmLeadEmailTask().run()
        self.assertEqual(mail.outbox[mail_prior].subject,
            'Publish your first coupon today')
        self.assertFalse('/hudson-valley/create-coupon/' in
            mail.outbox[mail_prior].body)
        self.assertFalse('/hudson-valley/create-coupon/' in
            mail.outbox[mail_prior].alternatives[0][0])
        target_string = '/hudson-valley/join-me/%s/create-coupon/' % ad_rep.url
        self.assertTrue(target_string in mail.outbox[mail_prior].body)
        self.assertTrue(target_string in
            mail.outbox[mail_prior].alternatives[0][0])
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue("This coupon could be complete with just a few clicks."
            in mail.outbox[mail_prior].alternatives[0][0])
        self.assertEqual(mail.outbox[mail_prior + 1].to, [ad_rep.email])
        self.assertEqual(mail.outbox[mail_prior + 1].subject,
            'WARM LEAD: Publish your first coupon today')

    def test_send_offer_recent_coupon(self):
        """ Assert email includes a recent coupon from another business. """
        offer = OFFER_FACTORY.create_offer()
        advertiser = offer.business.advertiser
        # A current coupon on the same site:
        slot = SLOT_FACTORY.create_slot()
        recent_coupon = slot.get_active_coupon()
        self.prep_advertiser(advertiser, 70)
        WarmLeadEmailTask().run()
        self.assertTrue('New coupons from Hudson Valley businesses' in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue(recent_coupon.offer.business.business_name in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue(recent_coupon.offer.headline in
            mail.outbox[0].alternatives[0][0])
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue('Attract Hudson Valley customers today!' in
            mail.outbox[0].alternatives[0][0])

    def test_send_offer_40(self):
        """ Assert email for a 10 day old advertiser acct showing offer. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        self.prep_advertiser(advertiser, 40)
        WarmLeadEmailTask().run()
        self.assertEqual(mail.outbox[0].subject, 'Publish this Coupon today')
        self.assertTrue('/hudson-valley/create-coupon/' in mail.outbox[0].body)
        self.assertTrue(coupon.offer.headline in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue(coupon.offer.qualifier in
            mail.outbox[0].alternatives[0][0])
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue('potential Hudson Valley customers in mere minutes.' in
            mail.outbox[0].alternatives[0][0])

    def test_send_offer_1_ad_rep(self):
        """ Assert task for 1 day old advertiser acct with a referring ad_rep.
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create(ad_rep=ad_rep, advertiser=advertiser)
        mail_prior = len(mail.outbox)
        self.prep_advertiser(advertiser, 1)
        WarmLeadEmailTask().run()
        self.assertEqual(mail.outbox[mail_prior].subject,
            'Publish this Coupon today')
        self.assertEqual(mail.outbox[mail_prior + 1].subject,
            'WARM LEAD: Publish this Coupon today')
        self.assertTrue('An email was sent on your behalf.' in
            mail.outbox[mail_prior + 1].body)
        # Assert text version contains Sales Rep signature.
        self.assertTrue('Reputable Salesperon'
            in mail.outbox[mail_prior + 1].body)
        # Assert text version contains Ad Rep signature.
        self.assertTrue(ad_rep.first_name in mail.outbox[mail_prior + 1].body)
        self.assertTrue(ad_rep.last_name in mail.outbox[mail_prior + 1].body)
        self.assertTrue(ad_rep.email in mail.outbox[mail_prior + 1].body)
        # Assert HTML version.
        self.assertTrue('Below is an email sent on your behalf.' in
            mail.outbox[mail_prior + 1].alternatives[0][0])
        self.assertTrue(coupon.offer.business.business_name in
            mail.outbox[mail_prior + 1].alternatives[0][0])
        # Assert text version contains Ad Rep signature.
        self.assertTrue(ad_rep.first_name in
            mail.outbox[mail_prior + 1].alternatives[0][0])
        self.assertTrue(ad_rep.last_name in
            mail.outbox[mail_prior + 1].alternatives[0][0])
        self.assertTrue(ad_rep.email in
            mail.outbox[mail_prior + 1].alternatives[0][0])
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue('This coupon could be complete with just a few ' in
            mail.outbox[mail_prior].alternatives[0][0])

    def test_send_offer_130_ad_rep(self):
        """ Assert task for 130 day old advertiser acct with a referring ad_rep
        generates an email with a promotion code.
        """
        promo_code = 'ONEYEAR399'
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create(ad_rep=ad_rep, advertiser=advertiser)
        mail_prior = len(mail.outbox)
        self.prep_advertiser(advertiser, 130)
        WarmLeadEmailTask().run()
        self.assertEqual(mail.outbox[mail_prior].subject,
            'Publish up to 10 coupons and save $100')
        self.assertEqual(mail.outbox[mail_prior + 1].subject,
            'WARM LEAD: Publish up to 10 coupons and save $100')
        self.assertTrue('An email was sent on your behalf.' in
            mail.outbox[mail_prior + 1].body)
        # Assert text version contains Sales Rep signature.
        self.assertTrue('Reputable Salesperon'
            in mail.outbox[mail_prior + 1].body)
        # Assert text version promo_code.
        self.assertTrue(promo_code in mail.outbox[mail_prior + 1].body)
        # Assert HTML version contains promo_code.
        self.assertTrue(promo_code in
            mail.outbox[mail_prior + 1].alternatives[0][0])
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue('a hundred bucks</a>' in
            mail.outbox[mail_prior].alternatives[0][0])

    def test_send_business_130_ad_rep(self):
        """ Assert task for 130 day old advertiser acct without an offer with a
        referring ad_rep generates an email with a promotion code.
        """
        promo_code = 'ONEYEAR399'
        business = BUSINESS_FACTORY.create_business()
        advertiser = business.advertiser
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create(ad_rep=ad_rep, advertiser=advertiser)
        self.prep_advertiser(advertiser, 130)
        mail_prior = len(mail.outbox)
        WarmLeadEmailTask().run()
        self.assertEqual(mail.outbox[mail_prior].subject,
            'Finish your first Coupon today')
        # Assert text version promo_code.
        self.assertTrue(promo_code in mail.outbox[mail_prior].body)
        # Assert HTML version contains promo_code.
        self.assertTrue(promo_code in
            mail.outbox[mail_prior].alternatives[0][0])
        # Assert dynamic text that swings on schedule_item.
        self.assertTrue('a hundred bucks</a>' in
            mail.outbox[mail_prior].alternatives[0][0])


class TestSendWarmLeadsEmailOld(EnhancedTestCase):
    """ Test case for send_warm_leads_email task. """
    fixtures = ['test_consumer', 'test_advertiser', 'test_coupon', 
        'test_advertiser_views', 'test_auth_group', 'test_ecommerce', 
        'test_ecommerce_views', 'test_slot', 'test_log_history', 
        'test_subscriber', 'test_sales_rep']

    def test_send_warm_lead_email_norm(self):
        """ Assert that the warm leads email is generated to a qualifying
        advertiser, with the correct content.
        """
        business = Business.objects.get(id=113)
        business.business_create_datetime = datetime.datetime.now()
        business.save()
        offer = Offer.objects.get(id=300)
        offer.create_datetime = datetime.datetime.now()
        offer.save()
        warm_lead_email_task = WarmLeadEmailTask()
        warm_lead_email_task.test_mode = 'steve@10coupons.com'
        warm_lead_email_task.run(query_obj={'offer':offer, 'business':business})
        # Count non-admin emails sent:
        mail_count = 0
        for message in mail.outbox:
            if 'Warm leads Genie' not in message.extra_headers['From']:
                mail_count += 1
            LOG.debug("============== %s" % message.to)
        self.assertEqual(mail_count, 3)
        self.assertEqual(mail.outbox[0].subject, 
            'Publish this Coupon today')
        target_path = '%s/hudson-valley/create-coupon/' % (
            settings.HTTP_PROTOCOL_HOST)
        self.assertTrue(target_path in mail.outbox[0].body)
        self.assertTrue(target_path in mail.outbox[0].alternatives[0][0])
        self.assertTrue(offer.business.business_name in mail.outbox[0].body)
        self.assertTrue(offer.business.business_name in 
            mail.outbox[0].alternatives[0][0])
        sales_rep = SalesRep.objects.get(sites=1)
        self.assertTrue(sales_rep.consumer.first_name in mail.outbox[0].body)
        self.assertTrue(sales_rep.consumer.first_name in 
            mail.outbox[0].alternatives[0][0])
        self.assertTrue(sales_rep.consumer.last_name in mail.outbox[0].body)
        self.assertTrue(sales_rep.consumer.last_name in 
            mail.outbox[0].alternatives[0][0])
        LOG.debug([message.subject for message in mail.outbox])
        self.assertTrue('Warm leads since' 
            in mail.outbox[len(mail.outbox)-1].subject)

    def test_warm_offer_queries(self):
        """ Assert only advertisers meeting the following criteria are pulled:
            - Never had a purchase.
            - Do not belong to user_group advertisers__do_not_market.
            - Create datetime of offer/business is gt last_run.
            - No duplicate advertisers between offers and businesses queries.
        This test actually tests 3 service methods because 1 calls the other 2:
            - query_warm_offers_and_businesses
                - query_warm_offers_since
                - query_warm_businesses_since
        """
        warm_leads_email_task = WarmLeadEmailTask()
        warm_leads_email_task.start_datetime = datetime.datetime.strptime(
            '2010-01-01', '%Y-%m-%d')
        warm_leads_email_task.end_datetime = datetime.datetime.now()
        qs_b, qs_o = warm_leads_email_task.qry_warm_offers_and_businesses()
        advertisers = []
        accumulated_businesses = []
        for offer in qs_o:
            advertisers.append(offer.business.advertiser.id)
            accumulated_businesses.append(offer.business.id)
            if offer.business.advertiser.groups.filter(
                    name='advertisers__do_not_market'):
                self.fail('Advertiser in query in "do not market" group!')
            if offer.business.advertiser.groups.filter(name='Coldcall-Leads'):
                self.fail('Advertiser in query in "Coldcall-Leads" group!')
            # Assert Offer created after last_run.
            self.assertTrue(
                offer.create_datetime >= warm_leads_email_task.start_datetime)
            if OrderItem.objects.filter(
                business__advertiser__id=offer.business.advertiser.id):
                self.fail('Offer belongs to advertiser with purchase.')
        for biz in qs_b:
            advertisers.append(biz.advertiser.id)
            accumulated_businesses.append(biz.id)
            if biz.advertiser.groups.filter(name='Coldcall-Leads'):
                self.fail('Advertiser in query in "Coldcall-Leads" group!')
            if biz.advertiser.groups.filter(name='advertisers__do_not_market'):
                self.fail('Advertiser in query in "do not market" group!')
            if (biz.business_create_datetime <
                    warm_leads_email_task.start_datetime):
                self.fail('Business created after last_run.')
            if OrderItem.objects.filter(
                business__in=Business.objects.filter(
                advertiser__id=biz.advertiser.id)):
                self.fail('Business belongs to an advertiser with purchase.')
        # Confirm advertisers are unique and never purchased any orders.
        grouped_advertisers = [(a[0], 
            len(list(a[1]))) for a in groupby(advertisers)]
        for advertiser_id in grouped_advertisers:
            if advertiser_id[1] > 1:
                self.fail('Email would be sent to advertiser twice!')
        if Order.objects.filter(
        order_items__business__id__in=accumulated_businesses):
            self.fail('Businesses should be excluded by purchase.')
