""" This is a test module for coupon view testing. """
import logging

from django.core.urlresolvers import reverse

from consumer.factories.consumer_factory import CONSUMER_FACTORY
from common.service.payload_signing import PAYLOAD_SIGNING
from common.session import create_consumer_in_session
from common.test_utils import EnhancedTestCase
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import CouponAction, ConsumerAction, CouponCode
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRepAdvertiser
from sms_gateway import config
from sms_gateway.models import SMSMessageSent
from subscriber.models import Subscriber, MobilePhone

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestCouponRedirect(EnhancedTestCase):
    """ 
    Test case for redirect_view_single_coupon view. This view primarily reloads
    the page with the same content under a well-formed URL.
    """ 
    
    urls = 'urls_local.urls_2'
    
    def test_redirect_to_coupon(self):
        """ Assert redirect_to_single_coupon normal will redirect to revised URL
        (using combination of slug value and offer headline).
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        # Pass in coupon_id and slug to view.
        response = self.client.post(reverse('redirect-view-single-coupon', 
            kwargs={'coupon_id':coupon.id, 'slug':coupon.slug()}), follow=True)
        self.assertTrue(getattr(response, 'redirect_chain', False))
        response_path = response.request['PATH_INFO']
        # Redirect path should have business name and coupon_id in it 
        # as well as offer.
        self.assertTrue(coupon.slug() in response_path)
        self.assertTrue(str(coupon.id) in response_path)

    def test_show_all_offers(self):
        """ Assert redirect_show_all_offers view redirects to all-coupons view
        (to display all offers in that market).
        """
        response = self.client.get(reverse('view-all-offers'), follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/', "Failed redirect to home page")
        self.assertTrue('Hudson Valley Coupons' in response.content)


class TestBusinessUrlClick(EnhancedTestCase):
    """
    This class houses test methods for the processes involving the clicking
    of links to the business URL.
    """
    
    urls = 'urls_local.urls_2'
    
    def test_click_with_get_no_biz(self):
        """ Assert GET of click_business_web_url redirects to all coupons.
        Test view click_business_web_url by sending a get request, which will
        force it to redirect to all-coupons view since a business url is not 
        supplied.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        coupon_id = 0
        # Pass in coupon_id and consumer to view.
        response = self.client.get(reverse('click-business-web_url',
            kwargs={'coupon_id':coupon_id}), follow=True) 
        # Redirected to home by default.
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')
        
    def test_click_with_get_with_biz(self):
        """ Test view click_business_web_url by sending a get request, which
        forces it to redirect to a business url which is supplied.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        coupon_id = 0
        # Pass in coupon_id and consumer to view.
        response = self.client.get(reverse('click-business-web_url', 
            kwargs={'coupon_id':coupon_id}),
            data={"url":"http://google.com/xx_path_to_redirect_to_xx/"}, 
            follow=True) 
        # Redirected to home by default.
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/xx_path_to_redirect_to_xx/')
    
    def test_click_get_with_consumer(self):
        """ Test view click_business_web_url with consumer argument passed in.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        business = coupon.offer.business
        business.web_url = "http://google.com"
        business.save()
        response = self.client.post(
            reverse('click-business-web_url',
            kwargs={'coupon_id':coupon.id}), follow=True)
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(response.redirect_chain[0][0], "http://google.com")
        self.assertEqual(response.redirect_chain[0][1], 302)
        try:
            self.assertEqual(str(coupon.coupon_actions.all()[0].action.name), 
            'Clicked Link')
        except IndexError:
            self.fail('CouponAction not recorded')
        self.assertEqual(
            ConsumerAction.objects.filter(consumer=consumer.id).count(), 1)

    def test_click_post_invalid_coupon(self):
        """ Test post to click_business_web_url view with invalid coupon, which
        forces a redirects to all-coupons view.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        coupon_id = 0
        # Pass in coupon_id and consumer to view.
        response = self.client.post(reverse('click-business-web_url', 
            kwargs={'coupon_id':coupon_id}), follow=True) 
        # Redirected to home by default.
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')


class TestSendSMSSingleCoupon(EnhancedTestCase):
    """ Tests views for sending a coupon to sms. """
    
    def setUp(self):
        super(TestSendSMSSingleCoupon, self).setUp()
        config.TEST_MODE = True
    
    def test_send_sms_bad_coupon(self):
        """ Assert show send sms single coupon redirects for bad coupon_id. """
        response = self.client.get(reverse('show-send-sms-single-coupon',
            kwargs={'coupon_id': 999}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].endswith('/coupons/'))

    def test_show_send_sms_form(self):
        """ Assert the 'send this coupon to my cell' form displays. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        response = self.client.get(reverse('show-send-sms-single-coupon',
            kwargs = {'coupon_id':coupon.id}))
        self.assertContains(response, 
            'Send this coupon as a text message to my cell phone!')
        self.assertContains(response, 
            'form id="id_form_subscriber" name="frm_subscriber_registration"')

    def test_get_subscriber_in_session(self):
        """ Assert GET with subscriber in session pre-fills the form. """
        consumer = CONSUMER_FACTORY.create_consumer()
        CONSUMER_FACTORY.qualify_consumer(consumer)
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        LOG.debug("session = %s" % self.session)
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        response = self.client.get(reverse('show-send-sms-single-coupon',
            kwargs = {'coupon_id':coupon.id}))
        LOG.debug("response: %s" % response.content)
        self.assertContains(response, 'value="%s"' %
            consumer.subscriber.mobile_phones.latest('id').mobile_phone_number)
        self.assertContains(response,
            '<option value="2" selected="selected">AT&amp;T</option>')

    def test_post_send_sms_form(self):
        """ Assert processing of the send coupon via sms form with valid data
        saves the subscriber and the phone and sends the sms.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        sms = 'this is the sms field'
        coupon.sms = sms
        coupon.save()
        post_data = {'mobile_phone_number': '1115553001',
            'subscriber_zip_postal': '12550', 'carrier': '2'}
        response = self.client.post(reverse('show-send-sms-single-coupon',
            kwargs = {'coupon_id':coupon.id}), post_data)
        self.assertContains(response, 
            'This coupon was sent as a text message to your cell phone.')
        self.assertTrue(Subscriber.objects.filter(
            mobile_phones__mobile_phone_number='1115553001').count())
        sms_message_sent = SMSMessageSent.objects.latest('id')
        self.assertEqual(sms_message_sent.smsto, '1115553001')
        self.assertEqual(sms_message_sent.smsmsg[:39], 
            "10Coupons Alrts: %s " % sms)
        self.assertTrue(CouponCode.objects.filter(coupon=coupon, 
            code=sms_message_sent.smsmsg[39:43]).count())
        self.assertEqual(sms_message_sent.smsmsg[44:59], "Details@Website")
    
    def test_post_send_sms_w_11_digits(self):
        """ Asserts processing of the send coupon via sms form when phone number
        has 11 digits (preceding 1).
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        post_data = {'mobile_phone_number': '12225553001',
            'subscriber_zip_postal': '12551', 'carrier': '5'}
        response = self.client.post(reverse('show-send-sms-single-coupon',
            kwargs = {'coupon_id':coupon.id}), post_data)
        self.assertContains(response, 
            'This coupon was sent as a text message to your cell phone.')
        
    def test_post_send_sms_form_other(self):
        """ Assert sending a coupon via sms when user selects carrier Other
        preforms a carrier lookup while saving the subscriber.
        
        In test mode, a carrier lookup will always return carrier 2.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        phone_number = '1115553002'
        post_data = {'mobile_phone_number': phone_number, 
            'subscriber_zip_postal': '12550', 'carrier': '1'}
        response = self.client.post(reverse('show-send-sms-single-coupon',
            kwargs = {'coupon_id':coupon.id}), post_data)
        self.assertContains(response, 
            "This coupon was sent as a text message to your cell phone.")
        self.assertTrue(Subscriber.objects.filter(
                mobile_phones__mobile_phone_number=phone_number
            ).count())
        self.assertEqual(MobilePhone.objects.get(
            mobile_phone_number=phone_number).carrier.id, 2)


class TestScanQRCode(EnhancedTestCase):
    """ This class houses test methods for the QR code scan click tracker. """
    urls = 'urls_local.urls_2'
    
    def test_scan_invalid_qr_code(self):
        """ Assert scanning an invalid QR code redirects to coupons. """
        coupon_id = 0
        slug = "test"
        code = "A23456"
        response = self.client.get(reverse('qr-code-view-single-coupon',
            kwargs={'coupon_id':coupon_id, 'slug':slug, 'code':code }), 
            follow=True) 
        # Redirected to home by default.
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')

    def test_scan_valid_qr_code(self):
        """ Assert scanning a valid QR code redirects to home. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        code = "VALID4" # Caps are required. No 1, 0.
        CouponCode.objects.create(coupon=coupon, code=code)
        self.assertEqual(coupon.coupon_actions.count(), 0)
        response = self.client.get(reverse('qr-code-view-single-coupon',
            kwargs={'coupon_id':coupon.id, 'slug':coupon.slug(), 'code':code }),
            follow=True) 
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(response.status_code, 200)
        # Check if coupon action is incremented.
        self.assertEqual(
            coupon.coupon_actions.filter(action=12).count(), 1)
        self.assertTrue(str(coupon.id) in response.request['PATH_INFO'])
        self.assertContains(response, coupon.offer.headline)
        self.assertContains(response, coupon.id)


