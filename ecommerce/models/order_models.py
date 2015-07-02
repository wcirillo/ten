""" Order models for ecommerce app """
#pylint: disable=W0613
from decimal import Decimal
import datetime
import logging

from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ecommerce.service.calculate_current_price import calculate_current_price
from ecommerce.service.compute_amount_discounted import (
    compute_amount_discounted)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

METHOD_CHOICES = (
    ('C', _('credit card')),
    ('V', _('invoice')),
)


class Order(models.Model):
    """ A purchase transaction.
    
    An order with no cost shall use method 'invoice.'
    """
    billing_record = models.ForeignKey('advertiser.BillingRecord', 
        related_name='orders')
    method = models.CharField(max_length=2, choices=METHOD_CHOICES, default='V')
    promotion_code = models.ForeignKey('ecommerce.PromotionCode', 
        related_name='orders', blank=True, null=True, 
        verbose_name=_('tracking code'))
    subtotal = models.DecimalField(max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], editable=False,
        help_text=_("The sum of order item amounts."))
    amount_discounted = models.DecimalField(max_digits=8, decimal_places=2, 
        default=0, validators=[MinValueValidator(0)], editable=False,
        help_text=_("The amount saved off total due to this promotion."))
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], editable=False)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], editable=False)
    promoter_cut_amount = models.DecimalField(max_digits=8, decimal_places=2,
        default=0, validators=[MinValueValidator(0)], editable=False, 
        help_text=_("""The amount of the total reflecting the effective promoter  
        cut percentage in effect at the time of the order."""))
    invoice = models.CharField(max_length=24, blank=True,
        help_text=_('This gets created automatically.'))
    purchase_order = models.CharField(max_length=24, blank=True)
    create_datetime = models.DateTimeField(_('date/time created'), 
        auto_now_add=True)
    is_locked = models.BooleanField(_('Is this order locked?'), default=False)
    
    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        get_latest_by = 'create_datetime'
        
    def __unicode__(self):
        return u'%s' % self.invoice
        
    def save(self, *args, **kwargs):
        """ First, change PromotionCode.used_count if necessary.
        If this is update:
            If I have a promotion, but didn't use to, increment.
            If I have a promotion, and its different, increment new & decrement 
                old
            If I don't have a promotion, but use to, decrement.
        Else this is create:
            If I have a promotion, increment.
        """
        self.check_if_locked()
        if self.id:
            LOG.debug('updating order %s' % self.id)
            original = Order.objects.get(id=self.id)
            if self.promotion_code:
                LOG.debug('self.promotion_code: %s' % 
                    self.promotion_code)
                if original.promotion_code:
                    LOG.debug('original.promotion_code: %s' % 
                        original.promotion_code)
                    if self.promotion_code != original.promotion_code:
                        self.promotion_code.increment_used_count()
                        original.promotion_code.decrement_used_count()
                else:
                    self.promotion_code.increment_used_count()
            elif original.promotion_code:
                original.promotion_code.decrement_used_count()
        elif self.promotion_code:
            LOG.debug('creating order w/ code %s' % 
                self.promotion_code)
            self.promotion_code.increment_used_count()
        # Next, compute subtotal, tax, & promoter cut amount.
        self.compute_subtotal()
        self.compute_discount()
        self.compute_tax()
        self.compute_total()
        self.compute_promoter_cut_amount()
        super(Order, self).save(*args, **kwargs)
        
    def check_if_locked(self):
        """ Raise validation error if this Order is locked. """
        if self.id:
            original = Order.objects.get(id=self.id)
            if original.is_locked:
                error_message = 'Cannot modify a locked order.'
                LOG.error('%s %s' % (error_message, self.id))
                raise ValidationError(_(error_message))
    
    def is_promotion_valid_for_order(self):
        """ Validate this Promotion is valid for this Order. """
        LOG.debug('promotion code %s' % self.promotion_code)
        LOG.debug('self id %s' % self.id)
        do_test = False
        try:
            promotion = self.promotion_code.promotion
            has_promotion_code = True
        except AttributeError:
            has_promotion_code = False
        if has_promotion_code:
            self.is_promo_valid_for_order_item()
            if self.id:
                original = Order.objects.get(id=self.id)
                if original.promotion_code != self.promotion_code:
                    do_test = True
            else:
                do_test = True
        # Skip this test if modifying Order but not changing the promo code.
        if do_test:
            LOG.debug('doing test')
            promotion.can_be_used()
    
    def is_promo_valid_for_order_item(self):
        """ Validate this Promotion is valid for this Order with these
        OrderItems. These are all tests that can only be done when OrderItems
        are associated with the order.
        """
        if self.order_items.count() > 0:
            promotion = self.promotion_code.promotion
            products = promotion.product.filter(is_active=True)
            if self.order_items.filter(product__in=products).exists():
                pass
            else:
                error_message = 'This promotion is not valid for these items.'
                LOG.error(error_message)
                raise ValidationError(_(error_message))
            # Can this promotion be used by this advertiser?
            promotion.can_be_used_by_advertiser(self)

    def compute_subtotal(self):
        """ Sum order item amounts for this order, sets computed value. """
        if self.id:
            order_item_sum = self.order_items.all().aggregate(
                    models.Sum('amount')
                )
            self.subtotal = order_item_sum['amount__sum']
            # This would happen during create with post_save callback of itself:
            if self.subtotal == None:
                self.subtotal = 0
        else:
            self.subtotal = 0
    
    def compute_discount(self):
        """ Compute value for amount_discounted.
        Determines which OrderItems are for products that are associated with
        this promotion code.
        """
        try:
            promotion = self.promotion_code.promotion
            has_promotion_code = True
        except AttributeError:
            # If there used to be a promo, reset discount to 0.
            self.amount_discounted = 0
            self.promoter_cut_amount = 0
            has_promotion_code = False
        
        if self.order_items.count() == 0:
            self.amount_discounted = 0
            self.promoter_cut_amount = 0
            has_promotion_code = False
            
        if self.id and has_promotion_code:
            # Get all the active products associated with this promo code.
            LOG.debug(_('compute discount: promo id = %s') % 
                promotion.id)
            products = promotion.product.filter(is_active=True)
            # Get the sum of the amounts of qualifying order items.
            if self.order_items.count() == 0:
                self.amount_discounted = 0
            qualifying_items_subtotal = self.order_items.filter(
                        product__in=products
                    ).aggregate(models.Sum('amount'))['amount__sum']
            # There may be no qualifying items; items may be added later.
            if qualifying_items_subtotal:
                LOG.debug('compute discount: qualifying sub = %s' %
                    qualifying_items_subtotal)
                # Apply discount logic.
                self.amount_discounted = compute_amount_discounted(promotion,
                    qualifying_items_subtotal)

    def compute_promoter_cut_amount(self):
        """ Compute promoter cut amount, from the now discounted total. """
        if self.promotion_code:
            promoter_cut_amount = (self.total *
                self.promotion_code.promotion.promoter.promoter_cut_percent /
                Decimal(100))
            self.promoter_cut_amount = Decimal(
                str(round(promoter_cut_amount, 2)))
    
    def compute_tax(self):
        """ Easy until we have taxable products. """
        self.tax = 0
        
    def compute_total(self):
        """ Compute the total for this order. """
        self.total = self.subtotal - self.amount_discounted + self.tax
        
    def get_outstanding_balance(self):
        """ Outstanding balance = order.total - sum(approved payments) """
        LOG.debug('get_outstanding_balance: order.total = %s' % self.total)
        approved_payments = self.payments.filter(
                status='A'
            ).aggregate(models.Sum('amount'))
        approved_payments_sum = approved_payments['amount__sum']
        LOG.debug('get_outstanding_balance: approved_payments_sum = %s' 
            % approved_payments_sum)
        if approved_payments_sum == None:
            approved_payments_sum = 0
        outstanding_balance = self.total - approved_payments_sum
        LOG.debug('get_outstanding_balance: outstanding_balance = %s' 
            % outstanding_balance)
        return outstanding_balance
    
    def clean(self):
        self.check_if_locked()
        self.is_promotion_valid_for_order()
        self.compute_discount()
    
    def delete(self, *args, **kwargs):
        """ Prohibit deletion of locked orders. """
        if self.is_locked:
            error_message = 'Cannot delete locked order'
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(error_message)
        super(Order, self).delete(*args, **kwargs)


