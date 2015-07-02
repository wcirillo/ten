""" Test cases for firestorm.views.ad_rep_account_views """
import logging
import xml.dom.minidom

from django.core.urlresolvers import reverse
from django.http import Http404
from django.test import RequestFactory

from common.templatetags.format_phone_number import format_phone_number
from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import CouponAction, CouponType
from firestorm.connector import FirestormConnector
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.factories.ad_rep_lead_factory import AD_REP_LEAD_FACTORY
from firestorm.models import AdRepAdvertiser, AdRepConsumer, AdRepLead

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class TestAdRepAccountViews(EnhancedTestCase):
    """ Test views in the ad rep account. """

    urls = 'urls_local.urls_2'
    
    def test_downline_recruits(self):
        """ Assert recruits and their referred customer counts display. """
        ad_rep_list = AD_REP_FACTORY.create_ad_reps(create_count=3)
        parent_ad_rep = ad_rep_list[0]
        child_ad_rep_1 = ad_rep_list[1]
        child_ad_rep_2 = ad_rep_list[2]
        child_ad_rep_1.parent_ad_rep = parent_ad_rep
        child_ad_rep_1.save()
        child_ad_rep_2.parent_ad_rep = parent_ad_rep
        child_ad_rep_2.save()
        consumer = CONSUMER_FACTORY.create_consumer()
        AdRepConsumer.objects.create(ad_rep=child_ad_rep_1, consumer=consumer)
        self.session['ad_rep_id'] = parent_ad_rep.id
        self.login(email=parent_ad_rep.email)
        self.assemble_session(self.session)
        response = self.client.get(reverse('ad-rep-downline-recruits'))
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/ad-rep/downline-recruits/')
        self.assertContains(response, 
            'Click a name to display contact information')
        self.assertContains(response, '%s %s' % (child_ad_rep_1.first_name, 
            child_ad_rep_1.last_name))
        self.assertContains(response, '%s %s' % (child_ad_rep_2.first_name, 
            child_ad_rep_2.last_name))
        self.assertContains(response, '<strong>1</strong>')

class TestAdRepConsumers(EnhancedTestCase):
    """ Test case for view ad_rep_consumers. """
    fixtures = ['admin-views-users.xml', 'activate_switch_firestorm_feeds']

    def test_valid_ad_rep(self):
        """ Assert consumer eligibility is correctly reported for an ad_rep. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AD_REP_FACTORY.qualify_ad_rep(ad_rep)
        self.client.login(username='super', password='secret')
        response = self.client.get(reverse('admin-ad-rep-consumers',
            kwargs={'ad_rep_id': ad_rep.id}))
        LOG.debug(response.content)
        self.assertContains(response,
            """You've referred <strong style="font-size: 17px;">10""")
        self.assertContains(response, 'Signed Up for Email Flyers?')
        self.assertContains(response, 'NO')
        self.assertContains(response, 'YES')
        self.assertContains(response,
            'Independent Advertising Representatives, like you,')


