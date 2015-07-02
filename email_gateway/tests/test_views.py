""" Tests of email_gateway views. """
#pylint: disable=W0104
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from advertiser.models import Advertiser
from advertiser.factories.advertiser_factory import ADVERTISER_FACTORY
from advertiser.factories.business_factory import BUSINESS_FACTORY
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from common.service.payload_signing import PAYLOAD_SIGNING
from common.test_utils import EnhancedTestCase
from consumer.models import Consumer, UniqueUserToken
from coupon.models import Coupon
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY


class TestViews(EnhancedTestCase):
    """ Test cases for email_gateway views. """
    
    fixtures = ['test_advertiser', 'test_ad_rep']
    urls = 'urls_local.urls_2'
    
    def test_valid_opt_out_deprecated(self):
        """ Assert that opting-out of an email type works, this version is
        deprecated as of 12/2011 but was used in emails. """
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assertTrue(consumer.email_subscription.count() > 0)
        listid = '01234'
        response = self.client.get(reverse('optout_deprecated2', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email), 
                listid]), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST,
            reverse('opt-out-confirmation'))
        self.assertTrue(target_path in response.redirect_chain[0][0])       
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 'Unsubscribed from')
        self.assertContains(response, consumer.email)
        self.assertEqual(consumer.email_subscription.count(), 0)
    
    def test_valid_opt_out(self):
        """ Assert that opting-out of an email type works. """
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assertTrue(consumer.email_subscription.count() > 0)
        listid = [1]
        response = self.client.get(reverse('opt_out', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email,
                subscription_list=listid)]), follow=True)   
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(reverse('opt-out-confirmation') 
            in response.redirect_chain[0][0])
        self.assertContains(response, consumer.email)
        self.assertEqual(consumer.email_subscription.count(), 0)

    def test_opt_out_invalid_listid(self):
        """ Assert when a consumer opts out with an invalid listID, that she is
        redirected to the unsubscribe page.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assertEqual(consumer.email_subscription.count(), 1)
        response = self.client.get(reverse('opt_out', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email,
                subscription_list='BAD_listid')]), follow=True)
        self.assertTrue(response.redirect_chain[0][0].endswith('unsubscribe/'))
        self.assertEqual(response.redirect_chain[0][1], 302)

    def test_valid_multi_opt_out(self):
        """ Assert that opting-out of multiple email type renders well. """
        consumer = CONSUMER_FACTORY.create_consumer()
        response = self.client.get(reverse('opt_out',
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email,
                subscription_list=[2, 3])]), follow=True)   
        self.assertTrue(reverse('opt-out-confirmation')
            in response.redirect_chain[0][0])
        self.assertContains(response, 
            'longer send Advertiser Updates and External')
        self.assertContains(response, consumer.email)
        self.assertTrue(consumer.email_subscription.get(id=1))

    def test_invalid_hash_opt_out_dep(self):
        """ Checks behavior if an invalid payload is passed-into the
        deprecated version. """
        listid = '01234' 
        response = self.client.get(reverse('optout_deprecated', 
            args=['this-is-not-a-valid-signed-payload', listid], 
            urlconf='urls_local.urls_1'), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('unsubscribe', 'urls_local.urls_1'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 'The easiest method')
    
    def test_invalid_hash_opt_out(self):
        """ Checks behavior if an invalid payload is passed-in. """
        response = self.client.get(reverse('opt_out', 
            args=['this-is-not-a-valid-signed-payload'],
            urlconf='urls_local.urls_1'), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('unsubscribe', 'urls_local.urls_1'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 'The easiest method')
    
    def test_valid_verify_consumer(self):
        """ Assert email-verification button in in signup emails changes
        is_email_verified to True, and renders the correct page. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        email = consumer.email   
        self.assertEqual(consumer.is_email_verified, False)
        response = self.client.get(reverse('email_verify_consumer', 
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email)]),
            follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('all-coupons'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTemplateUsed(response, 
            "include/dsp/dsp_registration_rotation.html")
        self.assertContains(response, consumer.email)
        # Refresh consumer info since this changed it.
        consumer = Consumer.objects.get(email=email)
        self.assertEqual(consumer.is_email_verified, True)
    
    def test_invalid_verify_consumer(self):
        """ Assert email-verification button in signup emails with a bad 
        signed payload redirects to home page with no specific messaging.
        """
        response = self.client.get(reverse('email_verify_consumer', 
            args=["1230598173"]), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('all-coupons'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
    
    def test_valid_subscriber_reg(self):
        """ Assert email-verification button in in signup emails changes
        is_email_verified to True, and renders the correct page. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        self.assertEqual(consumer.subscriber, None)
        response = self.client.get(reverse('add_subscriber',
            args=[PAYLOAD_SIGNING.create_payload(email=consumer.email)]),
            follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST,
            reverse('subscriber-registration'))
        self.assertEqual(response.redirect_chain[0][0], target_path)    
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTemplateUsed(response,
            "include/frm/frm_subscriber_registration.html")
        self.assertContains(response, consumer.email)
        self.assertContains(response, consumer.consumer_zip_postal)
        
    def test_invalid_subscriber_reg(self):
        """ Assert subscriber registration button in unqualified emails
        with a bad signed payload redirects still redirects to subscriber 
        registration (just with no session).
        """
        response = self.client.get(reverse('add_subscriber', 
            args=["1230598173756"]), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST,
            reverse('subscriber-registration'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        
    def test_valid_login_advertiser_np(self):
        """ Tests the initial experience and advertiser would have from 
        clicking on "go to my account" in their receipt email, as they
        would not yet have a password set.
        """    
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        advertiser.password = '!'
        advertiser.save()
        response = self.client.get(reverse('login-advertiser-from-email', 
            args=[PAYLOAD_SIGNING.create_payload(email=advertiser.email)]), 
            follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('advertiser-account'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 'Create an Account Password')
                
    def test_login_advertiser(self):
        """ Test the effect of the "go to my account" button in a receipt 
        after the advertiser has set a password. 
        """    
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        BUSINESS_FACTORY.create_business(advertiser=advertiser)
        advertiser.password = 'sha1$e8a58$11a5e329d858dba184f3adaa71d0f58cbdb2c77a'
        advertiser.save()
        response = self.client.get(reverse('login-advertiser-from-email', 
            args=[PAYLOAD_SIGNING.create_payload(email=advertiser.email)]),
            follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('advertiser-account'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, self.client.session['consumer']\
            ['advertiser']['business'][0]['business_name'])
    
    def test_login_ad_rep(self):
        """ Test the effect of the "go to my account" button in a receipt 
        after the advertiser has set a password when they are an AdRep. 
        """    
        advertiser = Advertiser.objects.get(id=1001)
        advertiser.password = \
            'sha1$6efc0$f93efe9fd7542f25a7be94871ea45aa95de57161'
        advertiser.save()
        response = self.client.get(reverse('login-advertiser-from-email', 
            args=[PAYLOAD_SIGNING.create_payload(email=advertiser.email)]))
        self.assertTrue('hudson-valley/ad-rep/' 
            in response['location'])
        
    def test_invalid_login_advertiser(self):
        """ Tests method when passed an invalid 'signed' payload. """
        response = self.client.get(reverse('login-advertiser-from-email', 
            args=['goo']), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('all-coupons'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)

    def test_login_consumer_ad_rep(self):
        """ Test the effect of the "go to my account" button in a receipt 
        after the ad_rep has set a password. 
        """    
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        response = self.client.get(reverse('login-ad-rep-from-email', 
            args=[PAYLOAD_SIGNING.create_payload(email=ad_rep.email)]),
            follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('ad-rep-account'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(ad_rep.id, self.client.session['ad_rep_id'])


class TestSaleRedirectWithSession(EnhancedTestCase):
    """ Test case for sale_redirect_with_session view. """
    
    fixtures = ['test_advertiser', 'test_advertiser_views', 'test_coupon_views']
    urls = 'urls_local.urls_2'
    
    def test_good(self):
        """ Assert that the email becomes verified and the advertiser and promo 
        code are set in session.
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        my_id = advertiser.id
        advertiser.is_email_verified = False
        advertiser.save()
        response = self.client.get(reverse('sale-redirect-with-promo', 
            args=[PAYLOAD_SIGNING.create_payload(email=advertiser.email),
            'test promo']), follow=True)
        advertiser = Advertiser.objects.get(id=my_id)
        self.assertTrue(advertiser.is_email_verified)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('advertiser-registration'))
        self.assertEqual(response.redirect_chain[0][0], target_path)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(self.client.session['promo_code'], 'test promo') 
        self.assertEqual(
            self.client.session['consumer']['advertiser']['advertiser_id'], my_id) 
        
    def test_xss_scrubbed(self):
        """ Assert that submitted content is scrubbed of disallowed content. """
        xss_payload = """'';!--"<XSS>=&{()}"""
        response = self.client.get(reverse('sale-redirect-with-promo', 
            args=[xss_payload, xss_payload]), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('advertiser-registration'))
        self.assertEqual(response.redirect_chain[0][0], target_path)
        self.assertEqual(response.redirect_chain[0][1], 302)
        try:
            self.client.session['promo_code']
            self.fail('XSS in session')
        except KeyError:
            pass  
        try:
            self.client.session['consumer']
            self.fail('XSS in session')
        except KeyError:
            pass
        
    def test_coupon_renewal(self):
        """ Assert that the advertiser and promo code are set in session, and
        the rendered page is preview edit with the coupon_id passed in
        displayed.
        """
        advertiser = Advertiser.objects.get(id=119)
        response = self.client.get(reverse('sale-redirect-with-promo', 
            args=[PAYLOAD_SIGNING.create_payload(email=advertiser.email),
            'test promo', 2, 122]), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('preview-coupon'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(
            self.client.session['consumer']['advertiser']['advertiser_id'], 119) 
        curr_coupon = self.client.session['current_coupon']
        curr_business = self.client.session['current_business']
        curr_offer = self.client.session['current_offer']
        self.assertEqual(self.client.session['consumer']['advertiser']\
            ['business'][curr_business]['offer'][curr_offer]['coupon']\
            [curr_coupon]['coupon_id'], 122)
        self.assertEqual(self.client.session['promo_code'], 'test promo') 
        this_coupon = Coupon.objects.get(id=122)
        self.assertContains(response, this_coupon.offer.headline)
        self.assertContains(response, this_coupon.offer.qualifier)
        self.assertContains(response, this_coupon.custom_restrictions)
    
    def test_coupon_no_promo(self):
        """ Assert that the advertiser is set in session, and the 
        rendered page is preview edit with the coupon_id passed in displayed,
        and there is no promo in session.
        """
        advertiser = Advertiser.objects.get(id=119)
        response = self.client.get(reverse('sale-redirect', 
            args=[PAYLOAD_SIGNING.create_payload(email=advertiser.email), 
            2, 122]), follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        curr_coupon = self.client.session['current_coupon']
        curr_business = self.client.session['current_business']
        curr_offer = self.client.session['current_offer']
        self.assertEqual(self.client.session['consumer']['advertiser']\
            ['business'][curr_business]['offer'][curr_offer]['coupon']\
            [curr_coupon]['coupon_id'], 122)
        self.assertEqual(self.client.session.get('promo_code', None), None) 
        
        
class TestRemoteBounceReport(EnhancedTestCase):
    """ Test cases for remote_bounce_report view. """

    #fixtures = ['test_consumer', 'test_media_partner']
    
    def test_email_found(self):
        """ Assert request with matching email sets is_emailable to False and 
        returns status 0. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        email = consumer.email
        self.assertTrue(consumer.is_emailable)
        response = self.client.get(reverse('report-bouncing', 
            kwargs={'email_string':email, 'nomail_reason':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '0 re: %s bouncing' % email)
        consumer = Consumer.objects.get(email=email)
        self.assertFalse(consumer.is_emailable)

    def test_valid_payload(self):
        """ Assert request with valid signed payload sets is_emailable to False
        and returns status 0. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        email = consumer.email
        self.assertTrue(consumer.is_emailable)
        response = self.client.get(reverse('report-bouncing', 
            kwargs={'email_string':consumer.email_hash, 'nomail_reason':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '0 re: %s bouncing' % email)
        consumer = Consumer.objects.get(email=email)
        self.assertFalse(consumer.is_emailable)
    
    def test_already_bouncing(self):
        """ Assert request for a consumer already marked as bouncing
        returns a status message 1. 
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        email = consumer.email
        consumer.nomail_reason.add(1)
        response = self.client.get(reverse('report-bouncing', 
            kwargs={'email_string':email, 'nomail_reason':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1 re: %s bouncing' % email)
    
    def test_email_not_found(self):
        """ Assert requests with no matching email returns status 2. """
        response = self.client.get(reverse('report-bouncing', 
            kwargs={'email_string':'foo@', 'nomail_reason':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2 re: foo@')
        
    def test_hash_not_found(self):
        """ Assert requests with no matching email returns status 2. """
        response = self.client.get(reverse('report-bouncing', 
            kwargs={'email_string':'foo', 'nomail_reason':1}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2 re: foo')
        
    def test_bad_reason(self):
        """ Assert request with matching email and a bad reason leaves the 
        consumer as emailable.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        email = consumer.email
        consumer = Consumer.objects.get(email=email)
        self.assertTrue(consumer.is_emailable)
        response = self.client.get(reverse('report-bouncing', 
            kwargs={'email_string':email, 'nomail_reason':99}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2 re: %s --bad reason--' % email)
        consumer = Consumer.objects.get(email=email)
        self.assertTrue(consumer.is_emailable)

    def test_spam_complaint_normal_user(self):
        """ Assert request with media partner who reports spam gets a valid 
        response and that an administrtive email is sent.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        email = consumer.email
        self.assertTrue(consumer.is_emailable)
        response = self.client.get(reverse('report-spam', 
            kwargs={'email_string':email, 'nomail_reason':3, 
                    'email_type': 'test_email_type'}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, '0 re: %s blacklist_spam_complaint' % email)
        consumer = Consumer.objects.get(email=email)
        self.assertFalse(consumer.is_emailable)

    def test_spam_complnt_priority_usr(self):
        """ Assert request with media partner who reports spam gets a valid 
        response and that an administrtive email is sent.
        """
        consumer = AD_REP_FACTORY.create_ad_rep()
        # Ad Rep creation creates emails.
        mail.outbox = []
        email = consumer.email
        self.assertTrue(consumer.is_emailable)
        response = self.client.get(reverse('report-spam', 
            kwargs={'email_string':email, 'nomail_reason':3, 
                    'email_type': 'test_email_type'}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(mail.outbox), 1)
        
        self.assertContains(response, '0 re: %s blacklist_spam_complaint' % email)
        consumer = Consumer.objects.get(email=email)
        self.assertFalse(consumer.is_emailable)

class TestResetPasswordFromEmail(EnhancedTestCase):
    """ Test cases for reset_password_from_email email_gateway view. """
    
    fixtures = ['test_advertiser_views', 'test_ad_rep']
    
    def test_email_token_good(self):
        """ Assert requests with matching email token renders the reset 
        password form. 
        """
        token = UniqueUserToken.objects.get(id=111)
        token.is_expired = False
        token.save()
        response = self.client.get(reverse('reset-password-from-email', 
            kwargs={'email_token':token.hashstamp}), follow=True)
        target_path = '%s%s?next=%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('set-password'), reverse('advertiser-account'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        
    def test_email_token_expired(self):
        """ Assert requests with expired token renders the forgot password 
        form. 
        """
        response = self.client.get(reverse('reset-password-from-email', 
            kwargs={'email_token':'19a5599a9a86b848ff72b975f3f93f40e549ec98'}),
            follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('forgot-password'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        
    def test_email_token_not_found(self):
        """ Assert requests with no matching email returns status 2. """
        response = self.client.get(reverse('reset-password-from-email', 
            kwargs={'email_token':'foo'}), follow=True)
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST, 
            reverse('forgot-password'))
        self.assertEqual(response.redirect_chain[0][0], target_path)         
        self.assertEqual(response.redirect_chain[0][1], 302)
        
    def test_email_ad_rep(self):
        """ Assert requests with matching email token of an AdRep redirects to
        firestorm. 
        """
        token = UniqueUserToken.objects.get(id=1001)
        token.is_expired = False
        token.save()
        response = self.client.get(reverse('reset-password-from-email', 
            kwargs={'email_token':token.hashstamp}))
        self.assertEqual(response['location'], '%s%s%s' % (
            'https://my10coupons.com/MemberToolsDotNet/',
            'FirestormAuthenticatedLogin.aspx?DealerID=2&',
            'SecurityToken=TwL981KRSyqdTqLb4eOlqw%3D%3D'))