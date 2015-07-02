""" Product models for ecommerce app """
#pylint: disable=W0613
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import class_prepared
from django.utils.translation import ugettext_lazy as _

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class ProductManager(models.Manager):
    """ Default manager for Product class. """

    def cacheable_products(self):
        """ Return the Product QuerySet relevant for caching. """
        return self.filter(is_active=True)

    def set_cache(self):
        """ Set the Product object cache. """
        product_cache = self.cacheable_products()
        cache.set('product_cache', product_cache)
        for product in product_cache:
            product.set_cache()
        return product_cache

    def get_cache(self):
        """ Return the Site object cache (or it's equivalent for a dummy cache).
        """
        product_cache = cache.get('product_cache')
        if product_cache == None:
            product_cache = self.set_cache()
        return product_cache

    def clear_cache(cls):
        """ Clears the Product object cache and the cached pricing """
        cache.delete_many(['product_cache', 'product-1-price', 
            'product-2-price', 'product-3-price', 'product-1', 'product-2',
            'product-3'])
        
        # Clear the Product object cache.
        cache.delete('product_cache')
    clear_cache = classmethod(clear_cache)


class Product(models.Model):
    """ Something for purchase. """
    name = models.CharField(max_length=48, unique=True)
    is_active = models.BooleanField(default=False)
    base_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    base_units = models.DecimalField(max_digits=8, decimal_places=0, default=0)
    base_days = models.PositiveSmallIntegerField(default=0)
    content_type = models.ForeignKey(ContentType)
    objects = ProductManager()
    
    class Meta:
        app_label = 'ecommerce'
        ordering = ('id',)
        verbose_name = _("Product")
        verbose_name_plural = _("Products")
    
    def __unicode__(self):
        return u'%s' % self.name
        
    def save(self, *args, **kwargs):
        Product.objects.clear_cache()
        super(Product, self).save(*args, **kwargs)
        
    def delete(self, *args, **kwargs):
        if self.order_items.count():
            error_message = 'Cannot delete a product that has been ordered'
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(_(error_message))
        Product.objects.clear_cache()
        super(Product, self).delete(*args, **kwargs)
        
    def set_cache(self):
        """ Set the instance into cache. """
        cache_key = "product-%s" % self.id
        cache.set(cache_key, self)

def product_class_prepared(sender, *args, **kwargs):
    """ Send class_prepared signal for setting product_cache after model is
    registered.
    """
    Product.objects.set_cache()
class_prepared.connect(product_class_prepared, sender=Product)