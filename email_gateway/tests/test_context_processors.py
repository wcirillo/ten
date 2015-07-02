""" Tests for context_processors of email_gateway app of project ten. """

from django.test import TestCase

from advertiser.models import Advertiser
from consumer.models import Consumer
from email_gateway.context_processors import get_rep_context
from firestorm.models import AdRep, AdRepConsumer, AdRepAdvertiser
from market.models import Site

class TestGetRepContext(TestCase):
    """ Test case for process functions of email_gateway app. """

    fixtures = ['test_consumer', 'test_advertiser', 'test_ad_rep', 
        'test_sales_rep']
    
    def prep_test(self):
        """ Prepare an advertiser as an AdRepAdvertiser for testing. """
        self.advertiser = Advertiser.objects.latest('id')
        self.ad_rep = AdRep.objects.get(id=1000)
        AdRepAdvertiser.objects.create(
            ad_rep=self.ad_rep, advertiser=self.advertiser)

    def test_ad_rep_consumer(self):
        """ Assert an ad_rep_consumer produces the correct context. """
        consumer = Consumer.objects.latest('id')
        ad_rep = AdRep.objects.get(id=1000)
        AdRepConsumer.objects.create(ad_rep=ad_rep, consumer=consumer)
        context = get_rep_context(Site.objects.get(id=2), consumer.email, 
            cc_rep=True)
        self.assertEqual(context.get('signature_email', None), ad_rep.email)
        self.assertEqual(context.get('rep_first_name', None), ad_rep.first_name)
        self.assertTrue(context.get('cc_signature_flag', False))
        self.assertEqual(context['signature_title'], 
            'Advertising Representative')
        self.assertEqual(context['firestorm_id'], 1)

        # Re-test context w/o cc_rep=True
        context = get_rep_context(Site.objects.get(id=2), consumer.email)
        self.assertFalse(context.get('cc_signature_flag', False))
        self.assertEqual(context.get('firestorm_id', False), 1)

    def test_ad_rep_advertiser(self):
        """ Assert an ad_rep_advertiser produces the correct context. """
        self.prep_test()
        context = get_rep_context(Site.objects.get(id=2), 
                self.advertiser.email, cc_rep=True)
        self.assertEqual(context.get('headers', None).get('Reply-To', None),
            'Reputable@10Coupons.com')
        self.assertEqual(
            context.get('signature_email', None), self.ad_rep.email)
        self.assertEqual(context.get('firestorm_id', False), 1)
        
    def test_ad_rep_adv_instance(self):
        """ Assert that the context is set appropriately when the ad rep is of
        CUSTOMER rank and the recipient is an advertiser (should not use ad
        rep for context)
        """
        self.prep_test()
        self.ad_rep.rank = 'CUSTOMER'
        self.ad_rep.save()
        context = get_rep_context(Site.objects.get(id=2), self.advertiser.email,
            instance_filter='advertiser', cc_rep=True)
        self.assertEqual(context.get('headers', None).get('Reply-To', None),
            'Reputable@10Coupons.com')
        self.assertNotEqual(
            context.get('signature_email', None), self.ad_rep.email)
        self.assertEqual(context.get('firestorm_id', False), False)
    
