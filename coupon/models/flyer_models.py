""" Flyer models of the coupon app """

import datetime
import logging

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from coupon.models.coupon_models import Coupon
from geolocation.models import USCounty, USCity, USZip

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

SEND_STATUS_CHOICES = (
       ('0', _('Unsent')),
       ('1', _('Sending...')),
       ('2', _('Sent Successfully')),
       ('3', _('Sent with Errors')),
   )


class Subdivision(models.Model):
    """ Abstract base class for relating objects (Flyer and FlyerPlacements) to 
    geographic subdivisions of their markets using generic foreign key.S
    """
    geolocation_type = models.ForeignKey(ContentType, 
        limit_choices_to={"model__in": ("uszip", "uscity", "uscounty")},
        help_text=_("Is this a county or a zip?"))
    geolocation_id = models.PositiveIntegerField(
        help_text=_("Which specific county or zip?"))
    geolocation_object = generic.GenericForeignKey(ct_field="geolocation_type",
        fk_field="geolocation_id")
        
    class Meta:
        abstract = True
        app_label = 'coupon'
        
    def clean_object_within_county(self, related_objects):
        """ Assert this subdivision is not within a county already related to the
        instance.
        """
        if self.geolocation_object.us_county.id in related_objects.filter(
                geolocation_type__model='uscounty').values_list(
                'geolocation_id', flat=True):
            raise ValidationError(
                _("Cannot add %s when %s is already related." % (
                    self.geolocation_object,
                    self.geolocation_object.us_county)))

    def clean_object_containing_zips(self, related_objects):
        """ Assert this subdivision does not contain zips already related to the
        instance.
        """
        if self.geolocation_object.us_zips.filter(id__in=related_objects.filter(
                geolocation_type__model='uszip').values_list(
                'geolocation_id', flat=True)).count():
            raise ValidationError(
                _("Cannot add %s when zips it contains are already related." % (
                    self.geolocation_object)))

    def clean_county(self, instance, related_objects):
        """ Clean this subdivision, which is a county. """
        if self.geolocation_object in instance.site.us_county.all() \
        or self.geolocation_object.us_state == \
            self.flyer_placement.site.us_state:
            pass
        else:
            raise ValidationError(
                _("County must be part of %s." % instance.site))
        # Assert this county does not contain any cities already related.
        if self.geolocation_object.us_cities.filter(
                id__in=related_objects.filter(
                    geolocation_type__model='uscity').values_list(
                        'geolocation_id', flat=True)).count():
            raise ValidationError(
                _("Cannot add %s when a city within it is related." % (
                    self.geolocation_object)))
        self.clean_object_containing_zips(related_objects)

    def clean_city(self, instance, related_objects):
        """ Clean this subdivision, which is a city. """
        if self.geolocation_object in instance.site.us_city.all() \
        or self.geolocation_object.us_county in \
            instance.site.us_county.all() \
        or self.geolocation_object.us_state == instance.site.us_state:
            pass
        else:
            raise ValidationError(
                _("City must be part of %s." % self.flyer_placement.site))
        self.clean_object_within_county(related_objects)
        self.clean_object_containing_zips(related_objects)

    def clean_zip(self, instance, related_objects):
        """ Clean this subdivision, which is a US zip code. """
        if self.geolocation_object in instance.site.us_zip.all() \
        or self.geolocation_object.us_county in instance.site.us_county.all() \
        or self.geolocation_object.us_city in instance.site.us_city.all() \
        or self.geolocation_object.us_state == instance.site.us_state:
            pass
        else:
            raise ValidationError(
                _("Zip must be part of %s." % instance.site))
        if self.geolocation_object.us_city.id in related_objects.filter(
                geolocation_type__model='uscity').values_list(
                    'geolocation_id', flat=True):
            raise ValidationError(
                _("Cannot add %s when %s is already related." % (
                    self.geolocation_object, self.geolocation_object.us_city)))
        self.clean_object_within_county(related_objects)

    def clean_for_fk(self, instance, related_name):
        """ Assert geolocation exists and that this subdivision is within the
        market of this foreign key.

        Assert that this subdivision is not a member of a larger subdivision
        that is already related to this instance.
        """
        related_objects = getattr(instance, related_name)
        if not self.geolocation_object:
            raise ValidationError(_("No instance of a %s with id %s" % (
                self.geolocation_type, self.geolocation_id)))
        if instance.site.phase < 2:
            raise ValidationError(
                _("Subdivision of %s not permitted." % instance.site))
        if self.geolocation_type == ContentType.objects.get(model='uscounty'):
            self.clean_county(instance, related_objects)
        elif self.geolocation_type == ContentType.objects.get(model='uscity'):
            self.clean_city(instance, related_objects)
        elif self.geolocation_type == ContentType.objects.get(model='uszip'):
            self.clean_zip(instance, related_objects)


