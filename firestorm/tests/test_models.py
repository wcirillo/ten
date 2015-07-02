""" Test cases for models of firestorm app of project ten. """
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.test import TestCase

from advertiser.factories.advertiser_factory import ADVERTISER_FACTORY
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer, EmailSubscription
from common.test_utils import EnhancedTestCase
from ecommerce.factories.order_factory import ORDER_FACTORY
from ecommerce.models import Order, PromotionCode
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import (AdRep, AdRepAdvertiser, AdRepOrder, AdRepConsumer,
    BonusPoolAllocation, AdRepLead, AdRepSite, AdRepUSState)
from firestorm.tests.firestorm_test_case import FirestormTestCase


class TestAdRepModel(FirestormTestCase):
    """ Test case for the AdRep model. """

    def test_create_relate_ad_rep(self):
        """  Assert an ad_rep is created and related to an advertiser, an order,
        and a consumer.
        """
        email = 'test_create_ad_rep@example.com'
        ad_rep = AdRep.objects.create(username=email, email=email,
            firestorm_id=100)
        self.assertFalse(ad_rep.advertisers().count())
        self.assertFalse(ad_rep.orders().count())
        self.assertFalse(ad_rep.consumers().count())
        # Select an advertiser who may or may not have an ad_rep:
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        try:
            AdRepAdvertiser.objects.create(ad_rep=ad_rep, advertiser=advertiser)
        except IntegrityError: # This advertiser already has a rep; change reps.
            advertiser.ad_rep_advertiser.ad_rep = ad_rep
            advertiser.ad_rep_advertiser.save()
        self.assertTrue(ad_rep.advertisers().count())
        # Advertisers are a subclassed from Consumer, but relating an advertiser
        # to this ad_rep does *not* add the base consumer, too.
        self.assertFalse(ad_rep.consumers().count())
        order = ORDER_FACTORY.create_order()
        AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
        self.assertTrue(ad_rep.orders().count())
        # Select a consumer who does not have an ad_rep:
        consumer = CONSUMER_FACTORY.create_consumer()
        AdRepConsumer.objects.create(ad_rep=ad_rep, consumer=consumer)
        self.assertTrue(ad_rep.consumers().count())

    def test_save_ad_rep(self):
        """ Assert saving an AdRep whose rank is not 'CUSTOMER' removes this
        AdRep from AdRepConsumer as a consumer.
        """
        # Ad AdRep to have this AdRep as a consumer
        email = 'test_ad_rep_first@example.com'
        first_ad_rep = AdRep.objects.create(username=email, email=email,
            first_name=email, url='first', firestorm_id=101)
        email = 'test_ad_rep_second@example.com'
        second_ad_rep = AdRep.objects.create(username=email, email=email,
            first_name=email, url='second', firestorm_id=102, rank='CUSTOMER')
        AdRepConsumer.objects.create(ad_rep=first_ad_rep,
            consumer=second_ad_rep)
        second_ad_rep.rank = 'ADREP'
        second_ad_rep.save()
        self.assertEqual(first_ad_rep.ad_rep_consumers.filter(
            consumer=second_ad_rep).count(), 0)

    def test_parent_child_rels(self):
        """ Assert the child parent child relationship of ad_reps. """
        email = 'test_ad_rep_parent@example.com'
        parent_ad_rep = AdRep.objects.create(username=email, email=email,
            first_name=email, url='first', firestorm_id=103)
        email = 'test_ad_rep_child@example.com'
        child_ad_rep = AdRep.objects.create(username=email, email=email,
            first_name=email, url='second', parent_ad_rep=parent_ad_rep,
            firestorm_id=104)
        self.assertTrue(list(parent_ad_rep.child_ad_reps()), [child_ad_rep])

    def test_parent_generations(self):
        """ Assert upline generations are calculated. """
        ad_reps = AD_REP_FACTORY.create_generations(create_count=4)
        self.assertEqual(ad_reps[0].parent_generations(ad_reps[3]), 3)
        self.assertTrue(ad_reps[0].is_ad_rep_in_upline(ad_reps[3]))
        self.assertFalse(ad_reps[0].is_ad_rep_in_upline(ad_reps[3],
            max_generations=2))

    def get_ad_rep_for_lead_site(self):
        """ Assert an ad_rep of an AdRepSite is selected. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepSite.objects.create(ad_rep=ad_rep, site=ad_rep.site)
        self.assertEqual(ad_rep, AdRep.objects.get_ad_rep_for_lead(ad_rep.site))

    def get_ad_rep_default_site(self):
        """ Assert the latest ad_rep of site is selected but not a CUSTOMER. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        ad_rep.rank = 'CUSTOMER'
        ad_rep.save()
        with self.assertRaises(AdRep.DoesNotExist):
            AdRep.objects.get_ad_rep_for_lead(ad_rep.site)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.assertEqual(ad_rep, AdRep.objects.get_ad_rep_for_lead(ad_rep.site))
        
    def get_ad_rep_for_lead_market(self):
        """ Assert an ad_rep of an AdRepUSState is selected. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepUSState.objects.create(ad_rep=ad_rep,
            us_state=ad_rep.site.default_state_province)
        self.assertEqual(ad_rep, AdRep.objects.get_ad_rep_for_lead(ad_rep.site))

    def get_ad_rep_site_preferred(self):
        """ Assert an ad_rep of an AdRepSite is preferred over AdRepUSState.

        For HudsonValley, a market related to ad_rep1 through AdRepSite and
        in NY, a state related to ad_rep2 through AdRepUSState, leads should be
        given to ad_rep1.
        """
        ad_rep1, ad_rep2 = AD_REP_FACTORY.create_ad_reps(create_count=2)
        AdRepSite.objects.create(ad_rep=ad_rep1, site=ad_rep1.site)
        AdRepUSState.objects.create(ad_rep=ad_rep2,
            us_state=ad_rep1.site.default_state_province)
        self.assertEqual(ad_rep1,
            AdRep.objects.get_ad_rep_for_lead(ad_rep1.site))



class TestAdRepOrderModel(FirestormTestCase):
    """ Test case for AdRepOrder model. """
    fixtures = ['test_promotion']

    def test_change_ad_rep(self):
        """ Assert the ad_rep of an ad_rep_order cannot be changed. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        order = ORDER_FACTORY.create_order()
        ad_rep_order = AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
        ad_rep_2 = AD_REP_FACTORY.create_ad_rep()
        ad_rep_order.ad_rep = ad_rep_2
        with self.assertRaises(ValidationError):
            ad_rep_order.save()
    
    def test_check_order_promotion_good(self):
        """ Assert a valid promotion code of the promoter 'Firestorm Ad Reps' is
        not overridden.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        order = ORDER_FACTORY.create_order(product_id=3)
        promotion_code = PromotionCode.objects.get_by_natural_key('A475')
        # Apply promotion to order. Check recalculated values.
        order.promotion_code = promotion_code
        order.save()
        AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
        # Get fresh order, it has been resaved from underneath us.
        order = Order.objects.get(id=order.id)
        self.assertEqual(order.promotion_code, promotion_code)
        self.assertTrue(order.promoter_cut_amount > 0)
        self.assertEqual(order.amount_discounted, Decimal('24.00'))

    def test_check_order_promotion_bad(self):
        """ Assert a promotion code of a promoter who is not 'Firestorm Ad Reps'
        is replaced with the "default" promotion_code, "zero".
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        order = ORDER_FACTORY.create_order(product_id=3)
        # This is a test promotion.
        order.promotion_code = PromotionCode.objects.get_by_natural_key(
            'free flyer')
        order.save()
        AdRepOrder.objects.create(ad_rep=ad_rep, order=order)
        # Get fresh order, it has been resaved from underneath us.
        order = Order.objects.get(id=order.id)
        self.assertEqual(order.promotion_code,
            PromotionCode.objects.get_by_natural_key('zero'))
        self.assertTrue(order.promoter_cut_amount > 0)
        self.assertEqual(order.amount_discounted, Decimal('0.00'))


