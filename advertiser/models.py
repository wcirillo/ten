""" Models for the advertiser app """

import logging
import re

from esapi.conf.settings import Validator_URL

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection, models, transaction
from django.utils.translation import ugettext_lazy as _

from advertiser.business.tasks import index_all_business_coupons
from category.models import Category
from common.custom_format_for_display import build_slug
from common.utils import replace_problem_ascii
from consumer.models import Consumer
from geolocation.models import USZip

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)


class AdvertiserManager(models.Manager):
    """ Manager class of Advertiser """
    def create_advertiser_from_consumer(self, consumer, **kwargs):
        """ Creates an advertiser record for an existing consumer record. """
        advertiser_name = kwargs.get('advertiser_name')
        advertiser_area_code = kwargs.get('advertiser_area_code')
        advertiser_exchange = kwargs.get('advertiser_exchange')
        advertiser_number = kwargs.get('advertiser_number')
        advertiser_zip_postal = consumer.consumer_zip_postal
        try:
            city = USZip.objects.get(code=advertiser_zip_postal).us_city.name
            advertiser_state_province = USZip.objects.get(
                code=advertiser_zip_postal).us_state.abbreviation
        except USZip.DoesNotExist:
            advertiser_zip_postal = None
            city = None
            advertiser_state_province = None
        cursor = connection.cursor()
        # Django doesn't inform database about defaults, so we specify them.
        cursor.execute("""
            INSERT INTO advertiser_advertiser(
                consumer_ptr_id, approval_count, advertiser_name,
                advertiser_area_code, advertiser_exchange, advertiser_number, 
                advertiser_city, advertiser_state_province, advertiser_zip_postal,
                advertiser_create_datetime, advertiser_modified_datetime)
            VALUES (%s, 0, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW());""", 
                [consumer.id, advertiser_name, advertiser_area_code, 
                 advertiser_exchange, advertiser_number, city, 
                 advertiser_state_province, advertiser_zip_postal])
        transaction.commit_unless_managed()
        advertiser = self.get(id=consumer.id)
        advertiser.email_subscription.add(2)
        advertiser.email_subscription.add(4)
        advertiser.save()
        return advertiser


class Advertiser(Consumer):
    """ Advertiser subsclasses Consumer, and can have Businesses. """
    advertiser_name = models.CharField(max_length=50, null=True, 
        blank=True)
    advertiser_area_code = models.CharField('Area Code', max_length=3, 
        null=True, blank=True)
    advertiser_exchange = models.CharField('Exchange', max_length=3, null=True, 
        blank=True)
    advertiser_number = models.CharField('Number', max_length=4, null=True, 
        blank=True)
    approval_count = models.SmallIntegerField('Approval count', default=0)
    advertiser_address1 = models.CharField('Address 1', max_length=100, 
        null=True, blank=True)
    advertiser_address2 = models.CharField('Address 2', max_length=100, 
        null=True, blank=True)
    advertiser_city = models.CharField('City', max_length=75, null=True, 
        blank=True)
    advertiser_state_province = models.CharField('State/Province', 
        max_length=2, null=True, blank=True)
    advertiser_zip_postal = models.CharField('Zip/Postal', max_length=9, 
        null=True, blank=True)
    advertiser_create_datetime = models.DateTimeField('Create Date', 
        auto_now_add=True)
    advertiser_modified_datetime = models.DateTimeField('Modified Date', 
        auto_now=True)
    objects = AdvertiserManager()

    class Meta:
        verbose_name = 'advertiser'
        verbose_name_plural = 'advertisers'
    
    def __unicode__(self):
        return u'%s' % self.email if self.email else self.id

    def delete(self, *args, **kwargs):
        if BillingRecord.objects.filter(business__advertiser=self):
            error_message = _('Cannot delete an advertiser having an order.')
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(error_message)
        super(Advertiser, self).delete(*args, **kwargs)