class TestTweetCoupon(EnhancedTestCase):
    """ This class houses test methods for the Tweet coupon click tracker. """
    urls = 'urls_local.urls_2'
    
    def test_click_tweet_invalid_coupon(self):
        """ Assert Tweet of an invalid coupon redirects to coupons. """
        coupon_id = 0
        response = self.client.get(reverse('tweet-coupon',
            kwargs={'coupon_id':coupon_id }), follow=True) 
        # Redirected to home by default.
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')
    
    def test_click_tweet_valid_coupon(self):
        """ Assert Tweet of a valid coupon redirects to Twitter. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        self.assertEqual(coupon.coupon_actions.count(), 0)
        response = self.client.get(reverse('tweet-coupon',
            kwargs={'coupon_id':coupon.id }), follow=True)
        # Redirected to Twitter 
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertTrue('twitter.com' in response.redirect_chain[0][0])
        self.assertTrue(str(coupon.id) in response.redirect_chain[0][0])
        # Check if Tweet is tracked
        self.assertEqual(coupon.coupon_actions.filter(action=13).count(), 1)


class TestFacebookCoupon(EnhancedTestCase):
    """ This class houses test methods for the Facebook share coupon. """
    urls = 'urls_local.urls_2'
    
    def test_facebook_invalid_coupon(self):
        """ Assert Facebook share of an invalid coupon redirects to home. """
        coupon_id = 0
        response = self.client.get(reverse('facebook-coupon',
            kwargs={'coupon_id':coupon_id }), follow=True) 
        # Redirected to home by default.
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')
        
    def test_facebook_valid_coupon(self):
        """ Assert Facebook share of a valid coupon. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        self.assertEqual(coupon.coupon_actions.all().count(), 0)
        response = self.client.get(reverse('facebook-coupon',
            kwargs={'coupon_id':coupon.id }), follow=True)
        # Check if Facebook share is tracked.
        self.assertEqual(coupon.coupon_actions.all().filter(action=7).count(
            ), 0)
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/coupons/')


