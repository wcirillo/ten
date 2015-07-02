""" Tests service functions for media_partner app """
from decimal import Decimal

from django.test import TestCase

from ecommerce.factories.order_factory import ORDER_FACTORY
from ecommerce.models import Order, Payment
from market.models import Site
from media_partner.service import (get_site_active_media_mediums, get_subtotal,
    has_medium_partnered)


class TestService(TestCase):
    """ Test all the services in the media_partner app. """
    fixtures = ['test_media_partner']
    
    def test_site_active_media_mediums(self):
        """ Assert actively advertised mediums in a given market returned. """
        testHV = get_site_active_media_mediums(2)
        self.assertEqual(testHV, 'radio') # Hudson Valley has 2 radio affliates.
        testNJ = get_site_active_media_mediums(28)
        self.assertEqual(testNJ, '') #North Jersey has no pie shares configured.
        
    def test_has_medium_partnered(self):
        """ Assert that if a site has specific medium partnered,
        has_medium_partnered service function reports that. 
        """
        # Hudson Valley only partnered with radio.
        self.assertTrue(not has_medium_partnered(['newspaper'], 2))
        self.assertTrue(has_medium_partnered(['newspaper', 'radio'], 2))
        # North Jersey is not partnered with any media.
        self.assertTrue(not has_medium_partnered(
            ['newspaper', 'cable', 'radio'], 28))


class TestGetSubtotal(TestCase):
    """ TestCase for the service function get_subtotal. """

    def test_get_subtotal_less_cut(self):
        """ Assert an order displays net of promoter cut. """
        order = ORDER_FACTORY.create_order()
        payment = Payment.objects.create(order=order,
            amount=Decimal('199'))
        site = Site.objects.get(id=2)
        before_subtotal = get_subtotal(payment, site)
        self.assertEqual(order.promoter_cut_amount, Decimal('0.00'))
        order.promotion_code_id = 99
        order.save()
        order_after = Order.objects.get(id=order.id)
        self.assertTrue(order_after.promoter_cut_amount > 0)
        # Fresh payment
        payment = Payment.objects.get(id=payment.id)
        after_subtotal = get_subtotal(payment, site)
        self.assertTrue(float(before_subtotal) > float(after_subtotal))
        self.assertEqual(float(after_subtotal),
            float(before_subtotal) - float(order.promoter_cut_amount))
