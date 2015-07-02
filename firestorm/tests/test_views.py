""" Tests for views of firestorm app of project ten. """
# -*- coding: iso-8859-15 -*-
from BeautifulSoup import BeautifulSoup
import logging

from django.core import mail
from django.core.urlresolvers import NoReverseMatch, reverse, set_urlconf
from django.http import Http404
from django.test.client import RequestFactory

from advertiser.models import Advertiser
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from common.custom_format_for_display import format_phone
from common.test_utils import EnhancedTestCase
from common.session import create_consumer_in_session
from common.service.payload_signing import PAYLOAD_SIGNING
from firestorm.connector import FirestormConnector
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.factories.ad_rep_lead_factory import AD_REP_LEAD_FACTORY
from firestorm.models import (AdRepConsumer, AdRep, AdRepLead, AdRepWebGreeting)
from firestorm.views.views import (ad_rep_home, redirect_for_ad_rep,
    show_ad_rep_menu, show_offer_to_enroll, show_quick_start_assistance)
from firestorm.tests.test_tasks import MockSoap

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class MockConnector(FirestormConnector):
    """ A mock version of the firestorm connector. """
    def get_replicated_website_details(self, ad_rep_url):
        ad_rep_details = ['Error Occurred: foo',]
        if ad_rep_url == 'joeshmoe':
            ad_rep_details = ['Success', '1', 'Joe', 'Shmoe', 'Test Co',
                '5551234567','5555553212',
                'ad-rep-joe-shmoe@example.com',
                'Hello this is my web greeting.', 'CUSTOMER']
        elif ad_rep_url == 'jenkins_test1001':
            ad_rep_details = ['Success', '1', 'Test2', 'Account2', 'JSON2 Inc.',
                '1235551114', '1235551115', 'test-ad-rep2@example.com',
                "Howdy compadre.", '']
        elif ad_rep_url == 'jenkins_test1002':
            ad_rep_details = ['Success', '1', 'Test3', 'Account3',
                'No company.', '1235551114', '1235551115',
                'cust-ad-rep3@example.com', "Hey, what's up yo,", 'CUSTOMER']
        elif ad_rep_url == 'high_ascii_test':
            ad_rep_details = ['Success', '4', 'Test4', 'Account4',
                'Quotes ’R Us &amp; You&rsquo;ll&nbsp;love em',
                '1235551114', '1235551115',
                'cust-ad-rep4@example.com',
                "If this were a “real” &ldquo;web&rdquo;&nbsp;greeting… ",
                'CUSTOMER']
        elif ad_rep_url == 'test_ad_rep_url':
            ad_rep_details = ['Success', '1', 'Mister', 'Mittens', 'M.I.T.',
                '5551234555','5555556555',
                'ad-rep-test-mittens@example.com',
                'Stay warm!.', 'CUSTOMER']
        return ad_rep_details

    @staticmethod
    def call_update_task(ad_rep_dict):
        pass