class Business(models.Model):
    """ A business belongs to exactly one advertiser. """
    advertiser = models.ForeignKey(Advertiser, related_name='businesses', 
        blank=False)
    business_name = models.CharField(max_length=50)
    short_business_name = models.CharField(max_length=25, null=True, 
        blank=True)
    slogan = models.CharField(max_length=50, null=True, blank=True)
    is_active = models.BooleanField('Is Active', default=True)
    web_url = models.URLField(verify_exists=False, max_length=255, null=True, 
        blank=True)
    web_snap_path = models.CharField(max_length=100, null=True, blank=True)
    show_web_snap = models.BooleanField('Show Web Snap', default=True)
    show_map = models.BooleanField('Show Google Map', default=True)
    business_zip_postal = models.CharField('Zip/Postal', max_length=9, 
        null=True, blank=True)
    categories = models.ManyToManyField(Category, 
        related_name='businesses', null=True, blank=True)
    business_create_datetime = models.DateTimeField('Create Date/time', 
        auto_now_add=True)
    business_modified_datetime = models.DateTimeField('Modified Date/time', 
        auto_now=True)  

    def __unicode__(self):
        return self.business_name

    class Meta:
        verbose_name = 'business'
        verbose_name_plural = 'businesses'
        get_latest_by = 'business_create_datetime'
        
    def save(self, *args, **kwargs):
        """ Save a business. Update the search index for related coupons.
        
        Gets the search index for Coupon at most once, w/o importing the class.
        """
        super(Business, self).save(*args, **kwargs)
        self.index_coupons()
        return self
    
    def index_coupons(self):
        """ Update the search index for coupons of this business.
        
        Gets the search index for Coupon at most once, w/o importing the class.
        """
        if settings.CELERY_ALWAYS_EAGER is False:
            index_all_business_coupons.delay(self)
        return self
    
    def clean_web_url(self):
        return re.compile(Validator_URL).match(self.web_url) != None    
    
    def delete(self, *args, **kwargs):
        if BillingRecord.objects.filter(business=self):
            error_message = _('Cannot delete a business having an order.')
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(error_message)
        super(Business, self).delete(*args, **kwargs)

    def slug(self):
        """ Derive an SEO-friendly slug for this business, for use in URL. """
        slug_string = '%s' % (self.business_name)
        slug = build_slug(slug_string)
        return slug

    def clean_business_name(self, business_name=None):
        """ Shorten the business name to the first 50 characters. """
        if business_name:
            self.business_name = business_name[:50]
        elif self.business_name:
            self.business_name = self.business_name[:50]
    
    def set_short_business_name(self):
        """ Sets the short business name to the first 25 characters of 
        business_name.
        """
        self.short_business_name = self.business_name[:25]
    
    def get_short_business_name(self):
        """ Get short business name. If it equals none, it derives the value 
        and saves it to the business.
        """
        if self.short_business_name is None:
            self.set_short_business_name()
            self.save()
        return self.short_business_name

    def get_business_description(self):
        """ Get business description from business profile, if it exists. If it 
        equals none, return None.
        """
        try:
            return self.business_profile_description.business_description
        except (AttributeError, BusinessProfileDescription.DoesNotExist):
            return ''


class BusinessProfileDescription(models.Model):
    """ 
    A profile description belongs to exactly one business. 
    A business can have at most one profile description.
    """
    business = models.OneToOneField(Business, 
        related_name='business_profile_description')
    business_description = models.TextField(max_length=2500, null=True, 
        blank=True) 
    
    def save(self, *args, **kwargs):
        """ Saves a business_profile_description. """
        super(BusinessProfileDescription, self).save(*args, **kwargs)
        self.business.index_coupons()
        return self


class BillingRecord(models.Model):
    """ A billing record belongs to exactly one business. """
    business = models.ForeignKey(Business, related_name='billing_records')
    alt_first_name = models.CharField('Alt First Name', max_length=50, 
        null=True, blank=True)
    alt_last_name = models.CharField('Alt Last Name', max_length=50, null=True,
        blank=True)
    alt_email = models.EmailField('Alt Email', max_length=50, null=True, 
        blank=True)
    billing_address1 = models.CharField('Address 1', max_length=100, null=True,
        blank=True)
    billing_address2 = models.CharField('Address 2', max_length=100, null=True,
        blank=True)
    billing_city = models.CharField('City', max_length=75, null=True,
        blank=True)
    billing_state_province = models.CharField('State/Province', max_length=2,
        blank=True)
    billing_zip_postal = models.CharField('Zip/Postal', max_length=9,
        blank=True)

    class Meta:
        verbose_name = 'Billing Record'
        verbose_name_plural = 'Billing Records'

    def __unicode__(self):
        return self.business.business_name

    def delete(self, *args, **kwargs):
        if self.orders.count() > 0:
            error_message = _('Cannot delete a billing record of an order')
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(error_message)
        super(BillingRecord, self).delete(*args, **kwargs)


