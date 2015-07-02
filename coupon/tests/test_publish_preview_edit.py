"""
This is a test module for coupon view preview edit when in PUBLISH mode. 
"""

import datetime

from django.core.urlresolvers import reverse
  
from advertiser.models import Advertiser
from coupon.models import CouponType, Slot, SlotTimeFrame
from coupon.tests.test_cases import PreviewEditTestCase


class TestPublishModePreviewEdit(PreviewEditTestCase):
    """ Test case for the 'PUBLISH' Mode for PreviewEdit functionality.
    """
    fixtures = ['test_advertiser', 'test_coupon_views']
    
    def common_asserts(self, response):
        """ Common test assertions. """
        self.assertContains(response, "Publish up to 10 coupons")
        self.assertContains(response, "$199/month")

    def test_get_publish_coupon(self):
        """ 
        Test Get functionality when someone enters preview edit and 
        has a slot.  They should be in PUBLISH mode at this point and they
        shouldn't have to purchase a coupon.
        """
        today = datetime.date.today()
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        business = advertiser.businesses.all()[0]
        slot = Slot(site_id=2,
            business_id=business.id,
            renewal_rate=99, 
            is_autorenew=True,
            end_date=today + datetime.timedelta(days=10))
        slot.save()
        response = self.client.get(reverse('preview-coupon'), follow=True)
        self.assertNotContains(response, "$199/month")
        self.assertTemplateNotUsed(response, 
            'include/dsp/dsp_purchase_intent.html')

