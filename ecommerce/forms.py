""" Forms for ecommerce app """

from django import forms

from advertiser.models import BillingRecord
from common.custom_validation import validate_promo_code
from ecommerce.models import CreditCard
from ecommerce.service.credit_card_service import CreditCardService
from common.custom_cleaning import strip_to_numbers, trim_fields_in_form
from common.form_widgets import USStateSelect, RadioSelect
from ecommerce.validators import get_cc_type_from_number


class CheckoutProductSelection(forms.Form):
    """ Form field toggle control between product payment options. Used to
    switch between slot monthly payment and slot annual payment. This field is
    hidden to the user.
    """
    selected_product_id = forms.CharField()

    
class CheckoutCouponCreditCardForm(forms.ModelForm):
    """ Checkout coupon credit card form """
    cc_number = forms.CharField(widget=forms.TextInput(attrs={
        'size':'35',
        'maxlength':'19',
        'tabindex':'1',
        'autocomplete':'off',
        'onkeypress':'return formatCardNumber(this,event.keyCode,event.which)',
        'onblur':'return formatCardNumber(this,event.keyCode,event.which)'
        }))
    cvv_number = forms.CharField(widget=forms.TextInput(attrs={
        'size':'5',
        'maxlength':'4',
        'tabindex':'4'
        }))
    
    class Meta:
        model = CreditCard
        fields = ('exp_month', 'exp_year', 'card_holder',)
        widgets = {
            'exp_month': forms.TextInput(attrs={
                'size':'3',
                'maxlength':'2',
                'tabindex':'2'
                }),
            'exp_year': forms.TextInput(attrs={
                'size':'3',
                'maxlength':'2',
                'tabindex':'3'
                }),
            'card_holder': forms.TextInput(attrs={
                'size':'35',
                'maxlength':'50',
                'tabindex':'5'
                }),        
        }     
        
    def clean(self):
        """ Clean form fields. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data
    
    def clean_cc_number(self):
        """ Clean and strip out invalid characters from cc_number. """
        cc_number = strip_to_numbers(self.cleaned_data.get('cc_number', None))
        credit_card_service = CreditCardService(cc_number, None)
        is_verified, error_msg = credit_card_service.validate_cc_number()
        if not is_verified:
            raise forms.ValidationError(error_msg)
        self.cleaned_data['cc_number'] = cc_number
        return self.cleaned_data['cc_number']
    
    def clean_cvv_number(self):
        """ Clean and strip out invalid characters from cvv number. """
        cvv_number = self.cleaned_data.get('cvv_number', None)
        if cvv_number == "":
            raise forms.ValidationError("This field is required.")
        cvv_number = cvv_number.strip()
        if not cvv_number.isdigit():
            raise forms.ValidationError("CVV Code has invalid digits.")
        self.cleaned_data['cvv_number'] = cvv_number
        return self.cleaned_data['cvv_number']
    
    def clean_card_holder(self):
        """ Clean and strip out spaces from card holder's name. """        
        self.cleaned_data['card_holder'] = self.cleaned_data.get('card_holder', None).strip()
        if self.cleaned_data['card_holder'] == "":
            raise forms.ValidationError("Card Holder's name is required.")
        return self.cleaned_data['card_holder']
    
    def create_or_update(self, business_id, credit_card_id=None):
        """ Retrieve credit card from previous payment submit or create new 
        credit card record. Return credit card.
        """
        cc_number = self.cleaned_data['cc_number'].encode()
        exp_month = self.cleaned_data['exp_month']
        exp_year = self.cleaned_data['exp_year']
        cvv_number = self.cleaned_data['cvv_number']
        card_holder = self.cleaned_data['card_holder']
        try:
            credit_card = CreditCard.objects.get(id=credit_card_id,
                business__id=business_id)
            credit_card.exp_month = exp_month
            credit_card.exp_year = exp_year
            credit_card.card_holder = card_holder
        except CreditCard.DoesNotExist:
            credit_card = CreditCard(business_id=business_id, 
                exp_month=exp_month, exp_year=exp_year, 
                card_holder=card_holder)
        credit_card.cvv2 = cvv_number
        credit_card.cc_type = get_cc_type_from_number(cc_number)
        credit_card.encrypt_cc(cc_number)
        credit_card.is_storage_opt_in = True
        credit_card.save()
        return credit_card