class TestFlyerClickShowCoupon(EnhancedTestCase):
    """ This class houses test methods for the Flyer click link to coupon. """
    urls = 'urls_local.urls_2'
    
    def test_click_flyer_click_invalid(self):
        """ Assert click of invalid coupon redirects to home. """
        coupon_id = 0
        response = self.client.get(reverse('flyer-view-single-coupon',
            kwargs={'slug':'test', 
                    'coupon_id':coupon_id, 
                    'consumer_email_hash':'0' }), follow=True) 
        # Redirected to home by default.
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/coupons/')
    
    def test_click_flyer_valid_coupon(self):
        """ Assert click of a valid coupon, invalid slug, valid hash redirects
        to coupon.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assertEqual(coupon.coupon_actions.count(), 0)
        response = self.client.get(reverse('flyer-view-single-coupon',
            kwargs={'slug': 'test',
                    'coupon_id': str(coupon.id),
                    'consumer_email_hash': consumer.email_hash}), follow=True)
        self.assertTrue(getattr(response, 'redirect_chain', False))
        self.assertTrue(str(coupon.id) in response.request['PATH_INFO'])
        # Check for action on this coupon.
        self.assertEqual(coupon.coupon_actions.filter(action=9).count(), 1)
        try:
            self.assertEqual(coupon.consumer_actions.filter(
                action=9)[0].action.name, 'Viewed From Flyer')
        except IndexError:
            self.fail('ConsumerAction not recorded')
        # Make sure action is linked to this consumer.
        self.assertEqual(consumer.consumer_actions.filter(action=9).count(), 1)


class TestWindowDisplay(EnhancedTestCase):
    """ Test case for view window_display. """

    fixtures = ['activate_switch_replicated_website']

    urls = 'urls_local.urls_2'

    def test_window_display(self):
        """ Assert window_display renders correctly. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        response = self.client.get(reverse('window-display',
            kwargs={'coupon_id': coupon.id}))
        self.assertContains(response, 'HudsonValley')
        self.assertContains(response, coupon.offer.business.business_name)
        # QR code:
        self.assertContains(response, 
            'chart.apis.google.com/chart?chs=225x225&cht=qr&c')
        self.assertContains(response,
            '10coupons.com/hudson-valley/coupons/%s/%s/"/>' %
                (coupon.offer.business.slug(), coupon.offer.business.id))

    def test_window_display_bad(self):
        """ Assert window_display redirects for a bad coupon_id. """
        response = self.client.get(reverse('window-display',
            kwargs={'coupon_id': 999}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].endswith('/coupons/'))

    def test_ad_rep_window_display(self):
        """ Assert when business's coupon associated with ad rep the qr code
        path used to generate the issue uses join-me (redirect-for-ad-rep)
        view.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        AdRepAdvertiser.objects.create_update_rep(
            self.client, coupon.offer.business.advertiser, ad_rep)
        response = self.client.get(reverse('window-display',
            kwargs={'coupon_id': coupon.id}))
        self.assertContains(response,
            'hudson-valley/join-me/coupons/%s/%s/%s/"/>' %
                (coupon.offer.business.slug(),
                coupon.offer.business.id, ad_rep.url))


class TestEmailCoupon(EnhancedTestCase):
    """ Test case for show-email-coupon. """
    
    urls = 'urls_local.urls_2'
    
    def test_get_email_coupon(self):
        """ Assert GET of this view shows the consumer registration form with
        the appropriate values on the page.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        response = self.client.get(reverse('show-email-coupon',
            kwargs={'coupon_id': coupon.id}))
        self.assertContains(response, 'frm_consumer_registration')
        self.assertTemplateUsed(response, 
            'include/frm/frm_consumer_registration.html')
        
    def test_post_no_fields_filled(self):
        """ Assert the correct messages show when the form fields are not filled
        out correctly.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        response = self.client.post(reverse('show-email-coupon',
            kwargs={'coupon_id': coupon.id}),
            {'email': '', 'consumer_zip_postal': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'errors')
        self.assertContains(response, 'Please enter a valid email.')
        self.assertContains(response, 'Please enter a 5 digit zip')
        
    def test_new_consumer(self):
        """Assert the correct data gets passed back when this new registered
        consumer registers on the email this coupon form.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        response = self.client.post(reverse('show-email-coupon',
            kwargs={'coupon_id': coupon.id}),
            {'email': 'test_new_consumer@example.com',
            'consumer_zip_postal': 10990},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '"is_already_registered": false')
        
    def test_existing_consumer(self):
        """ Assert the correct data gets passed back when this existing consumer
        registers on the email this coupon form.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        consumer = CONSUMER_FACTORY.create_consumer()
        response = self.client.post(reverse('show-email-coupon',
            kwargs={'coupon_id': coupon.id}),
                    {'email': consumer.email,
                    'consumer_zip_postal': consumer.consumer_zip_postal},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '"is_already_registered": true')
        
    def test_existing_consumer_no_zip(self):
        """Assert correct data gets passed back when this existing consumer
        registers on the email this coupon form. A consumer_zip_postal is not a
        required field to move to a print screen if we recognize the consumers
        email already in our db.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        consumer = CONSUMER_FACTORY.create_consumer()
        response = self.client.post(reverse('show-email-coupon',
            kwargs={'coupon_id': coupon.id}),
            {'email': consumer.email,
            'consumer_zip_postal': ''},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '"is_already_registered": true')
        
    def test_email_coupon_confirmation(self):
        """ Assert the email coupon confirmation page shows the correct info
        when a coupon_id is passed into it.
        """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.post(reverse('email-coupon-confirmation',
            kwargs={'coupon_id': coupon.id}))
        self.assertContains(response, 'Check your email right away!')
        self.assertContains(response,
            'Your coupon: <strong>%s</strong> from %s' % (coupon.offer.headline,
                coupon.offer.business.business_name))
        self.assertContains(response, 
            'To print the coupon click the button in our email message.')
        self.assertContains(response, 
            'Your email address is verified when you click "Print the coupon.')
        self.assertContains(response, 'Qualify to Win $10,000!*')


