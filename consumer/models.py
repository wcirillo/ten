""" Models for the consumer app. """

import datetime
import hashlib
import logging

from django.db import DatabaseError, IntegrityError, models, transaction
from django.db.models import SET_NULL
from django.db.models.signals import m2m_changed
from django.contrib.auth.models import User, UserManager
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.utils.translation import ugettext_lazy as _

from common.utils import generate_email_hash, generate_guid
from consumer.signals import on_change_email_subscription
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)
LOG.info('Logging Started')


class EmailSubscriptionManager(models.Manager):
    """ Model manager for Email Subscription. """
    def get_by_natural_key(self, email_subscription_name):
        """ Return instance by name. """
        return self.get(email_subscription_name=email_subscription_name)


class EmailSubscription(models.Model):
    """ The email 'lists' a consumer may opt in to. """
    email_subscription_name = models.CharField('Email Subscription Name', 
        max_length=25)
    objects = EmailSubscriptionManager()

    def __unicode__(self):
        return self.email_subscription_name

    class Meta:
        verbose_name = 'Email Subscription'
        verbose_name_plural = 'Email Subscriptions'
        
    def delete(self):
        raise ValidationError('Cannot delete an email subscription.')
    
    def natural_key(self):
        """ Returns instance by name. """
        return (self.email_subscription_name)


class UnEmailableReason(models.Model):
    """ Allows list of reasons why someone might have is_emailable=False """
    name = models.CharField('Reason Identifyer', max_length=30)
    description = models.CharField('Verbose description of this reason',
        max_length=120)

    def __unicode__(self):
        return u'%s -- %s' % (self.name, self.description)
            
    class Meta:
        verbose_name = 'Reason for Not Emailable'
        verbose_name_plural = 'Reasons for Not Emailable'


class ConsumerManager(UserManager):
    """ Model manager for Consumer. """

    @transaction.commit_on_success
    def create_consumer(self, username, email, consumer_zip_postal, **kwargs):
        """ Creates and saves a Consumer with the given username, e-mail and
        password and zip_postal.
        """
        keyword_params = {'first_name': '', 'last_name': '',
            'consumer_zip_postal': consumer_zip_postal}
        keyword_params.update(kwargs)
        # Do not include site or password parameters unless valid (will default).
        site = keyword_params.get('site', None)
        password = keyword_params.get('password', None)
        email = email.strip().lower()
        if len(username) > 30:
            username = generate_guid()[:30]
        try:
            keyword_params.update({'email': email, 'username': username})
            if site or consumer_zip_postal:
                if not site or site.id == 1:
                    # No site passed in, use the consumer_zip_postal.
                    sites = list(Site.objects.get_sites_this_zip(
                        code=consumer_zip_postal))
                    if len(sites) > 0:
                        keyword_params['site'] = sites[0]
            consumer = self.create(**keyword_params)
            # Method set_password, sets unusable pwd if pwd is not True, but
            # doesn't save.
            consumer.set_password(password)
            consumer.save()

            # Subscribe to the "Email" Email Subscription.
            try:
                consumer.email_subscription.add(1)
            except ValueError:
                # Occurs when consumer did not get saved.
                pass
            return consumer
        except IntegrityError:
            # This Integrity Error will only get hit on a race condition for 
            # saving the consumer multiple times.
            # The following error will hit if this condition occurs.  
            # IntegrityError: duplicate key value violates unique constraint 
            # "auth_user_username_key"
            # Thus stating we tried to save the username twice.  A check for 
            # this username is already occurring in the consumer/views.py  This 
            # is just a secondary safety check for good measure so a consumer 
            # doesn't hit a road block!
            transaction.rollback()
            return self.get(email__iexact=email)
        except (DatabaseError, ValidationError) as error:
            LOG.error(error)
            transaction.rollback()
            raise error


