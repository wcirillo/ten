""" Coupon models of the coupon app """
#pylint: disable=W0404,W0613
import datetime
import logging

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import F, Q
from django.utils.translation import ugettext_lazy as _

from haystack.sites import site as haystack_site

from advertiser.business.location.service import get_location_coords_list
from common.custom_format_for_display import build_slug

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def now_plus_90():
    """ Return this date plus 90 days. """
    return datetime.date.today() + datetime.timedelta(days=90)


class DefaultRestrictions(models.Model):
    """ The set of restrictions that can be selected for a coupon. """
    restriction = models.CharField(max_length=75, null=True, blank=True)
    sort_order = models.CharField(max_length=1, unique=True)

    def __unicode__(self):
        return self.restriction

    class Meta:
        app_label = 'coupon'
        verbose_name = 'restriction'
        verbose_name_plural = 'restrictions'
    
    def delete(self, *args, **kwargs):
        raise ValidationError('Cannot delete a DefaultRestriction.')


class RedemptionMethod(models.Model):
    """ The various ways a coupon can be redeemed, such as Print or SMS. """
    redemption_method_name = models.CharField(max_length=40, null=True, 
        blank=True)

    def __unicode__(self):
        return self.redemption_method_name

    class Meta:
        app_label = 'coupon'
        verbose_name = 'redemption method'
        verbose_name_plural = 'redemption methods'


class Offer(models.Model):
    """ A business has offers. An offer has coupons. """
    business = models.ForeignKey('advertiser.Business', related_name='offers',
        null=True, blank=True)
    headline = models.CharField(max_length=25, null=True, blank=True)
    qualifier = models.CharField(max_length=40, null=True, blank=True)
    create_datetime = models.DateTimeField('Create Date Time', 
        auto_now_add=True)

    def __unicode__(self):
        return u'%s' % (self.headline,)

    class Meta:
        app_label = 'coupon'
        verbose_name = 'offer'
        verbose_name_plural = 'offers'
        get_latest_by = 'create_datetime'
        
    def save(self, *args, **kwargs):
        super(Offer, self).save(*args, **kwargs)
        index = haystack_site.get_index(Coupon)
        for coupon in self.coupons.all():
            index.update_object(coupon)
        return self


class CouponType(models.Model):
    """ The types of coupons (Free, Paid, Bulk etc.) """
    coupon_type_name = models.CharField(max_length=20)

    def __unicode__(self):
        return self.coupon_type_name

    class Meta:
        app_label = 'coupon'
        verbose_name = 'coupon type'
        verbose_name_plural = 'coupon types'
        
    def delete(self, *args, **kwargs):
        raise ValidationError('Cannot delete a CouponType.')


class CurrentCouponManager(models.Manager):
    """ A manager that filters current coupons in current slot time frames of
    current slots. 
    
    Business rules:
    - Coupon must be started.
    - Coupon must not be expired.
    - Slot must have already started.
    - Slot must have not ended yet.
    - Time frame must have started.
    - Time frame must be open-ended or have not ended yet.
    """
    def get_query_set(self):
        """ Fuzz 'now' to this hour to allow for query caching, else this query
        will *always* be unique.
        """
        now = datetime.datetime.now().replace(minute=0, second=0, microsecond=0)
        hour_future = now + datetime.timedelta(0, 0, 0, 0, 0, 1)
        today = datetime.date.today()
        return super(CurrentCouponManager, self).get_query_set().distinct(
            ).select_related('offer','offer__business'
            ).filter(
                # Q objects must proceed any keyword arguments.
                Q(slot_time_frames__end_datetime__gt=hour_future) |
                Q(slot_time_frames__end_datetime=None),
                start_date__lte=today,
                expiration_date__gte=today,
                slot_time_frames__start_datetime__lt=hour_future,
                slot_time_frames__slot__start_date__lte=today,
                slot_time_frames__slot__end_date__gte=today,
                coupon_type__coupon_type_name__in=('Paid', 'Free')
            )

    def get_current_coupons_by_site(self, site):
        """ Filter current coupons by site. """
        return self.get_query_set().filter(slot_time_frames__slot__site=site)