class TestExternalClickCoupon(EnhancedTestCase):
    """ Test case for view external_click_coupon. """

    urls = 'urls_local.urls_2'

    def test_external_click_coupon(self):
        """ Assert external click action gets incremented. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        coupon.precise_url = 'http://cnn.com'
        coupon.save()
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        try:
            before_clicks = CouponAction.objects.get(
                action__id=8, coupon=coupon).count
        except CouponAction.DoesNotExist:
            before_clicks = 0
        response = self.client.get(reverse('external-click-coupon',
            kwargs={'coupon_id': coupon.id}))
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response['location'], coupon.precise_url)
        self.assertEqual(CouponAction.objects.get(
            action__id=8, coupon=coupon).count, before_clicks + 1)
        try:
            ConsumerAction.objects.get(
                action__id=8, coupon=coupon, consumer=consumer)
        except ConsumerAction.DoesNotExist:
            self.fail('ConsumerAction not recorded.')

    def test_external_click_bad(self):
        """ Assert external click counter redirects for a bad coupon_id. """
        response = self.client.get(reverse('external-click-coupon',
            kwargs={'coupon_id': 999}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].endswith('/hudson-valley/'))


class TestFlyerClickCoupon(EnhancedTestCase):
    """ Test case for view flyer_click_coupon. """

    urls = 'urls_local.urls_2'

    def test_flyer_click_coupon(self):
        """ Assert flyer click action gets incremented. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.latest('id').coupon
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        payload = PAYLOAD_SIGNING.create_payload(email=consumer.email)
        response = self.client.get(reverse('flyer-click',
            kwargs={'coupon_id': coupon.id, 'payload': payload}))
        self.assertEqual(response.status_code, 301)
        self.assertTrue(
            response['location'].endswith('/coupon-%s/%s/' % (coupon.slug(),
                coupon.id)))
        self.assertTrue(
            CouponAction.objects.get(action__id=9, coupon=coupon).count, 1)
        try:
            ConsumerAction.objects.get(action__id=9, coupon=coupon,
                consumer=consumer)
        except ConsumerAction.DoesNotExist:
            self.fail('ConsumerAction not recorded.')

    def test_flyer_click_bad(self):
        """ Assert flyer click counter redirects for a bad coupon_id. """
        response = self.client.get(reverse('flyer-click',
            kwargs={'coupon_id': 999, 'payload': None}))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].endswith('/coupons/'))
