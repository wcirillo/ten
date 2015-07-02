""" This is a test module for coupon view testing. """

import datetime
from decimal import Decimal

from django.core.urlresolvers import reverse

from advertiser.models import Advertiser
from common.session import build_advertiser_session
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.offer_factory import OFFER_FACTORY
from coupon.factories.slot_factory import (SLOT_FACTORY,
    SLOT_TIME_FRAME_FACTORY)
from coupon.models import Coupon, CouponType
from coupon.service.expiration_date_service import (
    frmt_expiration_date_for_dsp, get_default_expiration_date)
from coupon.service.single_coupon_service import SINGLE_COUPON
from coupon.tests.test_cases import PreviewEditTestCase
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY


class TestPreviewEdit(PreviewEditTestCase):
    """ Test case for searching on a get or post of nothing. """

    def test_get_success(self):
        """ Test show_preview_coupon view for a successful GET. """
        # Ensure flyer_choice is wiped out when page finishes loading.
        build_advertiser_session(self, self.advertiser)
        self.session.update({'add_flyer_choice': 1})
        self.assemble_session(self.session)
        response = self.client.get(reverse('preview-coupon')) 
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/preview/')
        self.assertContains(response, "frm_edit_coupon")
        self.assertContains(response, "Publish up to 10 coupons")
        self.assertContains(response, "$199/month")
        self.assertEqual(self.client.session.get('add_flyer_choice', None), None)
        # Get of Preview edit page does not set product_list.
        self.assertEqual(self.client.session.get('product_list', False), False)
        self.assertContains(response, '%s%s"%s"' % 
            ('Business Name (required)</label>',
             '<input name="business_name" value=',
             self.coupon.offer.business.business_name))
        self.assertContains(response, '%s"%s"' %         
        ('Slogan (optional)</label><input name="slogan" value=',
         self.coupon.offer.business.slogan))
        self.assertContains(response, '%s"%s"' % 
            ('input name="headline" value=',
             self.coupon.offer.headline))
        self.assertContains(response, '%s"%s"' % 
            ('input name="qualifier" value=',
             self.coupon.offer.qualifier))
        self.assertContains(response, '%s"%s"' % 
            ('location_address1_1" value=',
             self.location.location_address1))
        self.assertContains(response, '%s"%s"' % 
            ('location_address2_1" value=',
             self.location.location_address2))
        self.assertContains(response, '%s"%s"' % 
            ('location_city_1" value=',
             self.location.location_city))
        self.assertContains(response, "%s%s" %
            ('id_location_state_province_1"><',
             'option value="">- select a state -</option>'))
        self.assertContains(response, '%s"%s"' % 
            ('location_zip_postal_1" value=',
             self.location.location_zip_postal))
        self.assertContains(response, '%s"%s"' % 
            ('location_description_1" value=',
             self.location.location_description))
        self.assertContains(response, '%s"%s"' % 
            ('location_area_code_1" value=',
             self.location.location_area_code))
        self.assertContains(response, '%s"%s"' % 
            ('location_exchange_1" value=',
             self.location.location_exchange))
        self.assertContains(response, '%s"%s"' % 
            ('location_number_1" value=',
             self.location.location_number))
        self.assertContains(response, 'One Coupon per Person, per Visit.')
        self.assertContains(response, 'Enter Custom Restriction(s).')
        self.assertContains(response, '%s%s' %
            ('"id_is_valid_monday" checked="checked" type="',
             'checkbox" class="monfri" name="is_valid_monday"'))
        self.assertContains(response, '%s%s' %
            ('"id_is_valid_tuesday" checked="checked" type="',
             'checkbox" class="monfri" name="is_valid_tuesday"'))
        self.assertContains(response, '%s%s' %
            ('"id_is_valid_wednesday" checked="checked" type="',
             'checkbox" class="monfri" name="is_valid_wednesday"'))
        self.assertContains(response, '%s%s' %
            ('"id_is_valid_thursday" checked="checked" type="',
             'checkbox" class="monfri" name="is_valid_thursday"'))
        self.assertContains(response, '%s%s' %
            ('"id_is_valid_friday" checked="checked" type="',
             'checkbox" class="monfri" name="is_valid_friday"'))
        self.assertContains(response, '%s%s' %
            ('"id_is_valid_saturday" checked="checked" type="',
             'checkbox" class="weekend" name="is_valid_saturday"'))
        self.assertContains(response, '%s%s' %
            ('"id_is_valid_sunday" checked="checked" type="',
             'checkbox" class="weekend" name="is_valid_sunday"'))
        self.assertContains(response,
            'Accept Printed AND Text Message Coupons.')
        self.assertContains(response, '%s%s' % 
            ('input checked="checked" type="radio" id="id_is_redeemed_by_sms_0',
            '" value="1" name="is_redeemed_by_sms"'))
        self.assertContains(response, 'Printed coupons only.')
        self.assertContains(response, 'Continue to Checkout')
        
    def test_show_with_annual_price(self):
        """ Test show_preview_coupon view coming back from checkout page, with
        an ad rep in session and the annual price option selected in session.
        """
        build_advertiser_session(self, self.advertiser)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session.update({'ad_rep_id': ad_rep.id,
            'add_annual_slot_choice' : 0})
        self.assemble_session(self.session)
        response = self.client.get(reverse('preview-coupon')) 
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/preview/')
        self.assertContains(response, "frm_edit_coupon")
        self.assertContains(response, 
            'Monthly plan available for $199/month')
        self.assertContains(response, 'coupon in minutes')
        self.assertEqual(self.client.session['add_annual_slot_choice'], 0)
        
    def test_post_success(self):
        """ Test show_preview_coupon view for a successful POST. """
        build_advertiser_session(self, self.advertiser)
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=10)
        response = self.client.post(reverse('preview-coupon'),
            self.post_data, follow=True)
        self.common_assertions(response, 'POST')
        # If no ad rep in session, product_list should default to monthly slot.
        self.assertEqual(self.client.session['product_list'][0][0], 2) 
        self.assertEqual(self.client.session['add_slot_choice'], 0)

    def test_post_w_annual_price(self):
        """ Test show_preview_coupon view for a successful POST when the
        annual price is in session (came back to preview from checkout). Assert
        annual price was not overwritten or dropped.
        """
        build_advertiser_session(self, self.advertiser)
        self.session.update({'add_annual_slot_choice' : 0})
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser)
        response = self.client.post(reverse('preview-coupon'),
            self.post_data, follow=True)
        self.common_assertions(response, 'POST')
        self.assertEqual(self.session['add_annual_slot_choice'], 0)
        
    def test_default_product_w_ad_rep(self):
        """ Test show_preview_coupon post when ad rep in session, we set the 
        product to monthly slot if no selection was made. """
        build_advertiser_session(self, self.advertiser)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session.update({'ad_rep_id': ad_rep.id})
        self.assemble_session(self.session)       
        self.setup_post_data(self.advertiser, location_count=1)
        response = self.client.post(reverse('preview-coupon'),
            self.post_data, follow=True)
        self.common_assertions(response, 'POST')
        # If no ad rep in session, product_list should default to monthly slot.
        self.assertEqual(self.client.session['product_list'][0][0], 2) 
        self.assertEqual(self.client.session['add_slot_choice'], 0)
        
    def test_respect_selected_product(self):
        """ Assert previous product selections are respected and not defaulted
        on preview edit post. """
        build_advertiser_session(self, self.advertiser)
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.session.update({'ad_rep_id': ad_rep.id, 
            'product_list': [(2, Decimal('199.00'), 'desc')]})
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertEqual(self.client.session['product_list'][0][0], 2)

    def test_no_current_business_key(self):
        """ Test show_preview_coupon POST with no current_business key to get 
        bounced to home.
        """
        build_advertiser_session(self, self.advertiser)
        del self.session['current_business'] # Does not exist.
        self.assemble_session(self.session)
        response = self.client.post(reverse('preview-coupon'), follow=True) 
        # Redirected to home by default.
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/coupons/')
    
    def test_get_no_offer(self):
        """ Test show_preview_coupon get for KeyError with no offer to bounce
        you home.
        """
        build_advertiser_session(self, self.advertiser)
        del self.session['consumer']['advertiser']['business']\
            [self.session['current_business']]['offer']
        self.assemble_session(self.session)
        response = self.client.get(reverse('preview-coupon'), follow=True) 
        # Redirected to home by default.
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/coupons/')

    def test_post_no_coupon_home(self):
        """ Test when the current coupon in session does not exist for 
        some reason, redirect back to home.
        """
        #self.coupon.delete()
        build_advertiser_session(self, self.advertiser)
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser)
        del self.session['consumer']['advertiser']['business'][0]['offer'][0]['coupon']
        self.assemble_session(self.session)
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.assertEqual(response.status_code, 200) 
        # Redirected to home by default.
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/coupons/')
        
    def test_post_blank_offer(self):
        """ Test blank out offer on POST. Offer is required, so this post should 
        render the preview page again.
        """
        build_advertiser_session(self, self.advertiser)
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser)
        # Delete headline because it is required.
        del self.post_data['headline']
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)        
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/preview/')      

