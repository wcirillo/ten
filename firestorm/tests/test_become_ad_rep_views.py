""" Test cases for views regarding becoming an ad rep, for firestorm app.
"""
import logging

from django.core import mail
from django.core.urlresolvers import reverse

from consumer.factories.consumer_factory import CONSUMER_FACTORY
from common.test_utils import EnhancedTestCase
from common.session import create_consumer_in_session
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.factories.ad_rep_lead_factory import AD_REP_LEAD_FACTORY
from firestorm.models import AdRepConsumer, AdRepLead

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestBecomeAdRepPitch(EnhancedTestCase):
    """ Tests case for generating ad rep leads from Become-An-Ad-Rep form. """
    urls = 'urls_local.urls_2'

    fixtures = ['test_sales_rep']

    def common_asserts(self, response):
        """ Assert common functionality for static ad rep pages. """
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.request['PATH_INFO'].endswith(
            '/become-a-sales-rep/'))
        self.assertTemplateUsed(response,
            'marketing_resources/display_become_an_ad_rep.html')

    def test_become_an_ad_rep(self):
        """ Assert ad rep pitch renders correctly. """
        response = self.client.get(reverse('show-ad-rep-form'))
        self.common_asserts(response)
        self.assertContains(response, 'The 10HudsonValleyCoupons.com Team')
        self.assertTemplateUsed(response, 'include/frm/frm_ad_rep_lead.html')
        self.assertContains(response, 'id_email')
        self.assertContains(response, 'id_primary_phone_number')
        self.assertContains(response, 'id_first_name')
        self.assertContains(response, 'id_last_name')
        self.assertContains(response, 'id_consumer_zip_postal')
        self.assertContains(response, 'id_right_person_text')
        self.assertTemplateUsed(response, 'include/frm/frm_ad_rep_lead.html')
        self.assertContains(response,
            'Become an Independent Advertising Representative')
        # When no session, assert terms-of-use mentioned.
        self.assertContains(response, 'Accept our <a href')

    def test_become_ad_rep_with_lead(self):
        """ Assert become ad rep with question qualified ad rep lead in session
        gets redirected to firestorm enrollment form. """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        ad_rep_lead.right_person_text = 'a'
        ad_rep_lead.save()
        create_consumer_in_session(self, ad_rep_lead.consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('show-ad-rep-form'), follow=True)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
       
    def test_post_lead_invalid_data(self):
        """ Assert ad rep lead post with invalid data returns form with error. 
        """
        response = self.client.post(reverse('show-ad-rep-form'), {'test': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/become-a-sales-rep/')
        self.assertContains(response, ' Please enter a valid email')

    def test_post_lead_bad_email(self):
        """ Assert ad rep lead post with invalid email returns error. """
        response = self.client.post(reverse('show-ad-rep-form'), {'email': 1,
            'consumer_zip_postal': 12550})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/become-a-sales-rep/')
        self.assertContains(response, 'Enter a valid e-mail address.')

    def test_post_lead_bad_phone(self):
        """ Assert ad rep lead post with bad formatted phone returns error. """
        response = self.client.post(reverse('show-ad-rep-form'),
            {'primary_phone_number': 1,
            'email': 'testadreplead@10coupons.com',
            'consumer_zip_postal': 12431, 
            'right_person_text': 'test'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/become-a-sales-rep/')
        self.assertContains(response, 'Please enter a 10 digit phone number')

    def test_post_lead_bad_zip(self):
        """ Assert ad rep lead post without session returns error. """
        response = self.client.post(reverse('show-ad-rep-form'),
            {'primary_phone_number': 1,
            'email': 'testadreplead@10coupons.com',
            'consumer_zip_postal': '',
            'right_person_text': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/become-a-sales-rep/')
        self.assertContains(response, 'Please enter a 5 digit zip')

    def test_update_lead(self):
        """ Assert existing lead will be updated with the new info. """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        primary_phone_number = '8455551019'
        first_name = 'Jim'
        last_name = 'Buffet'
        ad_rep1, ad_rep2 = AD_REP_FACTORY.create_ad_reps(create_count=2)
        ad_rep_lead.ad_rep = ad_rep1
        ad_rep_lead.save()
        self.add_ad_rep_to_session(ad_rep2)
        mail_prior = len(mail.outbox)
        response = self.client.post(reverse('show-ad-rep-form'),
            {'primary_phone_number': primary_phone_number,
            'email': ad_rep_lead.email.title(),
            'first_name': first_name, 'last_name': last_name,
            'consumer_zip_postal': '12525',
            'right_person_text': 'test'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
        self.assertContains(response, '%s%s' % (
            'We need more information ', 'to review your application'))
        self.assertContains(response, 'Provide a short paragraph or if you like')
        with self.assertRaises(AdRepLead.DoesNotExist):
            AdRepLead.objects.get(email=ad_rep_lead.email.title())
            # This consumer email should have been lower cased!'
        lead = AdRepLead.objects.get(id=ad_rep_lead.id)
        self.assertEqual(lead.email_subscription.count(), 3)
        self.assertEqual(lead.first_name, first_name)
        self.assertEqual(lead.last_name, last_name)
        self.assertEqual(lead.primary_phone_number, primary_phone_number)
        self.assertEqual(lead.ad_rep.id, ad_rep2.id)
        self.assertEqual(lead.consumer_zip_postal, '12525')
        self.assertEqual(lead.right_person_text, 'test')
        self.assertEqual(AdRepConsumer.objects.filter(
            consumer__email=ad_rep_lead.email).count(), 1)
        # Welcome email is not sent.
        self.assertEqual(len(mail.outbox), mail_prior)
    
    def test_new_lead_session(self):
        """ Assert ad rep lead form submit with existing consumer in session,
        adds lead to session.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        self.login(email=consumer.email)
        self.assemble_session(self.session)
        response = self.client.post(reverse('show-ad-rep-form'),
            {'primary_phone_number': '8455551020',
            'email': 'new' + consumer.email, 
            'consumer_zip_postal': 12601,
            'right_person_text': 'test'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
        #self.assertContains(response, 'new' + consumer.email)

    def test_create_new_lead(self):
        """ Assert new lead gets created. """
        primary_phone_number = '8455551020'
        email = 'Ad_Rep_lead2@example.com'
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(ad_rep)
        response = self.client.post(reverse('show-ad-rep-form'),
            {'primary_phone_number': primary_phone_number,
            'email': email, 'consumer_zip_postal': 12601,
            'right_person_text': 'test'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
        try:
            AdRepLead.objects.get(email = 'Ad_Rep_lead2@example.com')
            self.fail('This consumer email should have been lower cased!')
        except AdRepLead.DoesNotExist:
            pass
        lead = AdRepLead.objects.get(email = 'ad_rep_lead2@example.com')
        for subscription in [(1,), (5,), (6,)]: #format in values_list
            # Assert adreplead, email & ad rep meeting subscriptions exist.
            self.assertTrue(subscription in
                lead.email_subscription.values_list('id'))

    def test_update_lead_w_blanks(self):
        """ Assert existing lead will not be updated with NULLS and blanks. """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        primary_phone_number = first_name = last_name = ''
        response = self.client.post(reverse('show-ad-rep-form'),
            {'primary_phone_number': primary_phone_number,
            'email': ad_rep_lead.email,
            'consumer_zip_postal': '12551',
            'first_name': first_name, 'last_name': last_name,
            'right_person_text': 'test'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
        lead = AdRepLead.objects.get(id=ad_rep_lead.id)
        self.assertEqual(lead.first_name, ad_rep_lead.first_name)
        self.assertEqual(lead.last_name, ad_rep_lead.last_name)
        self.assertEqual(lead.primary_phone_number, 
            ad_rep_lead.primary_phone_number)

    def test_convert_consumer_to_lead(self):
        """ Asserts creating a lead from an existing consumer is successful. """
        consumer = CONSUMER_FACTORY.create_consumer()
        response = self.client.post(reverse('show-ad-rep-form'),
            {'primary_phone_number': '8455551212',
            'email': consumer.email,
            'first_name': consumer.first_name, 'last_name': consumer.last_name,
            'consumer_zip_postal': 12543,
            'right_person_text': 'test'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
        lead = consumer.adreplead
        self.assertEqual(lead.first_name, consumer.first_name)
        self.assertEqual(lead.last_name, consumer.last_name)
        self.assertEqual(lead.primary_phone_number, '8455551212')
        self.assertEqual(lead.ad_rep, None)
        for subscription in [(5,), (6,)]: #format in values_list
            # Assert adreplead and ad rep meeting reminder subscriptions exist.
            self.assertTrue(subscription in
                lead.email_subscription.values_list('id'))

    def test_initialized_form(self):
        """ Test show become an ad rep with a consumer in session to determine
        if the form is initialized properly.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        consumer.first_name = 'Angelo'
        consumer.last_name = 'Montiago'
        consumer.save()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('show-ad-rep-form'))
        self.assertTemplateUsed(response, 'include/frm/frm_ad_rep_lead.html')
        self.assertContains(response,
            'id="id_first_name" value="%s"' % consumer.first_name)
        self.assertContains(response,
            'id="id_last_name" value="%s"' % consumer.last_name)
        self.assertContains(response,
            'id="id_email" value="%s"' % consumer.email)
        self.assertContains(response,
            'id="id_consumer_zip_postal" value="%s"' % 
                consumer.consumer_zip_postal)
        self.assertContains(response, 'id="id_consumer_zip_postal" value="%s"' %
            consumer.consumer_zip_postal)

    def test_post_lead_is_ad_rep(self):
        """ Assert ad rep lead that is an ad rep will abort lead post process
        and load next page.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        mail.outbox = []
        response = self.client.post(reverse('show-ad-rep-form'),
            {'email': ad_rep.email,
             'consumer_zip_postal': '12601',
             'right_person_text': 'test test'}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/become-a-sales-rep/')
        # Assert no# emails from ad rep lead notify/welcome tasks.
        self.assertEqual(len(mail.outbox), 0)
        self.assertContains(response, '%s%s' % (ad_rep.first_name,
            ', your \n            Virtual Office has been activated'))


class TestBecomeAdRepGeneric(EnhancedTestCase):
    """ Tests cases for generating ad rep leads from Become-An-Ad-Rep form on
    site one. """
    fixtures = ['test_geolocation']

    def test_create_lead_site_1(self):
        """ Assert new lead gets created on site closest to zip entered. """
        email = 'Ad_Rep_lead2@example.com'
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.add_ad_rep_to_session(ad_rep)
        response = self.client.post(reverse('show-ad-rep-form'),
            {'first_name': 'Irvil', 'last_name': 'Murf',
             'email': email, 'consumer_zip_postal': 12601,
             'right_person_text': 'test'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
        lead = AdRepLead.objects.get(email = 'ad_rep_lead2@example.com')
        self.assertTrue(lead.first_name, 'Irvil')
        self.assertTrue(lead.last_name, 'Murf')
        self.assertTrue(lead.site.id, 2)
        self.assertTrue(lead.email_subscription.all(), [1])

class TestApplyReview(EnhancedTestCase):
    """ Tests for the review of ad rep lead question. """
    urls = 'urls_local.urls_2'
    
    def test_display_apply_review(self):
        """ Assert page displays for ad rep lead in session. """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        create_consumer_in_session(self, ad_rep_lead.consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('show-apply-review'))
        self.assertTrue(response.request['PATH_INFO'].endswith(
            '/apply-review/'))
        # right person text = ''
        self.assertTemplateUsed(response,
            'marketing_resources/display_apply_review.html')
        self.assertTemplateUsed(response, 
            'include/frm/frm_ad_rep_question_form.html')
        
    def test_apply_review_good(self):
        """ Assert apply review does not show form when ad rep lead has valid
        right person text. """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        ad_rep_lead.right_person_text = '12345'
        ad_rep_lead.save()
        create_consumer_in_session(self, ad_rep_lead.consumer)
        response = self.client.get(reverse('show-apply-review'))
        self.assertTrue(response.request['PATH_INFO'].endswith(
            '/apply-review/'))
        self.assertTemplateNotUsed(response,
            'marketing_resources/display_apply_review.html')
    
    def test_apply_review_save(self):
        """ Assert apply review saves the right person text to the ad rep lead. 
        """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        create_consumer_in_session(self, ad_rep_lead.consumer)
        self.login(email=ad_rep_lead.email)
        self.assemble_session(self.session)
        response = self.client.post(reverse('show-apply-review'),
            {'right_person_text': 'test123'}, follow=True)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/apply-review/')
        lead = AdRepLead.objects.get(id=ad_rep_lead.id)
        self.assertEqual(lead.right_person_text, 'test123')
    
    def test_apply_review_redirect(self):
        """ Assert consumer in session gets redirected from trying to view
        apply review page.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('show-apply-review'), follow=True)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/become-a-sales-rep/')
