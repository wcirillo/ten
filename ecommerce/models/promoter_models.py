""" Promoter models for ecommerce app """

import datetime
import logging

from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models 
from django.utils.translation import ugettext_lazy as _

from common.utils import generate_guid
from ecommerce.models.order_models import Order
from ecommerce.validators import require_date_not_past, require_percent

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

PROMO_TYPE_CHOICES = (
    ('1', _('% discount')),
    ('2', _('Fixed amount discount')),
    ('3', _('Fixed amount cost')),
)
USE_METHOD_CHOICES = (
    ('1', _('No limitation')),
    ('2', _('This promo can be used once per advertiser')),
    ('3', _('This promo can only be ever used once (like a gift certificate)')),
    ('4', _('Can be used a fixed number of times per month')),
)
CODE_METHOD_CHOICES = (
    ('one', _('Everyone uses the same code')),
    ('unique', _('Everyone gets his own unique code')),
)

def now_plus_365():
    """ Return this date plus 365 days. """
    return datetime.date.today() + datetime.timedelta(days=365)


class PromoterManager(models.Manager):
    """ Default manager for Promoter class."""
    def get_by_natural_key(self, name):
        """ Sane serialization. """
        return self.get(name=name)


class Promoter(models.Model):
    """ A way to describe a user who has promotions and receives a cut. """
    name = models.CharField(max_length=48, unique=True, db_index=True)
    content_type = models.ForeignKey(ContentType, blank=True, null=True,
        help_text=_("Which kind of object is this promoter related to?"))
    object_id = models.PositiveIntegerField(_('Object id'), blank=True, 
        null=True,
        help_text=_("Which instance is this promoter related to?"))
    related_object = generic.GenericForeignKey(ct_field="content_type",
        fk_field="object_id")
    guid = models.CharField(max_length=40, unique=True, null=True, blank=True,
        help_text=_("This gets generated automatically."))
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_paid_traffic = models.BooleanField(default=False)
    start_date = models.DateField(_('date promoter starts'), 
        default=datetime.date.today)
    end_date = models.DateField(_('date promoter ends'), blank=True, null=True)
    promoter_cut_percent = models.DecimalField(max_digits=5, decimal_places=2, 
        default=0, validators=[require_percent])
    create_datetime = models.DateTimeField(_('date/time created'), 
        auto_now_add=True)
    objects = PromoterManager()
    
    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Promoter")
        verbose_name_plural = _("Promoters")
    
    def __unicode__(self):
        return u'%s' % self.name

    def natural_key(self):
        """ Sane serialization. """
        return (self.name,)

    def save(self, *args, **kwargs):
        if not self.id:
            self.guid = generate_guid()
        super(Promoter, self).save(*args, **kwargs)

    def clean(self):
        if not self.start_date:
            self.start_date = datetime.date.today()
        if not self.id:
            require_date_not_past(self.start_date)
            if self.end_date:
                require_date_not_past(self.end_date)
        if self.end_date and self.end_date <= self.start_date:
            raise ValidationError(_('End date must be after start date.'))

    def delete(self, *args, **kwargs):
        if PromotionCode.objects.select_related('promotion__promoter').filter(
                promotion__promoter=self, 
                used_count__gt=0
            ).exists():
            error_message = \
                'Cannot delete a promoter having a promotion that has been used'
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(_(error_message))
        super(Promoter, self).delete(*args, **kwargs)


class PromotionManager(models.Manager):
    """ Default manager for Promotion class."""
    def get_by_natural_key(self, name):
        """ Sane serialization. """
        return self.get(name=name)