class TestPreviewEditExpirationDate(PreviewEditTestCase):
    """ Tests for expiration date stuff in Preview Edit. """
    def test_unicode_expiration_date(self):
        """ Pass in a unicode valid expiration date and make sure it gets 
        displayed on preview edit appropriately.
        """
        unicode_plus_a_week_date = frmt_expiration_date_for_dsp(
            datetime.date.today() + datetime.timedelta(days=7))
        build_advertiser_session(self, self.advertiser)
        self.session['consumer']['advertiser']['business'] \
            [self.session['current_business']]['offer'] \
            [self.session['current_offer']]['coupon'] \
            [self.session['current_coupon']]['expiration_date'] \
            = unicode_plus_a_week_date
        self.assemble_session(self.session)
        response = self.client.get(reverse('preview-coupon'), follow=True) 
        self.assertContains(response, unicode_plus_a_week_date)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/preview/')

    def test_type_date_expiration_date(self):
        """  Pass in a valid type(date()) expiration_date into session and make
        sure it get displayed in unicode format on the GET of preview edit.
        """
        type_date_plus_a_week = datetime.date.today() + datetime.timedelta(
            days=7)
        build_advertiser_session(self, self.advertiser)
        self.session['consumer']['advertiser']['business'] \
            [self.session['current_business']]['offer'] \
            [self.session['current_offer']]['coupon'] \
            [self.session['current_coupon']]['expiration_date'] \
            = type_date_plus_a_week
        self.assemble_session(self.session)
        response = self.client.get(reverse('preview-coupon'), follow=True)
        self.assertContains(response, 
                       frmt_expiration_date_for_dsp(type_date_plus_a_week)) 
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/preview/')
                 
    def test_unicode_expired_exp_date(self):
        """ Pass in an expired unicode expiration_date into session and make 
        sure it gets bumped up by the default expiration date and displays the 
        appropriate default_expiration_date in unicode format.
        """
        build_advertiser_session(self, self.advertiser)
        self.session['consumer']['advertiser']['business'] \
            [self.session['current_business']]['offer'] \
            [self.session['current_offer']]['coupon'] \
            [self.session['current_coupon']]['expiration_date'] \
            = frmt_expiration_date_for_dsp(
                datetime.date.today() - datetime.timedelta(days=7))
        self.assemble_session(self.session)
        response = self.client.get(reverse('preview-coupon'), follow=True)
        self.assertContains(response, get_default_expiration_date())
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/preview/')

    def test_typ_date_expired_exp_date(self):
        """
        Pass in an expired type(date()) expiration_date into session and make 
        sure it gets bumped up by the default expiration date and displays the 
        appropriate default_expiration_date in unicode format.
        """
        build_advertiser_session(self, self.advertiser)
        self.session['consumer']['advertiser']['business']\
            [self.session['current_business']]['offer']\
            [self.session['current_offer']]['coupon']\
            [self.session['current_coupon']]['expiration_date'] \
            = datetime.date.today() - datetime.timedelta(days=7)
        self.assemble_session(self.session)
        response = self.client.get(reverse('preview-coupon'), follow=True)
        self.assertContains(response, get_default_expiration_date()) 
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/preview/')

    
class TestPreviewEditOffer(PreviewEditTestCase):
    """ Tests for Offer Fields on the Preview Edit form.  Also ensures
    the correct data for this advertisers businesses offers are updated 
    appropriately in the session and the database.
    """
    def test_post_diff_offer(self):
        """ Update the existing business, offer coupon combination since it 
        has not been published yet.
        advertiser->business0->offer0->coupon('In Progress')
        """
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        self.post_data['headline'] = 'Different Headline'
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")
        self.assert_session_keys_current(
            current_biz=(0, 0), current_offer=(0, 0), current_coupon=(0, 0))
        self.assertEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['business_name'])
        self.assert_session_update(headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'], coupon_type_id=1)
        new_coupon_id = self.client.session['consumer']['advertiser'][
            'business'][0]['offer'][0]['coupon'][0]['coupon_id']    
        self.assert_new_coupon(new_coupon_id, coupon_id=self.coupon.id,
            coupon_type_id=1, offer_id=self.coupon.offer.id,
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_id=self.coupon.offer.business.id,
            business_name=self.post_data['business_name'])
       
    def test_same_offer_new_coupon(self):
        """Assert POST same business_name and offer as session but no InProgress
        coupon in session. Create a new coupon for this same business and offer.
        """
        pre_coupon_count = self.advertiser.businesses.all()[0].offers.all(
            )[0].coupons.count()
        self.coupon.coupon_type = CouponType.objects.get(id=3)
        self.coupon.save()
        self.prep_slot(self.coupon, self.coupon)
        build_advertiser_session(self, self.advertiser)        
        self.setup_post_data(self.advertiser, location_count=10)
        self.assemble_session(self.session)
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.assertEqual(response.status_code, 200)
        advertiser = Advertiser.objects.get(id=self.advertiser.id)
        post_coupon_count = advertiser.businesses.all(
            )[0].offers.all()[0].coupons.count()
        self.assertEqual(pre_coupon_count+1, post_coupon_count)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assert_session_keys_current(
            current_biz=(0, 0), current_offer=(0, 0), current_coupon=(0, 1))
        self.assertEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['business_name'])
        self.assert_session_update(headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'])
        self.assertEqual(3,
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_type_id'])
        self.assertEqual(1, 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][1]['coupon_type_id'])
        new_coupon_id = self.client.session['consumer']['advertiser'][
            'business'][0]['offer'][0]['coupon'][1]['coupon_id'] 
        self.assertNotEqual(int(self.coupon.id), new_coupon_id)
        self.assertEqual(3, self.coupon.coupon_type_id)      
        self.assert_new_coupon(new_coupon_id, coupon_type_id=1, 
            offer_id=self.coupon.offer.id, headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_id=self.coupon.offer.business.id,
            business_name=self.post_data['business_name'])

    def test_diff_offer_in_progress(self):
        """ POST a different offer from the current coupon we are working on
        in session. The different offer that got posted will exist and match an
        offer for this business in session.  In progress coupon exists == True.
        advertiser->business0->offer0->coupon0('In Progress')
        advertiser->business0->offer1->coupon0('Paid')('Slot Expired')
        """
        self.setup_post_data(self.advertiser)
        offer0 = OFFER_FACTORY.create_offer(
            business=self.advertiser.businesses.all()[0])
        coupon0 = COUPON_FACTORY.create_coupon(offer=offer0)
        self.prep_slot(coupon0, coupon0)         
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "frm_checkout_coupon_purchase")
        self.assert_session_keys_current(
            current_biz=(0, 0), current_offer=(1, 0), current_coupon=(0, 0))
        self.assert_session_update(business_name=self.post_data['business_name'],
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'], coupon_type_id=1)
        self.assertNotEqual(self.post_data['headline'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['headline'])
        self.assertNotEqual(self.post_data['qualifier'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['qualifier'])
        self.assertEqual(3,
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['coupon'][0]['coupon_type_id'])
        new_coupon_id = self.client.session['consumer']['advertiser'][
            'business'][0]['offer'][0]['coupon'][0]['coupon_id'] 
        self.assertEqual(1, self.coupon.coupon_type_id)        
        self.assert_new_coupon(new_coupon_id, coupon_id=self.coupon.id,
            coupon_type_id=1, offer_id=self.coupon.offer.id,
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_id=self.coupon.offer.business.id,
            business_name=self.post_data['business_name'])

    def test_diff_offer_not_in_progres(self):
        """ 
        POST a different offer from the current coupon we are working on
        in session. The different offer that got posted will exist and match an 
        offer for this business in session.  In progress coupon exists == False.
        offer0 will match the offer that gets posted.
        advertiser->business0->offer0->coupon0('Paid')('Slot Expired')
        advertiser->business0->offer1->coupon0('Paid')('Slot Expired')
        """
        self.setup_post_data(self.advertiser)
        self.coupon.coupon_type = CouponType.objects.get(id=3)
        self.coupon.save()
        offer0 = OFFER_FACTORY.create_offer(
            business=self.advertiser.businesses.all()[0])
        coupon0 = COUPON_FACTORY.create_coupon(offer=offer0)
        self.prep_slot(coupon0, self.coupon)        
        slot = SLOT_FACTORY.create_slot(coupon=self.coupon, 
            create_slot_time_frame=False)
        slot.end_date = datetime.date(2011, 1, 2)
        slot.save()
        SLOT_TIME_FRAME_FACTORY.create_expired_time_frame(slot=slot,
            coupon=self.coupon)          
        pre_coupon_count = self.advertiser.businesses.all()[0].offers.all(
            )[0].coupons.count()
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.common_assertions(response, 'POST')
        self.assert_session_keys_current(
            current_biz=(0, 0), current_offer=(1, 0), current_coupon=(0, 1))
        self.assertEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['business_name'])
        self.assert_session_update(headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'])
        self.assertNotEqual(self.post_data['headline'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['headline'])
        self.assertNotEqual(self.post_data['qualifier'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['qualifier'])
        self.assertEqual(3,
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_type_id'])
        self.assertEqual(3,
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['coupon'][0]['coupon_type_id'])
        self.assertEqual(1, 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][1]['coupon_type_id'])
        new_coupon_id = self.client.session['consumer']['advertiser'][
            'business'][0]['offer'][0]['coupon'][1]['coupon_id'] 
        post_coupon_count = self.advertiser.businesses.all().order_by(
            'id')[0].offers.all().order_by('id')[0].coupons.all().count()
        self.assertEqual(pre_coupon_count+1, post_coupon_count)
        self.assertNotEqual(int(self.coupon.id), new_coupon_id)
        self.assertNotEqual(self.coupon.id, coupon0.id)
        self.assertEqual(3, self.coupon.coupon_type_id)
        self.assertEqual(3, coupon0.coupon_type_id)       
        self.assert_new_coupon(new_coupon_id, coupon_type_id=1, 
            offer_id=self.coupon.offer.id, headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_id=self.coupon.offer.business.id,
            business_name=self.post_data['business_name'])

    def test_diff_off_no_match_not_in(self):
        """
        Different offer, No Match In Progress
        POST a different offer from the current coupon we are working on
        in session. The different offer that got posted will exist and match an 
        offer for this business in session.  In progress coupon exists == True.
        offer2-->coupon0 will get created in this test.
        advertiser->business0->offer0->coupon0('Paid')('Slot Expired')
        advertiser->business0->offer1->coupon0('Paid')('Slot Expired')
        """
        self.setup_post_data(self.advertiser)
        self.post_data['headline'] = 'Create Offer3'
        self.post_data['qualifier'] = 'And Coupon0'
        self.coupon.coupon_type = CouponType.objects.get(id=3)
        self.coupon.save()
        offer0 = OFFER_FACTORY.create_offer(
            business=self.advertiser.businesses.all()[0])
        coupon0 = COUPON_FACTORY.create_coupon(offer=offer0)
        self.prep_slot(coupon0, self.coupon)
        slot = SLOT_FACTORY.create_slot(coupon=self.coupon, 
            create_slot_time_frame=False)
        slot.end_date = datetime.date(2011, 1, 2)
        slot.save()
        SLOT_TIME_FRAME_FACTORY.create_expired_time_frame(slot=slot,
            coupon=self.coupon)          
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.common_assertions(response, 'POST')
        self.assert_session_keys_current(
            current_biz=(0, 0), current_offer=(1, 2), current_coupon=(0, 0))
        self.assertEqual(self.post_data['business_name'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['business_name'])
        self.assertNotEqual(self.post_data['headline'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['headline'])
        self.assertNotEqual(self.post_data['qualifier'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['qualifier'])
        self.assertNotEqual(self.post_data['headline'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['headline'])
        self.assertNotEqual(self.post_data['qualifier'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['qualifier'])
        self.assertEqual(self.post_data['headline'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][2]['headline'])
        self.assertEqual(self.post_data['qualifier'], 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][2]['qualifier'])
        self.assertEqual(3,
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][0]['coupon'][0]['coupon_type_id'])
        self.assertEqual(3,
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][1]['coupon'][0]['coupon_type_id'])
        self.assertEqual(1, 
            self.client.session['consumer']['advertiser']['business'][
                0]['offer'][2]['coupon'][0]['coupon_type_id'])
        new_coupon = Coupon.objects.get(
            id=self.client.session['consumer']['advertiser']['business'][
                0]['offer'][2]['coupon'][0]['coupon_id'])
        self.assertNotEqual(self.coupon.id, new_coupon.id)
        self.assertNotEqual(coupon0.id, new_coupon.id)
        self.assertEqual(3, self.coupon.coupon_type_id)
        self.assertEqual(3, coupon0.coupon_type_id)
        self.assertNotEqual(self.coupon.offer.id, new_coupon.offer.id)
        self.assertNotEqual(coupon0.offer.id, new_coupon.offer.id)       
        self.assert_new_coupon(new_coupon.id, coupon_type_id=1, 
            headline=self.post_data['headline'],
            qualifier=self.post_data['qualifier'],
            business_id=self.coupon.offer.business.id,
            business_name=self.post_data['business_name'])


class TestPreviewEditCoupon(PreviewEditTestCase):
    """ Tests for Business Fields on the Preview Edit form.  Also ensures
    the correct data for this advertisers businesses offers coupons
    are updated appropriately in the session and the database.
    """
    def test_change_coupon_custom(self):
        """ Test changing custom restriction on preview-edit page. """
        build_advertiser_session(self, self.advertiser)
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser)
        self.post_data["default_restrictions"] = [u'2', u'3', u'1']               
        self.post_data['custom_restrictions'] = [repr(u'Must be CA citizen. We\u2019l\
              l give you a detailed report. \r\n Bennivisions \u2122. 0000\
              0 000000000111 111111111111 222222222 2222222 22223333 333a33\
              333 33333334444444444444 4444444555555555 5555555555566f6 666\
              666666666666 677777777777 7777777778888 888888 8 88888f8 8899\
              99999 999999 9999999.  0000000 0000000000 0 0 0 11111s 1 1111\
              1111111112 222 222222 2222222 2 2 23333333333 3333 3a33334\
              4 4 4 44444444444444 4555555 55555555 555555666 666666s66666\
              6 66667777777777777777777 78888 8 8 88888888 8 8 8888 9p9999\
              9 9999999 99999 9. 00 0000000 00000 0000 001111111 111l1111\
              1 1 111222 222222222 2 22222 2 2 3 33333 3333 3 3333 3\
              j 3 3 34444444 4444 4 4 4 444444555555 55555 555555 555666 66\
              s666 666666 6666777 77777777 777777 7778888888 888888 888888\
              b999 9999999 9 999999999.  000000 0000 0 00000000 01111 111\
              1 a11111 1 11111222 2222 2 22222 2222 2223 33 333 33 333333\
              3 a33334 4 4 444444444444 44444555555 55555555555 55566 6 66\
              666a666 666 6 666666 6 6 66666666d677777 77777777777 7 7 7788\
              888888888 8 8888 888899 9 9 9999m9 9 999999999 .  0000000\
              0 0 000 00  0 000001111 1 1111111111 a 1 111222 2 2222 2 2222\
              2222222 333333333 3 3 3333333 33444 r444 4444 4 444444 445 5\
              55555 55 55555 5 5555566 6 6666666 6 n66666 6 6677\
              7 7 7 77 7 777 88 8 88888888888 8 8b99999999 9 99999999\
              9 9 9. 0000000 00001111 1111111 a1111111222 333333 388 888888\
              888 89999999 999999. 0y00000000 000000111 111111111 11111u11\
              222 22222222222 22222232223 ghjgh 33333333 bbbb3333333 44\
              4. This is the one-thousand five-hundredth marker her\
              e. Extra!')]
        response = self.client.post(reverse('preview-coupon'), 
            data=self.post_data,
            follow=True) 
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.default_restrictions.count(), 2, 
            "Default restrictions supplied for coupon interpreted incorrectly")
        if "Must be CA citizen" not in coupon.custom_restrictions:
            self.fail("Test custom restriction was not created successfully.")
        if "Extra" in coupon.custom_restrictions:
            self.fail("Custom restriction exceeds maximum length")
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, "Must be CA citizen")
        self.assertNotContains(response, "Extra!")
        # We now support unicode here, so changing this test
        ## Validate that unicode values removed:
        ## self.assertContains(response, "(tm)")
        self.assertContains(response, "u2019")

class TestPreviewEditLocation(PreviewEditTestCase):
    """ Tests for Location Fields on the Preview Edit form.  Also ensures
    the correct data for this advertisers locations
    are updated appropriately in the session and the database.
    """
    def test_diff_off_with_location(self):
        """ 
        POST a different offer from the current coupon we are working on
        in session. The different offer that got posted will exist and match an 
        offer for this business in session.  In progress coupon exists == False.
        Has a location
        """
        self.coupon.coupon_type = CouponType.objects.get(id=3)
        self.coupon.save()
        slot0 = SLOT_FACTORY.create_slot(coupon=self.coupon,
            create_slot_time_frame=False)
        slot0.end_date = datetime.date(2012, 1, 2)
        slot0.save()
        SLOT_TIME_FRAME_FACTORY.create_expired_time_frame(slot=slot0,
            coupon=self.coupon)        
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        self.advertiser.businesses.all()[0].locations.all().order_by('id')[1].delete()
        self.post_data['headline'] = 'No match Offer'
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.common_assertions(response, 'POST')
        self.assertEqual(self.location.id, self.client.session[
            'consumer']['advertiser']['business'][0]['location'][0]['location_id'])
        self.assertEqual(self.location.id, self.client.session[
            'consumer']['advertiser']['business'][0]['offer'][0][
                'coupon'][0]['location'][0])
        self.assertEqual(self.location.id, self.client.session[
            'consumer']['advertiser']['business'][0]['offer'][1][
                'coupon'][0]['location'][0]['location_id'])
        new_location = self.advertiser.businesses.all()[0].locations.all()[0]
        self.assertEqual(self.location.id, new_location.id)
        self.assertNotEqual(self.location.location_address1,
            new_location.location_address1)
        self.assertNotEqual(self.location.location_address2,
            new_location.location_address2)
        self.assertNotEqual(self.location.location_area_code,
            new_location.location_area_code)
        self.assertNotEqual(self.location.location_exchange,
            new_location.location_exchange)
        self.assertNotEqual(self.location.location_number,
            new_location.location_number)
        self.assertNotEqual(self.location.location_city,
            new_location.location_city)
        self.assertNotEqual(self.location.location_description,
            new_location.location_description)
        self.assertEqual(new_location.location_address1,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_address1'])
        self.assertEqual(new_location.location_address2,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_address2'])
        self.assertEqual(new_location.location_area_code,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_area_code'])
        self.assertEqual(new_location.location_exchange,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_exchange'])
        self.assertEqual(new_location.location_number,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_number'])
        self.assertEqual(new_location.location_city,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_city'])
        self.assertEqual(new_location.location_description,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_description'])

    def test_diff_off_post_new_location(self):
        """ 
        POST a different offer from the current coupon we are working on
        in session. The different offer that got posted will exist and match an 
        offer for this business in session.  In progress coupon exists == False.
        Has no location but we are POSTING the first location
        """        
        self.coupon.coupon_type = CouponType.objects.get(id=3)
        self.coupon.save()
        slot0 = SLOT_FACTORY.create_slot(coupon=self.coupon,
            create_slot_time_frame=False)
        slot0.end_date = datetime.date(2012, 1, 2)
        slot0.save()
        SLOT_TIME_FRAME_FACTORY.create_expired_time_frame(slot=slot0,
            coupon=self.coupon)        
        self.advertiser.businesses.all()[0].locations.all().delete()
        pre_location_count = self.advertiser.businesses.all()[0].locations.count()
        build_advertiser_session(self, self.advertiser)        
        self.assemble_session(self.session)
        self.setup_post_data(self.advertiser, location_count=1)
        self.advertiser.businesses.all()[0].locations.all().delete()
        self.post_data['headline'] = 'No match Offer'
        response = self.client.post(reverse('preview-coupon'), self.post_data, 
            follow=True)
        self.common_assertions(response, 'POST')
        post_location_count = self.advertiser.businesses.all()[0].locations.count()
        self.assertEqual(pre_location_count+1, post_location_count)
        new_location = self.advertiser.businesses.all()[0].locations.all()[0]
        self.assertEqual(new_location.location_address1,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_address1'])
        self.assertEqual(new_location.location_address2,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_address2'])
        self.assertEqual(new_location.location_area_code,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_area_code'])
        self.assertEqual(new_location.location_exchange,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_exchange'])
        self.assertEqual(new_location.location_number,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_number'])
        self.assertEqual(new_location.location_city,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_city'])
        self.assertEqual(new_location.location_description,
            self.client.session['consumer']['advertiser']['business'][0][
                'offer'][1]['coupon'][0]['location'][0]['location_description'])