class Flyer(models.Model):
    """ A grouping of coupons for distribution in a weekly email. 
    
    is_mini: This field is now deprecated.
    num_recipients: defaults to -1 to differentiate between flyers that went to 
    0 people and flyers that didn't acutally send (or save) properly for some 
    reason.
    """
    coupon = models.ManyToManyField(Coupon, related_name='flyers', 
        through='FlyerCoupon')
    site = models.ForeignKey('market.Site', related_name='flyers')
    send_date = models.DateField('Send Date', default=datetime.date.today,
        db_index=True,
        help_text=_('The scheduled send date for this flyer.'))
    create_datetime = models.DateTimeField('Created', auto_now_add=True)
    send_datetime = models.DateTimeField('Sent', blank=True, null=True)
    is_mini = models.BooleanField('Is a Mini Flyer', default=False)
    is_approved = models.BooleanField('Is Approved', default=False)
    send_status = models.CharField(max_length=1, default='0',
        choices=SEND_STATUS_CHOICES)
    num_recipients = models.IntegerField(default=-1,
        help_text=_('To how many addresses was this flyer sent?'))

    class Meta:
        app_label = 'coupon'
        get_latest_by = 'create_datetime'
            
    def __unicode__(self):
        return u'Flyer %s: %s %s Week %s' % (
            self.id, 
            self.site.name, 
            self.create_datetime.isocalendar()[0], 
            self.create_datetime.isocalendar()[1]
            )

    def num_consumers(self):
        """ Return count of consumers eligible to receive this flyer. """
        return self.site.consumers.filter(is_emailable=True, 
            email_subscription=1, is_active=True).count()


class FlyerCoupon(models.Model):
    """ The relation of a coupon to a flyer. """
    flyer = models.ForeignKey(Flyer, related_name='flyer_coupons')
    coupon = models.ForeignKey(Coupon, related_name='flyer_coupons')
    rank = models.PositiveSmallIntegerField(max_length=2, default=0,
        help_text=_('The ordering of the coupon within the flyer'))
    
    class Meta:
        app_label = 'coupon'
        unique_together = (("flyer","rank"),("flyer","coupon"))
        
    def __unicode__(self):
        return u'%s: %s' % (self.flyer, self.coupon)
        
    def clean(self):
        if self.rank == 0:
            try:
                self.rank = FlyerCoupon.objects.filter(
                    flyer=self.flyer).latest('rank').rank + 1
            except FlyerCoupon.DoesNotExist:
                self.rank = 1
        super(FlyerCoupon, self).clean()
        
    def save(self, *args, **kwargs):
        self.clean()
        super(FlyerCoupon, self).save(*args, **kwargs)


class FlyerConsumer(models.Model):
    """ A consumer who was sent a flyer. """
    flyer = models.ForeignKey(Flyer, related_name='flyer_consumers')
    consumer = models.ForeignKey('consumer.Consumer', 
        related_name='flyer_consumers')
    
    class Meta:
        app_label = 'coupon'
        unique_together = (("flyer","consumer"),)


