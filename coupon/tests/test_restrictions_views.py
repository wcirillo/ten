""" This is a test module for coupon view testing. """
import logging

from django.core.urlresolvers import reverse
from django.test.client import RequestFactory

from common.session import build_advertiser_session
from common.test_utils import EnhancedTestCase
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.models.coupon_models import DefaultRestrictions
from coupon.service.single_coupon_service import SINGLE_COUPON
from coupon.tests.test_cases import ValidDaysTestCase
from coupon.views.restrictions_views import process_create_restrictions
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def set_valid_all_days(coupon):
    """ Set all valid days to 'True' """
    coupon.is_valid_monday = True
    coupon.is_valid_tuesday = True
    coupon.is_valid_wednesday = True
    coupon.is_valid_thursday = True
    coupon.is_valid_friday = True
    coupon.is_valid_saturday = True
    coupon.is_valid_sunday = True


class TestCouponRestrictions(EnhancedTestCase):
    """ This class contains display and creation tests for coupon restriction 
    configurations handled by views: show_create_restrictions and 
    process_create_restrictions.
    """
    urls = 'urls_local.urls_2'
    
    def test_display_with_no_offer(self):
        """ Test show_create_restrictions view for redirect on key error when 
        missing current offer (in session/request).
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        coupon.offer.delete()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.post(reverse('create-restrictions'), follow=True) 
        # Redirected to home by default.
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/')
        
    def test_display_no_coupon(self):
        """ Test show_create_restrictions for redirect on key error when 
        missing coupon in offer (in session/request).
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        coupon.delete()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('create-restrictions'), follow=True) 
        # Redirected to home by default.
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/')
        
    def test_show_form_success(self):
        """ Test show create restrictions process for success. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('create-restrictions'))
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/restrictions/')
        self.assertContains(response, "frm_create_restrictions")
        self.assertContains(response, "$199/month")
    
    def test_fail_create_bad_coupon_id(self):
        """ Test post of coupon restrictions with invalid coupon in 
        context_instance.
        """
        factory = RequestFactory()
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        # Mimic coupon not in database yet, change coupon_id to something new to
        # spoof.
        self.session['consumer']['advertiser']['business']\
            [self.session['current_business']]['offer']\
            [self.session['current_offer']]['coupon']\
            [self.session['current_coupon']]['coupon_id'] = 599
        self.assemble_session(self.session)       
        request = factory.post(reverse('create-restrictions'),
            data={"is_redeemed_by_sms":1, "default_restrictions":[2, 3]})
        created_redirect = reverse('preview-coupon')
        required_fields_not_filled_out = \
            "coupon/display_create_restrictions.html"
        context_instance = {
            'js_create_restrictions':1,
            'business_name' : self.session['consumer']['advertiser'] \
                ['business'][self.session['current_business']]['business_name'],
            'slogan' : self.session['consumer']['advertiser']['business'] \
                [self.session['current_business']]['slogan'],
            'headline' : self.session['consumer']['advertiser'] \
                ['business'][self.session['current_business']]['offer'] \
                    [self.session['current_offer']]['headline'],
            'qualifier' : self.session['consumer']['advertiser'] \
                ['business'][self.session['current_business']]['offer'] \
                    [self.session['current_offer']]['qualifier']}
        request.session = self.session
        response = process_create_restrictions(request, created_redirect, 
            required_fields_not_filled_out, context_instance)
        # Redirected home.
        self.assertEqual(str(response['location']), '/hudson-valley/coupons/')
        
    def test_fail_create_missing_fields(self):
        """ Test process_create_restrictions from form submission missing
        required fields forcing the view to reload current form 
        selections/inputs.
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Default restriction_0 = one coupon per person per visit.
        response = self.client.post(reverse('create-restrictions'), 
            data={"default_restrictions" : [2, 3]}) 
        # Check to ensure previous selections still loaded.
        self.assertContains(response, 
            '"checked" type="checkbox" name="default_restrictions" value="2"')
        self.assertContains(response, 
            '"checked" type="checkbox" name="default_restrictions" value="3"')
        self.assertContains(response, 
            '<input type="checkbox" name="default_restrictions" value="4"')
        self.assertContains(response, 
            '<input type="checkbox" name="default_restrictions" value="5"')
        self.assertContains(response, 
            '<input type="checkbox" name="default_restrictions" value="6"')
        self.assertContains(response, 
            '<input type="checkbox" name="default_restrictions" value="7"')
        self.assertContains(response, 
            '<input type="checkbox" name="default_restrictions" value="1"')

        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/restrictions/')
    
    def test_create_success_no_custom(self):
        """ Test show_create_restrictions view with posted form submission so it
        will save the coupon restrictions to the database. Custom_restrictions 
        aresubmitted in the form blank and should not be recorded with 
        default_restrictions.
        Assert that when no ad rep is in session the product_list is populated
        with monthly pricing option.
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Default restriction_0 = one coupon per person per visit.
        response = self.client.post(reverse('create-restrictions'), 
            data={"is_redeemed_by_sms" : 1,
                  "default_restrictions" : [2, 3, 5, 7],
                  "custom_restrictions" : ""}, 
            follow=True) 
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.default_restrictions.all().count(), 4, 
            "Default restrictions supplied for coupon interpreted incorrectly")
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, 'frm_checkout_coupon_purchase')
        # Validate selections made are displayed as checked in preview.
        all_restrictions = DefaultRestrictions.objects.all()
        self.assertNotContains(response, all_restrictions.get(id=1).restriction)
        self.assertContains(response, all_restrictions.get(id=2).restriction)
        self.assertContains(response, all_restrictions.get(id=3).restriction)
        self.assertNotContains(response, all_restrictions.get(id=4).restriction)
        self.assertContains(response, all_restrictions.get(id=5).restriction)
        self.assertNotContains(response, all_restrictions.get(id=6).restriction)
        self.assertContains(response, all_restrictions.get(id=7).restriction)
        self.assertEqual(self.client.session['product_list'][0][0], 2)

    def test_post_set_annual_price(self):
        """ Assert that when an ad rep is in session, we default the slot
        pricing to monthly slot price.
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        build_advertiser_session(self, advertiser)
        self.session['ad_rep_id'] = ad_rep.id
        self.assemble_session(self.session)
        response = self.client.post(reverse('create-restrictions'), 
            data={"is_redeemed_by_sms" : 1, "default_restrictions" : [2],
                  "custom_restrictions" : ""}, follow=True)
        self.assertEqual(str(response.request['PATH_INFO']), 
            '/hudson-valley/create-coupon/checkout/')
        self.assertEqual(self.client.session['product_list'][0][0], 2)

    def test_create_success_w_custom(self):
        """ Test show_create_restrictions form submission, saves coupon 
        restrictions to database. Includes custom restrictions but still should 
        not be listed with default_restrictions in the database (value 1). Added 
        assertion that custom restriction does not exceed max length (currently 
        1500 char).
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.post(reverse('create-restrictions'), 
            data={"is_redeemed_by_sms":1,
                  "default_restrictions":[u'2', u'3', u'1'],
                  "custom_restrictions":[repr(u'Must be UK citizen. We\u2019ll \
                  give you a detailed report. \r\n Pennivisions \u2122. aaaaa 0\
                  aaaaa00011111111111111 222222222 2222222 22223333 3333aaaaa 3\
                  3333334444444444444 4444444555555555 555555555556666 6aaaaa0\
                  0 0000000 00000 0000 001111111 111111111 1 111222 222aaaaa2\
                  2 22222 2 2 3 33333 3333 3 3333 33 3 3 34444444 4444 4 4 4 44\
                  44aaaaa555 55555 555555 555666 666666 666666 6666777 7777777\
                  7 aaaaa7 7778888888 888888 888aaaaa22222222222233333333333333\
                  333333444444444444444444 445aaaaa 5 5 5 5aaaaa555556 6 66666\
                  6 6 6 666666666677777 77777777777 7 7 778888aaaaa88 8 8888 88\
                  8899 9 9 999999 9 999999999 .  000aaaaa 0 000 00  0 00000111\
                  1 1 11111111111 1 111222 2 2222 2 2aaaaa22222 333333333 3 3 3\
                  333333 33444 4444 4444 4 444444 445 555555 55 aaaaa 5 555556\
                  6 6 6666666 6 666666 6 66777 7 7 77 7 77aaaaa77777888 88 8 88\
                  888888888 8 8899999999 9 999999999 9 9. 0000aaaaa0000000 0000\
                  1111 1111111 11111111222 22222222222222222333333 333aaaaa3333\
                  3344444444444444444444555 555 55555 55555555566 6aaaaa 6666\
                  6 666677 7777777 7777777777 78899 999999. 00000000000000 0000\
                  aaaaa 111111111 11111111222 22222222222 222222333333333333333\
                  33333aaaaa 44444444444444455555555555555555555666 66666666666\
                  666 66677aaaaa 7777777777 777888888888 8888888888899994444444\
                  44444 44444444555555aaaaa5555555566 66666666666666 666677777\
                  7 777777777777778888 888 8aaaaa8888888999999999 9999999999\
                  9. 00000000 00000 00111111a 343478 aaaa1111 1122222222 222222\
                  3aaaaa333 33333333333 444. This is the one-thousand five-hund\
                  redth marker here. XYZXY!')]},
            follow=True) 
        coupon = SINGLE_COUPON.get_coupon(self)
        self.assertEqual(coupon.default_restrictions.all().count(), 2, 
            "Default restrictions supplied for coupon interpreted incorrectly")
        if "Must be UK citizen" not in coupon.custom_restrictions:
            self.fail("Test custom restriction was not created successfully.")
        if "XYZXY" in coupon.custom_restrictions:
            self.fail("Custom restriction exceeds maximum length")
        self.assertEqual(str(response.request['PATH_INFO']),
            '/hudson-valley/create-coupon/checkout/')
        self.assertContains(response, 'frm_checkout_coupon_purchase')
        # Validate selections made are displayed as checked in preview.
        self.assertNotContains(response,
            DefaultRestrictions.objects.get(id=1).restriction)
        self.assertContains(response,
            DefaultRestrictions.objects.get(id=2).restriction)
        self.assertContains(response,
            DefaultRestrictions.objects.get(id=3).restriction)
        self.assertNotContains(response,
            DefaultRestrictions.objects.get(id=4).restriction)
        self.assertNotContains(response,
            DefaultRestrictions.objects.get(id=5).restriction)
        self.assertNotContains(response,
            DefaultRestrictions.objects.get(id=6).restriction)
        self.assertNotContains(response,
            DefaultRestrictions.objects.get(id=7).restriction)
        self.assertContains(response, "Must be UK citizen")


class TestValidDays(ValidDaysTestCase):
    """ Test that the Valid Days are handled correctly. """
    urls = 'urls_local.urls_2'

    @staticmethod
    def set_all_days_false(coupon):
        """ Set all days false for this coupon. """
        for attr in ['is_valid_monday', 'is_valid_tuesday',
            'is_valid_wednesday', 'is_valid_thursday', 'is_valid_friday',
            'is_valid_saturday', 'is_valid_sunday']:
            setattr(coupon, attr, False)
    
    def test_valid_days_on_get(self):
        """ Assert all days are selected and form is correct. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        coupon.is_valid_monday = True
        coupon.is_valid_tuesday = True
        coupon.is_valid_wednesday = True
        coupon.is_valid_thursday = True
        coupon.is_valid_friday = True
        coupon.is_valid_saturday = True
        coupon.is_valid_sunday = True
        coupon.save()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.client.get(reverse('create-restrictions'))
        self.assertContains(response,
            'id="id_is_valid_monday" checked="checked"')
        self.assertContains(response,
            'id="id_is_valid_tuesday" checked="checked"')
        self.assertContains(response,
            'id="id_is_valid_wednesday" checked="checked"')
        self.assertContains(response,
            'id="id_is_valid_thursday" checked="checked"')
        self.assertContains(response,
            'id="id_is_valid_friday" checked="checked"')
        self.assertContains(response,
            'id="id_is_valid_saturday" checked="checked"')
        self.assertContains(response,
            'id="id_is_valid_sunday" checked="checked"')
        self.assertContains(response, "Offer good 7 days a week.")
         
    def test_all_valid_days(self):
        """ Assert valid_days_post_response for all seven days. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        coupon.is_valid_monday = True
        coupon.is_valid_tuesday = True
        coupon.is_valid_wednesday = True
        coupon.is_valid_thursday = True
        coupon.is_valid_friday = True
        coupon.is_valid_saturday = True
        coupon.is_valid_sunday = True
        coupon.save()
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer good 7 days a week.")
        self.assertContains(response, 'frm_checkout_coupon_purchase')
        
    def test_valid_monday(self):  
        """ Assert valid_days_post_response when only on Monday is posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        coupon.is_valid_sunday = True
        coupon.save()
        self.assemble_session(self.session)
        # Check Monday only.
        self.set_all_days_false(coupon)
        coupon.is_valid_monday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Monday only.")
         
    def test_valid_tuesday(self):  
        """ Assert valid_days_post_response when only on Tuesday is posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Tuesday only.
        self.set_all_days_false(coupon)
        coupon.is_valid_tuesday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Tuesday only.")
          
    def test_valid_wednesday(self):  
        """ Assert valid_days_post_response when only on Wednesday is posted."""
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Wednesday only.
        self.set_all_days_false(coupon)
        coupon.is_valid_wednesday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Wednesday only.")

    def test_valid_thursday(self):  
        """ Assert valid_days_post_response when only on Thursday is posted."""
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
         # Check Thursday only.
        self.set_all_days_false(coupon)
        coupon.is_valid_thursday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Thursday only.")

    def test_valid_friday(self):  
        """ Assert valid_days_post_response when only on Friday is posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Friday only.
        self.set_all_days_false(coupon)
        coupon.is_valid_friday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Friday only.")

    def test_valid_saturday(self):  
        """ Assert valid_days_post_response when only on Saturday is posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Saturday only.
        self.set_all_days_false(coupon)
        coupon.is_valid_saturday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Saturday only.")

    def test_valid_sunday(self):  
        """ Assert valid_days_post_response when only on Sunday is posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Sunday only.
        self.set_all_days_false(coupon)
        coupon.is_valid_sunday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Sunday only.")
        self.assertContains(response, 'frm_checkout_coupon_purchase')
        
    def test_valid_mon_tues(self):
        """ Assert valid_days_post_response for Monday and Tuesday only."""
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Monday & Tuesday.
        self.set_all_days_false(coupon)
        coupon.is_valid_monday = True
        coupon.is_valid_tuesday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer valid Monday and Tuesday only.")
    
    def test_valid_fri_sat(self):
        """ Assert valid_days_post_response for Friday and Saturday only. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Friday & Saturday.
        self.set_all_days_false(coupon)
        coupon.is_valid_friday = True
        coupon.is_valid_saturday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer good Friday and Saturday only.")
    
    def test_valid_sat_sun(self):
        """ Assert valid_days_post_response for Saturday and Sunday only. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Saturday & Sunday.
        self.set_all_days_false(coupon)
        coupon.is_valid_saturday = True
        coupon.is_valid_sunday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer good Saturday and Sunday only.")
        
    def test_valid_3_days(self):  
        """ Assert valid_days_post_response when 3 valid days are posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Monday & Wednesday & Friday.
        set_valid_all_days(coupon)
        coupon.is_valid_tuesday = False
        coupon.is_valid_thursday = False
        coupon.is_valid_saturday = False
        coupon.is_valid_sunday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response,
            "Offer valid Monday, Wednesday and Friday only.")
        # Check Friday & Saturday & Sunday.
        coupon.is_valid_monday = False
        coupon.is_valid_wednesday = False
        coupon.is_valid_saturday = True
        coupon.is_valid_sunday = True
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response,
            "Offer good Friday, Saturday and Sunday only.")

    def test_valid_4_days(self):  
        """ MAssert valid_days_post_response when 4 valid days are posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Monday & Wednesday & Friday & Saturday.
        set_valid_all_days(coupon)
        coupon.is_valid_tuesday = False
        coupon.is_valid_thursday = False
        coupon.is_valid_sunday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response,
            "Offer valid Monday, Wednesday, Friday and Saturday only.")
        # Check Monday - Thursday.
        coupon.is_valid_tuesday = True
        coupon.is_valid_thursday = True
        coupon.is_valid_friday = False
        coupon.is_valid_saturday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response,
            "Offer good Monday - Thursday only.")
        
    def test_valid_5_days(self):  
        """ Assert valid_days_post_response when 5 valid days are posted. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        # Check Monday - Friday.
        set_valid_all_days(coupon)
        coupon.is_valid_saturday = False
        coupon.is_valid_sunday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer good Monday - Friday only.")
        # Check Monday & Tuesday & Friday & Saturday & Sunday.
        set_valid_all_days(coupon)
        coupon.is_valid_wednesday = False
        coupon.is_valid_thursday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response,
            "Offer valid Monday, Tuesday, Friday, Saturday and Sunday only.")
        
    def test_not_valid_mondays(self):  
        """ Assert valid_days_post_response for offer not valid Monday. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        set_valid_all_days(coupon)
        # Check Not Valid Monday.
        coupon.is_valid_monday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer not valid Mondays.")
         
    def test_not_valid_tuesdays(self):  
        """ Make sure the correct message is displayed on the next page when 
        offer not valid Tuesday.
        """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        set_valid_all_days(coupon)
        # Check not valid Tuesday
        coupon.is_valid_tuesday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer not valid Tuesdays.")
         
    def test_not_valid_wednesdays(self):  
        """ Assert valid_days_post_response when offer not valid Wednesday. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        set_valid_all_days(coupon)
        # Check not valid Wednesday.
        coupon.is_valid_wednesday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer not valid Wednesdays.")
         
    def test_not_valid_thursdays(self):  
        """ MAssert valid_days_post_response when offer not valid Thursday. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        set_valid_all_days(coupon)
        # Check not valid Thursday.
        coupon.is_valid_thursday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer not valid Thursdays.")
         
    def test_not_valid_fridays(self):  
        """ Assert valid_days_post_response when offer not valid Friday. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        set_valid_all_days(coupon)
        # Check not valid Friday.
        coupon.is_valid_friday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer not valid Fridays.")
         
    def test_not_valid_saturdays(self):  
        """ Assert valid_days_post_response when offer not valid Saturday. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        set_valid_all_days(coupon)
        # Check not valid Saturday.
        coupon.is_valid_saturday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer not valid Saturdays.")
         
    def test_not_valid_sundays(self):  
        """ Assert valid_days_post_response when offer not valid Sunday. """
        coupon = COUPON_FACTORY.create_coupon()
        advertiser = coupon.offer.business.advertiser
        build_advertiser_session(self, advertiser)
        self.assemble_session(self.session)
        set_valid_all_days(coupon)
        # Check not valid Sunday.
        coupon.is_valid_sunday = False
        response = self.valid_days_post_response('create-restrictions', coupon) 
        self.assertContains(response, "Offer good Monday - Saturday only.")
        self.assertContains(response, 'frm_checkout_coupon_purchase')
