""" Payment models for ecommerce app """

import datetime
from dateutil import relativedelta
import logging

from esapi.core import ESAPI

from django.core.exceptions import ValidationError
from django.db import models 
from django.utils.translation import ugettext_lazy as _

from advertiser.models import Business
from ecommerce.validators import get_cc_type_from_number

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

CC_TYPE_CHOICES = (
    ('visa', _('Visa')),
    ('mastercard', _('MasterCard')),
    ('amex', _('American Express')),
    ('discover', _('Discover'))
)

PAYMENT_METHOD_CHOICES = (
    ('C', _('credit card')),
    ('D', _('debit card')),
    ('K', _('check')),
    ('E', _('electronic check')),
    ('M', _('money order')),
)
STATUS_CHOICES = (
    ('P', _('PENDING')), # This is for us, not a USAePay Status.
    ('A', _('APPROVED')),
    ('D', _('DECLINED')),
    ('E', _('ERROR')),
    ('J', _('ADJUSTMENT')),
    ('R', _('REFUND')),
    ('B', _('BAD DEBT')),
)

RESPONSE_STATUS_CHOICES = (
    ('A', _('APPROVED')),
    ('D', _('DECLINED')),
    ('E', _('ERROR')),
    ('V', _('VERIFICATION')),
)
AVS_RESULT_CHOICES = (
    ('YYY', _('Address: Match & 5 Digit Zip: Match')),
    ('NYZ', _('Address: No Match & 5 Digit Zip: Match')),
    ('YNA', _('Address: Match & 5 Digit Zip: No Match')),
    ('NNN', _('Address: No Match & 5 Digit Zip: No Match')),
    ('YYX', _('Address: Match & 9 Digit Zip: Match')),
    ('NYW', _('Address: No Match & 9 Digit Zip: Match')),
    ('XXW', _('Card Number Not On File')),
    ('XXU', _('Address Information not verified for domestic transaction')),
    ('XXR', _('Retry / System Unavailable')),
    ('XXS', _('Service Not Supported')),
    ('XXE', _('Address Verification Not Allowed For Card Type')),
    ('XXG', _('Global Non-AVS participant')),
    ('YYG', _('International Address: Match & Zip: Not Compatible')),
    ('GGG', _('International Address: Match & Zip: Match')),
    ('YGG', _('International Address: No Compatible & Zip: Match')),
)
CVV2_RESULT_CHOICES = (
    ('M', _('Match')),
    ('N', _('No Match')),
    ('P', _('Not Processed')),
    ('S', _('Should be on card but not so indicated')),
    ('U', _('Issuer Not Certified')),
    ('X', _('No response from association')),
)


class CreditCard(models.Model):
    """ A credit card. """
    cc_type = models.CharField(max_length=10, choices=CC_TYPE_CHOICES, 
        null=True, blank=True)
    encrypted_number = models.CharField(_('Encrypted credit card number'), 
        max_length=128, editable=False, null=True)
    business = models.ForeignKey(Business, related_name='credit_cards')
    is_storage_opt_in = models.BooleanField(_('Store this card info'), 
        default=False, 
        help_text=_("""Has the user opted for us to save this?"""))
    exp_month = models.PositiveSmallIntegerField(_('Expiration Month'),
        null=True)
    exp_year = models.PositiveSmallIntegerField(_('Expiration Year'), 
        null=True)
    card_holder = models.CharField(_('Name on card'), max_length=64, null=True)
    last_4 = models.CharField(_('Last four digits of card num'), max_length=4, 
        null=True)
    
    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Credit Card")
        verbose_name_plural = _("Credit Cards")
        
    def __unicode__(self):
        return u'%s: %s' % (self.id, self.business.business_name)
        
    def save(self, *args, **kwargs):
        """ Save a credit card, setting cc_type. """
        try:
            self.cc_type = get_cc_type_from_number(self.decrypt_cc())
        except AttributeError:
            # If cc is blank and made it this far (coming from admin), then
            # the cc_type is already in the database and must be preserved.
            pass
        super(CreditCard, self).save(*args, **kwargs)
        
    def encrypt_cc(self, cc_number):
        """ Encrypt credit card number for safe storage. """
        # Generate last_4
        self.last_4 = cc_number[-4:]
        # Encrypt
        instance = ESAPI.encryptor()
        self.encrypted_number = instance.encrypt(cc_number)
        
    def decrypt_cc(self):
        """ Decrypt a credit card. """
        instance = ESAPI.encryptor()
        cc_number = instance.decrypt(self.encrypted_number)
        return cc_number
        
    def clean(self):
        """ Clean a credit card. """
        if type(self.exp_month) != int or type(self.exp_year) != int:
            raise ValidationError(_('Card expiration date must be numeric.'))
        if int(self.exp_month) < 1 or int(self.exp_month) > 12:
            raise ValidationError(
                _('Card expiration month must be between 1 and 12.'))
        LOG.debug('cc clean method: exp year %s exp month %s' % 
            (self.exp_year, self.exp_month))
        # Expiration date is the last day of the month.
        expiration_date = (
            datetime.date(2000 + self.exp_year, self.exp_month, 1) + 
            relativedelta.relativedelta(months=1) -
            relativedelta.relativedelta(days=1))
        today = datetime.date.today()
        LOG.debug('cc clean method: exp date %s today %s' % 
            (expiration_date, today))
        if today > expiration_date:
            raise ValidationError(_('Card expired.'))
        # Ensure expiration is less than 30 years away.
        if expiration_date > today + datetime.timedelta(days=365*30):
            raise ValidationError(_('Card expiration date is not valid.'))
    
    def delete_private_data(self, *args, **kwargs):
        """
        Purge stuff we don't want to store unless user has given us
        permission to store. Keep minimum for audit trail.
        """
        self.exp_month = None
        self.exp_year = None
        self.encrypted_number = None
        self.card_holder = None
        super(CreditCard, self).save(
                force_insert=False, force_update=True, **kwargs
            )
            
    def delete(self, *args, **kwargs):
        """ 
        Maintain cc_type and last_4_digits for account statement reporting.
        """
        self.delete_private_data(self, *args, **kwargs)

        