class Consumer(User):
    """ The 'base' class of user for the ten project. Subclasses contrib.auth.User.
    Advertiser subclasses Consumer.
    """
    site = models.ForeignKey(Site, related_name='consumers', default=1)
    is_email_verified = models.BooleanField('Verified by email', 
        default=False)
    consumer_zip_postal = models.CharField('Zip/Postal', max_length=9, 
        null=True, blank=True)
    geolocation_type = models.ForeignKey(ContentType, 
        limit_choices_to={"model__in": ("uszip",)},
        help_text=_("Is this a zip or a postal code?"))
    geolocation_id = models.PositiveIntegerField(null=True, blank=True,
        help_text=_("Which specific zip or a postal code?"))
    geolocation_object = generic.GenericForeignKey(ct_field="geolocation_type",
        fk_field="geolocation_id")
    email_subscription = models.ManyToManyField(EmailSubscription, 
        related_name='consumers', blank=True)
    subscriber = models.OneToOneField('subscriber.Subscriber',
        related_name='subscribers',
        blank=True, null=True, on_delete=SET_NULL)
    consumer_create_datetime = models.DateTimeField('Create Date', 
        auto_now_add=True)
    consumer_modified_datetime = models.DateTimeField('Modified Date',
        auto_now=True)
    email_hash = models.CharField('Opting and Bounce function hash', 
        max_length=42, null=True, blank=True)
    is_emailable = models.BooleanField('Is Emailable?', default=True, 
        db_index=True)
    nomail_reason = models.ManyToManyField(UnEmailableReason,
        related_name='consumers', blank=True, help_text=_("If not, why not?"))
    objects = ConsumerManager()

    def __unicode__(self):
        return u'%s' % (self.email)

    class Meta:
        verbose_name = 'consumer'
        verbose_name_plural = 'consumers'
    
    def clean(self):
        """ Clean fields before saving to database. Specifically, make email
        lower case."""
        if self.email:
            self.email = self.email.strip().lower()
        return self
        
    def clear_cache(self):
        """ Clears the Consumer count from cache. This method gets called from
        email_subscription m2m signal.
        """
        cache.delete("site-%s-consumer-count" % self.site.id)
    
    def save(self, *args, **kwargs):
        """ Saves consumer after checking uniqueness of email address.
        Establishes generic fk relationship.
        """
        self.clean()
        try:
            if self.email:
                if self.id:
                    LOG.debug('trying save method of consumer %s' % (self.id))
                    Consumer.objects.exclude(id=self.id).get(email=self.email)
                else:
                    Consumer.objects.get(email=self.email)
                error_message = 'Cannot create user with this email.'
                LOG.error('Consumer %s already exists' % (self.email))
                raise ValidationError(_(error_message))
        except Consumer.DoesNotExist:
            pass
        if len(self.username) > 30:
            self.username = generate_guid()[:30]
        self.email_hash = generate_email_hash(self.email)
        self.get_geolocation_id()
        super(Consumer, self).save(*args, **kwargs)
        return self
    
    def delete(self, *args, **kwargs):
        self.is_active = False
        self.consumer_actions.all().delete()
        super(Consumer, self).save(*args, **kwargs)
        
    def get_geolocation_id(self):
        """ Derives correct content type for GenericForeignKey. """
        try:
            self.geolocation_type
        except ObjectDoesNotExist:
            self.geolocation_type = ContentType.objects.get(
                    app_label="geolocation", model="uszip"
                )
        if self.consumer_zip_postal:
            try:
                self.geolocation_id = self.geolocation_type.get_object_for_this_type(
                    code=self.consumer_zip_postal
                    ).id
            except ObjectDoesNotExist:
                pass
        return self


class UniqueUserToken(models.Model):
    """ A uid for a user that can stale out used when generating Reset Password
    emails.
    """
    user = models.ForeignKey(Consumer)
    timestamp = models.DateTimeField('Request Datetime', auto_now=True)
    hashstamp = models.CharField('Unique hash for this token request', 
        max_length=42, null=True, blank=True)
    lifetime = models.IntegerField('lifetime in seconds', default=86400, 
        null=False)
    has_expiration = models.BooleanField(
        'Does this token ever expire?', 
        default=True)
    
    def save(self, *args, **kwargs):
        self.timestamp = datetime.datetime.now()
        pre_hash = "%s%s%s" % (
            self.user.password, 
            self.timestamp, 
            self.user.email
            )
        self.hashstamp = hashlib.sha1(pre_hash).hexdigest()
        super(UniqueUserToken, self).save(*args, **kwargs)
        return self
    
    def is_expired(self):
        """ Returns boolean value: is this token expired? """
        if self.has_expiration is False:
            return False
        now = datetime.datetime.now()
        age = now-self.timestamp
        return age > datetime.timedelta(seconds=self.lifetime)


class BadUserPattern(models.Model):
    """ Forms of email addresses we know we can just remove as test data. """
    pattern = models.CharField('Email address Pattern', max_length=30)
    
    def __unicode__(self):
        return u'%s' % self.pattern


class SalesRep(models.Model):
    """ Repository for info on our sales reps """
    consumer = models.ForeignKey(Consumer, related_name='salesreps')
    sites = models.ManyToManyField(Site, verbose_name='Sites covered', 
        related_name="reps", null=True, blank=True )
    extension = models.CharField(_('Phone Extension'), 
        max_length=25, blank=True, null=True)
    title = models.CharField(_('Professional Title for signature'), 
            max_length=25, blank=True, null=True)
    
    def __unicode__(self):
        return u'%s -- %s' % (self.consumer.first_name, 
            ', '.join(self.sites.all().values_list('name', flat=True)))

#
HISTORY_EVENT_TYPE_CHOICES = (
       ('0', _('Initial Signup')),
       ('1', _('Opt-out')),
       ('2', _('Re-subscribe to email')),
       ('3', _('Spam Complaint')),
       ('4', _('Bounce received')),
       ('5', _('Re-verification Sent')),
       ('6', _('Verification Completed')),
       ('7', _('Password reset verification sent')),
       ('8', _('Password reset button clicked')),
       ('9', _('Password reset completed')),
       ('10', _('Email Sent')),
    )

class ConsumerHistoryEvent(models.Model):
    """ Historical log of consumer actions and events defined in
    HISTORY_EVENT_TYPE_CHOICES.
    """
    consumer = models.ForeignKey(Consumer, related_name='history')
    event_datetime = models.DateTimeField('Request Datetime', auto_now_add=True)
    event_type = models.CharField(max_length=2, default='0',
        choices=HISTORY_EVENT_TYPE_CHOICES)
    data = models.CharField('Data relevent to this event',
        max_length=250, null=True, blank=True)
    ip = models.IPAddressField('Source IP for request', default='0.0.0.0')

    get_latest_by = 'event_datetime'

    def __unicode__(self):
        return u'%s---%s--%s--%s' % (self.event_datetime, self.event_type,
            self.ip, self.data)

# Signal for EmailSubscription to clear consumer-site-count when it changes.
m2m_changed.connect(on_change_email_subscription,
    sender = Consumer.email_subscription.through)
