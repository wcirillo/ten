""" Action models of the coupon app """
import datetime
import logging

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from coupon.models.coupon_models import Coupon

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class Action(models.Model):
    """
    All of the actions that can be done with a coupon, such as viewing it
    and printing it, for tracking and reporting.
    """
    name = models.CharField(max_length=20)
    
    class Meta:
        app_label = 'coupon'
        
    def __unicode__(self):
        return u'%s' % self.name
    
    def delete(self):
        raise ValidationError('Cannot delete an action.')


class CouponAction(models.Model):
    """
    How many times has an action been performed on a specific coupon (by
    Consumers or anonymous users).
    """
    action = models.ForeignKey(Action, related_name='coupon_actions')
    coupon = models.ForeignKey(Coupon, related_name='coupon_actions')
    count = models.IntegerField(default=0)
    
    class Meta:
        app_label = 'coupon'
        ordering = ['action']
        unique_together = (("action","coupon"),)
        
    def __unicode__(self):
        return u'%s %s' % (self.coupon, self.action.name)
    
    def increment_count(self):
        """ Increment count of this action for this coupon. """
        self.count = F('count') + 1
        self.save()


class ConsumerAction(models.Model):
    """
    Records a specific action by a specific consumer on a specific coupon.
    """    
    action = models.ForeignKey(Action, related_name='consumer_actions')
    coupon = models.ForeignKey(Coupon, 
        related_name='consumer_actions')
    consumer = models.ForeignKey('consumer.Consumer', 
        related_name='consumer_actions')
    create_datetime = models.DateTimeField(_('date/time created'), 
        auto_now_add=True)
 
    class Meta:
        app_label = 'coupon'
    
    def __unicode__(self):
        return u'%s %s %s' % (self.consumer, self.action.name, self.coupon)


class SubscriberAction(models.Model):
    """
    Records a specific action for a specific subscriber for a specific coupon.
    """    
    action = models.ForeignKey(Action, related_name='subscriber_actions')
    coupon = models.ForeignKey(Coupon, related_name='subscriber_actions')
    subscriber = models.ForeignKey('subscriber.Subscriber', 
        related_name='subscriber_actions')
    create_datetime = models.DateTimeField(_('date/time created'), 
        auto_now_add=True)
 
    class Meta:
        app_label = 'coupon'
    
    def __unicode__(self):
        return u'%s %s %s' % (self.subscriber, self.action.name, self.coupon)


class RankDateTime(models.Model):
    """ A computed field for ordering coupons. """
    coupon = models.OneToOneField(Coupon, related_name='rank_datetime')
    rank_datetime = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'coupon'

    def __unicode__(self):
        return u'%s: %s' % (self.coupon, self.rank_datetime)

    def save(self, *args, **kwargs):
        try:
            shares = self.coupon.coupon_actions.get(action__id=7).count
        except CouponAction.DoesNotExist:
            shares = 0
        try:
            prints = self.coupon.coupon_actions.get(action__id=3).count
        except CouponAction.DoesNotExist:
            prints = 0
        self.rank_datetime = (self.coupon.coupon_create_datetime +
            datetime.timedelta(15 * shares + 3 * prints))
        super(RankDateTime, self).save(*args, **kwargs)
