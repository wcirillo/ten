""" Test case for sending of sale emails. """
import logging
import datetime

from django.core import mail

from advertiser.models import Advertiser
from common.test_utils import EnhancedTestCase
from email_gateway.sale_sends import start_10

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)


class TestSaleSends(EnhancedTestCase):
    """ Assertations for sending sale emails. """
    
    fixtures = ['test_advertiser_views', 'test_sales_rep']
    
    def test_start_10(self):
        """ Assert the start_10 sale selects the correct advertisers and 
        contains the correct content.
        Assert email contains opt out link.
        """
        advertiser = Advertiser.objects.get(id=111)
        advertiser.is_emailable = True
        advertiser.site_id = 2
        advertiser.save()
        advertiser.email_subscription.add(2)
        inactive_date = datetime.date(2011, 2, 28)
        start_10(inactive_date, promo_code='tester')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 
            'Display your coupon for just ten bucks on 10HudsonValleyCoupons.com')
        self.assertEqual(mail.outbox[0].to[0], advertiser.email)
        self.assertTrue('bounce-advertiser_start_10-' in 
            mail.outbox[0].from_email)
        self.assertTrue('@bounces.10coupons.com' in mail.outbox[0].from_email)
        self.assertTrue(advertiser.email_hash in mail.outbox[0].from_email)
        # Assert headers.
        self.assertEqual(mail.outbox[0].extra_headers['From'],
            'Reputable at 10HudsonValleyCoupons.com <Coupons@10Coupons.com>')
        self.assertTrue('/hudson-valley/opt-out-list/' in 
            mail.outbox[0].extra_headers['List-Unsubscribe'])
        # Assert email_hash is also in this header.
        self.assertTrue(advertiser.email_hash in
            mail.outbox[0].extra_headers['List-Unsubscribe'])        
        self.assertTrue('<mailto:list_unsubscribe-advertiser_start_10-' in 
            mail.outbox[0].extra_headers['List-Unsubscribe'])
        self.assertTrue('@bounces.10coupons.com>' in 
            mail.outbox[0].extra_headers['List-Unsubscribe'])
        self.assertEqual(mail.outbox[0].extra_headers['Reply-To'],
            'Reputable@10Coupons.com')
        # Assert contents.
        self.assertTrue('tester' in mail.outbox[0].body)
        # Assert opt out link in both versions.
        self.assertTrue('/hudson-valley/opt-out-list/' in mail.outbox[0].body)
        self.assertTrue('">unsubscribe</a>' in 
            mail.outbox[0].alternatives[0][0])