#    def test_blank_out_offer(self):
#        """ Assert offer is blanked out because this coupon is PAID. """
#        advertiser = Advertiser.objects.get(id=11)
#        build_advertiser_session(self, advertiser)
#        self.session['consumer']['advertiser']['business']\
#            [self.session['current_business']]['offer']\
#            [self.session['current_offer']]['coupon']\
#            [self.session['current_coupon']]['coupon_type'] = 3
#        self.assemble_session(self.session)
#        response = self.client.get(reverse('preview-coupon'), follow=True) 
#        self.assertEqual(str(response.request['PATH_INFO']), 
#            '/hudson-valley/create-coupon/preview/')

    def test_get_pay_for_coupon(self):
        """ Test Get functionality when someone enters preview edit and 
        does not have a slot.  They should have to purchase a coupon.
        """
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        response = self.client.get(reverse('preview-coupon'), follow=True)
        self.common_asserts(response)
        
    def test_10_now_pay_again(self):
        """ Test Get functionality when someone enters preview edit and 
        has 10 active slots and time_frames.  They have to pay for coupon
        number 11.
        """
        today = datetime.date.today()
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0]
        coupon = business.offers.all()[0].coupons.all()[0]
        count = 0
        renewal_rate = 99
        is_autorenew = True
        parent_slot_id = None
        while count < 10:
            slot = Slot.objects.create(site_id=2,
                business_id=business.id,
                renewal_rate=renewal_rate, 
                is_autorenew=is_autorenew,
                parent_slot_id = parent_slot_id,
                end_date=today + datetime.timedelta(days=count+1))
            if not parent_slot_id:
                parent_slot_id = slot.id
            SlotTimeFrame.objects.create(slot_id=slot.id,
                coupon_id=coupon.id)
            renewal_rate = None
            is_autorenew = False
            count += 1
        self.login(email=advertiser.email)
        response = self.client.get(reverse('preview-coupon'), follow=True)
        self.common_asserts(response)
 
    def test_pay_for_first_coupon(self):
        """ Assert an advertiser gets sent to the pay page for his first coupon.
        """
        advertiser = Advertiser.objects.get(id=10)
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        response = self.client.post(reverse('preview-coupon'), 
            self.post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")

    def test_pay_for_coupon_11(self):
        """ Test POST functionality when someone enters preview edit and 
        has 10 active slots and time_frames. They have to pay for coupon
        number 11.
        """
        today = datetime.date.today()
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0]
        coupon = business.offers.all()[0].coupons.all()[0]
        count = 0
        renewal_rate = 99
        is_autorenew = True
        parent_slot_id = None
        while count < 10:
            if count == 0:
                slot = Slot(site_id=2, 
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    end_date=today + datetime.timedelta(days=count+1))
            else:
                slot = Slot(site_id=2, 
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    parent_slot_id=parent_slot_id,
                    end_date=today + datetime.timedelta(days=count+1))
            slot.save()
            if count == 0:
                parent_slot_id = slot.id
            SlotTimeFrame.objects.create(slot_id=slot.id,
                coupon_id=coupon.id)
            renewal_rate = None
            is_autorenew = False
            count += 1
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        response = self.client.post(reverse('preview-coupon'), 
                                   self.post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")

    def test_publish_coupon_2(self):
        """ Assert when someone has a parent slot he does not pay for child
        number 1.  Assert that the first coupon does not get overwritten in the
        session and that the second coupon  and the current positions are 
        set accordingly.
        """
        today = datetime.date.today()
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0]
        coupon = business.offers.all()[0].coupons.all()[0]
        coupon_type = CouponType.objects.get(id=3)
        coupon.coupon_type = coupon_type
        coupon.save()
        slot = Slot.objects.create(site_id=2,
            business_id=business.id,
            renewal_rate=99, 
            is_autorenew=True,
            end_date=today + datetime.timedelta(days=10))
        SlotTimeFrame.objects.create(slot_id=slot.id, coupon_id=coupon.id)
        self.login_build_set_assemble(advertiser)
        current_offer1 = self.client.session['consumer']['advertiser']\
            ['business'][self.client.session['current_business']]['offer']\
            [self.client.session['current_offer']]
        self.assertEqual(self.client.session['current_business'], 0)
        self.assertEqual(self.client.session['current_offer'], 0)
        self.assertEqual(self.client.session['current_coupon'], 0)
        self.assertEqual(current_offer1['coupon']\
            [self.client.session['current_coupon']]['coupon_type_id'], 3)
        self.setup_post_data(advertiser, location_count=10)
        self.post_data['headline'] = 'A Differenet Headline'
        self.post_data['qualifier'] = 'A New Qualifier'
        response = self.client.post(reverse('preview-coupon'), 
            self.post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
        current_offer2 = self.client.session['consumer']['advertiser']\
            ['business'][self.client.session['current_business']]['offer']\
            [self.client.session['current_offer']]
        self.assertEqual(self.client.session['current_business'], 0)
        self.assertEqual(self.client.session['current_offer'], 1)
        self.assertEqual(self.client.session['current_coupon'], 0)
        self.assertEqual(current_offer1['headline'], coupon.offer.headline)
        self.assertEqual(current_offer1['qualifier'], coupon.offer.qualifier)
        self.assertEqual(current_offer2['coupon']\
            [self.client.session['current_coupon']]['coupon_type_id'], 3)
        self.assertEqual(current_offer2['headline'], self.post_data['headline'])
        self.assertEqual(current_offer2['qualifier'],
            self.post_data['qualifier'])
        # Make sure both of these keys got deleted.  If one exists and the 
        # other is not there, it can drop us into unexpected logic on a browser
        # back button click.
        self.assertTrue('coupon_mode' not in self.client.session)
        self.assertTrue('family_availability_dict' not in self.client.session)

    def test_publish_coupon_10(self):
        """ Assert when someone has a parent slot, they don't pay for child
        number 9.
        """
        today = datetime.date.today()
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0]
        coupon = business.offers.all()[0].coupons.all()[0]
        count = 0
        renewal_rate = 99
        is_autorenew = True
        parent_slot_id = None
        while count < 9:
            if count == 0:
                slot = Slot.objects.create(site_id=2,
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    end_date=today + datetime.timedelta(days=count+1))
            else:
                slot = Slot.objects.create(site_id=2,
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    parent_slot_id=parent_slot_id,
                    end_date=today + datetime.timedelta(days=count+1))
            if count == 0:
                parent_slot_id = slot.id
            SlotTimeFrame.objects.create(slot_id=slot.id, coupon_id=coupon.id)
            renewal_rate = None
            is_autorenew = False
            count += 1
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        response = self.client.post(reverse('preview-coupon'), 
            self.post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
        
    def test_empty_parent_slot(self):
        """ Test POST functionality when someone enters preview edit and 
        has 10 slots. The parent does not have an active time frame, but the
        9 children have active time_frames. So, this advertiser does not have 
        to pay for their next coupon.  It should get published utilizing the 
        parents slot that has already been created.
        """ 
        today = datetime.date.today()
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0]
        coupon = business.offers.all()[0].coupons.all()[0]
        count = 0
        renewal_rate = 99
        is_autorenew = True
        parent_slot_id = None
        while count < 10:
            if count == 0:
                slot = Slot.objects.create(site_id=2,
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    end_date=today + datetime.timedelta(days=count+1))
            else:
                slot = Slot.objects.create(site_id=2,
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    parent_slot_id=parent_slot_id,
                    end_date=today + datetime.timedelta(days=count+1))
            if count == 0:
                parent_slot_id = slot.id
            if count != 0:   
                SlotTimeFrame.objects.create(slot_id=slot.id,
                    coupon_id=coupon.id)
            renewal_rate = None
            is_autorenew = False
            count += 1
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        response = self.client.post(reverse('preview-coupon'), 
            self.post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')

    def test_empty_child_slot(self):
        """ Test POST functionality when someone enters preview edit and 
        has 10 slots. The parent and 8 children have a time_frame. One of
        the children does not have an active time frame. So, this advertiser
        does not have to pay for their next coupon.  It should get published
        utilizing the child slot that has already been created.
        """
        today = datetime.date.today()
        advertiser = Advertiser.objects.get(id=10)
        business = advertiser.businesses.all()[0]
        coupon = business.offers.all()[0].coupons.all()[0]
        count = 0
        renewal_rate = 99
        is_autorenew = True
        parent_slot_id = None
        while count < 10:
            if count == 0:
                slot = Slot.objects.create(site_id=2,
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    end_date=today + datetime.timedelta(days=count+1))
            else:
                slot = Slot.objects.create(site_id=2,
                    business_id=business.id,
                    renewal_rate=renewal_rate, 
                    is_autorenew=is_autorenew,
                    parent_slot_id=parent_slot_id,
                    end_date=today + datetime.timedelta(days=count+1))
            if count == 0:
                parent_slot_id = slot.id      
            if count != 5:
                SlotTimeFrame.objects.create(slot_id=slot.id,
                    coupon_id=coupon.id)
            renewal_rate = None
            is_autorenew = False
            count += 1
        self.login(email=advertiser.email)
        self.setup_post_data(advertiser, location_count=10)
        response = self.client.post(reverse('preview-coupon'), 
            self.post_data, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/advertiser/')