class Payment(models.Model):
    """ The payment record(s) of an order. """
    order = models.ForeignKey('ecommerce.Order', related_name='payments')
    credit_card = models.ForeignKey(CreditCard, related_name='payments', 
        null=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0,)
    method = models.CharField(max_length=1, choices=PAYMENT_METHOD_CHOICES, 
        default='C')
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, 
        default='p')
    create_datetime = models.DateTimeField(_('date/time created'), 
        auto_now_add=True)
    is_void = models.BooleanField(_('Has this been voided?'), default=False)
    is_locked = models.BooleanField(_('Is this payment locked?'), 
        default=False)
    
    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        
    def __unicode__(self):
        return u'%s: %s %s' % (self.id, self.get_status_display(), self.amount)
    
    def save(self, *args, **kwargs):
        self.check_if_locked()
        super(Payment, self).save(*args, **kwargs)
    
    def check_if_locked(self):
        """ Check if this payment is locked. """
        if self.id:
            original = Payment.objects.get(id=self.id)
            if original.is_locked:
                error_message = 'Cannot modify a locked payment.'
                LOG.error('%s %s' % (error_message, self.id))
                raise ValidationError(_(error_message))
    
    def clean(self):
        self.check_if_locked()
        
    def delete(self, *args, **kwargs):
        if self.is_locked:
            error_message = 'Cannot delete locked payment'
            LOG.error('%s %s' % (error_message, self.id))
            raise ValidationError(_(error_message))
        super(Payment, self).delete(*args, **kwargs)


class PaymentResponse(models.Model):
    """
    When the payment is by credit card, more info about the response from
    credit care processor.
    
    See http://wiki.usaepay.com/developer/transactionapi for more info,
    althought this model stores payment responses for all gateways, not just
    USAePay.
    """
    payment = models.OneToOneField(Payment, related_name='payment_responses')
    status = models.CharField(max_length=1, choices=RESPONSE_STATUS_CHOICES)
    reference_number = models.CharField(max_length=10, blank=True)
    batch = models.CharField(max_length=10, blank=True)
    error_description = models.CharField(max_length=255, blank=True)
    avs_result_code = models.CharField(max_length=3, 
        choices=AVS_RESULT_CHOICES, blank=True)
    cvv2_result_code = models.CharField(max_length=1, 
        choices=CVV2_RESULT_CHOICES, blank=True)
    converted_amount = models.DecimalField(max_digits=6, decimal_places=2, 
        null=True, blank=True)
    conversion_rate = models.DecimalField(max_digits=6, decimal_places=4, 
        null=True, blank=True)
    is_duplicate = models.BooleanField(default=False, 
        help_text='Was this flagged as a duplicate transaction?')
     
    class Meta:
        app_label = 'ecommerce'
        verbose_name = _("Payment Response")
        verbose_name_plural = _("Payment Responses")
        
    def __unicode__(self):
        return u'Payment Response %s: %s' % (self.id, self.status)
    
    def save(self, *args, **kwargs):
        self.check_if_locked()
        super(PaymentResponse, self).save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        self.check_if_locked()
        super(PaymentResponse, self).delete(*args, **kwargs)
    
    def check_if_locked(self):
        """ Check if Payment is locked. """
        if self.id:
            # Get the payment as is exists in the db now.
            payment = Payment.objects.get(id=self.payment.id)
            if payment.is_locked:
                error_message = 'Cannot modify responses of a locked payment.'
                LOG.error('%s %s' % (error_message, self.id))
                raise ValidationError(_(error_message))
                
    def clean(self):
        self.check_if_locked()
        # Clean data based on http://wiki.usaepay.com/developer/avsresultcodes. 
        if self.avs_result_code in ('Y', 'YYA', 'YYD'):
            self.avs_result_code = 'YYY'
        elif self.avs_result_code == 'Z':
            self.avs_result_code = 'NYZ'
        elif self.avs_result_code in ('A', 'YNY'):
            self.avs_result_code = 'YNA'
        elif self.avs_result_code in ('N', 'NN'):
            self.avs_result_code = 'NNN'
        elif self.avs_result_code == 'X':
            self.avs_result_code = 'YYX'
        elif self.avs_result_code == 'W':
            self.avs_result_code = 'NYW'
        elif self.avs_result_code in ('R', 'U', 'E'):
            self.avs_result_code = 'XXR'
        elif self.avs_result_code == 'S':
            self.avs_result_code = 'XXS'
        elif self.avs_result_code in ('G', 'C', 'I'):
            self.avs_result_code = 'XXG'
        elif self.avs_result_code in ('B', 'M'):
            self.avs_result_code = 'YYG'
        elif self.avs_result_code == 'D':
            self.avs_result_code = 'GGG'
        elif self.avs_result_code == 'P':
            self.avs_result_code = 'YGG'