class CheckoutCouponBillingRecordForm(forms.ModelForm):
    """ The billing record form during coupon purchase """
    class Meta:
        model = BillingRecord
        fields = ('billing_address1', 'billing_address2', 'billing_city',
                    'billing_state_province', 'billing_zip_postal')
        widgets = {
            'billing_address1': forms.TextInput(attrs={
                'size':'35','maxlength':'50',
                'tabindex':'6'
                }),
            'billing_address2': forms.TextInput(attrs={
                'size':'35',
                'maxlength':'50',
                'tabindex':'7'
                }),
            'billing_city': forms.TextInput(attrs={
                'size':'35',
                'maxlength':'50',
                'tabindex':'8'
                }),
            'billing_state_province': USStateSelect(attrs={'tabindex':'9'}),
            'billing_zip_postal': forms.TextInput(attrs={
                'size':'10',
                'maxlength':'9',
                'tabindex':'10'
                }),         
                }        
    def clean(self):
        """ 
        Clean all fields and de-populate default state if no other address 
        info is present.
        """
        self.cleaned_data = trim_fields_in_form(self)
        if not self.cleaned_data['billing_zip_postal'] and not self.cleaned_data['billing_city'] \
        and not self.cleaned_data['billing_address2'] and not self.cleaned_data['billing_address1']:
            self.cleaned_data['billing_state_province'] = ""
        return self.cleaned_data

    def create_or_update(self, business_id, billing_record_id=None):
        """ Retrieve billing record from previous payment submit or create new 
        billing record. Return billing record.
        """
        billing_address1 = self.cleaned_data['billing_address1']
        billing_address2 = self.cleaned_data['billing_address2']
        billing_city = self.cleaned_data['billing_city']
        billing_state_province = self.cleaned_data['billing_state_province']
        billing_zip_postal = self.cleaned_data['billing_zip_postal']
        try:
            billing_record = BillingRecord.objects.get(id=billing_record_id,
                business__id=business_id)
            billing_record.billing_address1 = billing_address1
            billing_record.billing_address2 = billing_address2
            billing_record.billing_city = billing_city
            billing_record.billing_state_province = billing_state_province
            billing_record.billing_zip_postal = billing_zip_postal
        except BillingRecord.DoesNotExist:
            billing_record = BillingRecord(business_id=business_id,
                billing_address1 = billing_address1,
                billing_address2 = billing_address2,
                billing_city = billing_city,
                billing_state_province = billing_state_province,
                billing_zip_postal = billing_zip_postal)
        billing_record.save()
        return billing_record
        
class CheckoutCouponPromoCodeForm(forms.Form):
    """ . """
    code = forms.CharField(widget=forms.TextInput(
        attrs={
            'size':'15',
            'maxlength':'64'
            }), 
        required=False
        )
    def clean(self):
        """ Clean CheckoutCouponPromoCodeForm fields. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data
    
    def clean_code(self):
        self.cleaned_data['code'] = self.cleaned_data.get('code', None).strip()
        validate_promo_code(self, self.cleaned_data['code'], 'code')
        return self.cleaned_data['code']
    
class AddSlotForm(forms.Form):
    """
    This form allows an advertiser to add a New Slot and possibly Flyers.
    """
    def __init__(self, *args, **kwargs):
        super(AddSlotForm, self).__init__(*args, **kwargs)
        all_choices = (
            '1', 'One Flyer',
            '2', 'Two Flyers',
            '3', 'Three Flyers',
            '4', 'Four Flyers',
            '0', 'No Flyers',
        )
        slot_choices = all_choices[0:2], all_choices[2:4], all_choices[4:6], all_choices[6:8], all_choices[8:10] 
        self.fields['add_slot_choices'] = forms.ChoiceField(widget=RadioSelect, choices=slot_choices, initial="1")
    
    def clean(self):
        """ Clean AddSlotForm fields. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data
    
class AddFlyersForm(forms.Form):
    """
    This form allows an advertiser to add Flyers to an existing Slot.
    """
    def __init__(self, *args, **kwargs):
        super(AddFlyersForm, self).__init__(*args, **kwargs)
        all_choices = (
            '1', 'Choice 1',
            '2', 'Choice 2',
            '3', 'Choice 3',
            '4', 'Choice 4',
        )
        flyer_choices = all_choices[0:2], all_choices[2:4], all_choices[4:6], all_choices[6:8] 
        self.fields['add_flyer_choice'] = forms.ChoiceField(widget=RadioSelect, choices=flyer_choices, initial="2")
        
    def clean(self):
        """ Clean AddFlyersForm fields. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data
