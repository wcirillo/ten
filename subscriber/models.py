""" Models for subscriber app """

from django.core.cache import cache
from django.db import models

from consumer.models import Consumer
from market.models import Site


class SMSSubscriptionManager(models.Manager):
    """ Manager class for SMS Subscription """
    def get_by_natural_key(self, sms_subscription_name):
        """ Returns instance by name. """
        return self.get(sms_subscription_name=sms_subscription_name)


class SMSSubscription(models.Model):
    """ A distribution list a subscriber can opt in to. """
    sms_subscription_name = models.CharField('SMS Subscription Name', 
        max_length=25)
    objects = SMSSubscriptionManager()

    class Meta:
        verbose_name = 'SMS Subscription'
        verbose_name_plural = 'SMS Subscriptions'

    def __unicode__(self):
        return self.sms_subscription_name
    
    def natural_key(self):
        """ Returns instance by name. """
        return self.sms_subscription_name


class Subscriber(models.Model):
    """
    Person to have a mobile_phone. A subscriber may be a consumer but is not
    necessarily one.
    """
    site = models.ForeignKey(Site, related_name='subscribers', default=1)
    subscriber_zip_postal = models.CharField('Zip/Postal', max_length=9, 
        null=True)
    sms_subscription = models.ManyToManyField(SMSSubscription, 
        related_name='subscribers', blank=True, null=True)
    subscriber_create_datetime = models.DateTimeField('Create Date', 
        auto_now_add=True) 
    subscriber_modified_datetime = models.DateTimeField('Modified Date', 
        auto_now=True)

    def __unicode__(self):
        try:
            display = self.mobile_phones.all()[0].mobile_phone_number
        except IndexError:
            display = ''
        return display

    class Meta:
        verbose_name = 'Subscriber'
        verbose_name_plural = 'Subscribers'

    def is_verified(self):
        """ Does this subscriber have a mobile_phone that is verified? """
        return self.mobile_phones.filter(is_verified=True).count()

    def consumer(self):
        """ Return the consumer having a OneToOne relationship to this
        subscriber.
        """
        return Consumer.objects.get(subscriber__id=self.id)


class CarrierManager(models.Manager):
    """ Default model manager for Carrier class. """

    def get_or_set_carrier_cache(self):
        """ Get carriers from cache else get dynamically and set cache. """
        carrier_cache = cache.get('carrier-cache')
        if not carrier_cache:
            carrier_cache = self.filter(is_major_carrier=True).only(
                'carrier', 'carrier_display_name')
            cache.set('carrier-cache', carrier_cache)
        return carrier_cache


class Carrier(models.Model):
    """ The telephone network a mobile_phone belongs to. """
    carrier = models.CharField('Mobile Phone Carrier', max_length=20, 
        unique=True)
    carrier_display_name = models.CharField(max_length=75, unique=True)
    user_name = models.CharField('Carrier Username', max_length=25, null=True, 
        blank=True)
    password = models.CharField('Carrier Password', max_length=25, null=True, 
        blank=True)
    site = models.ManyToManyField(Site, related_name='carriers')
    is_major_carrier = models.BooleanField(default=False)
    objects = CarrierManager()

    class Meta:
        verbose_name = 'Carrier'
        verbose_name_plural = 'Carriers'
        ordering = ('-is_major_carrier', 'carrier_display_name')

    def __unicode__(self):
        return self.carrier_display_name


class MobilePhone(models.Model):
    """ A mobile phone is related to exactly one subscriber. """
    mobile_phone_number = models.CharField(unique=True, max_length=20)
    is_verified = models.BooleanField('Is this mobile phone verified?',
        default=False)
    carrier = models.ForeignKey(Carrier, related_name='mobile_phones')
    subscriber = models.ForeignKey(Subscriber, related_name='mobile_phones')

    class Meta:
        verbose_name = 'Mobile Phone'
        verbose_name_plural = 'Mobile Phones'

    def __unicode__(self):
        return u'%s' % self.mobile_phone_number
