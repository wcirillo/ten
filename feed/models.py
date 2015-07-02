""" Models for the Feed app """

import datetime

from django.db import models
from advertiser.models import Advertiser
from coupon.models import Coupon
from django.utils.translation import ugettext_lazy as _

def now_plus_90():
    """ Return this date plus 90 days. """
    return datetime.date.today() + datetime.timedelta(days=90)


class FeedProvider(models.Model):
    """ 
    The feed provider represents each external feed company that will import 
    coupons to out site.
    """
    name = models.CharField(max_length=100, unique=True,
            help_text=_("Company that provides feed to us."))
    feed_url = models.URLField(max_length=255, verify_exists=True, 
        help_text=_("This is a direct web link to the feed file."))
    advertiser = models.ForeignKey(Advertiser, related_name='advertiser', 
        help_text=_("""Feed will use this advertiser site to create coupons. 
        The advertiser should be unemailable."""))
    create_datetime = models.DateTimeField('Created', auto_now_add=True)
    modified_datetime = models.DateTimeField('Last Modified', auto_now=True)

    def __unicode__(self):
        return self.name  


class FeedCoupon(models.Model):
    """ 
    For every provider, each imported feed promo code is uniquely related to 
    only one internal coupon.  
    Each feed provider has many promos.  
    Multiple promos are related to only one feed provider.
    """
    feed_provider = models.ForeignKey(FeedProvider, 
        related_name='feed_coupons')
    external_id = models.CharField(max_length=50, 
        help_text=_("External identifier for this feed coupon."))
    business_name = models.CharField(max_length=100)
    business_url = models.URLField(max_length=255, verify_exists=False,
        null=True, blank=True)
    business_description = models.TextField(max_length=2500, null=True, 
        blank=True)
    offer = models.CharField(max_length=65)
    start_date = models.DateField(default=datetime.date.today,
        db_index=True)
    expiration_date = models.DateField(default=now_plus_90(), db_index=True)
    coupon_url = models.URLField(max_length=255, verify_exists=False,
        null=True, blank=True, help_text=_("""Link to the external web page of 
        this feed coupon."""))
    logo_url = models.URLField(max_length=255, verify_exists=False,
        null=True, blank=True, help_text=_("""Link to this feed coupon business logo."""))
    address1 = models.CharField('Address 1', max_length=100, 
        null=True, blank=True, default="Online Purchases Only")
    address2 = models.CharField('Address 2', max_length=100, 
        null=True, blank=True)
    city = models.CharField('City', max_length=75, null=True, 
        blank=True)
    state_province = models.CharField('State/Province', max_length=2, null=True,
        blank=True)                       
    zip_postal = models.CharField('Zip/Postal', max_length=9, null=True, 
        blank=True)
    custom_restrictions = models.TextField(max_length=400, null=True, 
blank=True)
    create_datetime = models.DateTimeField('Created', auto_now_add=True)
    modified_datetime = models.DateTimeField('Last Modified', auto_now=True)

    def __unicode__(self):
        return u'%s - %s, expires %s' % (self.business_name, self.external_id, 
            self.expiration_date) 


class FeedRelationship(models.Model):
    """ 
    For each provider, each feed coupon has a related local coupon.
    """
    feed_provider = models.ForeignKey(FeedProvider, 
        related_name='feed_relationship') 
    feed_coupon = models.ForeignKey(FeedCoupon, 
        related_name='feed_relationship')
    coupon = models.ForeignKey(Coupon, related_name='feed_relationship')
    create_datetime = models.DateTimeField('Created', 
        auto_now_add=True)
    modified_datetime = models.DateTimeField('Last Modified', 
        auto_now=True)
 
    class Meta:
        """ 
        This model uses a unique key. For each feed provider, each feed 
        coupon can be here once when related to each live coupon.
        """
        unique_together = (('feed_coupon', 'coupon'), 
                           ('feed_coupon', 'feed_provider'),)   

    def __unicode__(self):
        return u'%s: %s related to %s' % (self.feed_coupon.feed_provider, 
            self.feed_coupon.external_id, self.coupon.id)  