class Location(models.Model):
    """ A location belongs to exactly one business. """
    business = models.ForeignKey(Business, related_name='locations')
    location_url = models.URLField(max_length=255, null=True, blank=True)
    location_address1 = models.CharField(max_length=50, null=True, blank=True)
    location_address2 = models.CharField(max_length=50, null=True, blank=True)
    location_city = models.CharField(max_length=50, null=True, blank=True)
    location_state_province = models.CharField(max_length=2, null=True, 
        blank=True)
    location_zip_postal = models.CharField('Zip/Postal', max_length=9, 
        null=True, blank=True, db_index=True)
    location_area_code = models.CharField('Area Code', max_length=3, null=True, 
        blank=True)
    location_exchange = models.CharField('Exchange', max_length=3, null=True, 
        blank=True)
    location_number = models.CharField('Number', max_length=4, null=True, 
        blank=True)
    location_description = models.CharField(max_length=50, null=True, 
        blank=True)
    location_create_datetime = models.DateTimeField('Create Date', 
        auto_now_add=True)

    def __unicode__(self):
        location_label = self.location_address1 if self.location_address1 \
            else self.location_url if self.location_url \
            else self.location_zip_postal if self.location_zip_postal \
            else '%s%s%s' % (self.location_area_code, self.location_exchange, 
                             self.location_number) if self.location_area_code \
            else u'%s' % self.id
        return u'%s: %s' % (self.business, location_label)

    class Meta:
        verbose_name = 'location'
        verbose_name_plural = 'locations'
    
    def geo_purge(self):
        """
        Validate that the address fields are sufficiently populated for geocode 
        processing (None values may come in through feeds).
        """
        if self.location_zip_postal in ('', None) and \
        self.location_city in ('', None):
            return None
        address =  (getattr(self, 'location_address1') or '') + ' '
        if self.location_city not in (None, '')\
        and self.location_state_province not in(None, ''):
            address += (getattr(self, 'location_city') or '') \
             + ', ' + (getattr(self, 'location_state_province') or '')
        else:
            address += (getattr(self, 'location_city') or '') \
            + (getattr(self, 'location_state_province') or '') 
        address += ' ' + (getattr(self, 'location_zip_postal') or '')
        # Replace smart quotes etc.
        address = replace_problem_ascii(address)
        # Remove extra internal whitespace chars if necessary.
        return address.replace('  ', ' ').strip()

    def get_coords(self):
        """ 
        Get location coordinates (lng/lat) for this location, if doesn't exist, 
        retrieve through task. 
        """
        try:
            coords = (self.location_coordinate.location_longitude, 
                self.location_coordinate.location_latitude)
        except LocationCoordinate.DoesNotExist:
            from advertiser.business.location.tasks \
            import create_location_coordinate
            create_location_coordinate(self.id)
            try:
                coords = (self.location_coordinate.location_longitude, 
                self.location_coordinate.location_latitude)
            except LocationCoordinate.DoesNotExist:
                coords = None
        return coords
    
    def save(self, *args, **kwargs):
        """ Saves and returns a location. """
        if (self.location_state_province or self.location_city 
        or self.location_exchange or self.location_area_code 
        or self.location_number or self.location_description 
        or self.location_zip_postal or self.location_address1 
        or self.location_address2 or self.location_url):
            from advertiser.business.location.tasks import \
                create_location_coordinate
            super(Location, self).save(*args, **kwargs)
            # Get and save location coords.
            create_location_coordinate.delay(self.id)
        self.business.index_coupons()
        return self
    
    def to_dict(self):
        """ Turn this model into a dict """
        return {"location_address1": self.location_address1,
        "location_address2": self.location_address2,
        "location_city": self.location_city,
        "location_state_province": self.location_state_province,
        "location_zip_postal": self.location_zip_postal,
        "location_area_code": self.location_area_code,
        "location_exchange": self.location_exchange,
        "location_number": self.location_number,
        "location_description": self.location_description,}


class LocationCoordinate(models.Model):
    """ 
    A set of latitude/longitude coordinates belongs to exactly one Location.
    """
    location = models.OneToOneField(Location, primary_key=True, 
        related_name= 'location_coordinate')
    location_latitude = models.DecimalField(max_digits=19, decimal_places=16)
    location_longitude = models.DecimalField(max_digits=19, decimal_places=16)
    
    def __unicode__(self):
        return u'%s, %s' % (self.location_longitude, self.location_latitude)        


####### Signals for Business #######
# Included here to make sure it is loaded before a request needs it
from advertiser.signals import business_categories_callback

####### Register signals #######
# Use a dispatch UID to prevent this from getting kicked multiple times 
# (for every models import).
#######
models.signals.m2m_changed.connect(business_categories_callback, 
    sender=Business, dispatch_uid=__name__)