class Coupon(models.Model):
    """ Coupons belong to exactly one offer. Related to a business through
    offer.
    """
    offer = models.ForeignKey(Offer, related_name='coupons', null=True, 
        blank=True)
    coupon_type = models.ForeignKey(CouponType, related_name='coupons')
    redemption_method = models.ManyToManyField(RedemptionMethod, 
        related_name='coupons', null=True, blank=True)
    is_valid_monday = models.BooleanField('Valid Monday', default=True)
    is_valid_tuesday = models.BooleanField('Valid Tuesday', default=True)
    is_valid_wednesday = models.BooleanField('Valid Wednesday', default=True)
    is_valid_thursday = models.BooleanField('Valid Thursday', default=True)
    is_valid_friday = models.BooleanField('Valid Friday', default=True)
    is_valid_saturday = models.BooleanField('Valid Saturday', default=True)
    is_valid_sunday = models.BooleanField('Valid Sunday', default=True)
    start_date = models.DateField('Start Date', default=datetime.date.today,
        db_index=True)  
    expiration_date = models.DateField('Expiration Date', default=now_plus_90,
        db_index=True)
    location = models.ManyToManyField('advertiser.Location', 
        related_name='coupons', null=True, blank=True)
    default_restrictions = models.ManyToManyField(DefaultRestrictions, 
        related_name='coupons', null=True, blank=True)
    custom_restrictions = models.TextField(max_length=400, null=True, 
        blank=True)
    simple_code = models.CharField(max_length=10, null=True, blank=True)
    is_redeemed_by_sms = models.BooleanField('Redeemed by SMS', default=True)
    is_coupon_code_displayed = models.BooleanField('Is Unique Code Displayed', 
        default=True)
    is_approved = models.BooleanField('Is Approved', default=False)
    precise_url = models.URLField(max_length=255, verify_exists=False,
        null=True, blank=True,)
    sms = models.CharField('SMS coupon content', max_length=61, null=True, 
        blank=True, help_text="""10Coupon Alrts: {{the above}} CODE Details On 
        Website Reply HELP for Help. Reply STOP to Stop. Msg&Data Rates May 
        Apply""")
    coupon_create_datetime = models.DateTimeField('Created', 
        auto_now_add=True)
    coupon_modified_datetime = models.DateTimeField('Last Modified', 
        auto_now=True)
    objects = models.Manager()
    current_coupons = CurrentCouponManager()
        
    class Meta:
        app_label = 'coupon'
        verbose_name = 'coupon'
        verbose_name_plural = 'coupons'
        get_latest_by = 'coupon_create_datetime'
        
    def __unicode__(self):
        return u'%s %s: %s - %s, expires %s' % (
            self.coupon_type.coupon_type_name, self.id, 
            self.offer.business.business_name, self.offer.headline, 
            self.expiration_date)

    def save(self, *args, **kwargs):
        """ Save and return a coupon. If coupon is approved, fire tasks. """
        # Get instance as it exists in database.
        coupon_before = None
        self.frmt_expiration_date_for_save()
        if self.id:
            coupon_before = Coupon.objects.get(id=self.id)
        super(Coupon, self).save(*args, **kwargs)
        if self.is_approved:
            from coupon.tasks import update_widget
            from sms_gateway.tasks import text_blast_coupon
            from coupon.tasks import tweet_approved_coupon
            
            LOG.debug('calling widget task')
            update_widget.delay(self)
            if coupon_before and coupon_before.is_approved == False:
                LOG.debug('calling text_blast_coupon task')
                text_blast_coupon.delay(self)
                LOG.debug('calling tweet approved coupon')
                tweet_approved_coupon.delay(self)
        return self
        
    def get_absolute_url(self):
        """ Return unique url for this coupon.
        Assumes the coupon is on the advertiser's site.
        """
        url = '/%s%s' % (self.offer.business.advertiser.site.directory_name,
            reverse('view-single-coupon',
                kwargs={'slug': self.slug(), 'coupon_id': self.id}))
        LOG.debug(url)
        return url
            
    def clean(self):
        if self.is_coupon_code_displayed and len(self.sms) > 56:
            raise ValidationError("""Since unique code will be displayed, max
                length of SMS coupon content is 56.""")
    
    def get_location_coords_list(self):
        """ Build a nested list containing locations for this coupon. Return two
        lists, one of latitudes and one of longitudes, respective to their key.
        """
        locations = self.location.all().order_by('id')
        location_coords = get_location_coords_list(locations)  
        return location_coords
    
    def get_location_string(self):
        """ Build location city/state list for page title single coupon display.
        Returns list of all unique locations. 
        """
        loc_list = []
        hold_state = None
        first_city = []
        # Since we are slicing judiciously, and a slice on a QuerySet preforms
        # a new query, flatten this to a list of tuples.
        locations = list(self.location.distinct().exclude(location_city=''
            ).values_list(
                'location_city', 'location_state_province'
            ).order_by('id'))
        i = 0
        while i < len(locations):
            if locations[i][0]:
                if not first_city:
                    first_city.append(locations[i][0])
                    if locations[i][1] != '':
                        first_city.append(', %s' % locations[i][1])
                loc_list.append(locations[i][0])
            if hold_state and hold_state != locations[i][1]:
                loc_list[i-1] = '%s, %s' % (loc_list[i-1], hold_state)
            if locations[i][1] != '':
                hold_state = locations[i][1]
            else:
                hold_state = None
            LOG.debug('first_city: %s' % first_city)
            LOG.debug('loc_list: %s' % loc_list)
            i += 1
        i -= 1
        if hold_state:
            loc_list[i] = '%s, %s' % (loc_list[i], hold_state)
        first_city = "".join(first_city)
        if not first_city:
            first_city = None
        LOG.debug('first_city: %s' % first_city)
        LOG.debug('loc_list: %s' % loc_list)
        return loc_list, first_city

    def get_default_sms(self):
        """ Derive an SMS message for this coupon. Can be overwritten in UI. """
        if self.offer.business.short_business_name:
            use_name = self.offer.business.short_business_name
        else:
            use_name = self.offer.business.business_name
        sms = '%s %s' % (self.offer.headline, use_name)
        return sms
    
    def get_site(self):
        """ Get the site with which this coupon is associated. """
        try:
            site = self.slot_time_frames.select_related(
                'slot__site').only('slot__site__id')[0].slot.site
        except IndexError:
            site = self.offer.business.advertiser.site
        return site
      
    def frmt_expiration_date_for_save(self):
        """ Set the expiration date about to be saved back into proper date
        format.  The reason for this is because the session could at any time
        hold a different formatted unicode version.
        """
        # Delayed import to allow models to load.
        from coupon.service.expiration_date_service import (
            frmt_expiration_date_for_db)
        
        self.expiration_date = frmt_expiration_date_for_db(self.expiration_date)
        return self
        
    def slug(self):
        """ Derive an SEO-friendly slug for this coupon, for use in URL. """
        slug_string = '%s %s' % (self.offer.business.business_name, 
            self.offer.headline)
        slug = build_slug(slug_string)
        return slug

    def to_dict(self):
        """ Turn this model into a dict """
        return {"offer": self.offer,
                "coupon_type": self.coupon_type,
                "redemption_method": self.redemption_method,
                "is_valid_monday": self.is_valid_monday,
                "is_valid_tuesday": self.is_valid_tuesday,
                "is_valid_wednesday": self.is_valid_wednesday,
                "is_valid_thursday": self.is_valid_thursday,
                "is_valid_friday": self.is_valid_friday,
                "is_valid_saturday": self.is_valid_saturday,
                "is_valid_sunday": self.is_valid_sunday,
                "start_date": self.start_date,
                "expiration_date": self.expiration_date,
                "location": self.location,
                "default_restrictions": self.default_restrictions,
                "custom_restrictions": self.custom_restrictions,
                "is_redeemed_by_sms": self.is_redeemed_by_sms,
                "sms": self.sms}

    def update_index(self):
        """ Update the coupon index for this specific coupon """        
        index = haystack_site.get_index(Coupon)
        index.update_object(self)


class CouponCode(models.Model):
    """ These are generated when a coupon is printed or sent by sms.
    Allows for unique redemption.
    """
    coupon = models.ForeignKey(Coupon, related_name='coupon_codes')
    code = models.CharField(max_length=64)
    used_count = models.PositiveSmallIntegerField(max_length=8, default=0,
        editable=False,
        help_text=_('How many times has this coupon code been used?'))
    
    class Meta:
        app_label = 'coupon'
        verbose_name = _("coupon code")
        verbose_name_plural = _("coupon codes")
        unique_together = (('coupon', 'code'),)

    def __unicode__(self):
        return u'%s' % self.code
        
    def decrement_used_count(self):
        """ Decrement used_count of the coupon_code. """
        self.used_count = F('used_count') - 1
        self.save()
        
    def increment_used_count(self):
        """ Increment used_count of the coupon_code. """
        self.used_count = F('used_count') + 1
        self.save()
        
    def delete(self, *args, **kwargs):
        if self.used_count > 0:
            error_message = _('Cannot delete a used coupon code:')
            LOG.info('%s %s' % (error_message, self.code))
            raise ValidationError(error_message)
        super(CouponCode, self).delete(*args, **kwargs)
