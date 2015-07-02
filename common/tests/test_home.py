""" Tests for showing different versions of the home page """

from django.core.urlresolvers import reverse

from common.session import create_consumer_in_session
from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY


class TestShowMarketHome(EnhancedTestCase):
    """ Test cases for Market Home. """
    urls = 'urls_local.urls_2'
    
    def test_get_show_home(self):
        """ No consumer in session and is not an ajax request. """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'frm_consumer_registration')
        self.assertContains(response, 'frm_subscriber_registration')
        self.assertContains(response, 
            "input type='hidden' name='csrfmiddlewaretoken'")
        self.assertContains(response, 'input name="email"')
        self.assertContains(response, 'input name="consumer_zip_postal"')
        self.assertContains(response, 'input name="mobile_phone_number"')
        self.assertContains(response, 'input name="subscriber_zip_postal"')
        self.assertContains(response, 'name="carrier"')

    def test_get_home_consumer(self):
        """ Consumer in session and is not an ajax request. """
        consumer = CONSUMER_FACTORY.create_consumer()
        create_consumer_in_session(self, consumer)
        self.assemble_session(self.session)
        response = self.client.get(reverse('home'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEquals(str(response.request['PATH_INFO']), '/hudson-valley/')
        self.assertContains(response, 'frm_consumer_registration')
        self.assertContains(response, 'frm_subscriber_registration')
        self.assertContains(response, consumer.email)
        self.assertContains(response, consumer.consumer_zip_postal)
        
    def test_home_post_con_reg(self):
        """ No consumer in session. Now post the consumer registration form
        with an ajax request with good data.
        """
        post_data = {'ajax_mode': 'consumer_reg', 
            'email': 'will+validconsumer@10coupons.com', 
            'consumer_zip_postal': '10990'}
        response = self.client.post(reverse('home'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 
            '"is_already_registered": true')
        self.assertNotContains(response, 'errors')

    def test_home_post_con_reg_bad(self):
        """ No consumer in session. Now post the consumer registration form
        with an ajax request with bad data.
        """
        post_data = {'ajax_mode': 'consumer_reg', 
            'email': 'NotValidEmail', 
            'consumer_zip_postal': 'ABC'}
        response = self.client.post(reverse('home'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotContains(response, 
            '"is_already_registered": true')
        self.assertContains(response, 
            '"email": ["Enter a valid e-mail address."]')
        self.assertContains(response, 
            '"consumer_zip_postal": ["Please enter a 5 digit zip"]')
        self.assertContains(response, 'errors')
            
    def test_home_post_sub_reg(self):
        """ Consumer in session. Now post the subscriber registration form
        with an ajax request with good data.
        """
        post_data = {'ajax_mode': 'subscriber_reg', 
            'mobile_phone_number': '5555551010', 
            'carrier': '7',
            'subscriber_zip_postal': '10990'}
        response = self.client.post(reverse('home'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 
            '"is_already_registered": true')
        self.assertNotContains(response, 'errors')

    def test_home_post_sub_reg_bad(self):
        """ Consumer in session. Now post the subscriber registration form
        with an ajax request with bad data.
        """
        post_data = {'ajax_mode': 'subscriber_reg', 
            'mobile_phone_number': 'ABCDEFGHIJ', 
            'carrier': '',
            'subscriber_zip_postal': 'ABC'}        
        response = self.client.post(reverse('home'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotContains(response, 
            '"is_already_registered": true')
        self.assertContains(response, 
            '"mobile_phone_number": [" Please enter the 10 digit number of your cell phone"]')
        self.assertContains(response, 
            '"subscriber_zip_postal": ["Please enter a 5 digit zip"]')        
        self.assertContains(response, 
            '"carrier": ["Select your cell phone service provider"]')
        self.assertContains(response, 'errors')