class TestAdRepHomeActive(EnhancedTestCase):
    """ Tests for the ad_rep_home view when the gargoyle switch 
    'replicated-website' is active.
    """
    fixtures = ['activate_switch_replicated_website']

    def test_customer_ad_rep_url(self):
        """ Assert a valid ad_rep_url serves a page with a 200 response,
        including data for an ad rep, abiding by rules omitting contact info for
        ad reps of rank CUSTOMER.
        """
        connector = MockConnector()
        factory = RequestFactory()
        ad_rep = AD_REP_FACTORY.create_ad_rep(url='joeshmoe')
        ad_rep.rank = 'CUSTOMER'
        ad_rep.save()
        request = factory.get('/hudson-valley/joeshmoe/')
        # WSGIRequest does not have a session.
        request.session = self.client.session
        request.session['ad_rep_id'] = ad_rep.id
        request.META['site_id'] = 2
        response = ad_rep_home(request, 'joeshmoe', connector)
        LOG.debug(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Advertising Rep')
        self.assertContains(response, '%s %s' % (ad_rep.first_name,
            ad_rep.last_name))
        self.assertContains(response, ad_rep.company)
        self.assertNotContains(response,
            format_phone(ad_rep.primary_phone_number))
        self.assertNotContains(response,
            format_phone(ad_rep.home_phone_number))
        self.assertNotContains(response, 'Advertising Representative</em')
        self.assertContains(response, ad_rep.email)
        self.assertContains(response, 'frm_consumer_registration')
        self.assertContains(response, 'frm_subscriber_registration')
        self.assertContains(response, 'input name="email"')
        self.assertContains(response, 'input name="consumer_zip_postal"')
        self.assertContains(response, 'input name="mobile_phone_number"')
        self.assertContains(response, 'input name="subscriber_zip_postal"')
        self.assertContains(response, 'name="carrier"')

    def test_normal_ad_rep_url(self):
        """ Assert a valid ad_rep_url serves a page with a 200 response,
        including data for a non-CUSTOMER ranked ad rep, will include contact
        phone number and title.
        """
        connector = MockConnector()
        factory = RequestFactory()
        ad_rep = AD_REP_FACTORY.create_ad_rep(url='jenkins_test1001')
        AdRepWebGreeting.objects.create(ad_rep=ad_rep, web_greeting='xxx999')
        request = factory.get('/hudson-valley/jenkins_test1001/')
        # WSGIRequest does not have a session.
        request.session = self.client.session
        request.session['ad_rep_id'] = ad_rep.id
        request.META['site_id'] = 2
        response = ad_rep_home(request, 'jenkins_test1001', connector)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Advertising Representative</em')
        self.assertContains(response, '%s %s' % (ad_rep.first_name,
            ad_rep.last_name))
        self.assertContains(response, ad_rep.company)
        self.assertContains(response,
            format_phone(ad_rep.primary_phone_number))
        self.assertContains(response, format_phone(ad_rep.home_phone_number))
        self.assertContains(response, ad_rep.email)
        self.assertContains(response, ad_rep.ad_rep_web_greeting.web_greeting)

    def test_error_response(self):
        """ Assert a well-formed ad_rep_url that does not match an existing ad
        rep with return a 404. Uses a mock connector.
        """
        connector = MockConnector()
        factory = RequestFactory()
        request = factory.get(reverse('ad-rep-home', args=['error']))
        try:
            ad_rep_home(request, 'error', connector)
            self.fail('Error message not handled.')
        except Http404:
            pass

    def test_invalid_ad_rep_url(self):
        """ Assert an ad_rep_url with invalid chars throws a NoReverseMatch. """
        try:
            self.client.get(reverse('ad-rep-home', args=['name$is+invalid.']))
            self.fail('Invalid ad_rep_url accepted.')
        except NoReverseMatch:
            pass

    def test_high_ascii(self):
        """ Assert character entities are preserved in company and web greeting.
        """
        connector = MockConnector()
        factory = RequestFactory()
        ad_rep = AD_REP_FACTORY.create_ad_rep(url='high_ascii_test')
        ad_rep.company = 'Quotes ’R Us &amp; You&rsquo;ll&nbsp;love em'
        ad_rep.save()
        AdRepWebGreeting.objects.create(ad_rep=ad_rep,
            web_greeting=
                "If this were a “real” &ldquo;web&rdquo;&nbsp;greeting… ")
        request = factory.get('/hudson-valley/high_ascii_test/')
        # WSGIRequest does not have a session.
        request.session = self.client.session
        request.session['ad_rep_id'] = ad_rep.id
        request.META['site_id'] = 2
        response = ad_rep_home(request, 'high_ascii_test', connector)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You&rsquo;ll&nbsp;love em')
        self.assertContains(response, '&ldquo;web&rdquo;&nbsp;')

    def test_unicode_url(self):
        """ Assert a Unicode ad_rep_url returns a 404. """
        # This is Cantonese for barbecued pork. Yum!
        response = self.client.get(reverse('ad-rep-home',
            args=['チャーシュー']))
        self.assertEqual(response.status_code, 404)

    def test_ad_rep_url_does_not_exist(self):
        """ Assert a well-formed ad_rep_url that does not match an existing ad
        rep will return a 404. This test does not use a mock connector.
        """
        response = self.client.get(reverse('ad-rep-home',
            args=['IfAnAdRepPicksThisUrlHeOrSheIsCrazy']))
        self.assertEqual(response.status_code, 404)

    def test_connector_invalid_url(self):
        """ Assert get_replicated_website_details for non-matching url."""
        connector = FirestormConnector()
        repl_website_details = connector.get_replicated_website_details('foo')
        self.assertEqual(repl_website_details, ['Not Found', ''])


class TestRedirectForAdRep(EnhancedTestCase):
    """ Test case for view redirect_for_ad_rep. """
    fixtures = ['activate_switch_replicated_website']

    def test_404(self):
        """ Assert when ad rep is not at end of url, 404 is returned. """
        response = self.client.get(reverse('redirect-for-ad-rep', 
            kwargs={'redirect_string': "%s" %  
                'contact-us/my_ad_rep_url_never_used'}), follow=True)
        self.assertEqual(response.request['PATH_INFO'],
            '/join-me/contact-us/my_ad_rep_url_never_used/')
        self.assertEqual(response.status_code, 404)

    def test_good_redirect(self):
        """ Assert redirect and referring ad rep. """
        connector = MockConnector()
        factory = RequestFactory()
        ad_rep = AD_REP_FACTORY.create_ad_rep(url='joeshmoe')
        redirect_string = 'coupons/derma-laser-center-inc/3460/joeshmoe'
        request = factory.get(redirect_string)
        # WSGIRequest does not have a session.
        request.session = self.client.session
        request.session['ad_rep_id'] = ad_rep.id
        request.META['site_id'] = 2
        response = redirect_for_ad_rep(request, redirect_string, connector)
        self.assertEqual(response.status_code, 302)
        LOG.debug('response: %s' % response.__dict__)
        self.assertEqual(response['location'],
            '/hudson-valley/coupons/derma-laser-center-inc/3460/')
        self.assertEqual(request.session['ad_rep_id'], ad_rep.id)

    def test_redirect_site_1(self):
        """ Assert redirect and referring ad rep for a url on site 1. """
        connector = MockConnector()
        factory = RequestFactory()
        ad_rep = AD_REP_FACTORY.create_ad_rep(url='joeshmoe')
        redirect_string = 'about-us/joeshmoe'
        request = factory.get(redirect_string)
        # WSGIRequest does not have a session.
        request.session = self.client.session
        request.session['ad_rep_id'] = ad_rep.id
        request.META['site_id'] = 1
        response = redirect_for_ad_rep(request, redirect_string, connector)
        self.assertEqual(response.status_code, 302)
        LOG.debug('response: %s' % response.__dict__)
        self.assertEqual(response['location'],
            '/about-us/')
        self.assertEqual(request.session['ad_rep_id'], ad_rep.id)


class TestStaticAdRepViews(EnhancedTestCase):
    """ Test case for static views of firestorm app. """
    urls = 'urls_local.urls_2'

    def common_asserts(self, response):
        """ Assert common functionality for static ad rep pages. """
        self.assertEqual(response.status_code, 200)

    def assert_good_enrollment_link(self, response):
        """ Assert good enrollment link. """
        self.assertContains(response, reverse('become-an-ad-rep'))

    def test_benefits_for_business(self):
        """ Assert show_benefits_for_business loads. """
        response = self.client.get(reverse('benefits-for-business'))
        self.common_asserts(response)

    def test_our_competition(self):
        """ Assert show_our_competition loads. """
        response = self.client.get(reverse('our-competition'))
        self.common_asserts(response)

    def test_10localcoupons_story(self):
        """ Assert show_the_10localcoupons_story loads with secure link. """
        response = self.client.get(reverse('the-10localcoupons-story'))
        self.common_asserts(response)
        self.assert_good_enrollment_link(response)

    def test_show_your_opportunity(self):
        """ Assert show_your_opportunity loads with secure link. """
        response = self.client.get(reverse('your-opportunity'))
        self.common_asserts(response)
        self.assert_good_enrollment_link(response)

    def test_compensation_plan(self):
        """ Assert show_compensation_plan loads. """
        response = self.client.get(reverse('compensation-plan'))
        self.common_asserts(response)

    def test_terms_of_agreement(self):
        """ Assert show_terms_of_agreement loads. """
        response = self.client.get(reverse('terms-of-agreement'))
        self.common_asserts(response)

    def test_policies_procedures(self):
        """ Assert show_policies_procedures loads. """
        response = self.client.get(reverse('policies-procedures'))
        self.common_asserts(response)

    def test_compensation_overview(self):
        """ Assert show_compensation_overview loads. """
        response = self.client.get(reverse('compensation-overview'))
        self.common_asserts(response)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/marketing-resources/compensation-overview/')
        self.assertTemplateUsed(response, 
            'include/dsp/dsp_testimonial_ad_rep.html')
        self.assert_good_enrollment_link(response)

    def test_comp_overview_w_ad_rep(self):
        """ Assert when ad rep in session, compensation overview enrollment
        link has dealer ID in URL. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        response = self.client.get(reverse('compensation-overview'))
        self.common_asserts(response)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/marketing-resources/compensation-overview/')
        self.assert_good_enrollment_link(response)


class TestContextProcessors(EnhancedTestCase):
    """ Test case for the default context processor firestorm_ad_rep. """
    fixtures = ['activate_switch_replicated_website']

    def test_ad_rep_consumer_session(self):
        """ Assert when the user views a page other than ad_rep_home and has a
        user in session that is a consumer of an ad_rep but does not have a
        referring_ad_rep in session, the correct ad rep data is displayed.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        AdRepWebGreeting.objects.create(ad_rep=ad_rep,
            web_greeting='test_ad_rep_consumer_session')
        consumer = CONSUMER_FACTORY.create_consumer()
        AdRepConsumer.objects.create(ad_rep=ad_rep, consumer=consumer)
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('contact-us'))
        self.assertContains(response,
            '%s %s' % (ad_rep.first_name, ad_rep.last_name))
        self.assertContains(response, ad_rep.company)
        self.assertContains(response, format_phone(ad_rep.home_phone_number))
        self.assertContains(response, format_phone(ad_rep.primary_phone_number))
        self.assertContains(response, ad_rep.email)
        self.assertContains(response, 'test_ad_rep_consumer_session')
        self.assertNumQueries(1)


