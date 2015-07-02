#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
""" Unit tests for views of the advertiser account in the advertiser app. """
import datetime

from django.core.urlresolvers import reverse

from advertiser.factories.business_factory import BUSINESS_FACTORY
from common.session import get_this_coupon_data
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.service.expiration_date_service import (default_expiration_date,
    get_default_expiration_date)
from coupon.models import Coupon, Slot, SlotTimeFrame


class TestAdvertiserAccount(EnhancedTestCase):
    """ Test case for requests of advertiser account view. 

    This view accepts GET, or POST with ajax.
    """
    urls = 'urls_local.urls_2'

    @staticmethod
    def get_slot_advertiser():
        """ Get a slot, and make its advertiser email verified.
        """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        return slot, advertiser

    def test_get_sign_in_no_session(self):
        """ Show advertiser sign in page. """
        response = self.client.get(reverse('advertiser-account'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'create-coupon')
        self.assertContains(response, 'Reset your password')
        self.assertContains(response, 'Keep me signed in')
        self.assertTemplateUsed(response, 'include/frm/frm_sign_in.html')
        
    def test_get(self):
        """ Assert that an advertiser with a current coupon gets the correct 
        view.
        """
        slot, advertiser = self.get_slot_advertiser()
        business = slot.business
        business.categories.add(7)
        coupon = slot.slot_time_frames.all()[0].coupon    
        self.login(advertiser.email)
        response = self.client.get(reverse('advertiser-account'))
        self.assertContains(response, 
            "%s%s%s" % ('href="/hudson-valley/business/edit/', business.id, 
            '/">customize business info</a>'))
        self.assertContains(response, 'frm_select_business')
        try:
            category = advertiser.businesses.all()[0].categories.all()[0].name
        except IndexError:
            category = ''
        self.assertContains(response, '%s is included in the %s category.'
            % (advertiser.businesses.all()[0].business_name, category))
        self.assertContains(response, 'Auto Renew is ON')
        self.assertContains(response,
            'Payment of $10.00 is scheduled for Jan. 1, 2099')
        self.assertContains(response, coupon.offer.headline)
        self.assertContains(response, coupon.offer.qualifier)
        
    def test_multiple_businesses(self):
        """ Make sure that when an advertiser is associated with multiple 
        businesses the correct information shows up on the page. 
        """
        slot, advertiser = self.get_slot_advertiser()
        business_1 = slot.business
        business_2 = BUSINESS_FACTORY.create_business(advertiser=advertiser)
        self.login(advertiser.email)
        response = self.client.get(reverse('advertiser-account'))
        self.assertContains(response, '%s is included in the' %
            business_1.business_name)
        self.assertContains(response,
            'select name="business_id" id="id_select_business">')
        self.assertContains(response,
            '<option value="%s"  selected>%s</option>' %
            (business_1.id, business_1.business_name))
        self.assertContains(response,
            '<option value="%s" >%s</option>' %
            (business_2.id, business_2.business_name))

    def test_not_my_business(self):
        """ Assert that an advertiser posting a business ID of another 
        advertiser is redirected non-permanently to the all coupons page.
        """
        advertiser = self.get_slot_advertiser()[1]
        self.login(advertiser.email)
        not_my_business = BUSINESS_FACTORY.create_business()
        response = self.client.post(reverse('advertiser-account'), 
            {'business_id': str(not_my_business.id)}, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/coupons/')
  
    def test_turn_on_display(self):
        """ Assert a coupon can be turned on for display when a slot exists.
        This coupon is expired and a slot exists for this business that has no
        active slot_time_frame. Make sure the expiration_date bumps up to the required default
        expiration date and the appropriate message gets growled back to the
        advertiser.
        """
        today = datetime.date.today()
        slot, advertiser = self.get_slot_advertiser()
        business = slot.business
        coupon = COUPON_FACTORY.create_coupon(business=business)
        coupon.coupon_type_id = 1
        coupon.expiration_date = today - datetime.timedelta(7)
        coupon.save()
        self.login(advertiser.email)
        this_coupon = get_this_coupon_data(self.client)[1]
        # Make sure this coupon is expired in the session.
        self.assertTrue(this_coupon['expiration_date'] < today)
        # Assert coupon_type_id has been set to in_progress in session, which
        # means it has NOT been published.
        self.assertEqual(this_coupon['coupon_type_id'], 1)
        headline = 'Test turn-display-on functionality'
        post_data = {'ajax_mode': 'turn-display-on', 
            'coupon_id': str(coupon.id), 'business_id': business.id,
            'headline': headline}
        response = self.client.post(reverse('advertiser-account'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '%s is now displayed.' % headline)
        self.assertContains(response, 
            '"expiration_date": "%s"' % (get_default_expiration_date()))
        coupon = Coupon.objects.get(id=coupon.id)
        this_coupon = get_this_coupon_data(self.client)[1]
        # Assert coupon_type_id has been set to paid, which means it has been
        # published. Check the values in session and in the database.
        self.assertEqual(coupon.coupon_type_id, 3)
        self.assertEqual(this_coupon['coupon_type_id'], 3)
        # Assert coupon is not expired in the session and database anymore.
        # Make sure the expiration date got bumped up with the 
        # default_expiration_date.
        self.assertEqual(this_coupon['expiration_date'],
            default_expiration_date())
        self.assertEqual(coupon.expiration_date, default_expiration_date())
        # Assert new time frame is opened, for this slot.
        self.assertTrue(coupon.slot_time_frames.latest('id').start_datetime <
            datetime.datetime.now())
        self.assertEqual(coupon.slot_time_frames.latest('id').end_datetime,
            None)
        self.assertEqual(coupon.slot_time_frames.latest('id').slot.id,
            slot.id + 1)

    def test_buy_display(self):
        """ Assert a coupon can be turned on for display when no slot exists.
        Turn this coupon display on. This coupon is expired and NO active slot
        exists for this business that has no active slot_time_frame. Make sure
        the appropriate data gets passed back to the view in order to push this
        advertiser to the purchase page.
        """
        today = datetime.date.today()
        coupon = COUPON_FACTORY.create_coupon(coupon_type_id=1)
        coupon.expiration_date = today - datetime.timedelta(7)
        coupon.save()
        advertiser = coupon.offer.business.advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        self.login_build_set_assemble(advertiser)
        post_data = {'ajax_mode': 'turn-display-on',
            'coupon_id': str(coupon.id),
            'business_id': coupon.offer.business.id,
            'headline': coupon.offer.headline}
        response = self.client.post(reverse('advertiser-account'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotContains(response, 
            '%s is now displayed.' % coupon.offer.headline)
        self.assertContains(response, 'has_full_family')
        
    def test_turn_on_restricted(self):
        """ Assert an advertiser cannot turn on a coupon he does not own. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        self.login(advertiser)
        post_data = {'ajax_mode': 'turn-display-on',
            'coupon_id': '999', 'business_id': coupon.offer.business.id,
            'headline': coupon.offer.headline}
        response = self.client.post(reverse('advertiser-account'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotContains(response, 
            '%s is now displayed.' % coupon.offer.headline)
        self.assertContains(response, 
            'You are restricted to do anything with this coupon!')
        
    def test_turn_off_display(self):
        """ Assert coupon display can be turned off, and slot_time_frame closes.
        """
        slot, advertiser = self.get_slot_advertiser()
        slot_time_frame = slot.slot_time_frames.all()[0]
        coupon = slot_time_frame.coupon
        self.login(advertiser.email)
        self.assertEqual(slot_time_frame.end_datetime, None)
        post_data = {'ajax_mode': 'turn-display-off',
            'coupon_id': coupon.id, 'display_id': slot.id,
            'headline': coupon.offer.headline}
        response = self.client.post(reverse('advertiser-account'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 
            '%s has been removed.' % coupon.offer.headline)
        updated_time_frame = SlotTimeFrame.objects.get(id=slot_time_frame.id)
        self.assertNotEqual(updated_time_frame.end_datetime, None)
        if updated_time_frame.end_datetime > datetime.datetime.now():
            self.fail('This frame should be closed and is not!')

    def test_turn_off_restricted(self):
        """ Assert an advertiser cannot turn on a coupon he does not own. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        advertiser.is_email_verified = True
        advertiser.save()
        self.login(advertiser)
        post_data = {'ajax_mode': 'turn-display-on',
            'coupon_id': '999', 'display_id': '1',
            'headline': coupon.offer.headline}
        response = self.client.post(reverse('advertiser-account'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertNotContains(response,
            '%s is now displayed.' % coupon.offer.headline)
        self.assertContains(response, 
            'You are restricted to do anything with this coupon!')
  
    def test_auto_renew_on_good(self):
        """ Assert that an advertiser can turn auto-renewal on. """
        slot, advertiser = self.get_slot_advertiser()
        self.login(advertiser.email)
        response = self.client.post(reverse('advertiser-account'),
            {'ajax_mode': 'turn-autorenew-on', 'display_id': str(slot.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'Auto Renew is now ON')
        self.assertTrue(Slot.objects.get(id=slot.id).is_autorenew)
        
    def test_auto_renew_on_bad(self):
        """ Assert that an advertiser cannot turn auto-renewal on for a slot
        she does not own.
        """
        slot, advertiser = self.get_slot_advertiser()
        self.login(advertiser.email)
        another_slot = SLOT_FACTORY.create_slot()
        self.client.post(reverse('advertiser-account'), {
            'ajax_mode': 'turn-autorenew-on',
            'display_id': str(another_slot.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(Slot.objects.get(id=slot.id).is_autorenew)
        self.assertFalse(Slot.objects.get(id=another_slot.id).is_autorenew)

    def test_auto_renew_off_good(self):
        """ Assert that an advertiser can turn auto-renewal off. """
        slot, advertiser = self.get_slot_advertiser()
        self.login(advertiser.email)
        response = self.client.post(reverse('advertiser-account'),
            {'ajax_mode': 'turn-autorenew-off', 'display_id': str(slot.id)},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, 'Auto Renew is now OFF')
        self.assertFalse(Slot.objects.get(id=slot.id).is_autorenew)
        
    def test_json_no_mode(self):
        """ Assert that a advertiser malforming POST to json loads blank data. 
        
        This should not occur naturally, is hostile.
        """
        advertiser = self.get_slot_advertiser()[1]
        self.login(advertiser.email)
        post_data = {'foo': 'crap data'}
        response = self.client.post(reverse('advertiser-account'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response, '{"msg": ""}')

    def test_json_unicode_headline(self):
        """ Assert that unicode in the headline results in fall back text.

        This should not occur naturally, is hostile.
        """
        slot, advertiser = self.get_slot_advertiser()
        self.login(advertiser.email)
        coupon = slot.slot_time_frames.all()[0].coupon
        headline = '99¢'
        post_data = {'ajax_mode': 'turn-display-off',
            'coupon_id': str(coupon.id), 'display_id': str(slot.id),
            'headline': headline}
        response = self.client.post(reverse('advertiser-account'), post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertContains(response,
            '{"msg": "Your coupon has been removed."}')
