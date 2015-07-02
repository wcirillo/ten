"""Coupon Offer Testing"""
import datetime

from django.core.urlresolvers import reverse
from django.http import HttpRequest

from advertiser.factories.advertiser_factory import ADVERTISER_FACTORY
from advertiser.models import Advertiser, Business
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from common.session import build_advertiser_session, create_consumer_in_session
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.offer_factory import OFFER_FACTORY
from coupon.models import Offer
from coupon.service.expiration_date_service import get_default_expiration_date


class TestCreateOffer(EnhancedTestCase):
    """ This class houses test methods for creating a coupon offer. """
    urls = 'urls_local.urls_2'
    
    def test_show_get_new_offer(self):
        """ Assert successful create offer request. """
        advertiser = Advertiser()
        advertiser.email = 'dennis-testCo1@example.com'
        advertiser.advertiser_create_datetime = datetime.datetime.now()
        advertiser.advertiser_modified_datetime = datetime.datetime.now()
        advertiser.consumer_create_datetime = datetime.datetime.now()
        advertiser.consumer_modified_datetime = datetime.datetime.now()
        advertiser.save()
        business = Business()
        business.business_name = 'Dennis Test Co. 1'
        business.slogan = "Mull it over"
        business.advertiser = advertiser
        business.save()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        self.assertEqual(self.session['consumer']['advertiser']['business']\
            [0]['categories'], None)
        response = self.client.get(reverse('add-offer')) 
        self.assertEquals(response.status_code, 200) # Not redirected.
        rendered_html = response.content
        # Page contains email from session.
        self.assertTrue(str(advertiser.email) in rendered_html) 
        # Page contains form with headline.
        self.assertTrue(str('id_headline') in rendered_html) 
        # Page contains form with qualifier.
        self.assertTrue(str('id_qualifier') in rendered_html)
        self.assertContains(response, get_default_expiration_date())
        # Page defaults to select category 7.
        self.assertContains(response, 'value="7" selected=')
        self.assertContains(response,
            'Help customers find you fast by choosing a category.')
        self.assertContains(response, "$199/month")

    def test_show_deny_consumer(self):
        """ Assert offer process with missing advertiser redirects to advertiser
        registration form.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('add-offer'), follow=True)
        self.assertEquals(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/')

    def test_show_no_business(self):
        """ Assert create offer missing list of businesses will redirect to ad
        reg. This scenario causes an IndexError.
        """
        advertiser = Advertiser()
        advertiser.email = 'dennis-testCo4@example.com'
        advertiser.advertiser_create_datetime = datetime.datetime.now()
        advertiser.advertiser_modified_datetime = datetime.datetime.now()
        advertiser.consumer_create_datetime = datetime.datetime.now()
        advertiser.consumer_modified_datetime = datetime.datetime.now()
        advertiser.save()
        business = Business()
        business.business_name = 'Dennis Test Co. 4'
        business.slogan = "Thrice times the charm"
        business.advertiser = advertiser
        business.save()
        build_advertiser_session(self, advertiser)
        self.session['current_business'] = 100 # Cause index error.
        self.assemble_session(self.session)
        response = self.client.get(reverse('add-offer'), follow=True) 
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')

    def test_show_no_coupon(self):
        """ Assert create offer success without coupon offer. """
        advertiser = OFFER_FACTORY.create_offer().business.advertiser
        build_advertiser_session(self, advertiser)
        self.session['current_offer'] = 0
        expiration_date = '10/23/11'
        self.session['expiration_date'] = expiration_date
        self.session['consumer']['advertiser']['business'][0]['offer'][0]\
            ['headline'] = 'Magical Headline'
        self.session['consumer']['advertiser']['business'][0]['offer'][0]\
            ['qualifier'] = 'AbbraKaddabra'
        self.assemble_session(self.session)
        response = self.client.get(reverse('add-offer'))
        self.assertEquals(response.status_code, 200)
        rendered_html = response.content
        # Page contains our headline?
        self.assertTrue(str(self.session['consumer']['advertiser']['business']\
            [0]['offer'][0]['headline']) in rendered_html) 
        # Page contains our qualifier?
        self.assertTrue(str(self.session['consumer']['advertiser']['business']\
            [0]['offer'][0]['qualifier']) in rendered_html)
        self.assertContains(response, expiration_date)
        
    def test_show_no_coupon_index(self):
        """ Assert create offer success without list of offers. """
        business = COUPON_FACTORY.create_coupon().offer.business
        business.categories.add(1)
        build_advertiser_session(self, business.advertiser)
        self.session['consumer']['advertiser']['business'][0]['offer'][0]\
            ['coupon'] = {}# Remove coupon from session.
        self.session['current_offer'] = 0
        self.session['consumer']['advertiser']['business'][0]['offer'][0]\
            ['headline'] = 'Magical Headline 6'
        self.session['consumer']['advertiser']['business'][0]['offer'][0]\
            ['qualifier'] = 'AbbraKaddabra 6'
        self.assemble_session(self.session)
        self.assertEqual(str(self.session['consumer']['advertiser']['business']\
            [0]['categories']), '[1]')
        del self.session['current_coupon'] # Cause KeyError.
        response = self.client.get(reverse('add-offer'))
        self.assertEquals(response.status_code, 200)
        rendered_html = response.content
        # Page contains our business name?
        self.assertTrue(str(self.session['consumer']['advertiser']['business']\
            [0]['business_name']) in rendered_html) 
        self.assertTrue(str(self.session['consumer']['advertiser']['business']\
            [0]['offer'][0]['qualifier']) in rendered_html)

    def test_show_offer_with_coupon_id(self):
        """ Assert create offer success with offer and coupon ID. """
        business = COUPON_FACTORY.create_coupon().offer.business
        business.categories.add(1)
        build_advertiser_session(self, business.advertiser)
        self.session['consumer']['advertiser']['business'][0]['offer'][0]\
            ['headline'] = 'Magical Headline 7'
        self.session['consumer']['advertiser']['business'][0]['offer'][0]\
            ['qualifier'] = 'AbbraKaddabra 7'
        self.assemble_session(self.session)
        response = self.client.get(reverse('add-offer'))
        self.assertEquals(response.status_code, 200) 
        rendered_html = response.content
        # Page contains our business name?
        self.assertTrue(str(self.session['consumer']['advertiser']['business']\
            [0]['business_name']) in rendered_html) 
        self.assertTrue(str(self.session['consumer']['advertiser']['business']\
            [0]['offer'][0]['qualifier']) in rendered_html)
        self.assertContains(response, 'id="id_category" class="selector"')
        self.assertContains(response, 'option value="3">Entertainment')
        self.assertTrue(str("frm_create_offer") in rendered_html)
        self.assertContains(response, 'option value="1" selected')

    def test_process_incomplete_form(self):
        """ Assert create offer with missing form fields causes page reload. """
        advertiser = OFFER_FACTORY.create_offer().business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.post(reverse('add-offer'))
        rendered_html = response.content
        self.assertTrue(str("frm_create_offer") in rendered_html)
        self.assertTrue(str(advertiser.email) in rendered_html)
        # Return to page with form data.
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/offer/')
    
    def test_post_form_no_category(self):
        """ Assert create offer with missing category (should not be possible)
        will force page reload. 
        """
        advertiser = OFFER_FACTORY.create_offer().business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        expiration_date = '10/23/13'
        response = self.client.post(reverse('add-offer'), data={
                "headline":"Test This View 10", 
                "qualifier": "Heads up!",
                'expiration_date':expiration_date},)
        # Return to page with form data.
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/offer/')
        self.assertContains(response, 'Please select a category')
        
    def test_process_no_curr_offer(self):
        """ Assert completed form fields, missing offer redirects to get
        location.
        """
        advertiser = ADVERTISER_FACTORY.create_advertiser()
        advertiser.email = 'process_no_curr_offer0@example.com'
        advertiser.save()
        business = Business()
        business.business_name = 'Test Co. 10'
        business.slogan = "Pretty Pennies"
        business.advertiser = advertiser
        business.save()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        expiration_date = '10/23/11'
        headline = "Test This View 10"
        response = self.client.post(reverse('add-offer'), 
            data={
                "headline": headline,
                "qualifier": "Heads up!",
                'expiration_date': expiration_date,
                'category': 1}, 
            follow=True)
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/add-location/')
        # Check if new offer was saved.
        saved_biz = Business.objects.get(id=business.id)
        self.assertEqual(
            str(saved_biz.categories.values_list('id', flat=True)), '[1]')
        # Check if saved in database successfully.
        self.assertTrue(Offer.objects.filter(headline=headline).count())
        self.assertEquals(response.status_code, 200)
        self.assertEquals(self.client.session['expiration_date'], 
            expiration_date)
        self.assertContains(response, 'Test This View 10')

    def test_process_post_complete(self):
        """ Assert create offer completed form fields redirects to get location.
        """
        advertiser = OFFER_FACTORY.create_offer().business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        expiration_date = '10/23/78'
        response = self.client.post(reverse('add-offer'), 
            data={"headline":'Test This View 9', 'qualifier':'Heads up!',
                  'expiration_date':expiration_date,
                  'category':7},
            follow=True)
        # Check if new offer was saved.
        saved_headline = str(Offer.objects.filter(
                headline = 'Test This View 9'
            )[0].headline)
        # Check if saved in database successfully.
        self.assertEquals(saved_headline, 'Test This View 9') 
        self.assertEquals(response.status_code, 200)
        self.assertContains(response, 'frm_create_location')
        self.assertContains(response, 'Test This View 9')
        self.assertEquals(self.client.session['expiration_date'], 
            expiration_date)
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/add-location/')
        
    def test_process_no_curr_business(self):
        """ Assert completed form fields, missing current business will redirect
        to coupons page.
        """
        advertiser = COUPON_FACTORY.create_coupon().offer.business.advertiser
        build_advertiser_session(self, advertiser)
        # Delete business_id to try to force key error.
        del self.session['current_business']
        self.assemble_session(self.session)
        expiration_date = '10/23/78'
        request = HttpRequest()
        post_data = {"headline": "Test This View 9", "qualifier": "Heads up!",
            'expiration_date': expiration_date, 'category': 2}
        request.session = self.session
        response = self.client.post(reverse('add-offer'), 
            data=post_data,
            follow=True)
        self.assertTrue(response.status_code == 200) 
        self.assertEquals(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/')
