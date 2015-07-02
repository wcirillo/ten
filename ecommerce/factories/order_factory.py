""" A factory for making order instances for unit testing. """
import datetime

from django.contrib.contenttypes.models import ContentType

from advertiser.models import BillingRecord
from common.utils import random_string_generator
from coupon.factories.slot_factory import SLOT_FACTORY
from ecommerce.models import Order, OrderItem


class OrderFactory(object):
    """ Order Factory class. """

    @staticmethod
    def _create(**kwargs):
        """ Create a single order instance. """
        slot = SLOT_FACTORY.create_slot()
        billing_record = BillingRecord.objects.create(business=slot.business)
        order = Order.objects.create(billing_record=billing_record)
        if not kwargs.get('no_order_item', False):
            OrderItem.objects.create(
                site=slot.site,
                order=order,
                product_id=kwargs.get('product_id', 2),
                item_id=slot.id,
                business=slot.business,
                description=kwargs.get('description', random_string_generator()),
                end_datetime=datetime.datetime.today() + datetime.timedelta(30),
                content_type=ContentType.objects.get(model='slot'),
            )
        if kwargs.get('is_locked', False):
            order.is_locked = True
            order.save()
        return order

    def create_order(self, **kwargs):
        """ Create exactly one order instance. """
        return self._create( **kwargs)

    def create_orders(self, create_count=1, **kwargs):
        """  Create n orders. """
        order_list = []
        while len(order_list) < create_count:
            order_list.append(self._create(**kwargs))
        return order_list

ORDER_FACTORY = OrderFactory()
