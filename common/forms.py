""" All common Forms in front of login should go in this section! """
from django import forms
from django.forms.util import ErrorList
from django.contrib.auth import authenticate
from django.core import validators
from django.utils.translation import ugettext_lazy as _

from advertiser.models import Advertiser
from common.custom_cleaning import clean_email_form_field, trim_fields_in_form
from common.custom_validation import validate_passwords
from consumer.service import get_consumer_instance_type
from firestorm.soap import FirestormSoap, MockSoap

ERROR_MESSSAGE = u'%s %s' % ('Enter an Email Address.',
    'Be sure the format is correct format, no spaces, etc')


class SetPasswordForm(forms.Form): 
    """ Set/Update Password form. """
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'30',
        'maxlength':'128', 'tabindex':'11'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'size':'30',
        'maxlength':'128', 'tabindex':'12'}))
    
    def clean(self):
        self.cleaned_data = trim_fields_in_form(self)
        validate_passwords(self, 'password1', self.cleaned_data['password1'], 
            self.cleaned_data['password2'])
        return self.cleaned_data
    
    def save(self, request):
        """ Save password. """
        user = request.user
        user.set_password(self.cleaned_data.get('password1', None))
        user.save()


class SignInForm(forms.Form):
    """ Sign In Form for all user_types. """
    email = forms.CharField(widget=forms.TextInput(attrs={'size':'30',
        'maxlength':'50', 'tabindex':'1'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'size':'12',
        'maxlength':'128', 'tabindex':'2'}), required=False)
    ad_rep_sign_in = forms.IntegerField(widget=forms.HiddenInput(), 
        required=False, initial=0)
    
    def __init__(self, *args, **kwargs):
        """ Instantiate form variables. """
        self.soap_connector = FirestormSoap
        try:
            if kwargs.pop('test_mode'):
                self.soap_connector = MockSoap
        except KeyError:
            pass
        super(SignInForm, self).__init__(*args, **kwargs)

    def clean(self):
        self.cleaned_data = trim_fields_in_form(self)
        email = self.cleaned_data.get('email', '')
        if email:
            email = email.strip().lower()
        password = self.cleaned_data.get('password')
        validate_email = validators.EmailValidator(validators.email_re,
            _(u'Please use this format: me@example.com '), 'invalid')
        if email:
            validate_email(email)
            user_type, is_ad_rep = get_consumer_instance_type(email)
            # Add extra fields to form to use again in login processing.
            self.cleaned_data.update({'is_ad_rep': is_ad_rep, 
                'user_type': user_type})
            if user_type != ('consumer') or is_ad_rep:
                user = authenticate(username=email, password=password)
                if user is None:
                    self.errors['email'] = ErrorList(
                            ["Email Address and Password don't match."])
        return self.cleaned_data

    def clean_email(self):
        """ Clean form's email field. """
        self.cleaned_data['email'] = self.cleaned_data.get(
            'email', None).strip().lower()
        return self.cleaned_data['email']

        
def get_sign_in_form_initial_data(request):
    """ Set the initial data to be passed into the Sign In form so it is
    populated.
    """
    initial_data = {}
    try:
        email = request.session['consumer']['email']
        initial_data['email'] = email
    except KeyError:
        pass
    return initial_data


class OptInOptOutForm(forms.Form):
    """ Opt In Opt Out Form to Opt In or Out of subscriptions."""
    email = forms.CharField(widget=forms.HiddenInput(),
        validators=[validators.validate_email],
        error_messages = {
            'required': ERROR_MESSSAGE,
            'invalid': ERROR_MESSSAGE
            })
    def clean(self):
        """ Clean form. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data


class ForgotPasswordForm(forms.ModelForm):
    """ Forgot password form. """
    class Meta:
        model = Advertiser
        fields = ('email',)
    
    def clean(self):
        """ Clean form. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data
        
    def clean_email(self):
        """ Clean email. """
        return clean_email_form_field(self)
   

class TermsOfUseForm(forms.Form):
    """ Terms of Use form to confirm acknowledgment of terms via checkbox."""
    terms_of_use = forms.BooleanField(widget=forms.CheckboxInput(
        attrs={}),
        error_messages = {
        'required': 'You must agree to the terms before proceeding.'})
    
    def __init__(self, *args, **kwargs):
        """ Make error message for terms_of_use checkbox dynamic. """
        try:
            err_msg = kwargs.pop('err_msg')
        except KeyError:
            err_msg = None
        super(TermsOfUseForm, self).__init__(*args, **kwargs)
        if err_msg:
            self.fields['terms_of_use'].error_messages['required'] = err_msg
