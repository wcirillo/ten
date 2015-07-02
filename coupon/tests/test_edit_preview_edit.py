""" This is a test module for coupon view preview edit when in EDIT mode. """
from copy import deepcopy

from django.core.urlresolvers import reverse
  
from advertiser.models import Advertiser
from coupon.models import Coupon, Offer
from coupon.tests.test_cases import PreviewEditTestCase


class TestEditModePreviewEdit(PreviewEditTestCase):
    """ 
    This class tests the 'EDIT' Mode for PreviewEdit functionality.
    """
    fixtures = ['test_advertiser', 'test_coupon_views']
    
    def test_get_edit_coupon(self):
        """ 
        Test the GET of the edit coupon process. This should result in all
        coupon data filled out, including Offer.headline and Offer.qualifier.
        """
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        response = self.client.get(reverse('edit-coupon', 
            kwargs={'coupon_id':110}), self.post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/edit-coupon/110/')
        self.assertContains(response, "frm_edit_coupon")
        self.assertContains(response, "Preview Edit Headline")
        self.assertContains(response, "Preview Edit Qualifier")
        
    def test_post_no_changes(self):
        """ Assert session and database remain the same for POST this coupon
        with no changes. """
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        original_coupon = Coupon.objects.get(id=110)
        original_offer_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'])
        original_headline = self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['headline']
        original_qualifier = self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['qualifier']
        original_coupon_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][0]['coupon'])
        response = self.client.post(reverse('edit-coupon', 
            kwargs={'coupon_id':110}), self.post_data, follow=True)
        saved_coupon = Coupon.objects.get(id=110)
        saved_offer_count = len(self.client.session['consumer']['advertiser']
            ['business'][0]['offer'])
        saved_headline = self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['headline']
        saved_qualifier = self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['qualifier']
        saved_coupon_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['coupon'])
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
        self.assertEqual(original_coupon, saved_coupon)
        self.assertEqual(original_offer_count, saved_offer_count)
        self.assertEqual(original_headline, saved_headline)
        self.assertEqual(original_qualifier, saved_qualifier)
        self.assertEqual(original_coupon_count, saved_coupon_count)

    def test_post_offer_update(self):
        """ 
        POST this coupon with the offer changed. Old offer should get updated 
        since there is only this PAID coupon associated with this offer.
        """
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        new_headline = '2nd Headline'
        self.post_data['headline'] = new_headline
        original_coupon = Coupon.objects.get(id=110)
        original_offer_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'])
        original_qualifier1 = self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['qualifier']
        original_coupon_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][0]['coupon'])
        response = self.client.post(reverse('edit-coupon', 
            kwargs={'coupon_id':110}), self.post_data, follow=True)
        saved_coupon = Coupon.objects.get(id=110)
        saved_offer_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'])
        saved_headline1 = self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['headline']
        saved_qualifier1 = self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['qualifier']
        saved_coupon_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['coupon'])
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
        self.assertEqual(original_coupon, saved_coupon)
        self.assertEqual(original_offer_count, saved_offer_count)
        self.assertEqual(new_headline, saved_headline1)
        self.assertEqual(original_qualifier1, saved_qualifier1)
        self.assertEqual(original_coupon_count, saved_coupon_count)
      
    def test_post_new_offer(self):
        """ 
        POST this coupon with the offer changed.  Old offer should stay the 
        same. New offer should get created.  Coupon should move from old 
        offer to new offer since the old offer has another published coupon
        associated with it besides the one we are moving.
        """
        Coupon(offer_id=110, coupon_type_id=3, sms='Hello Hello').save()
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)        
        self.setup_post_data(advertiser, location_count=10)
        new_headline = '2nd Headline'
        self.post_data['headline'] = new_headline
        original_coupon = Coupon.objects.get(id=110)
        original_offer_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'])
        original_session = deepcopy(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][0])
        original_coupon_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][0]['coupon'])
        response = self.client.post(reverse('edit-coupon', 
            kwargs={'coupon_id':110}), self.post_data, follow=True)
        saved_coupon = Coupon.objects.get(id=110)
        saved_offer_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'])
        saved_coupon_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['coupon'])
        new_coupon_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][1]['coupon'])
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
        self.assertEqual(original_coupon, saved_coupon)
        self.assertEqual(original_offer_count+1, saved_offer_count)
        self.assertEqual(original_session['headline'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][0]['headline'])
        self.assertEqual(new_headline,
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][1]['headline'])
        self.assertEqual(original_session['qualifier'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][0]['qualifier'])
        self.assertEqual(original_coupon_count-1, saved_coupon_count)
        self.assertEqual(new_coupon_count, 1)
 
    def test_post_existing_offer(self):
        """ 
        POST this coupon with the offer changed.  Old offer should stay the 
        same. New offer should get created.  Coupon should move from old 
        offer to new offer since the old offer has another published coupon
        associated with it besides the one we are moving.
        """
        offer = Offer.objects.create(business_id=10,
            headline='Non matching headline',
            qualifier='Non matching qualifier')
        Coupon.objects.create(offer_id=offer.id, coupon_type_id=3,
            sms='Hello Hello')
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        existing_headline = offer.headline
        existing_qualifier = offer.qualifier
        self.post_data['headline'] = existing_headline
        self.post_data['qualifier'] = existing_qualifier
        original_coupon = Coupon.objects.get(id=110)
        original_session = deepcopy(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'])
        original_offer_count = len(original_session)
        original_coupon2_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][1]['coupon'])
        response = self.client.post(reverse('edit-coupon', 
            kwargs={'coupon_id':110}), self.post_data, follow=True)
        saved_coupon = Coupon.objects.get(id=110)
        saved_offer_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'])
        saved_coupon2_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][1]['coupon'])
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
        self.assertEqual(original_coupon, saved_coupon)
        self.assertEqual(original_offer_count, saved_offer_count)
        self.assertEqual(original_session[0]['headline'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][0]['headline'])
        self.assertEqual(original_session[1]['headline'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][1]['headline'])
        self.assertEqual(original_session[0]['qualifier'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][0]['qualifier'])
        self.assertEqual(original_session[1]['qualifier'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][1]['qualifier'])
        self.assertEqual(original_coupon2_count+1, saved_coupon2_count)
        
    def test_post_lonely_offer(self):
        """ 
        POST this coupon and move the coupon to an offer that is lonely.  A
        lonely offer is one that has no coupon associated with it. So, update
        the lonely offer with the new POSTED offer since the POSTED offer 
        does not exist in session already.  Basically this will harness a record
        that may not have had a chance to be used otherwise.
        """
        Offer.objects.create(business_id=10, headline='Non matching headline',
          qualifier='Non matching qualifier')
        Coupon.objects.create(offer_id=110, coupon_type_id=3,
            sms='Hello Hello')
        original_coupon = Coupon.objects.get(id=110)
        original_coupon.coupon_type_id = 3
        original_coupon.save()
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        non_match_headline = 'Match headline'
        non_match_qualifier = 'Match qualifier'
        self.post_data['headline'] = non_match_headline
        self.post_data['qualifier'] = non_match_qualifier
        original_offer_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'])
        original_session = deepcopy(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][0])
        original_coupon1_count = len(self.client.session['consumer']\
            ['advertiser']['business'][0]['offer'][0]['coupon'])
        original_coupon2_count = 0
        response = self.client.post(reverse('edit-coupon', 
            kwargs={'coupon_id':110}), self.post_data, follow=True)
        saved_coupon = Coupon.objects.get(id=110)
        saved_offer_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'])
        saved_coupon2_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][1]['coupon'])
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
        self.assertEqual(original_coupon, saved_coupon)
        self.assertEqual(original_offer_count, saved_offer_count)
        self.assertEqual(original_session['headline'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][0]['headline'])
        self.assertEqual(non_match_headline,
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][1]['headline'])
        self.assertEqual(original_session['qualifier'],
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][0]['qualifier'])
        self.assertEqual(non_match_qualifier,
            self.client.session['consumer']['advertiser']\
                ['business'][0]['offer'][1]['qualifier'])
        saved_coupon1_count = len(self.client.session['consumer']['advertiser']\
            ['business'][0]['offer'][1]['coupon'])
        self.assertEqual(original_coupon1_count-1, saved_coupon1_count) 
        self.assertEqual(original_coupon2_count+1, saved_coupon2_count) 