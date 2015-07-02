""" This is a test module for coupon view testing. """
import datetime
import logging
import urlparse

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from advertiser.factories.business_factory import BUSINESS_FACTORY
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from common.session import create_consumer_in_session
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import Slot
from coupon.service.expiration_date_service import frmt_expiration_date_for_dsp
from coupon.views import print_single_coupon
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestAllCouponsView(EnhancedTestCase):
    """ Test for coupon views. """
    fixtures = ['test_geolocation']
    urls = 'urls_local.urls_2'
    
    def test_local_site_with_consumer(self):
        """  Assert home page hits consumer's all-coupons site no redirect. """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('all-coupons'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/coupons/')
        self.assertTemplateUsed(response, 'coupon/display_all_coupons.html')
        self.assertContains(response, '10NorthJerseyCoupons.com')
        self.assertNotContains(response, 'load_like_contest_not_qualified')
        
    def test_coupons_no_consumer(self):
        """ Assert non redirect to home when not site 1. """
        response = self.client.get(reverse('all-coupons'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.redirect_chain), 0)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/coupons/')
        self.assertTemplateUsed(response, 'coupon/display_all_coupons.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_nearby_sites.html')
        self.assertTemplateUsed(response,
            'include/dsp/dsp_market_counties.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_all_offers.html')
        self.assertNotContains(response, 'load_like_contest_not_qualified')
        self.assertContains(response, 'Hudson Valley coupons for consum')
        self.assertContains(response, '$199/month')

    def test_home_with_subscriber(self):
        """ Assert xfbml for facebook like appears for subscriber on home page.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        CONSUMER_FACTORY.qualify_consumer(consumer)
        mobile_phone = consumer.subscriber.mobile_phones.all()[0]
        mobile_phone.is_verified = False
        mobile_phone.save()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('all-coupons'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/coupons/')
        self.assertTemplateUsed(response, 'coupon/display_all_coupons.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_share_site.html')
        # Assumes contest is running:
        self.assertContains(response, 'load_like_contest_not_qualified')


class TestAllCouponsFacebookView(EnhancedTestCase):
    """ Test case for the coupon view show_all_coupons_facebook. """
    urls = 'urls_local.urls_2'

    def test_good(self):
        """ Assert the view for facebook has links targeting new windows. """
        slot = SLOT_FACTORY.create_slot()
        response = self.client.get(reverse('all-coupons-facebook'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ' target="new">')
        self.assertContains(response, slot.slot_time_frames.latest(
            'id').coupon.offer.business.business_name)
        self.assertContains(response, slot.slot_time_frames.latest(
            'id').coupon.offer.headline)
        self.assertTemplateUsed(response, 'frames/web/iframeBody.html')
        self.assertTemplateUsed(response,
            'coupon/display_all_coupons_facebook.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_all_offers.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_single_offer.html')


class TestGenericAllCouponsView(EnhancedTestCase):
    """ Test all coupons view from site 1. """
    def test_show_on_site_1_no_session(self):
        """ Assert /coupons/ on site 1 with no session redirects to home. """
        response = self.client.get('/coupons/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse.urlparse(response['location']).path, '/')
        
    def test_show_on_site_1_w_session(self):
        """ Assert view when hit /coupons/ on site 1 with session. """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get('/coupons/')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlparse.urlparse(response['location']).path,
            '/hudson-valley/coupons/')


class TestPrintCoupon(EnhancedTestCase):
    """ Test coupon printing. """
    
    urls = 'urls_local.urls_2'
    
    def test_print_invalid_coupon(self):
        """ Assert the print view when coupon is invalid redirects. """
        factory = RequestFactory()
        request = factory.post('coupon/0/')
        response = print_single_coupon(request, coupon_id=0)
        # Should redirect to coupons page.
        self.assertEqual(str(response['location']), "/hudson-valley/coupons/", 
            "Print coupon page with no coupon failed to redirect to home page")
        
    def test_print_coupon_success(self):
        """ Assert successfully loaded coupon print view. """
        factory = RequestFactory()
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        headline = coupon.offer.headline
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        request = factory.post('coupon/%s/' % coupon.id)
        request.session = self.session
        response = print_single_coupon(request, coupon_id=coupon.id)
        # Should display print view.
        self.assertContains(response, 'class="printmarket')
        self.assertContains(response, "Print this coupon")
        self.assertContains(response, headline[:16])
        # Check for consumer action recorded for this coupon.
        try:
            self.assertEqual(coupon.consumer_actions.all()[0].action.name, 
                'Printed')
        except IndexError:
            self.fail('ConsumerAction not recorded') 

    def test_print_coupon_x_site(self):
        """ Assert successfully loaded coupon print view displays weblogo
        with the site name where the coupon resides, not necessarily the site
        name in the session from the URL.
        """
        factory = RequestFactory()
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        site = Site.objects.get(id=4)
        Slot.objects.filter(id=slot.id).update(site=site)       
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        request = factory.post('coupon/%s/' % coupon.id)
        request.session = self.session
        response = print_single_coupon(request, coupon_id=coupon.id)
        # Should display print view.
        self.assertContains(response, "Print this coupon")
        # Check slot's site Capital-Area used in view and links.
        self.assertContains(
            response, 'href="/capital-area/coupons/"><p>CapitalArea</p></a>')
        self.assertContains(response, "/capital-area/coupon-%s" % coupon.slug())


class TestViewSingleCoupon(EnhancedTestCase):
    """ Test case for view-single-coupon. """
    
    urls = 'urls_local.urls_2'
    
    def test_view_single_coupon(self):
        """ Assert a valid coupon displays correctly with a consumer in session.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        coupon.is_valid_thursday = False
        coupon.save()
        coupon.default_restrictions.add(3)
        business = coupon.offer.business
        consumer = CONSUMER_FACTORY.create_consumer(subscription_list=False)
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        self.assertEqual(coupon.consumer_actions.filter(action=2).count(), 0)
        response = self.client.get(reverse('view-single-coupon', 
            kwargs={'slug': coupon.slug(), 'coupon_id': coupon.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'coupon/display_single_coupon.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_single_coupon.html')
        self.assertContains(response, '<meta name="robots" content="noydir">')
        self.assertContains(response, '<meta name="robots" content="noodp">')
        self.assertContains(response, '<a class="button largeBtn" ' + 
            'href="/hudson-valley/coupon/%s/" rel="nofollow">' % coupon.id)
        self.assertContains(response, 
            'href="/hudson-valley/"><div >HudsonValley</div>')
        self.assertContains(response,
            'href="/hudson-valley/coupons/%s/%s/">%s' % (
                business.slug(), business.id, business.business_name))
        self.assertContains(response, 'class="business_name">%s' %
            business.business_name)
        self.assertContains(response, 'class="headline">%s' %
            coupon.offer.headline)
        self.assertContains(response, 
            '<h4 class="qualifier">\n                %s\n' %
            coupon.offer.qualifier)
        self.assertContains(response, 'Tax and Gratuity Not Included.')
        self.assertContains(response, 
            'No cash value. Not valid in combination with other offers.')
        self.assertContains(response, 'Coupon void if altered.')
        self.assertContains(response, 
            'class="valid_days">Offer not valid Thursdays.')
        self.assertContains(response, 
            'class="redemption_window">Valid through %s' %
            frmt_expiration_date_for_dsp(coupon.expiration_date))
        self.assertNotContains(response, 'Send this coupon to your inbox.')
        self.assertNotContains(response, 'Send My Coupon')
        # Assumes contest is running:
        self.assertContains(response, '%s%s' % ('Create a coupon like',
            ' this for YOUR business'))
        # Check for consumer action recorded for this coupon
        self.assertEqual(coupon.consumer_actions.filter(action=2).count(), 1)
        # Check for facebook meta for like button.
        self.assertTemplateUsed(response, 'include/dsp/dsp_facebook_meta.html')
        self.assertContains(response, 
            'meta property="og:url" content="%s/hudson-valley/coupon-%s/%s/"' %
            (settings.HTTP_PROTOCOL_HOST, coupon.slug(), coupon.id))
        self.assertTemplateUsed(response, 
            'include/dsp/dsp_facebook_like_small.html')
        self.assertContains(response,
            'fb:like href="%s/hudson-valley/coupon-%s/%s/"' %
            (settings.HTTP_PROTOCOL_HOST, coupon.slug(), coupon.id))
    
    def test_get_no_consumer(self):
        """ Assert a valid coupon displays with no consumer in session. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        response = self.client.get(reverse('view-single-coupon',
            kwargs={'slug': coupon.slug(), 'coupon_id': coupon.id}))
        self.assertTemplateUsed(response, 'coupon/display_single_coupon.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_single_coupon.html')
        self.assertContains(response, '<a class="button largeBtn ' +
            'modaltriggerSm" name="print_coupon_iframe%s" rel="nofollow">' %
            coupon.id)

    def test_view_single_coupon_expired(self):
        """ Assert an expired coupon redirects temporarily. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        coupon.expiration_date = datetime.date.today() - datetime.timedelta(1)
        coupon.save()
        response = self.client.get(reverse('view-single-coupon',
            kwargs={'slug': coupon.slug(), 'coupon_id': coupon.id}), 
            follow=True)
        self.assertTrue(len(response.redirect_chain))
        self.assertTrue('/hudson-valley/coupons/1/' 
            in response.redirect_chain[0][0])
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 
            'Oops! Sorry, the coupon you are looking for is not available.')
        self.assertContains(response, 
            'Check out the current coupons in the Hudson Valley Area below.')
            
    def test_view_single_non_coupon(self):
        """ Assert a coupon id that does not exist redirects temporarily.
        """
        response = self.client.get(reverse('view-single-coupon', 
            kwargs={'slug': 'foo', 'coupon_id': '0'}), follow=True)
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertTrue('/hudson-valley/coupons/1/' 
            in response.redirect_chain[0][0])
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 
            'Oops! Sorry, the coupon you are looking for is not available.')
        self.assertContains(response, 
            'Check out the current coupons in the Hudson Valley Area below.')
    
    def test_view_multi_location(self):
        """ Assert that the coupon meta tag has all locations listed in it. """
        coupon = COUPON_FACTORY.create_coupon_many_locations(
            business_location_count=2, coupon_location_count=2)
        COUPON_FACTORY.normalize_coupon_locations(coupon)
        SLOT_FACTORY.create_slot(coupon=coupon)
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        # Assert that meta description tag lists all locations.
        self.assemble_session(self.session)
        response = self.client.get(reverse('view-single-coupon', 
            kwargs={'slug': coupon.slug(), 'coupon_id': coupon.id}))
        self.assertEqual(response.status_code, 200)
        LOG.debug('-----test_view_multi_location Page Content Start-----')
        LOG.debug(response.content[:800])
        LOG.debug('-----test_view_multi_location Page Content End-----')
        locations = coupon.location.all()
        self.assertTrue(
            '"description" content="Get %s %s at %s in %s and %s, %s' % (
            coupon.offer.headline.title(), coupon.offer.qualifier.title(),
            coupon.offer.business.business_name,
            locations[0].location_city, locations[1].location_city,
            locations[1].location_state_province,)
            in response.content[:800])
        
    def test_websnap_and_mapview(self):
        """ Assert a valid coupon displays web snap and map view correctly. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        business = coupon.offer.business
        business.web_snap_path = "test_websnap_1.png"
        business.save()
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('view-single-coupon', 
            kwargs={'slug': coupon.slug(), 'coupon_id': coupon.id}))
        self.assertEqual(response.status_code, 200)
        # In body onload:
        self.assertContains(response, 'ol_map.build_location_map(')
        # Displays map:
        self.assertContains(response, '<div class="map" id="displaymap">')
        self.assertContains(response,
            '/media/images/web-snap/test_websnap_1.png')


class TestShowAllCouponsThisBiz(EnhancedTestCase):
    """ Test for show_all_coupons_this_business view. """

    urls = 'urls_local.urls_2'

    def setUp(self):
        super(TestShowAllCouponsThisBiz, self).setUp()
        self.slot_list = SLOT_FACTORY.create_slot_family(create_count=3)[1]
        self.coupon_list = SLOT_FACTORY.get_active_coupons(
            slot_list=self.slot_list)
        self.coupon0 = self.coupon_list[0]
        self.business = self.coupon0.offer.business
        self.consumer = self.business.advertiser.consumer
        self.request_data = None
        self.response = None
        
    def test_all_coupons_this_biz(self):
        """ Assert show_all_coupons_this_business with valid business id. """
        create_consumer_in_session(self, self.consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('view-all-businesses-coupons', 
            kwargs={'slug':self.business.slug(),
                'business_id':self.business.id}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 
            'coupon/display_all_coupons_for_this_business.html')
        self.assertContains(response,
            'class="business_name">\n            %s' % 
            self.business.business_name)
        for coupon in self.coupon_list:
            self.assertContains(response, coupon.offer.headline)
            # Check for consumer action recorded for this coupon
            self.assertEqual(coupon.consumer_actions.all().count(), 1)
        self.assertNotContains(response, 'Send this coupon to your inbox.')
        self.assertNotContains(response, 'Send My Coupon')
    
    def test_all_coupons_this_biz_meta(self):
        """ Assert all coupons for business displays meta tags for SEO. """
        response = self.client.get(reverse('view-all-businesses-coupons', 
            kwargs={'slug':self.business.slug(),
                'business_id':self.business.id}))
        self.assertEqual(response.status_code, 200)
        location = self.business.locations.all()[0]
        self.assertContains(response, '<title>%s, %s</title>' % (
            self.business.business_name, location.location_city))
        self.assertContains(response, 'content="%s coupons in %s, %s.' % (
            self.business.business_name,
            location.location_city,
            location.location_state_province))

    def test_national_coupon(self):
        """ Assert a business with a National coupon is displayed.
        Assert that if this is not the advertiser's site, canonicalize to
        advertiser's site.
        """ 
        self.coupon0.coupon_type_id = 6
        self.coupon0.is_approved = True
        self.coupon0.save()
        response = self.client.get(reverse('view-all-businesses-coupons', 
            kwargs={'slug':self.business.slug(),
                'business_id':self.business.id},
            urlconf='urls_local.urls_3'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 
            'coupon/display_all_coupons_for_this_business.html')
        self.assertContains(response,
            'class="business_name">\n            %s' % 
            self.business.business_name)
        self.assertContains(response, self.coupon0.offer.headline)
        self.assertContains(response, '<link rel="canonical" href="http://')
        self.assertContains(response, '/hudson-valley/coupons/%s/%s/"/>' %
            (self.business.slug(), self.business.id))

    def test_all_coupons_bad_slug(self):
        """ Assert valid business id but wrong slug redirects. """
        response = self.client.get(reverse('view-all-businesses-coupons', 
            kwargs={'slug':'foo', 'business_id':self.business.id}))
        self.assertEqual(response.status_code, 301)

    def test_all_coupons_no_biz(self):
        """ Asserts invalid business id 302 redirects to coupons. """
        response = self.client.get(reverse('view-all-businesses-coupons', 
            kwargs={'slug':'foo', 'business_id':50000000}), follow=True)
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[0][0], 
            '%s/hudson-valley/coupons/' % settings.HTTP_PROTOCOL_HOST)
        self.assertEqual(response.redirect_chain[0][1], 302)
        
    def test_no_current_coupons(self):
        """ Assert a business with no current coupons temporarily redirects to
        coupon page with a specific message. 
        """
        business = BUSINESS_FACTORY.create_business(create_location=True)
        response = self.client.get(reverse('view-all-businesses-coupons',
            kwargs={'slug':business.slug(), 'business_id':business.id},
            urlconf='urls_local.urls_3'), follow=True)
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(response.redirect_chain[0][0], 
            '%s/triangle/coupons/1/' % settings.HTTP_PROTOCOL_HOST)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTemplateUsed(response, 'include/dsp/dsp_all_offers.html')
        self.assertContains(response, 
            'Oops! Sorry, the coupon you are looking for')
        self.assertContains(response,
            'Check out the current coupons in the Triangle Area below.')
