""" Test case for service functions of firestorm app of project ten. """
import logging

from django.test import TestCase
from django.test.client import RequestFactory

from advertiser.factories.advertiser_factory import ADVERTISER_FACTORY
from common.test_utils import EnhancedTestCase
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRepAdvertiser
from firestorm.service import build_adv_url_with_ad_rep, get_consumer_bonus_pool

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class TestGetConsumerBonusPool(TestCase):
    """ Test case for get_consumer_bonus_pool. """

    def test_get_consumer_bonus_pool(self):
        """ Assert the consumer bonus pool is calculated correctly. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        pool = get_consumer_bonus_pool()
        self.assertEqual(pool, 0)
        AD_REP_FACTORY.qualify_ad_rep(ad_rep)
        self.assertEqual(ad_rep.verified_consumers().count(), 10)
        ad_rep.consumer_points = '100'
        ad_rep.save()
        pool = get_consumer_bonus_pool()
        self.assertEqual(pool, 100)
        
class TestBuildURLForAdRepLoading(EnhancedTestCase):
    """ Test cases for service function build_adv_url_with_ad_rep that builds
    a url that calls join-me view and then redirects to final destination URL
    (after loading ad rep in session). If there is no ad rep, for advertiser
    (and no url supplied), then just pass back the destination URL.
    """

    def prep_test(self, ad_rep_advertiser=False):
        """ Create a request to test with. """
        self.advertiser = ADVERTISER_FACTORY.create_advertiser()
        self.ad_rep = AD_REP_FACTORY.create_ad_rep()
        factory = RequestFactory()
        self.request = factory.get('/hudson-valley/', follow=True)
        self.request.session = self.session
        self.request.session['ad_rep_id'] = self.ad_rep.id
        self.request.session['referring_ad_rep_dict'] = self.ad_rep
        if ad_rep_advertiser:
            AdRepAdvertiser.objects.create_update_rep(
                self.request, self.advertiser, self.ad_rep)

    def test_no_ad_rep_no_ad_rep_url(self):
        """ Assert when advertiser does not have an ad rep and no ad rep url
        supplied as a parameter, the destination URL is passed back.
        """
        self.prep_test()
        test_url = '/omega/alpha/pluralis/'
        formatted_url = build_adv_url_with_ad_rep(self.advertiser, test_url)
        self.assertEqual(formatted_url, test_url)

    def test_ad_rep_no_ad_rep_url(self):
        """ Assert when advertise  has an ad rep the link is formatted and
        returned correctly.
        """
        self.prep_test(True)
        test_url = '/omega/alpha/pluralis/'
        formatted_url = build_adv_url_with_ad_rep(self.advertiser, test_url)
        self.assertEqual(formatted_url,
            '/join-me/omega/alpha/pluralis/%s/' % self.ad_rep.url)

    def test_ad_rep_url(self):
        """ Assert whatever is passed at the ad rep url is used in the finally
        return (minimizes db hits).
        """
        self.prep_test(False)
        test_url = '/omega/alpha/pluralis/'
        formatted_url = build_adv_url_with_ad_rep(
            self.advertiser, test_url, self.ad_rep.url)
        self.assertEqual(formatted_url,
            '/join-me/omega/alpha/pluralis/%s/' % self.ad_rep.url)