class OrderItem(models.Model):
    """ The itemization of an Order. """
    site = models.ForeignKey('market.Site', related_name='order_items')
    order = models.ForeignKey(Order, related_name='order_items')
    product = models.ForeignKey('ecommerce.Product', related_name='order_items')
    item_id = models.PositiveIntegerField(_('Item id'), blank=True, null=True,
        help_text=_("""For website placement or future flyer placement, which 
            slot? If the flyer placement has already occurred, which 
            FlyerCoupon?"""))
    business = models.ForeignKey('advertiser.Business',
        related_name='order_items')
    description = models.CharField(_('description'), max_length=150)
    units = models.PositiveSmallIntegerField(_('units'), default=1)
    amount = models.DecimalField(_('amount'), max_digits=8, decimal_places=2, 
        default=0, validators=[MinValueValidator(0)], editable=False)
    is_taxable = models.BooleanField(_('is taxable?'), default=False)
    start_datetime = models.DateTimeField(_('date/time service begins'), 
        default=datetime.datetime.now)
    end_datetime = models.DateTimeField(_('date/time service ends'))
    content_type = models.ForeignKey(ContentType, editable=False,
        limit_choices_to={"model__in": 
            ("slot", "flyercoupon", "flyerplacement")})
    ordered_object = generic.GenericForeignKey(ct_field="content_type",
        fk_field="item_id")
    
    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")
        get_latest_by = 'start_datetime'

    def __unicode__(self):
        return _(u'Order item %s: %s') % (self.id, self.description)

    def check_if_locked(self):
        """ Raise validation error if the order is locked. """
        if self.id:
            order = Order.objects.get(id=self.order.id)
            if order.is_locked:
                error_message = 'Cannot modify items of a locked order.'
                LOG.error('%s %s' % (error_message, self.id))
                raise ValidationError(_(error_message))
    
    def calculate_amount(self):
        """ Calculate this order items amount. """
        self.amount = calculate_current_price(self.product.id, site=self.site, 
            consumer_count=self.site.get_or_set_consumer_count()) * self.units
        
    def set_content_type(self):
        """ Set this order_items content type to the product type. """
        self.content_type = self.product.content_type
        
    def clean(self):
        self.check_if_locked()
        if self.start_datetime and self.end_datetime \
        and self.start_datetime > self.end_datetime:
            raise ValidationError(_('Start date must not be after end date.'))
        
    def save(self, *args, **kwargs):
        self.check_if_locked()
        if not self.amount or self.amount == 0:
            self.calculate_amount()
        if not self.id:
            self.set_content_type()
            if not self.order.invoice:
                self.order.invoice = '%s-%s' % (self.site.id, self.order.id)
        super(OrderItem, self).save(*args, **kwargs)
        # Now that order item is saved, give Order the opportunity to  
        # recalculate subtotal, promo discount, etc:
        self.order.save()
        
    def delete(self, *args, **kwargs):
        """ Prohibit deletion of order items of locked orders. """
        if self.order.is_locked:
            error_message = 'Cannot delete an order item of a locked order'
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(_(error_message))
        else:
            super(OrderItem, self).delete(*args, **kwargs)
            # Now that order item is deleted, give Order the opportunity to  
            # recalculate subtotal, promo discount, etc:
            self.order.save()