class TestBonusPoolAllocation(FirestormTestCase):
    """ Test case for BonusPoolAllocation model. """

    def test_percentage_cap(self):
        """ Assert allocation amounts cannot exceed n percent of order total."""
        ad_reps = AD_REP_FACTORY.create_ad_reps(create_count=5)
        order = ORDER_FACTORY.create_order(product_id=3)
        # Avoid close_ad_reps calculation, for performance.
        ad_reps[0].consumer_zip_postal = None
        ad_reps[0].save()
        ad_rep_order = AdRepOrder.objects.create(ad_rep=ad_reps[0], order=order)
        for counter, ad_rep in enumerate(ad_reps):
            bonus_pool_allocation = BonusPoolAllocation(
                ad_rep_order=ad_rep_order, ad_rep=ad_rep,
                consumer_points=1,
                amount=Decimal(str(float(order.total) * .021)))
            if counter < 5:
                bonus_pool_allocation.save()
            else:
                with self.assertRaises(ValidationError):
                    bonus_pool_allocation.save()


class TestAdRepLeadModel(FirestormTestCase):
    """ Test case for the AdRepLead model. """

    def test_clean_ad_rep_lead(self):
        """ Assert an ad_rep_lead having the same email address of an ad_rep
        does not pass cleaning.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        ad_rep_lead = AdRepLead(email=ad_rep.email, username='foo',
            primary_phone_number='8885550000')
        try:
            ad_rep_lead.clean()
            self.fail('AdRepLead with email of AdRep passed cleaning.')
        except ValidationError:
            pass

    def test_create_lead_from_con(self):
        """ Assert an ad_rep_lead is created from a consumer. """
        email = 'test_ad_rep_lead_from_consumer@example.com'
        consumer = Consumer.objects.create_consumer(username=email, email=email,
            consumer_zip_postal='12601', site_id=2)
        ad_rep_lead_dict = {'primary_phone_number': None, 
            'email': consumer.email}
        ad_rep_lead = AdRepLead.objects.create_ad_rep_lead_from_con(consumer.id,
            ad_rep_lead_dict)
        self.assertEqual(ad_rep_lead.id, consumer.id)

    def test_convert_lead_to_ad_rep(self):
        """ Assert an ad_rep_lead is converted to an ad_rep. """
        email = 'test_ad_rep_lead@example.com'
        ad_rep_lead = AdRepLead.objects.create(email=email, username=email)
        ad_rep_lead.email_subscription.add(1, 5, 6)
        ad_rep_dict = {'email': email, 'firestorm_id': 12,}
        for field in ['url'] + self.ad_rep_repl_website_fields:
            ad_rep_dict[field] = 'ad_rep_lead'
        ad_rep = AdRep.objects.create_ad_rep_from_ad_rep_lead(ad_rep_lead.id,
            ad_rep_dict)
        self.assertEqual(ad_rep.email, email)
        try:
            AdRepLead.objects.get(id=ad_rep_lead.id)
            self.fail('AdRepLead not deleted after converting to AdRep.')
        except AdRepLead.DoesNotExist:
            pass
        # Assert adreplead email subscription is removed on creation of ad rep.
        with self.assertRaises(EmailSubscription.DoesNotExist):
            ad_rep.email_subscription.get(id=5)
        self.assertEqual(len(ad_rep.email_subscription.all()), 2)


class TestAdRepLeadAdmin(EnhancedTestCase):
    """ Test case for the AdRepLead model. """

    fixtures = ['admin-views-users.xml']

    def test_admin(self):
        """ Asserts ad_rep_lead change_list is rendered. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.client.login(username='super', password='secret')
        # A minimal ad_rep_lead.
        email = 'test_ad_rep_lead_minimal@example.com'
        AdRepLead.objects.create(email=email, username=email)
        # Another ad_rep_lead.
        email = 'test_ad_rep_lead_maximal@example.com'
        AdRepLead.objects.create(email=email, username=email,
            first_name='foo', last_name='bar',
            ad_rep_id=ad_rep.id, primary_phone_number='8885550001')
        response = self.client.get(
            reverse('admin:firestorm_adreplead_changelist'))
        self.assertTemplateUsed(response, 'admin/change_list.html')


class TestAdRepUSState(TestCase):
    """ Test case for AdRepUSState model. """

    def test_state_unicity(self):
        """ Assert a state cannot be related to multiple ad reps. """
        ad_rep_1, ad_rep_2 = AD_REP_FACTORY.create_ad_reps(create_count=2)
        AdRepUSState.objects.create(ad_rep=ad_rep_1, us_state_id=1)
        with self.assertRaises(IntegrityError):
            AdRepUSState.objects.create(ad_rep=ad_rep_2, us_state_id=1)