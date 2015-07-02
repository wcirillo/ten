""" Admin config for ecommerce app """

from django.contrib import admin
from django import forms

from common.custom_cleaning import AdminFormClean
from ecommerce.models import (Product, Promoter, Promotion, PromotionCode,
    Order, OrderItem, CreditCard, Payment, PaymentResponse)
from ecommerce.forms import CheckoutCouponCreditCardForm
from market.models import Site


class PromotionCodeInline(admin.StackedInline):
    """ Promotion code inline used by Promotion """
    model = PromotionCode
    extra = 1
    form = AdminFormClean


class PaymentResponseInline(admin.StackedInline):
    """ Payment response inline used by Payment """
    model = PaymentResponse
    extra = 0
    form = AdminFormClean


class OrderItemInline(admin.StackedInline):
    """ Order Item Inline used by Order """
    model = OrderItem
    max_num = 10
    extra = 0
    readonly_fields = ('content_type', 'amount')
    search_fields = ['order__invoice',  'business__business_name']
    raw_id_fields = ('order', 'business')
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(OrderItemInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(OrderItemInline, self).queryset(request)
        self.data = OrderItem.objects.select_related().filter(id__in=qs
            ).defer('site__envelope', 
                'site__geom', 
                'site__point')
        return self.data


class ProductAdmin(admin.ModelAdmin):
    """ Admin class for Product """
    list_display = ('name', 'is_active', 'base_rate', 'base_units', 'base_days')
    actions = None
    form = AdminFormClean


class PromoterAdmin(admin.ModelAdmin):
    """ Admin class for Promoter """
    list_display = ('name', 'is_approved', 'is_active', 'start_date', 
         'end_date', 'promoter_cut_percent')
    form = AdminFormClean


class PromotionAdmin(admin.ModelAdmin):
    """ Admin class for Promotion """
    search_fields = ['name', 'description']
    list_display = ('name', 'promoter', 'description', 'is_active',
        'create_datetime')
    list_filter = ('create_datetime','promoter')
    inlines = [
        PromotionCodeInline,
    ]
    form = AdminFormClean

def promotion_name(obj):
    """ Return the promotion name for this promotion code. """
    return ("%s" % (obj.promotion.name))

class PromotionCodeAdmin(admin.ModelAdmin):
    """ Admin class for PromotionCode """
    list_display = ('code', promotion_name, 'used_count')
    form = AdminFormClean
    search_fields = ['code']


class CreditCardAdminForm(CheckoutCouponCreditCardForm):
    """ Admin class for Credit Card """
    cc_number = forms.CharField(widget=forms.TextInput(attrs={
                'size':'30', 'maxlength':'19'}),
                label='Card Number', required=False)
    last_4 = forms.CharField(widget=forms.TextInput(attrs={
                'size':'5', 'maxlength':'4'}),
                label='Last Four of Card Number', required=False)
    cvv_number = forms.CharField(widget=forms.TextInput(attrs={
                'size':'5', 'maxlength':'4'}),
                label='CVV', required=False)
    
    class Meta:
        model = CreditCard
        
    def __init__(self, *args, **kwargs):
        super(CreditCardAdminForm, self).__init__(*args, **kwargs)
        if kwargs.has_key('instance'):
            instance = kwargs['instance']
            self.encrypted_number = instance.encrypted_number
    
    def clean_cc_number(self):
        """ Preserve the cc_number from the database if blank, then proceed. """
        # If cc_number is blank, use previous data from DB to preserve it.
        if self.cleaned_data['cc_number'] == '':
            if getattr(self, 'encrypted_number', ''
                    ) != '' and self.encrypted_number:
                old_encrypted = self.encrypted_number
                model = super(CreditCardAdminForm, self).save(commit=False)
                model.encrypted_number = old_encrypted
                self.cleaned_data['cc_number'] = model.decrypt_cc()
                if model.last_4 != self.cleaned_data['last_4']:
                    # User is trying to change the last_4 of a card stored in 
                    # database without changing the card.
                    raise forms.ValidationError("""You must enter the full 
                        credit card number to change the last 4 of an existing 
                        card.""")
                # Encrypted value could be ''.
                if self.cleaned_data['cc_number'] != '':
                    return CheckoutCouponCreditCardForm.clean_cc_number(self)
        else:
            return CheckoutCouponCreditCardForm.clean_cc_number(self)
        return self.cleaned_data['cc_number']
        
    def clean_cvv_number(self):
        """ We do not input cvv_number through admin, pass. """
        pass
    
    def save(self, commit=True):
        """ Save credit card input. """
        model = super(CreditCardAdminForm, self).save(commit=False)
        if self.cleaned_data['cc_number'] != '':
            model.encrypted_number = self.cleaned_data['cc_number']
            # Encrypt cc_number.
            model.encrypt_cc(self.cleaned_data['cc_number'])
            # Update the last_4 field with the last four of decrypted cc_number.
            model.last_4 = self.cleaned_data['cc_number'][-4:]
        elif model.is_storage_opt_in:
            model.is_storage_opt_in = False
        if commit:
            model.save()
        return model

def advertiser(obj):
    """ The order this order_item is for. """
    invoice = obj.business.advertiser
    return ("%s" % (invoice))
advertiser.admin_order_field = 'business__advertiser'


class CreditCardAdmin(admin.ModelAdmin):
    """  Admin Class for Credit Card """
    form = CreditCardAdminForm
    fields = ('business', 'is_storage_opt_in', 'cc_type', 'exp_month',
        'exp_year', 'card_holder', 'last_4', 'cc_number' )
    actions = None
    list_display = ('id', 'business', advertiser)
    search_fields = ['business__business_name', 'business__advertiser__email']
    save_on_top = True
    raw_id_fields = ("business",)

    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(CreditCardAdmin, self).queryset(request)
        self.data = CreditCard.objects.select_related().filter(id__in=qs
            ).defer('business__advertiser__site__envelope', 
                'business__advertiser__site__geom', 
                'business__advertiser__site__point')
        return self.data


class OrderAdmin(admin.ModelAdmin):
    """ Admin class for Order """
    actions = None
    date_hierarchy = 'create_datetime'
    inlines = [
        OrderItemInline,
    ]
    list_display = ('invoice', 'subtotal', 'amount_discounted', 'total', 
        'promoter_cut_amount', 'create_datetime')
    list_filter = ('create_datetime',)
    search_fields = ['invoice', ]
    raw_id_fields = ('billing_record',)
    readonly_fields = ('subtotal', 'amount_discounted', 'total')
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(OrderAdmin, self).queryset(request)
        self.data = Order.objects.select_related().filter(id__in=qs
            ).defer('billing_record__business__advertiser__site__envelope', 
                'billing_record__business__advertiser__site__geom', 
                'billing_record__business__advertiser__site__point')
        return self.data

def order_invoice(obj):
    """ The order this order_item is for. """
    invoice = obj.order.invoice
    return ("%s" % (invoice))
order_invoice.admin_order_field = 'order__invoice'


class OrderItemAdmin(admin.ModelAdmin):
    """ Admin class for Order Item """
    actions = None
    date_hierarchy = 'start_datetime'
    list_filter = ('start_datetime', 'product', 'site__name' )
    list_display = (order_invoice, 'amount', 'product', 'units')
    search_fields = ['order__invoice', 'business__business_name', 'site__name']
    readonly_fields = ('amount', 'content_type',)
    raw_id_fields = ('order', 'business',)
    form = AdminFormClean

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(OrderItemAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)


class PaymentAdmin(admin.ModelAdmin):
    """ Admin class for Payment """
    actions = None
    date_hierarchy = 'create_datetime'
    inlines = [
        PaymentResponseInline,
    ]
    list_display = ('id', 'amount', 'method', 'status', 'create_datetime', 
        'is_void', 'is_locked')
    list_filter = ('create_datetime', 'status')
    ordering = ('-create_datetime',)
    search_fields = ['id','amount']
    raw_id_fields = ('order', 'credit_card',)
    form = AdminFormClean


class PaymentResponseAdmin(admin.ModelAdmin):
    """ Admin class for Payment Response """
    list_display = ('id', 'status', 'reference_number', 'batch',
        'is_duplicate')
    list_filter = ('status',)
    search_fields = ['payment__id',]
    raw_id_fields = ('payment',)
    form = AdminFormClean

admin.site.register(Product, ProductAdmin)
admin.site.register(Promoter, PromoterAdmin)
admin.site.register(Promotion, PromotionAdmin)
admin.site.register(PromotionCode, PromotionCodeAdmin)
admin.site.register(CreditCard, CreditCardAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(PaymentResponse, PaymentResponseAdmin)
