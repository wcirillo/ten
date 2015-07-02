""" Tests for add_flyer_views of the ecommerce app. """
import datetime

from django.core.urlresolvers import reverse
from django.template.defaultfilters import date as date_filter

from coupon.models import Slot, FlyerPlacement
from coupon.service.flyer_service import next_flyer_date
from ecommerce.service.calculate_current_price import calculate_current_price
from ecommerce.tests.ecommerce_test_case import EcommerceTestCase
from market.models import Site


class TestAddFlyerDates(EcommerceTestCase):
    """ Test class for add-flyer-dates view. """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_consumer',
        'test_geolocation']
    urls = 'urls_local.urls_2'
        
    def test_get_add_flyer_dates(self):
        """ Assert a logged in advertiser can get to the purchase flyer-by-date
        page with the default checked and previous days in the month not
        checked. """
        self.prep_for_flyer_purchase()
        response = self.client.get(reverse('add-flyer-dates',
            args=[self.slot.id]))
        self.assertContains(response,
            self.advertiser.site.get_or_set_consumer_count())
        self.assertContains(response, 
            'checked="checked" name="%s" value="%s"' %
                (str(date_filter(next_flyer_date(), "F j")),
                str(next_flyer_date())))
        if int(date_filter(next_flyer_date(), "j")) > 7:
            previous_date = next_flyer_date() + datetime.timedelta(days=-7)
            self.assertContains(response,
                'disabled="disabled" type="checkbox" ' +
                'name="%s" value="%s" id="id_%s" /><span class="light">' % (
                (str(date_filter(previous_date, "F j")),
                 str(previous_date),
                 str(date_filter(previous_date, "F j")))))

    def test_post_add_flyer_dates(self):
        """ Assert when a logged in advertiser selects dates from the 
        flyer-by-date page, they get pushed to the ecommerce page with the
        appropriate order items in the order summary display."""
        self.prep_for_flyer_purchase()
        first_purchase_date = next_flyer_date() + datetime.timedelta(days=14)
        second_purchase_date = next_flyer_date() + datetime.timedelta(days=28)
        first_purchase_date_key = date_filter(first_purchase_date, "F j")
        second_purchase_date_key = date_filter(second_purchase_date, "F j")
        kwargs = {
            str(first_purchase_date_key): str(first_purchase_date),
            str(second_purchase_date_key): str(second_purchase_date),
            'subdivision_consumer_count': 100}
        response = self.client.post(reverse('add-flyer-dates',
            args=[self.slot.id]), kwargs, follow=True)
        self.assertTemplateUsed(response,
            'ecommerce/display_checkout_coupon_purchase.html')
        self.common_flyer_purchase_asserts(response, first_purchase_date,
            second_purchase_date)

    def test_sold_market_flyer_date(self):
        """ Assert when the next_flyer_date() is sold out, the user can not
        select the date to purchase flyers on the sold out date.
        """
        count = 1
        while count <= 10:
            slot = Slot(site_id=2, 
                business_id=count,
                renewal_rate=99, 
                is_autorenew=True,
                end_date=datetime.date.today() + datetime.timedelta(
                    days=count))
            slot.save()
            flyer_placement = FlyerPlacement(
                site_id=2, 
                slot=slot, 
                send_date=next_flyer_date())
            flyer_placement.save()
            count += 1
        self.prep_for_flyer_purchase()
        response = self.client.get(reverse('add-flyer-dates',
            args=[self.slot.id]))
        self.assertContains(response, 'disabled="disabled" type="checkbox" ' + 
            'name="%s" value="%s" id="id_%s" /><span class="light">' % (
            (str(date_filter(next_flyer_date(), "F j")), 
            str(next_flyer_date()), 
            str(date_filter(next_flyer_date(), "F j")))))

    def test_with_no_dates_selected(self):
        """ Test Add flyer purchase form submit when no dates selected. """
        kwargs = {'subdivision_consumer_count': 220}
        self.prep_for_flyer_purchase()
        response = self.client.post(reverse('add-flyer-dates',
            args=[self.slot.id]), kwargs)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 
            'include/frm/frm_add_flyer_dates.html')
        self.assertContains(response,
            'You must choose at least one date to send out a flyer')

    def test_post_no_consumer_count(self):
        """ Test Add flyer purchase form submit when subdivision_consumer_count
        hidden field is missing.
        """
        kwargs = {}
        self.prep_for_flyer_purchase()
        response = self.client.post(reverse('add-flyer-dates',
            args=[self.slot.id]), kwargs, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'], 
            '/hudson-valley/contact-us/')
    
    def test_post_bad_consumer_count(self):
        """ Test Add flyer purchase form submit when subdivision_consumer_count
        hidden field has alphanumeric value.
        """
        kwargs = {'subdivision_consumer_count': 'a120'}
        self.prep_for_flyer_purchase()
        response = self.client.post(reverse('add-flyer-dates',
            args=[self.slot.id]), kwargs, follow=True)
        self.assertEqual(response.redirect_chain[0][1], 302)
        self.assertEqual(response.request['PATH_INFO'],
            '/hudson-valley/contact-us/')


class TestAddFlyerByMap(EcommerceTestCase):
    """ Test case for add_flyer_views views. """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_consumer']
    urls = 'urls_local.urls_2'
    
    def test_show_add_flyers(self):
        """ Assert advertiser with valid slot gets good add flyers form. """
        self.prep_for_flyer_purchase()
        response = self.client.get(reverse('add-flyer-by-map', 
            args=[self.slot.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'form id="frm_add_flyer_by_map"')
        self.assertContains(response,
            'Consumers have requested Hudson Valley coupons by email')
        self.assertContains(response, 'Include zip codes within')
        
    def test_process_add_flyers(self):
        """ 
        Assert POST with a valid slot displays the flyers purchase form.
        """
        kwargs = {'zip_array':'1234,12345',
                  'county_array':'',
                  'subdivision_consumer_count':'123'}
        self.prep_for_flyer_purchase()
        response = self.client.post(reverse('add-flyer-by-map', 
            args=[self.slot.id]), kwargs, follow=True)
        self.assertContains(response, 
            'frm_add_flyer_dates')
        
class TestAddFlyerEntireMarket(EcommerceTestCase):
    """ Test case for add_flyer_views views. """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_consumer']   
    urls = 'urls_local.urls_2'
    
    def test_show_add_flyers(self):
        """ Assert advertiser with valid slot gets good add flyers form. """
        self.prep_for_flyer_purchase()
        response = self.client.get(reverse('buy-market-flyer', 
            args=[self.slot.id]), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'frm_add_flyer_dates"')
        key_list = ['add_slot_choice', 'add_flyer_choice', 'flyer_dates_list']
        for key in key_list:
            this_key = self.client.session.get(key, None)
            self.assertEqual(this_key, None)
        subdivision_dict = self.client.session.get('subdivision_dict', None)
        self.assertEqual(self.client.session['locked_flyer_price'],
            calculate_current_price(product_id=1,
                consumer_count=Site.objects.get(
                    id=2).get_or_set_consumer_count()))
        self.assertEqual(self.client.session['locked_consumer_count'],
            Site.objects.get(id=2).get_or_set_consumer_count())
        self.assertEqual(subdivision_dict['county_array'], ())
        self.assertEqual(subdivision_dict['city_array'], ())
        self.assertEqual(subdivision_dict['zip_array'], ())
        self.assertEqual(subdivision_dict['subdivision_consumer_count'],
            Site.objects.get(id=2).get_or_set_consumer_count())
