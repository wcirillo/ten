""" Tests for common views of the ten project. """
import datetime

from django.core.urlresolvers import reverse

from advertiser.factories.advertiser_factory import ADVERTISER_FACTORY
from advertiser.factories.business_factory import BUSINESS_FACTORY
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from common.service.payload_signing import PAYLOAD_SIGNING
from common.session import (create_consumer_in_session,
    build_advertiser_session)
from common.test_utils import EnhancedTestCase
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import Flyer, FlyerCoupon
from ecommerce.service.calculate_current_price import get_product_price
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from market.models import Site


class TestGenericViews(EnhancedTestCase):
    """ Tests common views. """
   
    def test_contact_us(self):
        """ Assert the contact us page is displayed. """
        response = self.client.get(reverse('contact-us'))
        self.assertTemplateUsed(response, 'display_contact_us.html')
        
    def test_contest_rules(self):
        """ Assert the contest rules page is displayed. """
        response = self.client.get(reverse('contest-rules'))
        self.assertTemplateUsed(response, 'display_contest_rules.html')
        self.assertContains(response, 'Sweepstakes')
        self.assertContains(response, '10LocalCoupons.com')
        
    def test_show_help(self):
        """ Assert the help page is displayed. """
        response = self.client.get(reverse('help'))
        self.assertTemplateUsed(response, 'display_help.html')
        self.assertContains(response, 'Help / Frequently Asked Questions')
    
    def test_generic_how_it_works(self):
        """ Assert the how it works page redirects to home for site 1. """
        response = self.client.get(reverse('how-it-works'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/' in response['location'])

    def test_show_how_it_works(self):
        """ Assert that when zip is in session on local site 1, the page is 
        loaded in the respective market.
        """
        self.session['consumer'] = {'consumer_zip_postal': '12550'}
        self.assemble_session(self.session)
        response = self.client.get(reverse('how-it-works'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue('/hudson-valley/how-it-works/' in response['location'])

    def test_redirect_site_directory(self):
        """ Assert the site directory is displayed. """
        response = self.client.get('/hudson-valley/site-directory/')
        self.assertEqual(response.status_code, 301)
        self.assertTrue('/map/' in response['location'])

    def test_show_site_directory(self):
        """ Assert the site directory is displayed. """
        response = self.client.get(reverse('site-directory'))
        self.assertContains(response, 
            '/%s/">%s</a>' % ('hudson-valley', '10HudsonValleyCoupons.com'))
        self.assertTemplateUsed(response, 'display_site_directory.html')
        
    def test_show_privacy_policy(self):
        """ Assert the privacy policy is displayed. """
        response = self.client.get(reverse('privacy-policy'))
        self.assertTemplateUsed(response, 'display_privacy_policy.html')
        
    def test_show_sample_flyer(self):
        """ Assert the sample flyer is displayed. """
        response = self.client.get(reverse('sample-flyer'))
        self.assertTemplateUsed(response, 'display_sample_flyer.html')
        self.assertTemplateUsed(response, 
            'include/dsp/dsp_sample_coupons_for_flyer.html')
        
    def test_show_terms_of_use(self):
        """ Assert the Terms of Use is displayed. """
        response = self.client.get(reverse('terms-of-use'))
        self.assertTemplateUsed(response, 'display_terms_of_use.html')
        
    def test_media_partner_explanation(self):
        """ Assert the media partner home is displayed. """
        response = self.client.get(reverse('media-partner-home'))
        self.assertTemplateUsed(response, 
            'media_partner/display_media_partner_home.html')
        
    def test_media_partner_half_off(self):
        """ Assert the media partner half off is displayed. """
        response = self.client.get(reverse('media-partner-half-off'))
        self.assertTemplateUsed(response, 
            'media_partner/display_media_partner_half_off.html')
            
    def test_press_release(self):
        """ Assert the media partner press release is displayed. """
        response = self.client.get(reverse('press-release'))
        self.assertTemplateUsed(response, 
            'media_partner/display_press_release.html')

    def test_show_inside_radio(self):    
        """ Assert the Inside Radio article is displayed. """
        response = self.client.get(reverse('inside-radio'))
        self.assertTemplateUsed(response, 
            'media_partner/display_inside_radio.html')
    
    def test_show_generic_sign_in(self):
        """ Show sign in page on local site 1. """
        response = self.client.get(reverse('sign-in'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'create-coupon')
        self.assertTemplateUsed(response, 'include/frm/frm_sign_in.html')
        self.assertContains(response, 'Reset your password')
        self.assertContains(response, '/password-help/')


class TestLocalView(EnhancedTestCase):
    """ Test common views of page in market directory. """
    urls = 'urls_local.urls_2'
    
    def test_show_how_it_works(self):
        """ Assert the how it works page is displayed on market page. """
        email = 'test-how-it-works-market@test.com'
        consumer = Consumer(email=email, consumer_zip_postal='12601', 
            site_id=2)
        consumer.save()
        response = self.client.get(reverse('how-it-works'))
        self.assertTemplateUsed(response, 'display_how_it_works.html')
        # next test for slot price on page
        self.assertEqual(response.context['request'].META['site_id'], 2)
        site = Site.objects.get(id=2)
        slot_price = get_product_price(2, site=site)
        self.assertContains(response, 'in the counties of  Dutchess,')
        self.assertContains(response, 'Map')
        self.assertTrue(str(slot_price) in response.content)
        self.assertContains(response, "What's an Email Coupon Flyer?")      

    def test_how_it_works_ad_rep(self):
        """ Assert when the how it works page is displayed with an ad rep
        in session (without an advertiser signed in), it displays annual price. 
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        response = self.client.get(reverse('how-it-works'))
        self.assertTemplateUsed(response, 'display_how_it_works.html')
        self.assertContains(response, 'Display up to 10 coupons online')
        self.assertContains(response, 'get a full year')

    def test_hv_show_spots(self):
        """ Assert show_spots loads media sample content for this site. """
        response = self.client.get(reverse('show-spots'))
        self.assertContains(response, 'Media Spots')
        self.assertTemplateUsed(response, 'display_site_spots.html')
        self.assertContains(response, 'First aired')
        self.assertContains(response, 
            '%s%s' % ('href="/media/spots/HV/10Coupons_2011', 
            '_09_Change_HV_30_CareerChange.mp3"'))
        self.assertContains(response, '"Change"')

    def test_triangle_show_spots(self):
        """ Assert show_spots redirects to coupons if no slots are available on
        this site.
        """
        response = self.client.get('/triangle/spots/', follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'],
            '/triangle/coupons/')


class TestShowSampleFlyer(EnhancedTestCase):
    """
    Test common view sample-flyer that shows the most recent flyer sent on this
    site, or it shows a hard-coded sample of coupons in the flyer format.

    We need a tiny fixture here because flyer_createdatetime cannot be
    overridden in the ORM.
    """
    fixtures = ['test_flyer_401']
    urls = 'urls_local.urls_2'

    def test_show_sample_flyer(self):
        """ Assert the sample flyer is displayed. """
        flyer = Flyer.objects.get(id=401)
        flyer.send_status = 2
        flyer.save()
        sent_date = '%s%s' % (flyer.send_date.strftime('%A, %B '),
            flyer.send_date.strftime('%e').strip())
        slots = SLOT_FACTORY.create_slots(create_count=2)
        coupons = SLOT_FACTORY.prepare_slot_coupons_for_flyer(slots)
        for coupon in coupons:
            FlyerCoupon.objects.create(flyer=flyer, coupon=coupon)
        response = self.client.get(reverse('sample-flyer'))
        self.assertTemplateUsed(response, 'display_sample_flyer.html')
        self.assertTemplateUsed(response,
            'include/dsp/dsp_coupons_for_flyer.html')
        self.assertContains(response, sent_date)
        self.assertContains(response, flyer.coupon.all()[0].offer.headline)


class TestCrossSiteSignIn(EnhancedTestCase):
    """ Test cross site logins """
    
    urls = 'urls_local.urls_3'
    
    def test_cross_site_sign_in(self):
        """ Login an advertiser and make sure they go to the correct site. 
        This test is showing that the advertiser currently on site 3 gets 
        redirected to site 2 appropriately since that is the site the advertiser
        is associated with. Currently the advertiser is signing in on .triangle'
        """
        # A business is required for login.
        advertiser = BUSINESS_FACTORY.create_business().advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        response = self.client.post(reverse('sign-in'),
            data={ "email":advertiser.email, "password": "password"},
            follow=True)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/advertiser/')
        
    def test_show_sign_in_consumer(self):
        """ Test sign in page for consumer in session. """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('sign-in'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'display_sign_in.html')
        self.assertContains(response, 'Welcome back! Sign in with your email')
        self.assertNotContains(response, 'create a coupon</a>')
        self.assertContains(response, consumer.email)
    
    def test_show_sign_in_no_session(self):
        """ Test sign in page when no session. """
        response = self.client.get(reverse('sign-in'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'create a coupon</a>')
        self.assertTemplateUsed(response, 'display_sign_in.html')
        self.assertTemplateUsed(response, 'include/frm/frm_sign_in.html')
        self.assertContains(response, 'Welcome back! Sign in with your email')
        
    def test_show_sign_in_advertiser(self):
        """ Test sign in page when unauthenticated advertiser in session. """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('sign-in'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please sign in to continue to your')
        self.assertContains(response, 'create a coupon</a>')
        self.assertContains(response, advertiser.email)
        self.assertTemplateUsed(response, 'display_sign_in.html')
        self.assertTemplateUsed(response, 'include/frm/frm_sign_in.html')


class TestSignIn(EnhancedTestCase):
    """ Tests for set_password view. """
    
    fixtures = ['test_media_partner']
    urls = 'urls_local.urls_2'

    def test_get_set_password(self):
        """ Assert that when set password form is requested without a user,
        the request is redirected to sign in form. 
        """
        response = self.client.get(reverse('set-password'), follow=True)
        self.assertTemplateUsed(response, 
            'display_sign_in.html')
    
    def test_sign_in_consumer(self):
        """ Test when consumer signs in via sign-in form that they are added
        to the session and redirected to all-coupon view.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        response = self.client.post(reverse('sign-in'), data={
            "email": consumer.email,
            "password": "password"}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/coupons/')
        self.assertEqual(self.client.session['consumer']['email'],
            consumer.email)
        # Assert backoffice link to Firestorm is absent.
        self.assertNotContains(response, 'FireStormLogin.aspx')
    
    def test_post_consumer_no_pwd(self):
        """ Test when consumer signs in via sign-in form that password is not
        required.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        response = self.client.post(reverse('sign-in'), data={
            "email": consumer.email}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/coupons/')
        self.assertEqual(self.client.session['consumer']['email'],
            consumer.email)
        
    def test_sign_in_advertiser(self):
        """ Test when an advertiser signs in that they are authenticated
        and redirected to their advertiser account.
        """
        # A business is required for login.
        advertiser = BUSINESS_FACTORY.create_business().advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        response = self.client.post(reverse('sign-in'), data={
            "email": advertiser.email,
            "password": "password"}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/advertiser/')
        self.assertEqual(self.client.session['consumer']['email'], 
            advertiser.email)
    
    def test_sign_in_ad_rep(self):
        """ Test when an ad rep signs in that they are authenticated
        and redirected to their ad rep account in their market.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        response = self.client.post(reverse('sign-in',
            urlconf='urls_local.urls_1'), 
            data={
            "email": ad_rep.email,
            "password": "password"}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/ad-rep/')
        self.assertEqual(self.client.session['consumer']['email'], 
            ad_rep.email)

    def test_inactive_advertiser(self):
        """ Test when an inactive advertiser tries to sign in, they are 
        redirected to contact-us page.
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        advertiser.is_active = False
        advertiser.save()
        response = self.client.post(reverse('sign-in'), data={
            "email": advertiser.email,
            "password": "password"}, follow=True)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/contact-us/')
    
    def test_advertiser_no_pwd(self):
        """ Test when an advertiser tries to sign in with no password. """
        advertiser_email = 'user114@company.com'
        response = self.client.post(reverse('sign-in'), data={
            "email": advertiser_email, "password": ""})
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/sign-in/')
        self.assertContains(response, 
            "Email Address and Password don&#39;t match")
        self.assertContains(response, '/password-help/')
        
    def test_sign_in_media_partner(self):
        """ Test when media partner signs in that they are authenticated
        and redirected to their media partner report.
        """
        media_partner_email = 'test_media_group@example.com'
        response = self.client.post(reverse('sign-in'), data={
            "email": media_partner_email,
            "password": "password"}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/media-partner/')
        self.assertEqual(self.client.session['consumer']['email'], 
            media_partner_email)
        # Assert backoffice link to Firestorm is absent.
        self.assertNotContains(response, 'FireStormLogin.aspx')
    
    def test_sign_in_affiliate_partner(self):
        """ Test when affiliate partner signs in that they are authenticated
        and redirected to their media partner report.
        """
        affiliate_email = 'test_affiliate@example.com'
        response = self.client.post(reverse('sign-in'), data={
            "email": affiliate_email,
            "password": "password"}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/media-partner/')
        self.assertEqual(self.client.session['consumer']['email'], 
            affiliate_email)
        # Assert backoffice link to Firestorm is absent.
        self.assertNotContains(response, 'FireStormLogin.aspx')
        
    def test_sign_out(self):
        """ Assert a consumer is removed from session. """
        email = 'bounce-test-null-sign-out@bounces.10coupons.com'
        consumer = Consumer(email=email, consumer_zip_postal='12550', 
            site_id=2)
        consumer.save()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('sign-out'), follow=True)
        self.assertEqual(response.status_code, 200)
        # Asserting that it does not say "...@10coupons.com | My Account"
        self.assertContains(response, 'Get 10 Hudson Valley coupons sent to')
        self.assertContains(response, 'your email address')
        self.assertContains(response, 'zip code')
        self.assertContains(response, 'sign in</a>')
    
    def test_sign_out_w_ad_rep(self):
        """ Assert a consumer is removed from session but ad rep is retained.
        """
        email = 'bounce-test-null-sign-out2@bounces.10coupons.com'
        consumer = Consumer(email=email, consumer_zip_postal='12524', 
            site_id=2)
        consumer.save()
        create_consumer_in_session(self, consumer)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(ad_rep)
        self.assemble_session(self.session)
        response = self.client.get(reverse('sign-out'), follow=True)
        self.assertEqual(response.status_code, 200)
        # Assert consumer is gone.
        self.assertEqual(self.client.session.get('consumer', None), None)
        # Assert ad rep exists.
        self.assertEqual(self.client.session.get('ad_rep_id'), ad_rep.id)


class TestAdRepSignIn(EnhancedTestCase):
    """ Test Case for sign-in functionality for a firestorm.AdRep. """

    def test_sign_in(self):
        """ Assert a valid ad_rep sign-in form is redirected to the correct url.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        response = self.client.post(reverse('sign-in'), data={
            "email": ad_rep.email,
            "password": "password"}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(response.redirect_chain[0][0].endswith('/ad-rep/'))

    def test_invalid_sign_in(self):
        """ Assert an invalid ad_rep sign-in displays correct results. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        response = self.client.post(
            reverse('sign-in'), data={'email': ad_rep.email,
            'password': 'b;dsfjslkf4'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response,
            'Welcome back! Sign in with your email address')
        self.assertContains(response,
            "You don't need a password just to get coupons")
        # Assert "reset the password" link updates to firestorm url.
        self.assertNotContains(response, '/virtual-office-password-help/')


class TestPasswordReset(EnhancedTestCase):
    """ Tests for password reset request. """
    urls = 'urls_local.urls_2'
                
    def test_unauthorized_advertiser(self):
        """ Show sign in form when set-password requested with unauthenticated 
        advertiser in session. 
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('set-password'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], '/sign-in/')

    def test_show_password_reset(self):
        """ Test display of password reset """
        response = self.client.get(reverse('forgot-password')) 
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 
            'form name="frm_advertiser_forgot_password"')

    def test_post_password_reset_email(self):
        """ Test post password reset with no email """
        response = self.client.post(reverse('forgot-password')) 
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter an Email Address')

    def test_password_reset_bad_email(self):
        """ Post to password reset form with invalid data. """
        post_data = {'email': 'test-doesnotexist@company.com'}
        response = self.client.post(reverse('forgot-password'), post_data, 
            follow=True)
        # Goes to confirmation page.
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/password-help/')
        self.assertContains(response, 'Add Coupons@10Coupons.com as a contact.')

    def test_post_valid_password_reset(self):
        """ Post to password reset form with valid data. """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        post_data = {'email': advertiser.email}
        response = self.client.post(reverse('forgot-password'), post_data, 
            follow=True)
        # Goes to confirmation page.
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/password-help/')
        self.assertContains(response, 
            'Add Coupons@10Coupons.com as a contact.')
       

class TestOptInOptOutView(EnhancedTestCase):
    """ Tests opt in opt out view. """
    
    def test_show_opt_in_opt_out(self):
        """ Assert the form is not loaded on a GET when there is no
        consumer in session. Friendly message is displayed.
        """
        response = self.client.get(reverse('subscribe'))
        self.assertContains(response, 
            'Unsubscribing from Text Messages')
        
    def test_opt_out_consumer_session(self):
        """ Assert when a consumer is in session who is not subscribed, we 
        display a message of that. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.email_subscription.clear()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('unsubscribe'))
        self.assertContains(response,
            'Unsubscribed from 10LocalCoupons.com Email')
        self.assertContains(response, 
            "You've chosen not to receive messages from 10LocalCoupons.com") 
        self.assertContains(response, 
            'sent to this email address: <strong>%s</strong>' % consumer.email)
            
    def test_get_opt_out_consumer(self):
        """ Assert when a consumer is in session who is subscribed, we 
        display the unsubscribe button. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assemble_session(self.session)
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('unsubscribe'))
        self.assertContains(response, 
            'Unsubscribing from 10LocalCoupons.com Email')
        self.assertContains(response, 
            'We send messages to this email address: <strong>%s</strong>' % 
            consumer.email)
        self.assertContains(response, 
            '<form name="frm_opt_in_opt_out" method="post">')
        self.assertContains(response, 
            "input type='hidden' name='csrfmiddlewaretoken'")
        self.assertContains(response,
            '<input type="hidden" name="email" value="%s" id="id_email" />' % 
            consumer.email)
        self.assertContains(response, 
            'Unsubscribing from Text Messages')

    def test_opt_out_ext_recent(self):
        """ Assert display of external email subscription opt-out messages.
        Deprecated 12/11.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.email_subscription.add(3)
        listid = [3]
        response = self.client.get(reverse('opt_out', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email, 
                subscription_list=listid)]), follow=True)
        self.assertContains(response, 'be shared')
        
    def test_opt_out_ext_not_recent(self):
        """ Assert display of external email subscription opt-out messages.
        Deprecated 12/11.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.consumer_create_datetime = datetime.datetime.now() - \
            datetime.timedelta(days=10)
        consumer.save()
        consumer.email_subscription.add(3)
        listid = [3]
        # Check for different msg if consumer create date is > 5 days old
        response = self.client.get(reverse('opt_out', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email, 
                subscription_list=listid)]), follow=True)
        self.assertContains(response, 'stop sharing')

    def test_old_opt_out_ext_recent(self):
        """ Assert display of external email subscription opt-out messages.
        Deprecated 12/11.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.email_subscription.add(3)
        listid = '03234' # listid = 3 
        response = self.client.get(reverse('optout_deprecated2', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email), 
                listid]), follow=True)
        self.assertContains(response, 'be shared')
        
    def test_old_opt_out_ext_not_recent(self):
        """ Assert display of external email subscription opt-out messages.
        Deprecated 12/11.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.consumer_create_datetime = datetime.datetime.now() - \
            datetime.timedelta(days=10)
        consumer.save()
        consumer.email_subscription.add(3)
        listid = '03234' # listid = 3 
        # Check for different msg if consumer create date is > 5 days old
        response = self.client.get(reverse('optout_deprecated2', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email), 
                listid]), follow=True)
        self.assertContains(response, 'stop sharing')

    def test_post_opt_out_consumer(self):
        """ Assert when a consumer who is subscribed opts out, that she is 
        unsubscribed.
        """
        email = 'test-post-opt-out-consumer@example.com'
        consumer = Consumer()
        consumer.email = email
        consumer.consumer_zip_postal = '12550'
        consumer.site_id = 2
        consumer.save()
        site2_consumer_count = consumer.site.get_or_set_consumer_count()
        consumer.email_subscription.add(1)
        self.assertEqual(consumer.site.get_or_set_consumer_count(),
            site2_consumer_count + 1)
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        post_data = {'email':email}
        response = self.client.post(reverse('unsubscribe'), post_data, 
            follow=True)
        self.assertTemplateUsed(response, 
            'display_opt_out_confirmation.html')
        self.assertContains(response, 
            'Unsubscribed from 10LocalCoupons.com')
        self.assertEqual(consumer.email_subscription.count(), 0)
        self.assertEqual(consumer.site.get_or_set_consumer_count(), 
            site2_consumer_count)


class TestMarketSearchViews(EnhancedTestCase):
    """ Test site 1 home page zip code market search. """

    def test_get_market_search_form(self):
        """ Assert market search page display correctly (as iframe). """
        response = self.client.get(reverse('market-zip-search'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], '/market-zip-search/')
        self.assertContains(response, 'zip code')
        # Django bug? Sometimes request.templates is empty but response contents
        # are still the same.
        if len(response.templates):
            self.assertTemplateUsed(response,
                'include/frm/frm_market_search.html')
            self.assertTemplateUsed(response,
                'include/scripts/js_market_search_form.html')
        else:
            self.assertContains(response, '<form id="id_frm_market_search"')
            self.assertContains(response,
                '("#id_frm_market_search").submit(function(e)')

    def test_post_no_zip(self):
        """ Assert local site home page post with no zip, shows error. """
        response = self.client.post(reverse('market-zip-search'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], '/market-zip-search/')
        self.assertContains(response, "enter a 5 digit zip")

    def test_successful_zip_submit(self):
        """ Assert ajax response accepts valid zip. Cannot test rendering of
        close sites map displays or redirects supplied in url param 'next' 
        because it is handled in javascript. (those are tested in locate-market-
        map view).
        """
        response = self.client.post(reverse('market-zip-search'), 
            data={"consumer_zip_postal" : "12601"})
        self.assertContains(response, 'successful_submit')
        self.assertEqual(self.client.session['consumer']['consumer_zip_postal'],
            '12601')


class TestGenericLinkRedirects(EnhancedTestCase):
    """ Test redirects that use next url param after zip is submitted to go 
    to respective page. (These tests are a continuation of marketsearchviews.)
    """
    fixtures = ['test_geolocation']

    def test_market_zip_found(self):
        """ Assert local site home page post with market zip, redirects to 
        market (next url param). 
        """
        self.session['consumer'] = {'consumer_zip_postal': "12601"}
        self.assemble_session(self.session)
        response = self.client.get("%s?next=%s" % (reverse('locate-market-map'),
            reverse('advertiser-registration')), follow=True)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/create-coupon/')
    
    def test_non_market_zip_found(self):
        """ Assert local site home page post with market zip of non-market zip,
        shows nearby markets.
        """
        self.session['consumer'] = {'consumer_zip_postal': "00777"}
        self.assemble_session(self.session)
        response = self.client.get("%s?next=%s" % (reverse('locate-market-map'),
            reverse('advertiser-registration')), follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/locate-market-map/')
        self.assertContains(response, 'We\'re adding new markets every mont')
        self.assertContains(response, '10PuertoRicoCoupons.com')        
        
    def test_missing_next(self):
        """ Assert that locate-market-map view rendered missing "next" param
        redirects to home page.
        """
        #self.session['consumer'] = {'consumer_zip_postal': "12541"}
        self.assemble_session(self.session)
        response = self.client.get(reverse('locate-market-map'), follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/')

    def test_far_away_zip(self):
        """ Assert generic home page post with market zip, posted zip not 
        found in market list (or too far from any existing), displays site 
        directory). 
        """
        self.session['consumer'] = {'consumer_zip_postal': "99999"}
        self.assemble_session(self.session)
        response = self.client.get("%s?next=%s" % (reverse('locate-market-map'),
            reverse('advertiser-registration')), follow=True)
        self.assertEqual(response.request['PATH_INFO'], '/locate-market-map/')
        # Contains list of markets:
        self.assertContains(response, "10HudsonValleyCoupons.com")
        self.assertContains(response, "10CapitalAreaCoupons.com")
        # Contains links to state market maps.
        self.assertContains(response, '/map/new-york/')
        self.assertContains(response, '/map/puerto-rico/')
        self.assertContains(response, 'displaymap')


class TestGenericHomeView(EnhancedTestCase):
    """ Test home page displays and redirects when on non-market (site 1) site.
    """

    def test_site_1_home_no_consumer(self):
        """ Assert generic site home page has search form (in iframe in hidden
        div) when no consumer. """
        response = self.client.get(reverse('home'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], '/')
        self.assertContains(response, "market-zip-search")
        
    def test_consumer_site_1(self):
        """ Assert generic site home page sends to map page if it cannot find
        a market for a consumer in session. """
        self.session['consumer'] = {'consumer_zip_postal': "00777"}
        self.assemble_session(self.session)
        response = self.client.get(reverse('home'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 'displaymap')
        self.assertEqual(response.request['PATH_INFO'], '/locate-market-map/')


class TestLocalHomeView(EnhancedTestCase):
    """ Test market home page displays and redirects. """
    fixtures = ['test_geolocation', 'test_consumer', 'test_subscriber']
    urls = 'urls_local.urls_2'
    
    def test_site_2_home_no_consumer(self):
        """ Assert non redirect to home when not site 1. """
        response = self.client.get('/hudson-valley/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], '/hudson-valley/')
        self.assertTemplateUsed(response, 'display_home.html')
        self.assertContains(response, 'your email address')
        self.assertContains(response, 'zip code')
        self.assertEqual(response.content.count('load_subscriber_form();'), 1)
        
    def test_local_home_override(self):
        """ Assert market home not rendered when /e/ at end of url 
        (sales override). 
        """
        response = self.client.get('/hudson-valley/e/', follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], '/f/')
        self.assertContains(response, "market-zip-search")
        
    def test_x_site_redirect(self):
        """ Assert when consumer on market site and enters a zip outside of this
        market, they are redirected to proper market. (Redirect is performed in
        javascript,  just check if url_to_change_market is correct).
        """
        self.session['consumer'] = {'email': 'test_consumer@xsiteredir.com', 
            'consumer_zip_postal': "12601"}
        self.assemble_session(self.session)
        response = self.client.post('/hudson-valley/', 
            data={'consumer_zip_postal': '00927', 'ajax_mode': 'consumer_reg',
            'email': 'test_consumer@xsiteredir.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual('00927', 
            self.client.session['consumer']['consumer_zip_postal'])
        format_content = response.content.replace(
            'true', 'True').replace('false', 'False')
        response_dict = eval(format_content)
        self.assertTrue(response_dict.get('url_to_change_market'))
        self.assertTrue('/puerto-rico/' 
            in response_dict['url_to_change_market'])

    def test_get_x_site_market_home(self):
        """ Assert when consumer entered zip in another market (different from
        the one they are on), and javascript redirected them (need Selenium
        test) that the resulting page with url parameter cross_site=true, calls
        the function to load the subscriber form.
        """
        self.session['consumer'] = {'email': 'test_consumer@xsiteredir.com', 
            'consumer_zip_postal': "00927"}
        self.assemble_session(self.session)
        response = self.client.get('/puerto-rico/?cross_site=true')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count('load_subscriber_form();'), 2)


class TestMapViews(EnhancedTestCase):
    """ Test home page displays and redirects. """
    fixtures = ['test_ny_markets']
    urls = 'urls_local.urls_2'
    def test_show_markets_in_state(self):
        """ Test display of state map with marker points. """
        state = 'new-york'
        response = self.client.get('/map/%s/' % state, follow=False)
        self.assertContains(response, 'ol_map.build_state_map')
        self.assertContains(response, ';Long Island;long-island|')
        self.assertContains(response, ';Buffalo;buffalo|')
        self.assertContains(response, '10HudsonValleyCoupons.com')
        self.assertContains(response, '/buffalo/"')
        self.assertContains(response, '/map/new-york/')
        self.assertContains(response, 'displaymap')
    
    def test_show_map_market_counties(self):
        """ Test display of county map for a given market. """
        response = self.client.get('/hudson-valley/map/', follow=False)
        self.assertContains(response, 'ol_map.build_market_map') 
        self.assertContains(response, ';Dutchess;')
        self.assertContains(response, 'and Westchester counties.')
        self.assertContains(response, 'div id="displaymap_controls"')


class TestNextFunctionality(EnhancedTestCase):
    """ Test the _next redirect functionality. """
    urls = 'urls_local.urls_2'

    def test_get_set_pass_next(self):
        """ Assert the set password form displays and the next values are still
        held in the querystring variables. This user is logged in and does
        not have a password yet.
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        self.login(email=advertiser.email)
        advertiser.password = '!'
        advertiser.save()
        response = self.client.post('%s?next=%s' % (reverse('set-password'), 
            reverse('advertiser-registration')),
            follow=False)
        self.assertContains(response, 'Create an Account Password')
        self.assertContains(response, 'Choose at least 6 characters.')
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/password-set/')
        self.assertEqual(response.request['QUERY_STRING'], 
            'next=/hudson-valley/create-coupon/')
    
    def test_get_reset_pass_next(self):
        """ Assert the reset password form displays and the next values are
        still held in the querystring variables. This user is logged in and
        has a password already.
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        self.login(email=advertiser.email)
        response = self.client.post('%s?next=%s' % (reverse('set-password'), 
            reverse('advertiser-registration')), follow=False)
        self.assertContains(response, 'Reset your Account Password')
        self.assertContains(response, 'Choose at least 6 characters.')
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/password-set/')
        self.assertEqual(response.request['QUERY_STRING'], 
            'next=/hudson-valley/create-coupon/')
        
    def test_get_reset_not_log_in(self):
        """ Test that the sign in form displays and the next values
        are still held in the querystring variables.  This user is not logged in 
        and and has a password already. Mostly this is testing that the 
        @login_required decorator remains a requirement o nthe set_password()
        function.
        """
        response = self.client.post('%s?next=%s' % (reverse('set-password'), 
            reverse('advertiser-registration')), follow=True)
        self.assertContains(response, 'frm_sign_in')
        self.assertNotContains(response, 'Create an Account Password')
        self.assertNotContains(response, 'Re-set your Account Password')
        self.assertNotContains(response, 'Choose at least 6 characters.')
        
    def test_post_reset_pass_next(self):
        """ After a password resets, make sure the next functionality pushes the 
        user to the correct page.
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        # Make sure there are no businesses associated with this advertiser
        # in the database.
        advertiser.businesses.all().delete()
        self.login(email=advertiser.email)
        response = self.client.post('%s?next=%s' % (reverse('set-password'), 
            reverse('advertiser-registration')),
            {'password1':'123456', 'password2':'123456'},
            follow=True)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/create-coupon/')
        
    def test_post_set_pass_next(self):
        """ After a password gets created for the first time make sure the next
        functionality pushes the user to the correct page.
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        # Make sure there are no businesses associated with this advertiser
        # in the database.
        advertiser.businesses.all().delete()
        self.login(email=advertiser.email)
        advertiser.password = '!'
        advertiser.save()
        response = self.client.post('%s?next=%s' % (reverse('set-password'), 
            reverse('advertiser-registration')),
            {'password1':'654321', 'password2':'654321'},
            follow=True)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/create-coupon/')


class TestConsumerMap(EnhancedTestCase):
    """ Test case for consumers map view. """
    urls = 'urls_local.urls_2'
    
    def test_show_consumer_map(self):
        """ Assert advertiser with valid slot gets good add flyers form. """
        response = self.client.get(reverse('show-consumer-map'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form id="frm_add_flyer_by_map"')
        self.assertContains(response, 'Include zip codes within')
        
class TestLoader(EnhancedTestCase):
    """ Test case for consumers map view. """
    urls = 'urls_local.urls_2'
    
    def test_loader(self):
        """ Test the loader will load when a encoded page to load is 
        passed in.
        """                
        response = self.client.get(reverse('loader',
            kwargs={'page_to_load':'load%5fterms%5fof%5fuse'}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Terms of Use Agreement')
