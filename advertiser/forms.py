""" Forms for the advertiser model """

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.forms.util import ErrorList

from common.custom_cleaning import trim_fields_in_form
from common.session import parse_curr_session_keys

class AdvertiserRegistrationForm(forms.Form):
    """ Register an advertiser. """
    business_name = forms.CharField(widget=forms.TextInput(
        attrs={'size':'40', 'maxlength':'50', 'tabindex':'1'}), 
        error_messages={'required': 'Please supply a Business Name'}
        )
    slogan = forms.CharField(widget=forms.TextInput(
        attrs={'size':'40', 'maxlength':'40', 'tabindex':'2'}), 
        required=False
        )
    email = forms.CharField(widget=forms.TextInput(
        attrs={'size':'40', 'maxlength':'50', 'tabindex':'3'}), 
        error_messages={'required': 'Please supply a valid Email Address'}
        )
    advertiser_name = forms.CharField(widget=forms.TextInput(
        attrs={'size':'25', 'maxlength':'50', 'tabindex':'4'}), 
        required=False
        )
    advertiser_area_code = forms.CharField(widget=forms.TextInput(
        attrs={'size':'3', 'maxlength':'3', 'tabindex':'5'}), 
        required=False
        )
    advertiser_exchange = forms.CharField(widget=forms.TextInput(
        attrs={'size':'3', 'maxlength':'3', 'tabindex':'6'}), 
        required=False
        )
    advertiser_number = forms.CharField(widget=forms.TextInput(
        attrs={'size':'6', 'maxlength':'4', 'tabindex':'7'}), 
        required=False
        )
    
    def clean(self):
        """ Generic clean method for this form. """
        self.cleaned_data = trim_fields_in_form(self)
        if self.cleaned_data['email']:
            try:
                validators.validate_email(self.cleaned_data['email'])
            except ValidationError as e:
                self.errors['email'] = ErrorList(e.messages)                  
        else:        
            self.errors['email'] = \
                ErrorList(["Please supply a valid Email Address"])
        if len(self.cleaned_data['advertiser_name']) < 2:
            self.cleaned_data['advertiser_name'] = None
        return self.cleaned_data
    
       
def get_advertiser_reg_init_data(request):
    """ Prepopulate the advertiser registration form when possible. """
    try:
        # Check for a consumer in session.
        this_consumer = request.session['consumer']
        email = this_consumer['email']
        try:
            session_dict = parse_curr_session_keys(request.session, 
                ['this_advertiser', 'this_business'])
            advertiser_name = session_dict['this_advertiser']['advertiser_name']
            advertiser_area_code = \
                session_dict['this_advertiser']['advertiser_area_code']
            advertiser_exchange = \
                session_dict['this_advertiser']['advertiser_exchange']
            advertiser_number = \
                session_dict['this_advertiser']['advertiser_number']     
            business_name = session_dict['this_business']['business_name']
            slogan = session_dict['this_business']['slogan']
            code = request.session.get('promo_code', None)
            initial_data = {
                'business_name':business_name,
                'slogan':slogan,
                'email':email,
                'advertiser_name':advertiser_name,
                'advertiser_area_code':advertiser_area_code,
                'advertiser_exchange':advertiser_exchange,
                'advertiser_number':advertiser_number,
                'code':code}
        except KeyError:
            initial_data = {'email':email}
    except KeyError:
        initial_data = {}
    return initial_data