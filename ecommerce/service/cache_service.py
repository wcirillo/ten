""" Service functions for retreiving ecommerce instances from cache. """

from django.core.cache import cache

from ecommerce.models.product_models import Product

def get_product_from_cache(product_id):
    """
    Gets instance from cache, or from ORM and cache it.
    """
    cache_key = 'product-%s' % product_id
    product = cache.get(cache_key)
    if product is None:
        product = Product.objects.get_cache().get(id=product_id)
        product.set_cache()
    return product