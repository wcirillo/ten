""" This is a test module for coupon view testing of business changes. """

from django.core.urlresolvers import reverse

from advertiser.factories.business_factory import BUSINESS_FACTORY
from advertiser.models import Advertiser
from common.session import build_advertiser_session
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.offer_factory import OFFER_FACTORY
from coupon.models import Coupon, CouponType
from coupon.tests.test_cases import PreviewEditTestCase


class TestPreviewEditBusiness(PreviewEditTestCase):
    """ Tests for Business Fields on the Preview Edit form.  Also ensures
    the correct data for this advertisers businesses are updated appropriately
    in the session and the database.
    """
    def test_post_diff_bizz_name(self):
        """ Assert POST with different business_name than session for
        current_business index.  Since none of the coupons have been published,
        the business name can be updated.
        advertiser->business0->offer0->coupon0('In Progress')
        Update business0 and utilize its offer and coupon since it has
        not been published yet.
        """
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=10)
        self.post_data['business_name'] = 'Different Business Name'
        self.post_data['headline'] = 'Different Offer'
        self.post_data['qualifier'] = 'Different Qualifier'
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.common_assertions(response, 'POST')
        self.assert_session_keys_current(
            current_biz=(0, 0), current_offer=(0, 0), current_coupon=(0, 0))
        self.assertNotEqual(self.post_data['business_name'],
            self.session['consumer']['advertiser']['business'][0][
                'business_name'])
        self.assertEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][0][
                'business_name'])
        self.assertNotEqual(self.post_data['headline'], 
            self.session['consumer']['advertiser']['business'][
                0]['offer'][0]['headline'])
        self.assertEqual(self.post_data['headline'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['headline'])
        self.assertNotEqual(self.post_data['qualifier'], 
            self.session['consumer']['advertiser']['business'][
                0]['offer'][0]['qualifier'])
        self.assertEqual(self.post_data['qualifier'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['qualifier'])
        self.assertEqual(1, 
            self.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_type_id'])
        self.assertEqual(1, 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_type_id'])
        new_coupon_id = self.client.session['consumer']['advertiser'][
            'business'][0]['offer'][0]['coupon'][0]['coupon_id']    
        self.assert_new_coupon(new_coupon_id, coupon_id=self.coupon.id,
            coupon_type_id=self.coupon.coupon_type_id, 
            offer_id=self.coupon.offer.id,
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_id=self.coupon.offer.business.id,
            business_name=self.post_data['business_name'])

    def test_diff_bizz_match_session(self):
        """ POST a different Business that has a match in session.
        business_exists_for_advertiser, business_has_offer, 
        business_has_unpublished_offer, business_has_coupon
        advertiser->business0->offer0->coupon0('In Progress')
        advertiser->business1->offer0->coupon0('Paid')
        Find a match for business0 and utilize its offer and coupon since it has
        not been published yet.
        """
        business_name = self.coupon.offer.business.business_name
        slogan = self.coupon.offer.business.slogan
        self.coupon.coupon_type = CouponType.objects.get(id=1)
        self.coupon.save()
        business = BUSINESS_FACTORY.create_business(advertiser=self.advertiser)
        offer = OFFER_FACTORY.create_offer(business=business)
        coupon = COUPON_FACTORY.create_coupon(offer=offer)
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        self.post_data['business_name'] = business_name
        self.post_data['slogan'] = slogan
        self.post_data['headline'] = 'Match This Headline'
        self.post_data['qualifier'] = 'New Offer'
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.assertEqual(response.status_code, 200) 
        advertiser = Advertiser.objects.get(id=self.advertiser.id)
        offer = advertiser.businesses.all().order_by(
            'id')[0].offers.all().order_by('id')[0]
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")
        self.assert_session_keys_current(
            current_biz=(1, 0), current_offer=(0, 0), current_coupon=(0, 0))
        self.assertEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['business_name'])
        self.assertNotEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                1]['business_name'])
        self.assertEqual(self.post_data['headline'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['headline'])
        self.assertNotEqual(self.session['consumer']['advertiser']['business'][
            0]['offer'][0]['headline'], 
                self.client.session['consumer']['advertiser']['business'][
                    0]['offer'][0]['headline'])
        self.assertEqual(self.post_data['qualifier'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['qualifier'])
        self.assertNotEqual(self.session['consumer']['advertiser']['business'][
            0]['offer'][0]['qualifier'], 
                self.client.session['consumer']['advertiser']['business'][
                    0]['offer'][0]['qualifier'])
        self.assertEqual(1, 
            self.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_type_id'])
        self.assertEqual(1, 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_type_id'])
        new_coupon = Coupon.objects.get(
            id=self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_id'])
        self.assertNotEqual(coupon.id, new_coupon.id)
        self.assertNotEqual(coupon.offer.id, new_coupon.offer.id)
        self.assertNotEqual(coupon.offer.business.id,
            new_coupon.offer.business.id)       
        self.assert_new_coupon(new_coupon.id, coupon_id=self.coupon.id,
            coupon_type_id=1, offer_id=self.coupon.offer.id,
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_name=self.post_data['business_name'])

    def test_diff_bizz_no_coupon(self):
        """ POST a different Business that has a match in session.
        business_exists_for_advertiser, business_has_offer, 
        business_has_unpublished_offer, 
        offer_has_coupon_association == FALSE
        advertiser->business0->offer0->(No Coupon for this offer yet)
        advertiser->business1->offer0->coupon0('Paid')
        business0 matches the business posted.  Use that business and its offer,
        then create a new coupon for this offer since no other 'In Progress'
        coupon exists for this advertiser.
        """
        business = BUSINESS_FACTORY.create_business(advertiser=self.advertiser)
        offer = OFFER_FACTORY.create_offer(business=business)
        coupon = COUPON_FACTORY.create_coupon(offer=offer)
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        self.post_data['business_name'] = self.coupon.offer.business.business_name
        self.post_data['slogan'] = self.coupon.offer.business.slogan
        self.post_data['headline'] = 'Match Biz No Coupon'
        self.post_data['qualifier'] = 'Different Offer'
        self.advertiser.businesses.all().order_by('id')[0].offers.all().order_by(
            'id')[0].coupons.all().delete()
        del self.session['consumer']['advertiser']\
            ['business'][0]['offer'][0]['coupon']
        self.assemble_session(self.session)
        pre_coupon_count = self.advertiser.businesses.all().order_by(
            'id')[0].offers.all().order_by('id')[0].coupons.all().count()
        response = self.client.post(
            reverse('preview-coupon'), self.post_data, follow=True
            )
        self.assertEqual(response.status_code, 200) 
        self.advertiser = Advertiser.objects.get(id=self.advertiser.id)
        post_coupon_count = self.advertiser.businesses.all().order_by(
            'id')[0].offers.all().order_by('id')[0].coupons.all().count()
        self.assertEqual(pre_coupon_count+1, post_coupon_count)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")
        self.assert_session_keys_current(current_biz=(1, 0), 
            current_offer=(0, 0), current_coupon=(0, 0))
        self.assert_session_update(business_name=self.post_data['business_name'],
            headline=self.post_data['headline'], 
            qualifier=self.post_data['qualifier'], coupon_type_id=1)
        self.assertNotEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                1]['business_name'])
        self.assertNotEqual(self.session['consumer']['advertiser']['business'][
            0]['offer'][0]['headline'], 
                self.client.session['consumer']['advertiser']['business'][
                    0]['offer'][0]['headline'])
        self.assertNotEqual(self.session['consumer']['advertiser']['business'][
            0]['offer'][0]['qualifier'], 
                self.client.session['consumer']['advertiser']['business'][
                    0]['offer'][0]['qualifier'])
        new_coupon = Coupon.objects.get(
            id=self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_id'])
        self.assertNotEqual(coupon.id, new_coupon.id)
        self.assertNotEqual(coupon.offer.id, new_coupon.offer.id)
        self.assertNotEqual(coupon.offer.business.id,
            new_coupon.offer.business.id)
        self.assert_new_coupon(new_coupon.id, coupon_type_id=1,
            offer_id=self.coupon.offer.id, headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_name=self.post_data['business_name'])
        
    def test_diff_bizz_no_offers(self):
        """ 
        POST a different Business that has a match in session.
        business_exists_for_advertiser, 
        business_has_offer == FALSE, 
        business_has_unpublished_offer == FALSE, 
        offer_has_coupon_association == FALSE
        """
        business = BUSINESS_FACTORY.create_business(advertiser=self.advertiser)
        offer = OFFER_FACTORY.create_offer(business=business)
        coupon = COUPON_FACTORY.create_coupon(offer=offer)
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        self.post_data['business_name'] = self.coupon.offer.business.business_name
        self.post_data['slogan'] = self.coupon.offer.business.slogan
        new_headline = 'Match Biz No Offer'
        self.post_data['headline'] = new_headline
        self.advertiser.businesses.all().order_by('id')[0].offers.all().delete()
        del self.session['consumer']['advertiser']['business'][0]['offer']
        self.assemble_session(self.session)
        pre_offer_count = self.advertiser.businesses.all().order_by(
            'id')[0].offers.all().count()
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.assertEqual(response.status_code, 200) 
        self.advertiser = Advertiser.objects.get(id=self.advertiser.id)
        post_offer_count = self.advertiser.businesses.all().order_by(
            'id')[0].offers.all().count()
        self.assertEqual(pre_offer_count+1, post_offer_count)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")
        self.assert_session_keys_current(
            current_biz=(1, 0), current_offer=(0, 0), current_coupon=(0, 0))
        self.assertNotEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
            1]['business_name'])
        self.assert_session_update(business_name=self.post_data['business_name'], 
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'], coupon_type_id=1)
        new_coupon = Coupon.objects.get(
            id=self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_id'])
        self.assertNotEqual(coupon.id, new_coupon.id)
        self.assertNotEqual(coupon.offer.id, new_coupon.offer.id)
        self.assertNotEqual(coupon.offer.business.id,
            new_coupon.offer.business.id)      
        self.assert_new_coupon(new_coupon.id, coupon_type_id=1,
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_name=self.post_data['business_name'])
        
    def test_diff_bizz_no_business(self):
        """ POST a different Business that has no match in session.
        advertiser->business0->offer0->coupon0('In Progress')
        advertiser->business1->offer0->coupon0('Paid')('Slot Expired')
        advertiser->business1->offer0->coupon1('In Progress')
        """
        business = BUSINESS_FACTORY.create_business(advertiser=self.advertiser)
        offer = OFFER_FACTORY.create_offer(business=business)
        coupon_list = COUPON_FACTORY.create_coupons(offer=offer, create_count=2)
        coupon0 = coupon_list[0]
        coupon1 = coupon_list[1]
        coupon1.coupon_type = CouponType.objects.get(id=1)
        coupon1.save()
        self.prep_slot(coupon0, coupon0)
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        self.post_data['business_name'] = 'This Will Not Match'
        self.assemble_session(self.session)
        pre_business_count = self.advertiser.businesses.all().count()
        response = self.client.post(
            reverse('preview-coupon'), self.post_data, follow=True
            )
        self.assertEqual(response.status_code, 200) 
        self.advertiser = Advertiser.objects.get(id=self.advertiser.id)
        post_business_count = self.advertiser.businesses.all().count()
        self.assertEqual(pre_business_count, post_business_count)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")
        self.assert_session_keys_current(
            current_biz=(1, 0), current_offer=(0, 0), current_coupon=(1, 0))
        self.assertNotEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                1]['business_name'])
        self.assert_session_update(business_name=self.post_data['business_name'],
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'], coupon_type_id=1)
        new_coupon_id = self.client.session['consumer']['advertiser'][
            'business'][0]['offer'][0]['coupon'][0]['coupon_id'] 
        self.assert_new_coupon(new_coupon_id, coupon_id=self.coupon.id,
            coupon_type_id=1, offer_id=self.coupon.offer.id,
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_id=self.coupon.offer.business.id,
            business_name=self.post_data['business_name'])
