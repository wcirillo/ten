""" Test case for common utils. """

import datetime

from django.test import TestCase

from common.utils import build_fb_like_meta, random_code_generator, \
    replace_problem_ascii, is_gmtime_recent, parse_phone
from advertiser.models import BusinessProfileDescription
from coupon.models import Coupon
from market.models import Site

class TestFacebookMetaBuilder(TestCase):
    """ Test the function that builds facebook meta used by 'like buttons'. """
    fixtures = ['test_advertiser', 'test_coupon']
    def test_fb_meta_w_coupon(self):
        """ 
        Test build_fb_like_meta function with coupon supplied and no 
        business profile.
        """
        coupon = Coupon.objects.get(id=300)
        fb_meta_dict = build_fb_like_meta(coupon.offer.business.advertiser.site,
             coupon)
        self.assertEqual(fb_meta_dict['ref'], coupon.id)
        self.assertTrue(coupon.offer.headline in fb_meta_dict['title'])
        self.assertTrue('Get this coupon!' in fb_meta_dict['title'])
        self.assertTrue(coupon.offer.business.advertiser.site.domain
            in fb_meta_dict['title'])
        self.assertTrue(str(coupon.expiration_date) 
            in fb_meta_dict['description'])
        self.assertTrue(coupon.offer.qualifier in fb_meta_dict['description'])

    def test_fb_meta_w_biz_profile(self):
        """ 
        Test build_fb_like_meta function with coupon supplied and business 
        profile.
        """
        profile = BusinessProfileDescription()
        profile.business_id = 114
        profile.business_description = "Amet consequat gravida neque " + \
        "convallis bibendum tincidunt, phasellus class phasellus nullam " + \
        "duis  nunc, est nunc massa, aliquam feugiat lacus sit vestibulum " + \
        "sapien, libero ut. Convallis per id eu orci, nunc absolem pordu vo" + \
        "shavus aqualabro fellum."
        profile.save()
        coupon = Coupon.objects.get(id=300)
        fb_meta_dict = build_fb_like_meta(coupon.offer.business.advertiser.site,
             coupon)
        self.assertEqual(fb_meta_dict['ref'], 300)
        self.assertTrue(profile.business_description[:200] \
            in fb_meta_dict['description'])
        self.assertTrue(coupon.offer.business.business_name \
            in fb_meta_dict['description'])
        
    def test_fb_meta_no_coupon(self):
        """
        Test build_fb_like_meta function when defaulted due to no coupon.
        """
        site = Site.objects.get(id=2)
        fb_meta_dict = build_fb_like_meta(site)
        self.assertEqual(fb_meta_dict['ref'], site.domain)
        self.assertTrue('Save money at the best' in fb_meta_dict['description'])
        self.assertTrue('get started today!' in fb_meta_dict['description'])
        self.assertEqual('Sign up for Hudson Valley Coupons.', 
            fb_meta_dict['title'])
        
class TestUtils(TestCase):
    """ Tests for common utils of project ten. """
    
    def test_random_code_generator(self):
        """ Tests the random code generator. """
        # Produces similar to '8FHGNH'
        code = random_code_generator()
        self.assertEquals(len(code), 6)
        code_2 = random_code_generator()
        if code == code_2:
            self.assertEquals(False)
        # Produces similar to 'CFB-U8X-9KE-TY8':
        code_3 = random_code_generator(12, 4, '-')
        self.assertEquals(len(code_3), 15)
        self.assertEquals(len(code_3.replace('-', '')), 12)
        code_4 = random_code_generator(100, banned_chars='X')
        self.assertEquals(code_4.find('X'), -1)
    
    def test_replace_problem_ascii(self):
        """ Test the replace_problem_ascii service method. """
        test_string = 'We' + u'\u2019' + ' help with your testing \
        efforts. Our company is the best for that, 10Coupons ' + u'\u2122' + '.'
        result_string = replace_problem_ascii(test_string)
        if "u2122" in result_string:
            self.fail("Unicode character not replaced.")
        if "u2019" in result_string:
            self.fail("Unicode character not replaced.")
        if "(tm)" not in result_string:
            self.fail("Replacement of unicode character unsuccessful.")
        test_string2 = "This is a purely ascii string."
        result_string2 = replace_problem_ascii(test_string2)
        self.assertEqual(test_string2, result_string2)
  
    def test_is_gmtime_recent(self):
        """ Test gmtime to local date time difference function. """
        now = datetime.datetime.now()
        # test that now is more recent than gmtime
        self.assertFalse(is_gmtime_recent("2011-06-05 17:03:21", 
            now))
        future = now + datetime.timedelta(hours=7)
        datetime_format = '%Y-%m-%d %H:%M:%S'
        future_format = future.strftime(datetime_format)
        # test that gmtime is more recent than now
        self.assertTrue(is_gmtime_recent(future_format, now))
    
    def test_parse_phone(self):
        """ Test that correct phone fields are returned. """
        phone_dict = parse_phone('800-555-1234')
        self.assertTrue(str(phone_dict), 
            "{'area_code': '800', 'exchange': '555', 'number': '1234'}")