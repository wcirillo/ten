""" Forms for consumer app. """

from django import forms
from django.core.exceptions import ValidationError

from common.custom_cleaning import clean_email_form_field, trim_fields_in_form
from common.custom_validation import validate_zip_postal
from consumer.models import Consumer, ConsumerHistoryEvent
from market.service import check_for_cross_site_redirect

class ConsumerRegistrationForm(forms.Form):
    """ Consumer registration. """
    first_name = forms.CharField(widget=forms.TextInput(
        attrs={'size': '25', 'maxlength': '50', 'tabindex':'1'}),
        required=False, initial=None)
    last_name = forms.CharField(widget=forms.TextInput(
        attrs={'size': '25', 'maxlength': '50', 'tabindex':'2'}),
        required=False, initial=None)
    email = forms.CharField(widget=forms.TextInput(
        attrs={'size':'30','maxlength':'50','tabindex':'3'}), required=True, 
        error_messages={'required': u' Please enter a valid email.'}
        )
    consumer_zip_postal = forms.CharField(widget=forms.TextInput(
        attrs={'size':'10','maxlength':'9','tabindex':'4'}), required=True
        )
    
    def add_or_update_consumer(self, request, site):
        """ Add consumer if it doesn't exist, update it if it has changed. """
        email = self.cleaned_data.get('email', None)
        consumer_zip_postal = self.cleaned_data.get('consumer_zip_postal', None)
        first_name = self.cleaned_data.get('first_name', None)
        last_name = self.cleaned_data.get('last_name', None)
        try:
            # Check if user exists already.
            consumer = Consumer.objects.get(email__iexact=email)
            if consumer.consumer_zip_postal != consumer_zip_postal \
            and consumer_zip_postal:
                consumer.consumer_zip_postal = consumer_zip_postal
            if consumer.site.id != site.id and site.id != 1:
                consumer.site = site
            if first_name:
                consumer.first_name = first_name
            if last_name:
                consumer.last_name = last_name
            consumer.save()
            # Subscribe this consumer to the Flyer if they don't have this 
            # subscription already.
            if not consumer.email_subscription.filter(id=1):
                consumer.email_subscription.add(1)
                event = ConsumerHistoryEvent.objects.create(
                    consumer=consumer, 
                    ip=request.META['REMOTE_ADDR'],
                    event_type='2',
                    )
                event.save()
        except Consumer.DoesNotExist:
            # Wrapped in try for race condition. 
            try:
                kwargs = self.cleaned_data.copy()
                kwargs.update({'site': site, 'username': email})
                consumer = Consumer.objects.create_consumer(**kwargs)
                event = ConsumerHistoryEvent.objects.create(
                    consumer=consumer, 
                    ip=request.META['REMOTE_ADDR'],
                    event_type='0',
                    )
                event.save()
            except ValidationError:
                # Prevent race condition, where creation of consumer is 
                # attempted twice rapidly - grab the consumer.
                consumer = Consumer.objects.get(email__iexact=email)
        return consumer

    def clean(self):
        """ Clean ConsumerRegistrationForm fields. """
        self.cleaned_data = trim_fields_in_form(self)
        consumer_zip_postal = self.cleaned_data.get('consumer_zip_postal', None)
        validate_zip_postal(self, consumer_zip_postal, 'consumer_zip_postal')
        # Always return cleaned_data back.
        return self.cleaned_data
    
    def clean_email(self):
        """ Clean email field in form. """
        return clean_email_form_field(self)
    
    def clean_consumer_zip_postal(self):
        """ Clean zip_postal field in form. """
        self.cleaned_data['consumer_zip_postal'] = \
            self.cleaned_data.get('consumer_zip_postal', None).strip()
        return self.cleaned_data['consumer_zip_postal']
    
    def save(self, request, redirect_path=None):
        """ Save consumer. """
        self.url_to_change_market = False
        self.site = self.set_site_and_redirect_path(request, redirect_path)
        consumer = self.add_or_update_consumer(request, self.site)
        return consumer
    
    def set_site_and_redirect_path(self, request, redirect_path=None):
        """ Set site based on zip code if it is site 1, and set redirect_path
        accordingly (where to redirect to on success).
        """
        consumer_zip_postal = self.cleaned_data.get('consumer_zip_postal', None)
        site, self.redirect_path, curr_site = check_for_cross_site_redirect(
            request, consumer_zip_postal, redirect_path)
        if site.id != curr_site.id:
            self.url_to_change_market = self.redirect_path
        return site

    
def get_consumer_reg_initial_data(request):
    """ Pre-populate the consumer registration form if possible. """
    initial_data = {}
    try:
        email = request.session['consumer']['email']
        consumer_zip_postal = request.session['consumer']['consumer_zip_postal']
        if consumer_zip_postal:
            initial_data = {
                'email':email, 
                'consumer_zip_postal':consumer_zip_postal
                }
        else:
            try:
                subscriber_zip_postal = request.session['consumer']['subscriber']['subscriber_zip_postal']
                initial_data = {
                    'email':email, 
                    'consumer_zip_postal':subscriber_zip_postal
                    }
            except KeyError:
                initial_data = {'email':email}
    except KeyError:
        try:
            subscriber_zip_postal = request.session['consumer']['subscriber']['subscriber_zip_postal']
            initial_data = {'consumer_zip_postal':subscriber_zip_postal}
        except KeyError:
            try:
                # Maybe they came from local home page zip request form.
                consumer_zip_postal = request.session['consumer']\
                        ['consumer_zip_postal']
                initial_data = {'email' : '', 
                        'consumer_zip_postal' : consumer_zip_postal}
            except KeyError:
                pass
    return initial_data

class MarketSearchForm(forms.Form):
    """ Find market by zipcode. """
    consumer_zip_postal = forms.CharField(widget=forms.TextInput(
        attrs={'size':'12','maxlength':'9','tabindex':'1'}), required=True
        )
    
    def clean(self):
        self.cleaned_data = trim_fields_in_form(self)
        try:
            consumer_zip_postal = self.cleaned_data['consumer_zip_postal']
        except KeyError:
            consumer_zip_postal = None
        validate_zip_postal(self, consumer_zip_postal, 'consumer_zip_postal')
        return self.cleaned_data