class FlyerSubdivision(Subdivision):
    """ A geographic entity, such as a county or zip code, within the market
    that a flyer is for.
    
    Flyers without subdivision relationships are for sending to an entire 
    market. Those with subdivisions are not.
    """
    flyer = models.ForeignKey(Flyer, related_name='flyer_subdivisions')
    
    class Meta:
        app_label = 'coupon'
        unique_together = (("flyer", "geolocation_type", "geolocation_id"),)
        
    def __unicode__(self):
        return u'%s' % (self.geolocation_object)

    def clean_flyer_county(self):
        """ Do not allow if another flyer for the same site for the same
        send_date exists and has a subdivision that is a city within this
        county or a zip within this county."""
        cities = USCity.objects.filter(us_county__id=self.geolocation_id)
        zips = USZip.objects.filter(us_county__id=self.geolocation_id)
        city_type = ContentType.objects.get(model='uscity')
        zip_type = ContentType.objects.get(model='uszip')
        matching_instances = Flyer.objects.exclude(id=self.flyer.id).filter(
            site=self.flyer.site, send_date=self.flyer.send_date).filter(
            Q(flyer_subdivisions__geolocation_id__in=cities,
                flyer_subdivisions__geolocation_type=city_type
            ) | Q(flyer_subdivisions__geolocation_id__in=zips,
                flyer_subdivisions__geolocation_type=zip_type
            ))
        return matching_instances

    def clean_flyer_city(self):
        """ Do not allow if another flyer for the same site for the same
        send_date exists and has a subdivision that is a county this city is in,
        or has a zip within this city."""
        county = USCounty.objects.get(id=self.geolocation_object.us_county_id)
        zips = USZip.objects.filter(us_city__id=self.geolocation_id)
        county_type = ContentType.objects.get(model='uscounty')
        zip_type = ContentType.objects.get(model='uszip')
        matching_instances = Flyer.objects.exclude(id=self.flyer.id).filter(
            site=self.flyer.site, send_date=self.flyer.send_date).filter(
            Q(flyer_subdivisions__geolocation_id=county.id,
                flyer_subdivisions__geolocation_type=county_type
            ) | Q(flyer_subdivisions__geolocation_id__in=zips,
                flyer_subdivisions__geolocation_type=zip_type
            ))
        return matching_instances

    def clean_flyer_zip(self):
        """ Do not allow if another flyer for the same site for the same
        send_date exists and has a subdivision that is a city or a county this
        zip is in.
        """
        county = USCounty.objects.get(id=self.geolocation_object.us_county_id)
        city = USCity.objects.get(id=self.geolocation_object.us_city_id)
        county_type = ContentType.objects.get(model='uscounty')
        city_type = ContentType.objects.get(model='uscity')
        matching_instances = Flyer.objects.exclude(id=self.flyer.id).filter(
            site=self.flyer.site, send_date=self.flyer.send_date).filter(
            Q(flyer_subdivisions__geolocation_id=county.id,
                flyer_subdivisions__geolocation_type=county_type
            ) | Q(flyer_subdivisions__geolocation_id=city.id,
                flyer_subdivisions__geolocation_type=city_type
            ))
        return matching_instances
        
    def clean(self):
        """ Assert this subdivision is related to no other flyers for this site
        for this send_date.
        """
        super(FlyerSubdivision, self).clean_for_fk(self.flyer,
            'flyer_subdivisions')
        flyers = Flyer.objects.filter(site=self.flyer.site, 
            send_date=self.flyer.send_date, 
            flyer_subdivisions__geolocation_id=self.geolocation_id,
            flyer_subdivisions__geolocation_type=self.geolocation_type)
        if self.id:
            # Exclude this flyer or the original flyer as needed.
            orig_flyer = FlyerSubdivision.objects.get(id=self.id).flyer
            if orig_flyer == self.flyer:
                flyers = flyers.exclude(id=self.flyer.id)
            else:            
                flyers = flyers.exclude(id=orig_flyer.id)
        if len(flyers):
            error = "%s can be related to at most one flyer for %s for %s" % (
                self.geolocation_object, self.flyer.site, self.flyer.send_date)
            LOG.debug(error)
            LOG.debug(flyers)
            raise ValidationError(_(error))
        if self.geolocation_type.model == 'uscounty':
            matching_instances = self.clean_flyer_county()
        elif self.geolocation_type.model == 'uscity':
            matching_instances = self.clean_flyer_city()
        elif self.geolocation_type.model == 'uszip':
            matching_instances = self.clean_flyer_zip()
        if matching_instances:
            raise ValidationError('%s for %s conflicts with %s: %s' % (
                self.geolocation_object, self.flyer, matching_instances,
                matching_instances[0].flyer_subdivisions.all()))

    def save(self, *args, **kwargs):
        self.clean()
        super(FlyerSubdivision, self).save(*args, **kwargs)