class TestAdRepEnrollment(EnhancedTestCase):
    """ Test Firestorm AdRep enrollment, final form. """
    fixtures = ['activate_switch_replicated_website']
    urls = 'urls_local.urls_2'
    
    def prep_test(self, instance_type='lead', payload=False, session=False):
        """ Prep session for testing. """
        if instance_type == 'lead':
            consumer_instance = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        elif instance_type == 'consumer':
            consumer_instance = CONSUMER_FACTORY.create_consumer()
        else: # AdRep.
            consumer_instance = AD_REP_FACTORY.create_ad_rep()
        if payload:
            payload = PAYLOAD_SIGNING.create_payload(
                email=consumer_instance.email)
        if session:
            create_consumer_in_session(self, consumer_instance)
            self.assemble_session(self.session)
        return consumer_instance, payload
    
    def assert_test_get(self, response):
        """ Make common assertions for GET request of enrollment-offer. """
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'firestorm/display_enrollment_offer.html')
        self.assertTemplateUsed(response, 'include/frm/frm_enroll_ad_rep.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_live_help.html')
        self.assertContains(response, 'Terms of Agreement')
        self.assertContains(response, 'Compensation Plan')
        self.assertContains(response, 'Welcome')
        self.assertContains(response, 'our invitation')
        self.assertContains(response, 'Create a web address ')
        self.assertContains(response, 'password1')

    def test_no_payload_no_session(self):
        """ Assert redirect to become-an-ad-rep page. """
        response = self.client.get(reverse('show-offer-to-enroll'), follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(response.redirect_chain[0][0].endswith(
            '/become-a-10coupons-sales-rep/'))
    
    def test_no_session_w_payload(self):
        """ Assert page loads. """
        lead, payload = self.prep_test(
            instance_type='lead', payload=True, session=False)
        response = self.client.get(reverse('show-offer-to-enroll', 
            kwargs={'payload': payload}))
        self.assert_test_get(response)
        self.assertContains(response, 'Welcome %s' % lead.first_name)
    
    def test_consumer_no_payload(self):
        """ Assert consumer in session that is not ad rep lead or ad rep stays
        on page even when no payload exists.
        """
        consumer = self.prep_test(
            instance_type='lead', payload=False, session=True)[0]
        response = self.client.get(reverse('show-offer-to-enroll'))
        self.assert_test_get(response)
        self.assertContains(response, 'Welcome %s' % consumer.first_name)
    
    def test_ad_rep_in_session(self):
        """ Assert if ad rep is in session, no forms render, just a link to 
        sign in.
        """
        ad_rep = self.prep_test(
            instance_type='adrep', payload=False, session=True)[0]
        response = self.client.get(reverse('show-offer-to-enroll'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Congratulations %s' % ad_rep.first_name)
        self.assertContains(response, 'presentative Account has been created.')
        self.assertContains(response, '/hudson-valley/ad-rep/')

    def test_show_lead_forms(self):
        """ Assert that ad rep lead is shown forms. """
        lead = self.prep_test(
            instance_type='lead', payload=False, session=True)[0]
        response = self.client.get(reverse('show-offer-to-enroll'))
        self.assert_test_get(response)
        self.assertContains(response, 'Welcome %s' % lead.first_name)

    def test_post_incomplete(self):
        """ Assert form post with no data renders proper error responses. """
        self.prep_test(instance_type='lead', payload=False, session=True)
        response = self.client.post(reverse('show-offer-to-enroll'),
            {'password1': '', 'password2': '', 'ad_rep_url': ''})
        self.assert_test_get(response)
        self.assertContains(response, 'This field is required')
        self.assertContains(response, 'Please choose a website name')
        self.assertContains(response, 'agree to the three documents listed')

    def test_post_pwd_mismatch(self):
        """ Assert posted form with mismatched passwords renders error. """
        self.prep_test(instance_type='lead', payload=False, session=True)
        response = self.client.post(reverse('show-offer-to-enroll'),
            {'password1': 'abcdef', 'password2': '123456', 'ad_rep_url': 'hi'})
        self.assert_test_get(response)
        self.assertContains(response, "Passwords don&#39;t match.")

    def test_post_unique_url(self):
        """ Assert form post with url already used gives error. """
        existing_ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.prep_test(instance_type='lead', payload=False, session=True)
        response = self.client.post(reverse('show-offer-to-enroll'),
            {'password1': '123456', 'password2': '123456',
            'ad_rep_url': existing_ad_rep.url})
        self.assert_test_get(response)
        self.assertContains(response, "%s" %
            'Sorry! We&#39;re growing fast. That website name is')
        self.assertContains(response, "%s" %
            'already in use. Please choose another')

    def test_post_success(self):
        """ Assert successful post renders sign-in link, creates new ad rep,
        updates password and deletes ad rep lead.
        """
        lead = self.prep_test(
            instance_type='lead', payload=False, session=True)[0]
        email = lead.email
        factory = RequestFactory()
        request = factory.post(reverse('show-offer-to-enroll'),
            {'password1': '123456', 'password2': '123456',
            'ad_rep_url': '10dealstesturl', 'terms_of_use': True})
        create_consumer_in_session(self, lead.consumer)
        request.session = self.session
        request.session = self.add_mock_cycle_key(request)
        self.assertEqual(len(mail.outbox), 0)
        response = show_offer_to_enroll(request, MockSoap())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'presentative Account has been created.')
        self.assertContains(response, '/hudson-valley/ad-rep/')
        # assert enrollment email was sent (cc to NOTIFY_AD_REP_ENROLLED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 
            "Welcome Aboard! Here's some help getting started.")
        email_body_html = mail.outbox[0].alternatives[0][0]
        self.verify_email_sub_list(email_body_html, 4)
        # Assert ad rep lead was converted to an AdRep.
        ad_rep = AdRep.objects.get(email=email)
        self.assertTrue(ad_rep.first_name in email_body_html)
        self.assertTrue(ad_rep.url in email_body_html)
        # make sure this email is different than recommend email
        self.assertTrue('Sign in to your ' in email_body_html)
        self.assertTrue('Use this email address' in email_body_html)
        # Assert ad rep lead no longer exists.
        with self.assertRaises(AdRepLead.DoesNotExist):
            AdRepLead.objects.get(email=email)
        # Assert password was updated.
        self.assertTrue(ad_rep.consumer.has_usable_password())
        self.assertEqual(ad_rep.primary_phone_number, lead.primary_phone_number)
        self.assertEqual(ad_rep.rank, 'ADREP')
        # Assert that ad rep is authenticated in session.
        self.assertTrue(self.session['_auth_user_id'])


class TestAdRepRecommend(EnhancedTestCase):
    """ Test firestorm view for ad rep enrollment when recommended by a 
    referring ad rep. 
    """
    fixtures = ['activate_switch_replicated_website', 'test_sales_rep']
    urls = 'urls_local.urls_2'
    
    def prep_test(self):
        """ Create an ad rep and add to session. """
        self.ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(self.ad_rep)
        # ad rep enrolled email sent
        self.assertEqual(len(mail.outbox), 1)
    
    def assert_test_get(self, response):
        """ Make common assertions for GET request. """
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, 'firestorm/display_recommend_enroll.html')
        self.assertTemplateUsed(response, 
            'include/frm/frm_recommend_ad_rep.html')
        self.assertTemplateUsed(response, 'include/dsp/dsp_live_help.html')

    def test_show_recommend(self):
        """ Assert that a user sees the ad rep enroll form. """
        self.prep_test()
        response = self.client.get(reverse('recommend-enroll'))
        self.assert_test_get(response)
    
    def test_show_initial_data(self):
        """ Assert that ad rep lead consumer initial data is shown in form 
        fields. 
        """
        self.prep_test()
        lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        create_consumer_in_session(self, lead.consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('recommend-enroll'))
        self.assert_test_get(response)
        self.assertContains(response, lead.email)
        self.assertContains(response, lead.first_name)
        self.assertContains(response, lead.last_name)
        self.assertContains(response, lead.consumer_zip_postal)
        self.assertContains(response, lead.primary_phone_number)

    def test_hide_initial_data(self):
        """ Assert that ad rep consumer initial data is not shown in form 
        fields. 
        """
        self.prep_test()
        self.ad_rep.consumer_zip_postal = '10570'
        self.ad_rep.save()
        create_consumer_in_session(self, self.ad_rep.consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('recommend-enroll'))
        self.assert_test_get(response)
        self.assertNotContains(response, self.ad_rep.consumer_zip_postal)
        
    def test_form_tab_index(self):
        """ Assert form tabindex values are sorted sequentially. """
        self.prep_test()
        response = self.client.get(reverse('recommend-enroll'))
        soup = BeautifulSoup(response.content)
        tab_list = []
        for form_input in soup.findAll('input', tabindex=True):
            tab_list.append(int(form_input['tabindex']))
        tab_list_orig = tab_list 
        tab_list.sort()
        self.assertEqual(tab_list_orig, tab_list)

    def test_show_form_errors(self):
        """ Assert that a user sees the ad rep enroll form with errors from
        all forms. 
        """
        self.prep_test()
        response = self.client.post(reverse('recommend-enroll'), {
            'first_name': '', 'last_name': '', 'email': '', 
            'consumer_zip_postal': '1', 'primary_phone_number': '1',
            'password1': '1', 'password2': '1', 'ad_rep_url': '',
            'terms_of_use': False})
        self.assert_test_get(response)
        self.assertContains(response, 'enter a valid email')
        self.assertContains(response, "Passwords must contain at least 6")
        self.assertContains(response, "10 digit phone number")
        self.assertContains(response, "Please choose a website name")
        self.assertContains(response, "agree to the three documents listed")

    def test_post_success(self):
        """ Assert successful post renders sign-in link, creates new ad rep,
        updates password, send enrollment email and deletes ad rep lead.
        """
        self.prep_test()
        mail_count = len(mail.outbox)
        consumer = CONSUMER_FACTORY.create_consumer()
        email = consumer.email
        response = self.client.post(reverse('recommend-enroll'),
            {'first_name': 'first', 'last_name': 'last',
             'email': email, 'consumer_zip_postal': 10570, 
             'primary_phone_number': '1235557890',
             'password1': '123456', 'password2': '123456',
             'ad_rep_url': '10url', 'terms_of_use': True}, 
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/recommend-success/')
        self.assertContains(response, 'Account has been created.')
        self.assertEqual(len(mail.outbox), mail_count + 2)
        self.assertContains(response, '/hudson-valley/sign-in/')
        # Assert enrollment email was sent
        self.assertEqual(mail.outbox[mail_count].subject,
            "Welcome Aboard! Here's some help getting started.")
        email_body_html = mail.outbox[mail_count].alternatives[0][0]
        self.verify_email_sub_list(email_body_html, email_sub_list_id=4)
        # Assert ad rep lead was converted to an AdRep.
        ad_rep = AdRep.objects.get(email=email)
        self.assertTrue(ad_rep.first_name in email_body_html)
        self.assertTrue(ad_rep.url in email_body_html)
        # make sure this email is not the same as enrollment offer email
        self.assertTrue('Activate your ' in email_body_html)
        self.assertTrue('confirm this email address' in email_body_html)
        # Assert ad rep lead no longer exists.
        with self.assertRaises(AdRepLead.DoesNotExist):
            AdRepLead.objects.get(email=email)
        # Assert password was updated.
        self.assertTrue(ad_rep.consumer.has_usable_password())
        self.assertEqual(ad_rep.primary_phone_number, '1235557890')
        self.assertEqual(ad_rep.rank, 'ADREP')
        self.assertEqual(ad_rep.url, '10url')
        self.assertEqual(ad_rep.consumer_zip_postal, '10570')
        self.assertEqual(ad_rep.parent_ad_rep_id, self.ad_rep.id)


class TestAdRepViews(EnhancedTestCase):
    """ Test Firestorm views. """
    fixtures = ['activate_switch_replicated_website']
    
    # Create mock connector and request from RequestFactory() for tests. 
    connector = MockConnector()
    factory = RequestFactory()

    def test_landing_non_advertiser(self):
        """ Assert build-your-network page loads correctly with when 
        non-advertiser is in session.
        """
        request = self.factory.get('/hudson-valley/build-your-network/')
        # WSGIRequest does not have a session.
        request.session = self.client.session
        response = show_ad_rep_menu(request, self.connector)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create Coupons for')
        self.assertContains(response, 'My Own Business')
        self.assertContains(response, 'Another Local Business')

    def test_landing_advertiser(self):
        """ Assert build-your-network page loads correctly with referring ad rep
        advertiser in session (will have advertiser options).
        Urlconf specified in request to mimic action of initial page redirect
        to market (another test, tests the redirect functionality).
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        ad_rep.url = 'test_ad_rep_url'
        ad_rep.save()
        self.login(ad_rep.email)
        request = self.factory.get('/hudson-valley/build-your-network/')
        # Request factory isnt building urls with market, manually set urlconf:
        set_urlconf('urls_local.urls_2')
        request = self.add_session_to_request(request, ad_rep)
        Advertiser.objects.create_advertiser_from_consumer(
            ad_rep.consumer, advertiser_name='James', 
            advertiser_area_code='854', advertiser_exchange='555',
            advertiser_number='1688')
        response = show_ad_rep_menu(request, self.connector)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage Coupons for')
        self.assertContains(response, 'Create Coupons for')
        self.assertContains(response, 'Another Local Business')
        self.assertContains(response, 'href="/hudson-valley/advertiser/"')
        set_urlconf('') # Reset urlconf used in these test cases.

    def test_landing_redirect(self):
        """ Assert build-your-network page reloads on correct site when on site
        1 and user in session belongs to a market).
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        request = self.factory.get('/build-your-network/')
        create_consumer_in_session(self, ad_rep.consumer)
        self.assemble_session(self.session)
        request = self.add_session_to_request(request, ad_rep, site_id=1)
        response = show_ad_rep_menu(request, self.connector)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], 
            '/hudson-valley/build-your-network/')
        
    def test_landing_site_1(self):
        """ Assert build-your-network page loads on site 1 when there is no
        consumer in session.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        ad_rep.url = 'test_ad_rep_url'
        ad_rep.save()
        self.login(ad_rep.email)
        request = self.factory.get('/hudson-valley/build-your-network/')
        request = self.add_session_to_request(request, ad_rep)
        # Remove site_id key.
        request.session['consumer'].pop('site_id')
        Advertiser.objects.create_advertiser_from_consumer(
            ad_rep.consumer, advertiser_name='Birdie',
            advertiser_area_code='854', advertiser_exchange='555',
            advertiser_number='1548')
        response = show_ad_rep_menu(request, self.connector)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Manage Coupons for')
        self.assertContains(response, 'Create Coupons for')
        self.assertContains(response, 'Another Local Business')
        self.assertContains(response, 'href="/advertiser/"')        

    def test_quick_start_assistance(self):
        """ Assert quick start page loads with and without and an ad rep in 
        session from a email payload. """
        request = self.factory.get('/hudson-valley/quick-start/')
        request.session = self.client.session
        response = show_quick_start_assistance(request)
        self.assemble_session(self.session)
        self.assertContains(response, 'Quick Start')
        self.assertContains(response, 'Start here!')
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        payload = PAYLOAD_SIGNING.create_payload(email=ad_rep.email)
        response = show_quick_start_assistance(request, payload)
        self.assertContains(response, 'Quick Start')
        self.assertContains(response, 'Start here!')
        self.assertContains(response, reverse('ad-rep-business-cards'))
        
    def test_show_share_links(self):
        """ Assert ad rep share site links display correctly. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.login(email=ad_rep.email, is_ad_rep=True)
        self.assemble_session(self.session)
        response = self.client.get(reverse('share-links'))
        self.assertContains(response, 
            'Market Coupon Publishing to Local Businesses')
        self.assertContains(response, 
            'Recommend New Advertising Representatives')
        self.assertContains(response, 'number of Customers using')
        self.assertContains(response, 
            'http://10HudsonValleyCoupons.com/join-me/how-it-works/%s/' 
            % ad_rep.url)
        self.assertContains(response, 
            'http://10HudsonValleyCoupons.com/join-me/recommend/%s/' 
            % ad_rep.url)
        self.assertContains(response, 
            'http://10HudsonValleyCoupons.com/%s/' % ad_rep.url)
    
    def test_ad_rep_summary_good(self):
        """ Assert ad rep summary loads data for this ad rep. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.login(email=ad_rep.email, is_ad_rep=True)
        self.assemble_session(self.session)
        ad_rep_recruit = AD_REP_FACTORY.create_ad_rep()
        response = self.client.get(
            "%s%s/" % (reverse('ad-rep-summary'),ad_rep_recruit.id))
        self.assertContains(response, ad_rep_recruit.first_name)
        self.assertContains(response, ad_rep_recruit.email)
        
    def test_ad_rep_summary_404(self):
        """ Assert ad rep summary returns 404 when no ad_rep_id. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.login(email=ad_rep.email, is_ad_rep=True)
        self.assemble_session(self.session)
        response = self.client.get(reverse('ad-rep-summary'))
        self.assertEqual(response.status_code, 404)
        

