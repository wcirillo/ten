""" Tests for views of consumer app. """

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse

from common.test_utils import EnhancedTestCase
from consumer.models import Consumer
from firestorm.models import AdRep, AdRepConsumer
from market.models import Site

class TestViews(EnhancedTestCase):
    """ Test cases for consumer views. """
    urls = 'urls_local.urls_2'
    
    def test_show_consumer_reg(self):
        """ Assert that the form is displayed. """
        response = self.client.get(reverse('all-coupons'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'frm_consumer_registration')
        self.assertContains(response, 
            "input type='hidden' name='csrfmiddlewaretoken'")
        self.assertContains(response, 'input name="email"')
        self.assertContains(response, 'input name="consumer_zip_postal"')
        
    def test_post_consumer_reg(self):
        """ Assert post to registration form without data redisplays the form
        with correct error text. 
        """
        response = self.client.post(reverse('all-coupons'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 
            'include/frm/frm_consumer_registration.html')
        self.assertContains(response, 'Please enter a valid email.')
        self.assertContains(response, 'Please enter a 5 digit zip')
        
    def test_valid_consumer_reg(self):
        """ Assert posting to registration form on site 1 with valid data and a 
        zip code of site 2 creates a valid consumer and generates an email with 
        the correct verification link. 
        """
        site2 = Site.objects.get(id=2)
        consumer_count = site2.get_or_set_consumer_count()
        email = 'test_valid_consumer_reg@example.com'
        post_data = {'email': email, 'consumer_zip_postal': '12550'}
        response = self.client.post(reverse('all-coupons'), 
            post_data, follow=True)
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('consumer-registration-confirmation')
            ))
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 
            'confirmation message was sent to %s' % email)
        try:
            consumer = Consumer.objects.get(email=email)
        except Consumer.MultipleObjectsReturned:
            self.fail("We created more than one consumer.")
        except Consumer.DoesNotExist:
            self.fail("We did create not a consumer.")
        self.assertEqual(consumer.site.get_or_set_consumer_count(), 
            consumer_count + 1)
        self.assertEqual(consumer.site_id, 2)
        self.assertEqual(mail.outbox[0].subject, 'IMPORTANT - Get your Coupons')
        self.assertEqual(mail.outbox[0].to[0], email)
        self.assertTrue('bounce-consumer_welcome' in mail.outbox[0].from_email)
        self.assertTrue('<a href="%s/hudson-valley/subscribe-consumer/' % 
            (settings.HTTP_PROTOCOL_HOST) in mail.outbox[0].alternatives[0][0])
        # Validate this consumer is subscribed to Flyer.
        self.assertEqual(consumer.email_subscription.values('id')[0]['id'], 1)         

    def test_valid_consumer_reg_cross(self):
        """ Assert posting to registration form on site 3 with valid data and a 
        zip code of site 2 creates a valid consumer and generates an email with 
        the correct verification link.
        """
        email = 'test_valid_consumer_reg_cross@example.com'
        post_data = {'email': email, 'consumer_zip_postal': '12550'}       
        response = self.client.post(reverse('all-coupons',
            urlconf='urls_local.urls_3'), 
            post_data, follow=True)
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('consumer-registration-confirmation')))         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 
            'message was sent to %s' % email)
        self.assertTrue(Consumer.objects.filter(email=email).count(), 1)
        consumer = Consumer.objects.get(email=email)
        self.assertEqual(consumer.site_id, 2)
        self.assertEqual(mail.outbox[0].subject, 
            'IMPORTANT - Get your Coupons')
        self.assertEqual(mail.outbox[0].to[0], email)
        self.assertTrue('bounce-consumer_welcome' in mail.outbox[0].from_email)
        self.assertTrue(
            '<a href="%s/hudson-valley/subscribe-consumer/' % 
            (settings.HTTP_PROTOCOL_HOST) in mail.outbox[0].alternatives[0][0])
            
    def test_repeat_consumer_reg(self):
        """ Post to registration form with existing consumer email. """
        email = 'test_repeat_consumer_reg@example.com'
        consumer = Consumer(email=email, consumer_zip_postal='12550', 
            site_id=2)
        consumer.save()
        # Different zip:
        post_data = {'email': email, 'consumer_zip_postal': '12601'}
        response = self.client.post(reverse('all-coupons'), 
            post_data, follow=True)
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('consumer-registration-confirmation')))         
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertContains(response, 
            'A confirmation message was sent to %s' % email)
        try:
            consumer = Consumer.objects.get(email=email)
        except Consumer.MultipleObjectsReturned:
            self.fail("We created more than one consumer.")
        except Consumer.DoesNotExist:
            self.fail("We did create not a consumer.")
        self.assertEqual(consumer.site_id, 2)   
        
    def test_redirect_consumer_reg(self):
        """ Assert redirect of consumer registration """
        response = self.client.get(reverse('consumer-registration'), 
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/')
        self.assertContains(response, "frm_consumer_registration")

class TestAdRepConsumer(EnhancedTestCase):
    """ Tests for the AdRepConsumer functionality from the firestorm models.
    """
    urls = 'urls_local.urls_2'
    def test_create_consumer_rep(self):
        """ Make sure an AdRepConsumer gets associated with this consumer that
        is registering for the first time.
        """
        ad_rep_email = 'test_consumer_ad_rep@example.com'
        ad_rep = AdRep.objects.create(username=ad_rep_email, email=ad_rep_email,
            firestorm_id=10, url='consumer_ad_rep')
        email = 'test_ad_rep_associate@example.com'
        post_data = {'email': email, 'consumer_zip_postal': '10990'}
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        response = self.client.post(reverse('all-coupons'), 
            post_data, follow=True)
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('consumer-registration-confirmation')
            ))
        consumer = Consumer.objects.get(email=email)
        AdRepConsumer.objects.get(ad_rep=ad_rep, consumer=consumer)
        # Validate this consumer is subscribed to Flyer.
        self.assertEqual(consumer.email_subscription.values('id')[0]['id'], 1)