class FlyerPlacement(models.Model):
    """ A slot designated for inclusion in a flyer on a given date for a given 
    site.
    """
    site = models.ForeignKey('market.Site', related_name='flyer_placements')
    slot = models.ForeignKey('coupon.Slot', related_name='flyer_placements')
    send_date = models.DateField('Send Date', db_index=True,
        help_text=_('The scheduled send date for this flyer placement.'))
    
    class Meta:
        app_label = 'coupon'
        unique_together = (("slot", "send_date"),)
    
    def __unicode__(self):
        return u'%s: Week %s %s' % (self.id, self.send_date.isocalendar()[1], 
            self.slot)
        
    def clean(self):
        if self.site != self.slot.site:
            raise ValidationError(
                _("Flyer placement must be for the slot site."))
        # send_date must be a Thursday.
        if self.send_date.isocalendar()[2] != 4:
            raise ValidationError(_("Send date must be a Thursday."))
    
    def save(self, *args, **kwargs):
        self.clean()
        super(FlyerPlacement, self).save(*args, **kwargs)  
        return self


class FlyerPlacementSubdivision(Subdivision):
    """ A geographic entity, such as a county or zip code, within the market
    that a flyer placement is for.
    
    Flyer placements without subdivision relationships are for sending to an 
    entire market. Those with subdivisions are not.
    """
    flyer_placement = models.ForeignKey(FlyerPlacement, 
        related_name='flyer_placement_subdivisions')
    
    class Meta:
        app_label = 'coupon'
        unique_together = (("flyer_placement", "geolocation_type", 
            "geolocation_id"),)
    
    def __unicode__(self):
        return u'%s' % (self.geolocation_object)

    def clean(self):
        super(FlyerPlacementSubdivision, self).clean_for_fk(
            self.flyer_placement, 'flyer_placement_subdivisions')

    def save(self, *args, **kwargs):
        self.clean()
        super(FlyerPlacementSubdivision, self).save(*args, **kwargs)
        return self


class FlyerSubject(models.Model):
    """ The customized subject line for flyers in a week. """
    title = models.CharField('Subject Line:', max_length=120)
    send_date = models.DateField('Week Chooser', db_index=True,
        default=datetime.date.today,
        help_text=_('Any day in the proper week will do'))
    week = models.PositiveSmallIntegerField(max_length=2, default=0, 
        editable=False,
        help_text=_('To which week # of the year does this subject apply?'))

    class Meta:
        app_label = 'coupon'

    def __unicode__(self):
        return u'Flyer Subject for week  %s: %s' % (self.week, self.title)
    
    def save(self, *args, **kwargs):
        self.week = self.send_date.isocalendar()[1]
        super(FlyerSubject, self).save(*args, **kwargs)
        return self