class Promotion(models.Model):
    """ A product promotion. """
    promoter = models.ForeignKey(Promoter, related_name='promotions')
    product = models.ManyToManyField('ecommerce.Product', 
        related_name='promotions')
    name = models.CharField(max_length=48, unique=True, db_index=True)
    description = models.CharField(max_length=64)
    promo_type = models.CharField(max_length=1, choices=PROMO_TYPE_CHOICES)
    promo_amount = models.SmallIntegerField(max_length=3, default=0,
        validators=[MinValueValidator(0)])
    use_method = models.CharField(max_length=1, choices=USE_METHOD_CHOICES)
    monthly_usages_allowed = models.SmallIntegerField(max_length=3, 
        default=0, validators=[MinValueValidator(0)], 
        help_text=_("Ignored except for 'x times per month' promos"))
    code_method = models.CharField(max_length=16, choices=CODE_METHOD_CHOICES)
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(_('date promotion starts'), 
        default=datetime.date.today)
    end_date = models.DateField(_('date promotion ends'), default=now_plus_365,
        validators=[require_date_not_past])
    create_datetime = models.DateTimeField(_('Date/time Created'), 
        auto_now_add=True)
    objects = PromotionManager()

    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Promotion")
        verbose_name_plural = _("Promotions")
    
    def __unicode__(self):
        return u'Promotion %s: %s' % (self.id, self.description)

    def natural_key(self):
        """ Sane serialization. """
        return (self.name,)

    def clean(self):
        if self.id:
            if self.promotion_codes.filter(used_count__gt=0).exists():
                self.check_modify_used_promo()
        else:
            # This rule only applies on create.
            require_date_not_past(self.start_date)
        if self.end_date <= self.start_date:
            raise ValidationError(_('End date must be after start date.'))
        # 0% off = $0 off. Normalize to the former.
        if self.promo_amount == 0 and self.promo_type == '2':
            self.promo_type = '1'
        if self.use_method == '3':
            if self.code_method == 'unique':
                raise ValidationError(_("""For promotions that can only ever be 
                    used once (like a gift certificate), selecting unique codes
                    is not valid."""))
        if self.use_method == '4':
            if self.monthly_usages_allowed == 0:
                raise ValidationError(_("""For monthly usage promotions, specify
                    number of uses per month allowed."""))
        else:
            self.monthly_usages_allowed = 0

    def check_modify_used_promo(self):
        """ Prevent modifying significant terms of a used promo. """
        original = Promotion.objects.get(id=self.id)
        error_msg = "Cannot change %s once the promo has been used."
        if self.promoter != original.promoter:
            raise ValidationError(_(error_msg % 'promoter'))
        elif self.promo_type != original.promo_type:
            raise ValidationError(_(error_msg % 'promoter type'))
        elif self.promo_amount != original.promo_amount:
            raise ValidationError(_(error_msg % 'promo amount'))
        elif self.use_method != original.use_method:
            raise ValidationError(_(error_msg % 'use method'))
        elif self.code_method != original.code_method:
            raise ValidationError(_(error_msg % 'code method'))
    
    def delete(self, *args, **kwargs):
        if PromotionCode.objects.filter(
                promotion=self, used_count__gt=0).exists():
            error_message = 'Cannot delete a promotion with a used code.'
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(_(error_message))
        super(Promotion, self).delete(*args, **kwargs)
        
    def can_be_used(self):
        """ Validate promotion for instance """
        if not self.is_active:
            raise ValidationError(_('Promotion is not active.'))
        if not self.promoter.is_active:
            raise ValidationError(_('Promoter is not active.'))
        if not self.promoter.is_approved:
            raise ValidationError(_('Promoter is not approved.'))
        today = datetime.date.today()
        if today < self.start_date:
            raise ValidationError(_('This promotion has not started yet.'))
        elif today > self.end_date:
            raise ValidationError(_('This promotion is already over.'))
        if today < self.promoter.start_date:
            raise ValidationError(_('This promoter is not valid yet.'))
        elif self.promoter.end_date and today > self.promoter.end_date:
            raise ValidationError(_('This promoter is no longer valid.'))
        if not self.product.filter(is_active=True).exists():
            raise ValidationError(_(
                'This promotion is not for a product that is active.'))
        LOG.debug('promotion use method %s' % self.use_method)
        self.can_be_used_by_use_method()
        
    def can_be_used_by_use_method(self):
        """ Validate based on use_method. """
        if self.use_method == '3':
            # Promotion can only be used once ever, like a gift certificate.
            used_count = self.promotion_codes.aggregate(
                    sum_used=models.Sum('used_count')
                )['sum_used']
            LOG.debug('promotion used_count %s' % used_count)
            if used_count > 0:
                raise ValidationError(_('This promotion is used up.'))
        elif self.use_method == '4':
            # Promotion can be used max x times per month.
            start_month = datetime.datetime.combine(
                datetime.date.today().replace(day=1), datetime.time())
            used_count = Order.objects.filter(
                    promotion_code__in=self.promotion_codes.all(), 
                    create_datetime__gt=start_month
                ).count()
            LOG.debug('promotion monthly usages allowed %s' 
                % self.monthly_usages_allowed)
            LOG.debug('used count %s' % used_count)
            if used_count >= self.monthly_usages_allowed:
                error_message = 'This monthly promotion is used up.'
                LOG.debug(error_message)
                raise ValidationError(_(error_message))

    def can_be_used_by_advertiser(self, order):
        """ Validate this promotion can be used by this advertiser. """
        if self.use_method == '2':
            # Promo can be used at most once by this advertiser.
            if Order.objects.exclude(id=order.id).filter(
                        promotion_code__in=self.promotion_codes.all(),
                        order_items__business__advertiser=order.order_items.all(
                            )[0].business.advertiser
                    ).count():
                error_message = 'This promotion has already been used.'
                LOG.debug(error_message)
                raise ValidationError(_(error_message))


class PromotionCodeManager(models.Manager):
    """ Default manager for PromotionCode class."""
    def get_by_natural_key(self, code):
        """ Sane serialization. """
        return self.get(code=code)


class PromotionCode(models.Model):
    """ The code a customer enters to receive a promotion. """
    # TO DO: How is this associated with an advertiser who:
    # is eligible to use it, when code is unique per advertiser?
    # has used it, when code is for everyone and usable once per advertiser?
    promotion = models.ForeignKey(Promotion, related_name='promotion_codes')
    code = models.CharField(max_length=64, unique=True, db_index=True)
    used_count = models.PositiveSmallIntegerField(max_length=8, default=0,
        editable=False,
        help_text=_('How many times has this promo been used?'))
    objects = PromotionCodeManager()
    
    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Promotion Code")
        verbose_name_plural = _("Promotion Codes")
    
    def __unicode__(self):
        return u'%s' % self.code
    
    def natural_key(self):
        """ Sane serialization. """
        return (self.code,)

    def delete(self, *args, **kwargs):
        if self.used_count > 0:
            error_message = 'Cannot delete a promotion code that has been used:'
            LOG.error('%s %s' % (error_message, self.code))
            raise ValidationError(_(error_message))
        super(PromotionCode, self).delete(*args, **kwargs)
        
    def clean_code(self):
        """ Checks if a PromoCode exists. """
        if PromotionCode.objects.filter(code__iexact=self.code):
            return True
        else:
            return False  

    def decrement_used_count(self):
        """ Decrement used_count of this promotion_code. """
        self.used_count = models.F('used_count') - 1
        self.save()

    def increment_used_count(self):
        """ Increment used_count of this promotion_code. """
        self.used_count = models.F('used_count') + 1
        self.save()
        LOG.debug("incremented promo '%s' used count" % self.code)
