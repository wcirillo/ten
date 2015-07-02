""" Models for media_partner app. """

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from consumer.models import Consumer
from market.models import Site

class MediaPartner(Consumer):
    """
    A MediaPartner inherits Consumer and can have 2 user_types.
    1.) media_group_partner (Media Group User)
       media_group_partner is a user of a MediaGroup
    2.) affiliate_partner (Affiliate User)
        affiliate_partner is a user of an Affiliate
    """
    def __unicode__(self):
        # Needs to return unicode string or validation will fail.
        return self.email or ''


class MediaGroup(models.Model):
    """ A MediaGroup is the Corporate Radio Partner. Example: ClearChannel """    
    media_group_partner = models.ManyToManyField(MediaPartner, 
        related_name='media_groups')
    name = models.CharField(max_length=50)
    contact_name = models.CharField(max_length=50)
    contact_phone = models.CharField(max_length=10)
    contact_email = models.CharField(max_length=255)
    
    def __unicode__(self):
        return self.name
    
class Medium(models.Model):
    """ A medium example could be 'radio' or 'cable'. """
    name = models.CharField(max_length=50)
    
    def __unicode__(self):
        return self.name

class Affiliate(models.Model):
    """ An Affiliate is a sub group of Media Groups.
    Example: Clear Channel of the Hudson Valley
    """
    name = models.CharField(max_length=50)
    affiliate_partner = models.ManyToManyField(MediaPartner, 
        related_name='affiliates')
    media_group = models.ForeignKey(MediaGroup, related_name='affiliates', 
        null=True, blank=True)
    contact_name = models.CharField(max_length=50)
    contact_phone = models.CharField(max_length=10)
    contact_email = models.CharField(max_length=255)
    address1 = models.CharField('Address 1', max_length=50, 
        null=True, blank=True)
    address2 = models.CharField('Address 2', max_length=50, 
        null=True, blank=True)
    city = models.CharField('City', max_length=50, null=True, 
        blank=True)
    state_province = models.CharField('State/Province', 
        max_length=2, null=True, blank=True)
    zip_postal = models.CharField('Zip/Postal', max_length=9, 
        null=True, blank=True)
    free_coupons = models.IntegerField(default=0)
    medium = models.ForeignKey(Medium, related_name='affiliates')
    site = models.ForeignKey(Site, related_name='affiliates')
    
    def __unicode__(self):
        return (str(self.id) + ' - ' + self.name)

        
class MediaPieShare(models.Model):
    """
    Affiliates have MediaPieShares.
    """
    affiliate = models.ForeignKey(Affiliate, related_name='media_pie_shares')
    share = models.FloatField()
    site = models.ForeignKey(Site, related_name='media_pie_shares')
    start_date = models.DateField('Start Date')
    end_date = models.DateField('End Date', null=True, blank=True)

    def __unicode__(self):
        return self.affiliate.name
    
    def clean(self):
        if self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError(_("""Please check your dates.  You can't  
                    end a share before it starts"""))            
            if self.start_date == self.end_date:
                raise ValidationError(_("""Please check your dates.  Start and  
                    end dates can't be equal."""))
        self.clean_all_media_pie_shares()
        self.check_shares_less_than_one()
        return self
        
    def clean_all_media_pie_shares(self):
        """
        Do all appropriate cleaning on all the media pie shares.
        """
        media_pie_shares = MediaPieShare.objects.filter(affiliate=self.affiliate)
        for media_pie_share in media_pie_shares:
            start_date = media_pie_share.start_date
            end_date = media_pie_share.end_date                
            if self.id != media_pie_share.id:
                if end_date is None:
                    self.compare_share_has_no_end_date(start_date)
                else:
                    self.compare_share_has_end_date(start_date, end_date)
        return self
    
    def compare_share_has_no_end_date(self, start_date):
        """
        Compare these 2 shares. The share getting compared has an no 
        end date.
        """
        if self.end_date is None:
            raise ValidationError(_("""Only one active share allowed
                 in a given time period for a give affiliate."""))
        else:
            if self.end_date > start_date:
                raise ValidationError(_("""You can't set the end 
                    date greater than another shares start date."""))
            if self.end_date == start_date:
                raise ValidationError(_("""You can't set the end 
                    date equal to another shares start date."""))
        return self
    
    def compare_share_has_end_date(self, start_date, end_date):
        """
        Compare these 2 shares. The share getting compared has an end date.
        """
        if self.start_date >= start_date and self.start_date <= end_date:
            raise ValidationError(_("""This affiliates shares can't 
                overlap."""))
        if self.end_date:
            if start_date >= self.start_date and start_date <= self.end_date:
                raise ValidationError(_("""This affiliates shares 
                    can't overlap."""))
            if self.start_date <= start_date and self.end_date >= end_date:
                raise ValidationError(_("""This share can't start 
                    before another share start and end after the 
                    other share ends."""))
            if self.end_date <= end_date and self.start_date >= start_date:
                raise ValidationError(_("""You can't start and end a
                     share in the middle of another shares running 
                     time."""))
        else:
            if self.start_date < end_date:
                raise ValidationError(_("""You can't set the start 
                    date less than another shares end date."""))
            if self.start_date == end_date:
                raise ValidationError(_("""This start date can not 
                    be equal to share# %s's end date.""" % 
                    str(self.id)))
        return self
                            
    def check_shares_less_than_one(self):
        """
        Check to ensure total active shares don't add up to over 1 which is 100%.
        """
        media_pie_shares = MediaPieShare.objects.filter(site=self.site).order_by('start_date')
        # Total active shares for this site:
        total_shares = 0
        for media_pie_share in media_pie_shares:
            if self.id != media_pie_share.id:
                if self.end_date:
                    if (media_pie_share.start_date <= self.start_date and media_pie_share.end_date is None) or \
                    (media_pie_share.start_date <= self.start_date and media_pie_share.end_date >= self.start_date) or \
                    (self.start_date <= media_pie_share.start_date and self.end_date >= media_pie_share.start_date):
                        total_shares = total_shares + media_pie_share.share
                else:
                    if (media_pie_share.end_date is None) or \
                    (self.start_date <= media_pie_share.start_date) or \
                    (self.start_date >= media_pie_share.start_date and self.start_date <= media_pie_share.end_date):
                        total_shares = total_shares + media_pie_share.share                        
        total_shares += self.share        
        if total_shares > 1:    
            raise ValidationError(_("""Can't have active shares adding up to over 
                100%. If shares for this affiliate are changing, please give the
                older shares that are changing an end date."""))
        return self                

    def save(self, *args, **kwargs):
        self.clean()
        super(MediaPieShare, self).save(*args, **kwargs)
        return self

class Outlet(models.Model):
    """
    An Outlet could be an Affiliate sub groups... Like 'WRRV' radio station would
    be an example of an Outlet.
    """
    name = models.CharField(max_length=25)
    affiliate = models.ForeignKey(Affiliate, related_name='outlets')
    band = models.CharField(choices=(('AM','AM'),('FM','FM')), max_length=2)
    frequency = models.CharField(max_length=5)
    format = models.CharField(max_length=25)
    slogan = models.TextField(max_length=50)
    website = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='logos')
    
    def __unicode__(self):
        return self.name
    
