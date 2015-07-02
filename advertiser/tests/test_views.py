""" Unit tests for views of the advertiser app. """

import datetime

from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.test.client import RequestFactory

from advertiser.factories.business_factory import BUSINESS_FACTORY
from advertiser.models import Advertiser, Business
from common.session import build_advertiser_session, parse_curr_session_keys
from common.test_utils import EnhancedTestCase
from common.utils import generate_guid
from consumer.models import Consumer
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.offer_factory import OFFER_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import (Coupon, CouponAction, CouponType, Offer, Slot, 
    SlotTimeFrame)
from firestorm.models import AdRep, AdRepConsumer, AdRepAdvertiser


class TestAdvertiserViews(EnhancedTestCase):
    """ Test case for advertiser views. """
    
    fixtures = ['test_advertiser_views']
    urls = 'urls_local.urls_2'
    
    def test_show_advertiser_reg_form(self):
        """ Test display of advertiser registration """
        response = self.client.get(reverse('advertiser-registration')) 
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form name="frm_advertiser_registration"')
        self.assertContains(response, "$199/month")

    def test_invalid_advertiser_reg(self):
        """ Test post advertiser registration form without data """
        response = self.client.post(reverse('advertiser-registration'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please supply a Business Name')
        self.assertContains(response, 'Please supply a valid Email Address')

    def test_post_valid_advertiser_reg(self):
        """ Post to registration form with valid data. """
        email = 'test_new_advertiser@company.com'
        business_name = 'My New Business Name'
        post_data = {'business_name': business_name, 'email': email}
        response = self.client.post(
            reverse('advertiser-registration'), post_data, follow=True)
        # Goes to coupon offer page.
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/offer/')
        self.assertContains(response, "$199/month")
    
    def test_post_adv_reg_bad_email(self):
        """ Post to registration form with invalid email. """
        email = 'test_new_advertiser@'
        business_name = 'T'
        post_data = {'business_name': business_name, 'email': email}
        response = self.client.post(
            reverse('advertiser-registration'), post_data, follow=True)
        # Reload create-coupon page with invalid email error displayed.
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/')
        self.assertContains(response, "Enter a valid e-mail address")
        
    def test_post_duped_advertiser_reg(self):
        """ Try to register existing advertiser """
        email = 'test@company.com'
        post_data = {'business_name': 'Test Business Name', 'email': email}
        response = self.client.post(
            reverse('advertiser-registration'), post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Check if 2 advertiser records exist.
        advertiser_count = Advertiser.objects.filter(email=email).count()
        self.assertEqual(advertiser_count, 1)
        
    def test_post_duped_business_reg(self):
        """ Try to register existing advertiser """
        email = 'test@company.com'
        business_name = 'Test Business Name'
        slogan = 'test slogan'
        post_data = {
            'business_name': business_name, 
            'email': email,
            'slogan' : slogan
            }
        response = self.client.post(reverse('advertiser-registration'), 
            post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        # Check if slogan is saved.
        self.assertEqual(Business.objects.get(
            business_name=business_name).slogan, slogan)
        # Check if 2 business records exist.
        business_count = Business.objects.filter(
            business_name=business_name).count()
        self.assertEqual(business_count, 1)
        
    def test_show_advertiser_account(self):
        """ Assert an advertiser with email verified can log in. """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        self.login(advertiser.email)
        response = self.client.get(reverse('advertiser-account'), follow=True)
        self.assertEqual(response.status_code, 200)
        # Next make sure user went to advertiser account.
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/advertiser/')
    
    def test_adv_reg_biz_in_session(self):
        """ Show advertiser registration with a business in session and make
        sure that the advertiser_email, advertiser_name, business_name and
        slogan show on the page.
        """
        business = BUSINESS_FACTORY.create_business()
        build_advertiser_session(self, business.advertiser)
        self.assemble_session(self.session)
        session_dict = parse_curr_session_keys(
            self.client.session, ['this_advertiser'])
        this_business = session_dict['this_advertiser']['business'][0]
        response = self.client.get(reverse('advertiser-registration'),
            follow=True)
        self.assertContains(response, business.advertiser.email)
        self.assertContains(response, business.advertiser.advertiser_name)
        self.assertContains(response, this_business['business_name'])
        self.assertContains(response, business.slogan)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/')

    def test_adv_reg_offer_in_session(self):
        """ Show advertiser registration with an offer in session and make sure
        that the headline and qualifier show on the page.
        """
        offer = OFFER_FACTORY.create_offer()
        build_advertiser_session(self, offer.business.advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('advertiser-registration'), 
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, offer.headline)
        self.assertContains(response, offer.qualifier)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/')

    def test_adv_reg_coupon_in_progress(self):
        """ Show advertiser Registration with a coupon in session that is
        in_progress and no paid coupon. Jump to preview-edit with the headline
        and qualifier populated on the form and the dsp_preview.
        """
        coupon = COUPON_FACTORY.create_coupon()
        coupon.coupon_type_id = 1
        coupon.save()
        build_advertiser_session(self, coupon.offer.business.advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('advertiser-registration'), 
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, coupon.offer.headline)
        self.assertContains(response, coupon.offer.qualifier)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/preview/')

    def test_adv_reg_coupon_paid(self):
        """ Show advertiser Registration with a coupon in session that is paid 
        and no in_progress coupon. Jump to preview-edit with the headline and 
        qualifier blanketed out. 
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('advertiser-registration'), 
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, coupon.offer.headline)
        self.assertNotContains(response, coupon.offer.qualifier)
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/preview/')

    def test_post_adv_reg_save_slogan(self):
        """  Existing advertiser, no offer, test that slogan is saved """
        business = BUSINESS_FACTORY.create_business()
        build_advertiser_session(self, business.advertiser)
        self.assemble_session(self.session)
        post_data = {
            'business_name': business.business_name,
            'email': business.advertiser.email,
            'slogan': 'test slogan' # Different than existing.
            }
        response = self.client.post(reverse('advertiser-registration'), 
            post_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Business.objects.get(id=business.id).slogan,
            'test slogan')

    def test_redirect_site_adv_acct(self):
        """ Assert an advertiser is redirected to his site after sign in."""
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        advertiser.site_id = 3
        advertiser.is_email_verified = True
        advertiser.save()
        response = self.client.get(reverse('advertiser-account'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), '/sign-in/')
        post_data = {'email': advertiser.email, 'password': 'password'}
        response = self.client.post(reverse('sign-in'), post_data, follow=True) 
        self.assertEqual(response.status_code, 200)
        # Next make sure user went to advertiser account on site 2.
        self.assertEqual(response.request['PATH_INFO'], 
            '/triangle/advertiser/')

    def test_show_faq(self):
        """ Test advertiser faq display page. """
        response = self.client.get(reverse('advertiser-faq'))
        self.assertTemplateUsed(response, 
            'advertiser/display_advertiser_faq.html')
        self.assertContains(response, 'Frequently Asked Questions')
        self.assertContains(response, 
            'When are my coupons available to consumers?')
        self.assertContains(response, 'Can I discuss any of this with the CEO?')


class TestAdvertiserViewsNoMarket(EnhancedTestCase):
    """ Test case for advertiser views with no market present. """
    
    def test_create_coupon(self):
        """ Test create coupon displays local (generic) home page when no market
        present (and no zip in session).
        """
        response = self.client.get(reverse('advertiser-registration'))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['location'].endswith('.10coupons.com/'))


def prep_for_reg_parent_redirect(advertiser, headline, qualifier):
    """ Prepare advertiser with active slot for TestRegParentRedirect test.
    """
    offer = Offer.objects.create(business_id=advertiser.businesses.all()[0].id,
        headline=headline,
        qualifier=qualifier)
    future_date = datetime.date.today() + datetime.timedelta(3)
    coupon = Coupon.objects.create(offer_id=offer.id, coupon_type_id=3,
        sms='HoT', expiration_date=future_date)
    slot = Slot.objects.create(site_id=2, business=coupon.offer.business,
        end_date=future_date)
    SlotTimeFrame.objects.create(slot=slot, coupon=coupon)


class TestRegParentRedirect(EnhancedTestCase):
    """ Test case for advertiser views. """
    
    urls = 'urls_local.urls_2'
        
    def test_active_parent_sign_in(self):
        """
        Show advertiser Registration with a coupon in session that is paid, 
        which has and active slot and no in_progress coupon. 
        Advertiser is not authenticated. Redirect to sign-in with the next path
        on the querystring.
        """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        prep_for_reg_parent_redirect(advertiser, 'Captain 3000', 'Home Run')
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('advertiser-registration'), 
            follow=True)
        self.assertEqual(str(response.request['QUERY_STRING']),
            'next=%2Fhudson-valley%2Fcreate-coupon%2F')
        self.assertEqual(str(response.request['PATH_INFO']), reverse('sign-in'))

    def test_active_parent_no_pass(self):
        """
        Show advertiser Registration with a coupon in session that is paid, 
        which has and active slot and no in_progress coupon. 
        Advertiser is not authenticated. Does not have a valid password.
        Redirect to the forgot password form. 
        """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        advertiser.password = '!'
        advertiser.is_email_verified = True
        advertiser.save()
        prep_for_reg_parent_redirect(advertiser, 'Bull Horn', 'Loud and Proud')
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('advertiser-registration'),
            follow=True)
        self.assertEqual(str(response.request['QUERY_STRING']),
            'next=%2Fhudson-valley%2Fcreate-coupon%2F')
        self.assertEqual(str(response.request['PATH_INFO']),
            reverse('forgot-password'))

    def test_authenticated_parent(self):
        """
        Show advertiser Registration with a coupon in session that is paid, 
        which has and active slot and no in_progress coupon. 
        Advertiser is not authenticated. Does not have a valid password.
        Redirect to the forgot password form. 
        """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        prep_for_reg_parent_redirect(advertiser, 'Bull Horn', 'Loud and Proud')
        self.login(advertiser.email)
        response = self.client.get(reverse('advertiser-registration'), 
            follow=True)
        self.assertEqual(str(response.request['PATH_INFO']),
            reverse('preview-coupon'))


class TestAdRepAdvertiser(EnhancedTestCase):
    """
    Tests for the AdRepAdvertiser functionality.
    """
    urls = 'urls_local.urls_2'

    def create_ad_rep_in_session(self):
        """
        Add an ad rep to the test session.

        An ad_rep is expected to have unique values for firestorm_id, url, etc.,
        and those are used to create unique promotion names during the post_save
        of an ad rep. Since we're using a factory pattern here, force unicity of
        the first_name.
        """
        ad_rep1_email = 'test_advertiser_ad_rep1@example.com'
        ad_rep1 = AdRep.objects.create(username=ad_rep1_email,
            email=ad_rep1_email, first_name=generate_guid()[:29],
            firestorm_id=10, url='advertiser_ad_rep1')
        self.session['ad_rep_id'] = ad_rep1.id
        self.assemble_session(self.session)
        return ad_rep1

    def test_create_advertiser_rep(self):
        """ Make sure an AdRepAdvertiser gets associated with this advertiser
        that is registering for the first time.
        """
        ad_rep_email = 'test_consumer_ad_rep@example.com'
        ad_rep = AdRep.objects.create(username=ad_rep_email,
            email=ad_rep_email,
            first_name=generate_guid()[:29],
            firestorm_id=10,
            url='advertiser_ad_rep')
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        email = 'test_ad_rep_associate@example.com'
        post_data = {
            'business_name': 'AdRepAdvertiser Bizz',
            'email': email,
            }
        response = self.client.post(reverse('advertiser-registration'), 
            post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']),
                         reverse('add-offer'))
        advertiser = Advertiser.objects.get(email=email)
        AdRepAdvertiser.objects.get(ad_rep=ad_rep, advertiser=advertiser)
        AdRepConsumer.objects.get(ad_rep=ad_rep,
            consumer=advertiser.consumer)
    
    def test_create_update_ad_rep_adv(self):
        """ Assert existing AdRepAdvertiser is being selected if it exists
        using AdRepAdvertiser create_update_rep manager.
        """
        ad_rep1_email = 'test_advertiser_ad_rep1@example.com'
        ad_rep1 = AdRep.objects.create(username=ad_rep1_email, 
            email=ad_rep1_email, first_name=generate_guid()[:29],
            firestorm_id=10, url='advertiser_ad_rep1')
        self.assemble_session(self.session)
        email = 'test_ad_rep_associate@example.com'
        advertiser = Advertiser.objects.create(username=email, email=email,
            consumer_zip_postal='12550', site_id=2)
        factory = RequestFactory() 
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        ad_rep_advertiser = AdRepAdvertiser(advertiser=advertiser, 
            ad_rep=ad_rep1)
        ad_rep_advertiser.save()
        AdRepConsumer.objects.create_update_rep(request, 
            consumer=advertiser.consumer, ad_rep=ad_rep1)
        try:
            AdRepAdvertiser.objects.create_update_rep(request, advertiser)
            self.assertTrue(True)
        except IntegrityError:
            self.assertTrue(False)
        
    def test_update_advertiser_rep(self):
        """ Make sure a different AdRepAdvertiser gets associated with this 
        advertiser that already had a different AdRepAdvertiser.
        """
        ad_rep1 = self.create_ad_rep_in_session()
        email = 'test_ad_rep_associate@example.com'
        advertiser = Advertiser.objects.create(username=email,
            email=email, consumer_zip_postal='12550', site_id=2)
        factory = RequestFactory() 
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        AdRepAdvertiser.objects.create_update_rep(request, advertiser)
        ad_rep_advertiser = AdRepAdvertiser.objects.get(ad_rep=ad_rep1,
            advertiser=advertiser)
        self.assertEqual(ad_rep_advertiser.ad_rep_id, ad_rep1.id)
        ad_rep2_email = 'test_advertiser_ad_rep2@example.com'
        ad_rep2 = AdRep.objects.create(username=ad_rep2_email,
            email=ad_rep2_email,
            first_name=generate_guid()[:29],
            firestorm_id=11,
            url='advertiser_ad_rep2')
        self.session['ad_rep_id'] = ad_rep2.id
        self.assemble_session(self.session)
        email = 'test_ad_rep_associate@example.com'
        post_data = {
            'business_name': 'AdRepAdvertiser Bizz',
            'email': email,
            }
        response = self.client.post(reverse('advertiser-registration'), 
            post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']),
            reverse('add-offer'))
        ad_rep_advertiser = AdRepAdvertiser.objects.get(ad_rep=ad_rep2,
            advertiser=advertiser)
        self.assertEqual(ad_rep_advertiser.ad_rep_id, ad_rep2.id)
        
    def test_up_adv_rep_not_con_rep(self):
        """ Make sure a different AdRepAdvertiser gets associated with this 
        advertiser that already had an AdRepAdvertiser. Also, make sure the
        AdRepConsumer does not no get updated.
        """        
        ad_rep1 = self.create_ad_rep_in_session()
        email = 'test_ad_rep_associate@example.com'
        factory = RequestFactory()
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        advertiser = Advertiser.objects.create(username=email, email=email,
            consumer_zip_postal='12550', site_id=2)
        AdRepAdvertiser.objects.create_update_rep(request, advertiser)
        ad_rep_consumer = AdRepConsumer.objects.get(ad_rep=ad_rep1,
            consumer=advertiser.consumer)
        self.assertEqual(ad_rep_consumer.ad_rep_id, ad_rep1.id)
        ad_rep_advertiser = AdRepAdvertiser.objects.get(ad_rep=ad_rep1,
            advertiser=advertiser)
        self.assertEqual(ad_rep_advertiser.ad_rep_id, ad_rep1.id)
        ad_rep2_email = 'test_advertiser_ad_rep2@example.com'
        ad_rep2 = AdRep.objects.create(username=ad_rep2_email,
            email=ad_rep2_email, first_name=generate_guid()[:29],
            firestorm_id=11, url='advertiser_ad_rep2')
        self.session['ad_rep_id'] = ad_rep2.id
        self.assemble_session(self.session)
        post_data = {
            'business_name': 'AdRepAdvertiser Bizz',
            'email': email,
            }
        response = self.client.post(reverse('advertiser-registration'), 
            post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']),
            reverse('add-offer'))
        ad_rep_advertiser = AdRepAdvertiser.objects.get(ad_rep=ad_rep2,
            advertiser=advertiser)
        self.assertEqual(ad_rep_advertiser.ad_rep_id, ad_rep2.id)
        ad_rep_consumer = AdRepConsumer.objects.get(ad_rep=ad_rep1,
            consumer=advertiser.consumer)
        self.assertEqual(ad_rep_consumer.ad_rep_id, ad_rep1.id)
        
    def test_no__ses_rep_use_con_rep(self):
        """ No rep in session, check if this user has an AdRepConsumer and 
        use this rep as the AdRepConsumer for this user.
        """
        ad_rep1_email = 'test_consumer_ad_rep1@example.com'
        ad_rep = AdRep.objects.create(username=ad_rep1_email, 
            email=ad_rep1_email, first_name=generate_guid()[:29],
            firestorm_id=10, url='consumer_ad_rep')
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        email = 'test_ad_rep_associate@example.com'
        consumer = Consumer.objects.create(username=email, email=email,
            consumer_zip_postal='12550', site_id=2)
        factory = RequestFactory() 
        request = factory.get('/hudson-valley/', follow=True)
        request.session = self.session
        AdRepConsumer.objects.create_update_rep(request, consumer)
        ad_rep_consumer = AdRepConsumer.objects.get(ad_rep=ad_rep,
            consumer=consumer)
        self.assertEqual(ad_rep_consumer.ad_rep_id, ad_rep.id)
        post_data = {'business_name':'AdRepCreation Biz', 'email': email}
        del request.session['ad_rep_id']
        self.assemble_session(self.session)
        response = self.client.post(reverse('advertiser-registration'), 
            post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']),
            reverse('add-offer'))
        advertiser = Advertiser.objects.get(email=email)
        ad_rep_advertiser = AdRepAdvertiser.objects.get(ad_rep=ad_rep,
             advertiser=advertiser)
        self.assertEqual(ad_rep_advertiser.ad_rep_id, ad_rep.id)
        ad_rep_consumer = AdRepConsumer.objects.get(ad_rep=ad_rep,
            consumer=consumer)
        self.assertEqual(ad_rep_consumer.ad_rep_id, ad_rep.id)


class TestCouponStats(EnhancedTestCase):
    """ Class that contains tests for advertiser views. """
    fixtures = ['test_advertiser', 'test_coupon', 'test_ecommerce', 'test_slot',
        'test_flyer',]
    
    def test_show_coupon_stats(self):
        """ Assert coupon stats page renders with required text. """
        advertiser = Advertiser.objects.get(id=114)
        self.login(advertiser.email)
        response = self.client.get(reverse('coupon-stats'))
        self.assertContains(response, "Stats and Data")
        self.assertContains(response, "Coupon Views")
        self.assertContains(response, "Total Clicks")
        self.assertContains(response, "Total Prints")
        self.assertContains(response, 
            '<option value="0">- View All Businesses -</option>')    
        self.assertContains(response, 'Test14 Biz')

    def test_show_coupon_ajax_all(self):
        """ Assert coupon stats ajax request contains correct data for all 
        businesses of a given advertiser. 
        """
        advertiser = Advertiser.objects.get(id=114)
        # Update one of these coupons that will render to in progress status.
        coupon = Coupon.objects.get(id=301)
        coupon.coupon_type = CouponType.objects.get(id=1)
        coupon.save()
        CouponAction.objects.create(action_id=1, coupon_id=300, count=3)
        CouponAction.objects.create(action_id=2, coupon_id=300, count=2)
        CouponAction.objects.create(action_id=3, coupon_id=300, count=1)
        self.login(advertiser.email)
        post_data = {'business_id': '0'}
        response = self.client.post(reverse('coupon-stats'), post_data)
        self.assertContains(response, 
            '"coupon_url": "/coupon-test14-biz-off-dine/300/"')
        self.assertContains(response, '"edit_coupon_url": "/edit-coupon/300/"')
        self.assertContains(response, '"views": [3]')
        self.assertContains(response, '"clicks": [2]')
        self.assertContains(response, '"prints": [1]')
        self.assertContains(response, '"business_name": "Test14 Biz"')
        self.assertContains(response, 
            '"default_restrictions": "Tax and Gratuity Not Included."')
        self.assertContains(response, 
            '"valid_days": "Offer not valid Thursdays."')
        self.assertContains(response, '"coupon_id": %s' % coupon.id)
    
    def test_show_coupon_ajax_biz(self):
        """ Assert coupon stats ajax request contains correct data for a given 
        business. 
        """
        advertiser = Advertiser.objects.get(id=114)
        CouponAction.objects.create(action_id=1, coupon_id=300, count=10)
        CouponAction.objects.create(action_id=2, coupon_id=300, count=5)
        self.login(advertiser.email)
        post_data = {'business_id': '114'}
        response = self.client.post(reverse('coupon-stats'), post_data)
        self.assertContains(response, 
            '"coupon_url": "/coupon-test14-biz-off-dine/300/"')
        self.assertContains(response, '"edit_coupon_url": "/edit-coupon/300/"')
        self.assertContains(response, '"views": [10]')
        self.assertContains(response, '"clicks": [5]')
        self.assertContains(response, '"prints": [null]')