class TestAdRepSignIn(EnhancedTestCase):
    """ Test iframe version of sign in form display and processing. """
    fixtures = ['activate_switch_firestorm_feeds',
        'activate_switch_replicated_website']

    def build_session(self):
        """ Common function to add Consumer to session. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        create_consumer_in_session(self, ad_rep)
        self.assemble_session(self.session)
        return ad_rep

    def assert_sign_in_page(self, response):
        """ Common asserts when sign in form is rendered. """
        self.assertTemplateUsed(response, 'include/frm/frm_sign_in.html')
        self.assertEqual(response.request['PATH_INFO'], '/sign-in/')
   
    def test_redirect_to_sign_in(self):
        """ Assert when protected view ad-rep-consumers is hit and no session
        is found, they are redirected to sign in and next url var is populated. 
        """
        response = self.client.get(reverse('ad-rep-downline-recruits'), 
            follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assert_sign_in_page(response)
        self.assertEqual(response.request['QUERY_STRING'], 
            'next=%2Fad-rep%2Fdownline-recruits%2F')
    
    def test_sign_in_with_next(self):
        """ Assert that the sign in process will put the ad rep in session and
        then redirect to url var 'next' when firestorm_id matches. 
        """
        ad_rep = self.build_session()
        response = self.client.post('%s?%s' % (reverse('sign-in'),
            'next=/ad-rep/downline-recruits/'),
            {'email': ad_rep.email, 'password': 'password'},
            follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/ad-rep/downline-recruits/')   


class TestVirtualOfficeLink(EnhancedTestCase):
    """ Test case for virtual office links available for Ad Rep's in the header
    area when they are signed in on 10coupons.com.
    """
    fixtures = ['activate_switch_firestorm_feeds',
        'activate_switch_replicated_website']
    
    def test_link_w_no_session(self):
        """ Assert that virtual-office link goes to sign-out when no ad_rep in 
        session.
        """
        response = self.client.get(reverse('firestorm-virtual-office'), 
            follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(response.redirect_chain[0][0].endswith('sign-out/'))
        
    def test_link_w_ad_rep(self):
        """ Assert that virtual-office link goes to sign-in when no ad_rep in 
        session.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.login(email=ad_rep.email, is_ad_rep=True)
        self.assemble_session(self.session)
        response = self.client.get(reverse('firestorm-virtual-office'), 
            follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertTrue(response.redirect_chain[0][0].startswith(
            'https://my10coupons.com/MemberToolsDotNet/'))
