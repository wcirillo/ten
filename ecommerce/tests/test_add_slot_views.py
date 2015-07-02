""" Tests for add_slot_views of the ecommerce app. """

import datetime
import logging
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse

from common.test_utils import EnhancedTestCase
from coupon.models import Slot
from ecommerce.service.calculate_current_price import get_product_price
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class TestAddNewDisplay(EnhancedTestCase):
    """ Test case for add_slot_views views. """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_consumer']   
    urls = 'urls_local.urls_2'
    
    def test_show_add_a_new_display(self):
        """ 
        Assert request with a valid coupon displays the add slot form.
        """
        kwargs = {'email':'will+addnew@10coupons.com',
                'consumer_zip_postal':'10990',
                'business_name':'add new',
                'short_business_name':'add new',
                'headline':'add new'}
        advertiser = self.make_advrt_with_coupon(**kwargs)
        # This page expects to follow advertiser account page, which locks
        # flyer cost etc.
        coupon_id = advertiser.businesses.all(
            )[0].offers.all()[0].coupons.all()[0].id
        self.login_build_set_assemble(advertiser)
        response = self.client.get(reverse('add-a-new-display', args=[coupon_id]))
        LOG.debug('test_show_add_a_new_display response: %s' % response)
        self.assertContains(response, 'form name="frm_add_slot"')
        self.assertContains(response, 'function submitAddSlot()')
        slot_price = get_product_price(2, advertiser.site)
        self.assertContains(response, slot_price)
        
    def test_process_add_new_display(self):
        """ 
        Assert POST with a valid coupon displays the slot purchase form.
        """
        kwargs = {'email':'will+processaddnew@10coupons.com',
                'consumer_zip_postal':'10990',
                'business_name':'process add new',
                'short_business_name':'process add new',
                'headline':'process add new'}
        advertiser = self.make_advrt_with_coupon(**kwargs)
        self.login_build_set_assemble(advertiser)
        coupon_id = advertiser.businesses.all(
            )[0].offers.all()[0].coupons.all()[0].id
        post_data = {'add_slot_choices': '1'}
        response = self.client.post(reverse('add-a-new-display', args=[coupon_id]), 
            post_data, follow=True)
        self.assertContains(response, 
            'form name="frm_checkout_coupon_purchase"')
        self.assertContains(response, 'Monthly 10Coupon Publishing Plan')
        site = Site.objects.get(id=2)
        slot_price = get_product_price(2, site)
        self.assertContains(response, '$%s' % slot_price)
        self.assertContains(response, 'Total')
        self.assertContains(response, '$%s' % str(Decimal(slot_price)))
        
    def test_add_display_bad_session(self):
        """ 
        Assert logged in advertiser with an incomplete session redirects to the 
        home page.
        """
        kwargs = {'email':'will+badaddnew@10coupons.com',
                'consumer_zip_postal':'10990',
                'business_name':'bad add new',
                'short_business_name':'bad add new',
                'headline':'bad add new'}
        advertiser = self.make_advrt_with_coupon(**kwargs)
        self.login(advertiser.email)
        coupon_id = advertiser.businesses.all(
            )[0].offers.all()[0].coupons.all()[0].id
        response = self.client.get(reverse('add-a-new-display', args=[coupon_id]),
            follow=True)
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % 
            (settings.HTTP_PROTOCOL_HOST, reverse('all-coupons')))
        self.assertEqual(response.redirect_chain[0][1], 302)
        
class TestAddNewDisplayOpenSlots(EnhancedTestCase):
    """ 
    Test case for add_slot_views views for an advertiser with current open 
    slots. 
    """
    
    fixtures = ['test_advertiser', 'test_coupon', 'test_ecommerce', 'test_slot']   
    urls = 'urls_local.urls_2'
    
    def test_add_display_slotted_coupon(self):
        """ 
        Assert requesting to add a slot for an advertiser with open slots 
        redirects to the advertiser account.
        """
        kwargs = {'email':'will+openaddnew@10coupons.com',
                'consumer_zip_postal':'10990',
                'business_name':'open add new',
                'short_business_name':'open add new',
                'headline':'open add new'}
        advertiser = self.make_advrt_with_coupon(**kwargs)
        future_date = datetime.date.today() + datetime.timedelta(3)
        coupon = advertiser.businesses.all(
            )[0].offers.all()[0].coupons.all()[0]
        slot = Slot.objects.create(site_id=2, business=coupon.offer.business,
            end_date=future_date)
        slot.save()
        self.login_build_set_assemble(advertiser)
        # This page expects to follow advertiser account page, which locks
        # flyer cost etc *and* sets request.user.is_athenticated = True.
        self.client.get(reverse('advertiser-account'))
        response = self.client.get(reverse('add-a-new-display', args=[coupon.id]),
            follow=True)
        self.assertEqual(response.redirect_chain[0][0], '%s%s' % 
            (settings.HTTP_PROTOCOL_HOST, reverse('advertiser-account')))
        self.assertEqual(response.redirect_chain[0][1], 302)

