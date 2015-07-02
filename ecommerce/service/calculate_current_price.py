""" calculate_current_price service function for ecommerce app """

import logging
from decimal import Decimal

from django.core.cache import cache

from ecommerce.service.cache_service import get_product_from_cache

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

def calculate_current_price(product_id, site=None, consumer_count=None):
    """ Calculate the price for this product on this site.
    Product 1 Flyers: product base rate +
        5cent first 1000, 3cents 1001-10000 and 1cent each over 10000
    Product 2 Monthly Slots Rate =  product base_rate + sites base_rate.
    Product 3 Annual Slots Rate = product base_rate.
    """
    product = get_product_from_cache(product_id)
    if product.id == 1:
        price = float(product.base_rate)
        if consumer_count > 10000:
            price += (consumer_count - 10000) * .01
            consumer_count = 10000
        if consumer_count > 1000:
            price += (consumer_count - 1000) * .03
            consumer_count = 1000
        price += consumer_count * .05
        price = Decimal(str(price))
        LOG.debug('Current price of %s with %s consumers is %s' % (
            product, str(consumer_count), price))
    elif product.id == 2:
        price = product.base_rate + site.base_rate
        LOG.debug('Current price of %s is %s' % (product, price))
    elif product.id == 3:
        price = product.base_rate
        LOG.debug('Current price of %s is %s' % (product, price))
    return price

def get_product_price(product_id, site):
    """ Get price of product given this site. If not in cache, call set and
    return. Cache-key is cleared when Site or Product is saved.
    """
    product_price_cache = cache.get(
        "product-%s-price" % (product_id))
    if not product_price_cache:
        product_price_cache = set_product_price(product_id, site)
    return product_price_cache

def set_product_price(product_id, site):
    """ Set this product price given this site in cache. Return price. """
    cache_key = "product-%s-price" % (product_id)
    product_price = calculate_current_price(product_id, site)
    cache.set(cache_key, product_price)
    return product_price     