class TestDownlineConsumers(EnhancedTestCase):
    """ Test case for view ad_rep_consumers. """
    fixtures = ['admin-views-users.xml', 'activate_switch_firestorm_feeds']

    def test_valid_ad_rep(self):
        """ Assert view displays downline consumer and qualified consumer counts
        for each.
        """
        child_ad_rep1, parent_ad_rep = AD_REP_FACTORY.create_generations(
            create_count=2)
        child_ad_rep2 = AD_REP_FACTORY.create_ad_rep()
        child_ad_rep2.parent_ad_rep = parent_ad_rep
        child_ad_rep2.save()
        consumers = CONSUMER_FACTORY.create_consumers(create_count=3)
        for consumer in consumers:
            CONSUMER_FACTORY.qualify_consumer(consumer)
        AdRepConsumer.objects.create(consumer=consumers[0],
            ad_rep=child_ad_rep1)
        AdRepConsumer.objects.create(consumer=consumers[1],
            ad_rep=child_ad_rep2)
        AdRepConsumer.objects.create(consumer=consumers[2],
            ad_rep=child_ad_rep2)
        self.client.login(username='super', password='secret')
        response = self.client.get(reverse('admin-downline-consumers',
            kwargs={'ad_rep_id': parent_ad_rep.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recruitment Activity for %s %s' %
            (parent_ad_rep.first_name, parent_ad_rep.last_name))
        self.assertContains(response, 'Customers')
        self.assertContains(response, '%s %s' %
            (child_ad_rep1.first_name, child_ad_rep1.last_name))
        self.assertContains(response,
            "Click a name to view that Advertising Representative's")
        self.assertTrue(response.content.count('>1</strong>'), 2)
        # Output is sorted by consumer count;, child_ad_rep2 comes first.
        self.assertTrue(response.content.index(child_ad_rep2.first_name) <
            response.content.index(child_ad_rep1.first_name))
        # Only market managers (rank) get this text:
        self.assertNotContains(response, 'commission is paid to you')

    def test_downline_drill_down(self):
        """ Assert an ad rep can view n level generations of downline. """
        ad_rep_list = AD_REP_FACTORY.create_generations(create_count=4)
        LOG.debug('ad_rep_list: %s' % ad_rep_list)
        # ad_rep_list[3] is the parent of [2], whi is a parent of [1]
        AD_REP_FACTORY.qualify_ad_rep(ad_rep_list[1])
        self.client.login(username='super', password='secret')
        response = self.client.get(reverse(
            'admin-downline-consumers-drill-down',
            kwargs={'ad_rep_id': ad_rep_list[3].id,
                'downline_ad_rep_id': ad_rep_list[2].id}))
        LOG.debug(response.content)
        self.assertContains(response,
            '/downline-consumers/%s/%s/">' % (
            ad_rep_list[3].id, ad_rep_list[1].id))
        self.assertContains(response, '%s %s' % (ad_rep_list[1].first_name,
            ad_rep_list[1].last_name))
        self.assertContains(response,
            'Recruitment Activity for %s' % ad_rep_list[2].first_name)
        self.assertContains(response, ad_rep_list[2].get_rank_display())
        self.assertContains(response, '#009933;">10</strong>')


class TestRecruitmentAd(EnhancedTestCase):
    """Test class for firestorm recruitment-ad view. """
    fixtures = ['admin-views-users.xml', 'activate_switch_firestorm_feeds']
    
    def test_recruitment_ad(self):
        """ Assert that when an ad rep in session recruitment ad can be 
        retrieved (shows advertisement text they can use on their own).
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.client.login(username='super', password='secret')
        response = self.client.get(reverse('admin-recruitment-ad',
            kwargs={'ad_rep_id': ad_rep.id}),
            {'id': ad_rep.firestorm_id, 's': 'DLFKJLKJDF'})
        self.assertTemplateUsed(response,
            'include/dsp/dsp_firestorm_recruitment_ad.html')
        self.assertContains(response, ad_rep.first_name)
        self.assertContains(response, ad_rep.last_name)
        self.assertContains(response, ad_rep.primary_phone_number)
        self.assertContains(response, ad_rep.email)
        self.assertContains(response, ad_rep.site.domain)
        self.assertContains(response, "Post this Help Wanted Ad")

class TestWebAddresses(EnhancedTestCase):
    """ Test case for web_addresses view. """

    fixtures = ['admin-views-users.xml']

    def test_ad_rep_good(self):
        """ Assert correct web addresses are displayed. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.client.login(username='super', password='secret')
        response = self.client.get(reverse('admin-web-addresses',
            kwargs={'ad_rep_id': ad_rep.id}))
        for string in [
            '10HudsonValleyCoupons.com/join-me/how-it-works/%s/',
            '10HudsonValleyCoupons.com/join-me/recommend/%s/',
            '10HudsonValleyCoupons.com/%s/'
            ]:
            self.assertContains(response, string % ad_rep.url)


class TestAdvertiserStats(EnhancedTestCase):
    """ Test case for view advertiser_stats. """

    fixtures = ['admin-views-users.xml', 'activate_switch_firestorm_feeds',
        'activate_switch_replicated_website']

    def test_valid_ad_rep(self):
        """ Assert stats for coupons are displayed for this ad_rep. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.client.login(username='super', password='secret')
        response = self.client.get(reverse('admin-advertiser-stats',
            kwargs={'ad_rep_id': ad_rep.id}))
        LOG.debug(response.content)
        self.assertContains(response, '%s %s - Advertiser Stats' % (
            ad_rep.first_name, ad_rep.last_name))
        self.assertContains(response,
            "input type=\'hidden\' name=\'csrfmiddlewaretoken\'")
        self.assertContains(response, 'Business Name')
        self.assertContains(response, 'Coupon Offer')

    def test_unpublished_coupons(self):
        """ Assert coupons belonging to related advertisers display and no
        unpublished coupons display (have to test ajax call). """
        coupon = COUPON_FACTORY.create_coupon()
        in_progress_coupon = COUPON_FACTORY.create_coupon()
        in_progress_coupon.coupon_type = CouponType.objects.get(id=1)
        in_progress_coupon.save()
        offer = in_progress_coupon.offer
        offer.business = coupon.offer.business
        offer.save()
        SLOT_FACTORY.create_slot(coupon=coupon)
        SLOT_FACTORY.create_slot(coupon=in_progress_coupon)
        # Relate this business to ad rep.
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepAdvertiser.objects.create(ad_rep=ad_rep, 
            advertiser=coupon.offer.business.advertiser)
        self.client.login(username='super', password='secret')
        response = self.client.post(reverse('admin-advertiser-stats',
            kwargs={'ad_rep_id': str(ad_rep.id)}),
            {'id': ad_rep.firestorm_id,'business_id': '0'})
        self.assertContains(response, '"coupon_id": %s' % coupon.id)
        self.assertNotContains(response, '"coupon_id": %s' % 
            in_progress_coupon.id)

    def test_ajax(self):
        """ Assert ajax contains data for coupons of advertiser's businesses.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        coupon_list = COUPON_FACTORY.create_coupons(create_count=3)
        count = 1
        for coupon in coupon_list:
            AdRepAdvertiser.objects.create(ad_rep=ad_rep,
                advertiser=coupon.offer.business.advertiser)
            for action_id in [1, 2, 3, 7]:
                CouponAction.objects.create(coupon=coupon,
                    action_id=action_id, count=count)
                count += 1
        self.client.login(username='super', password='secret')
        post_data = {'id': ad_rep.firestorm_id,
            'business_id': '0'}
        # The the view needs the POST dict.
        response = self.client.post(reverse('admin-advertiser-stats',
            kwargs={'ad_rep_id': str(ad_rep.id)}),
            post_data)
        LOG.debug(coupon_list)
        LOG.debug(response.content)
        for coupon in coupon_list:
            self.assertContains(response,
                '"headline": "%s"' % coupon.offer.headline)
            self.assertContains(response,
                '"qualifier": "%s"' % coupon.offer.qualifier)
        self.assertContains(response, '"views": [1]')
        self.assertContains(response, '"clicks": [2]')
        self.assertContains(response, '"prints": [3]')
        self.assertContains(response, '"shares": [4]')
        self.assertContains(response, '"views": [5]')
        self.assertContains(response, '"clicks": [6]')
        self.assertContains(response, '"prints": [7]')
        self.assertContains(response, '"shares": [8]')
        self.assertContains(response, '"views": [9]')
        self.assertContains(response, '"clicks": [10]')
        self.assertContains(response, '"prints": [11]')
        self.assertContains(response, '"shares": [12]')


class TestAdminViews(EnhancedTestCase):
    """ Test case for custom admin views for firestorm app. """
    # Note the order of these is important:
    fixtures = ['admin-views-users.xml']

    def test_views(self):
        """ Assert custom firestorm views return 200. """
        self.client.login(username='super', password='secret')
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        views = ['admin-ad-rep-consumers',
            'admin-downline-consumers', 'admin-advertiser-stats',
            'admin-web-addresses', 'admin-recruitment-ad']
        for view in views:
            response = self.client.get(reverse(view, kwargs={
                'ad_rep_id': ad_rep.id}))
            self.assertEqual(response.status_code, 200)
      
        