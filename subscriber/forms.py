""" Forms for subscriber app """
import logging

from django import forms
from django.forms import ValidationError
from django.forms.util import ErrorList

from django.contrib.localflavor.us.forms import USPhoneNumberField

from common.session import parse_curr_session_keys
from common.custom_cleaning import clean_phone_number, trim_fields_in_form
from common.custom_validation import validate_phone_number, validate_zip_postal
from sms_gateway.service import send_carrier_lookup
from subscriber.models import Carrier

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class SubscriberRegistrationForm(forms.Form):
    """ Register a subscriber. This is also the Send to Phone form. """
    email = forms.CharField(required=False)
    mobile_phone_number = USPhoneNumberField(widget=forms.TextInput(attrs={
        'class':'fulltext',
        'size': '20',
        'maxlength': '15',
        'tabindex':'1'}
        ), error_messages={
        'required': u' Please enter the 10 digit number of your cell phone',
        'invalid': u' Please enter the 10 digit number of your cell phone'}
        )
    carrier = forms.ModelChoiceField(
        queryset=Carrier.objects.get_or_set_carrier_cache(),
        empty_label = '- select carrier -', 
        widget=forms.Select(attrs={'class':'fulltext', 'tabindex':'3'}),
        error_messages={
        'required': u'Select your cell phone service provider',
        'invalid': u'Select a Carrier'}
        )
    subscriber_zip_postal = forms.CharField(widget=forms.TextInput(attrs={
        'size':'10',
        'maxlength':'9',
        'tabindex':'2'}
        ), required=True)

    def clean(self):
        # Only do carrier lookup if the rest of the form is good, since it
        # costs.
        self.cleaned_data = trim_fields_in_form(self)
        LOG.debug('cleaned_data: %s' % self.cleaned_data)
        if self.errors == {} and self.cleaned_data.get('carrier', None):
            carrier = self.cleaned_data.get("carrier")
            if carrier.id == 1:
                try:
                    carrier = send_carrier_lookup(
                        self.cleaned_data['mobile_phone_number'])
                    if carrier:
                        self.cleaned_data['carrier'] = carrier
                except ValidationError:
                    self.errors['mobile_phone_number'] = ErrorList(
                        ["Oops! We tried, but couldn't connect to that phone." +
                        " Please check the number."])
                    # The internationalization code below was erroring out the 
                    # subscriber reg form. Would block an ajax json encoded 
                    # submit.
                    #self.errors['mobile_phone_number'] = ErrorList(
                    #    [_("""Oops! We tried, but couldn't connect to that
                    #        phone. Please check the number.""")])
        subscriber_zip_postal = self.cleaned_data.get("subscriber_zip_postal")
        validate_zip_postal(self, subscriber_zip_postal,
            'subscriber_zip_postal')
        # Always return cleaned_data back
        return self.cleaned_data
    
    def clean_mobile_phone_number(self):
        self.cleaned_data['mobile_phone_number'] = clean_phone_number(
            self.cleaned_data.get('mobile_phone_number', None))
        validate_phone_number(self, self.cleaned_data['mobile_phone_number'],
            'mobile_phone_number')
        return self.cleaned_data['mobile_phone_number']
    
    def clean_subscriber_zip_postal(self):
        self.cleaned_data['subscriber_zip_postal'] = \
            self.cleaned_data.get('subscriber_zip_postal', None).strip()
        return self.cleaned_data['subscriber_zip_postal']
    
    def get_cleaned_data_for_sms(self):
        """ 
        Just clean phone and zip without validating entire form. This method
        was created to return the cleaned data fields after another process was 
        called which validated and handled resubmits:
            coupon.view.show_sms.send_sms_single_coupon 
        At this point the form submission has been accepted. 
        """
        if not hasattr(self, 'cleaned_data'):
            self.cleaned_data = {
                'mobile_phone_number': self.data['mobile_phone_number'],
                'subscriber_zip_postal': self.data['subscriber_zip_postal']}
        self.cleaned_data.update({
            'mobile_phone_number': self.clean_mobile_phone_number(),
            'subscriber_zip_postal': self.clean_subscriber_zip_postal()})
        return self.cleaned_data

def get_subscriber_reg_init_data(_session):
    """ Pre-populate the subscriber registration form if possible. """
    initial_data = {}
    try:
        session_dict = parse_curr_session_keys(_session, 
                ['carrier_id', 'mobile_phone_number', 'subscriber_zip_postal'])
        initial_data = {
            'mobile_phone_number':session_dict['mobile_phone_number'],
            'subscriber_zip_postal':session_dict['subscriber_zip_postal'],
            'carrier':session_dict['carrier_id']}
    except KeyError:
        try:
            consumer_zip_postal = \
                _session['consumer']['consumer_zip_postal']
            initial_data = {'subscriber_zip_postal':consumer_zip_postal}
        except KeyError:
            pass
    return initial_data
