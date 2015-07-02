""" Forms for firestorm app. """

from django import forms
from django.contrib.localflavor.us.forms import USPhoneNumberField
from django.core.validators import RegexValidator
from django.utils.translation import ugettext_lazy as _

from common.custom_cleaning import clean_phone_number
from common.custom_validation import validate_phone_number
from common.service.photo_upload import PHOTO_UPLOAD
from common.utils import create_unique_datetime_str
from consumer.forms import ConsumerRegistrationForm
from firestorm.models import AdRep, AdRepLead, AdRepConsumer


class AdRepUrlForm(forms.Form): 
    """ Ad rep url form. """
    ad_rep_url = forms.CharField(widget=forms.TextInput(
        attrs={'size': '15', 'maxlength': '25', 'tabindex':'20'}),
        error_messages={'required': 'Please choose a website name.'})
    
    def clean_ad_rep_url(self):
        """ Validate url and check if it is already in use by existing ad reps. 
        """
        prohibited_url_words = ['index', 'home', 'default']
        error_message = _("""Sorry! We're growing fast. That website name is 
            already in use. Please choose another.""")
        regex_validation = RegexValidator(regex='^[\w]+$', 
            message=error_message)
        ad_rep_url = self.cleaned_data.get('ad_rep_url', '').lower()
        if ad_rep_url:
            regex_validation(ad_rep_url)
            try:
                AdRep.objects.get(url=ad_rep_url)
                raise forms.ValidationError(error_message)
            except AdRep.DoesNotExist:
                pass
            if ad_rep_url in prohibited_url_words:
                raise forms.ValidationError(error_message)
        return ad_rep_url
    
    def save(self, ad_rep):
        """ Save url to ad rep. """
        ad_rep_url = self.cleaned_data.get('ad_rep_url')
        ad_rep.url = ad_rep_url
        ad_rep.save()   


class QuestionForm(forms.Form):
    """ Ad Rep lead question form. """
    right_person_text = forms.CharField(widget=forms.Textarea(attrs={
        'class':'small',
        'rows':'4',
        'size':'2000',
        'maxlength': 2000,
        'tabindex':'6'}
        ), required=False)

    def clean_right_person_text(self):
        """ Clean right person text. """
        return self.cleaned_data.get('right_person_text').strip()[:2000]

    def save(self, ad_rep_lead):
        """ Save answers to ad rep lead question form. """
        ad_rep_lead.right_person_text = self.cleaned_data.get(
            'right_person_text')
        ad_rep_lead.save()
        return ad_rep_lead


class AdRepLeadForm(ConsumerRegistrationForm):
    """ Ad Rep lead generator. """
    primary_phone_number = USPhoneNumberField(widget=forms.TextInput(attrs={
        'size': '20',
        'maxlength': '15',
        'tabindex':'5'}
        ), required=False)

    def add_or_update_ad_rep_lead(self, consumer, site):
        """ Add or update ad rep lead from consumer. """
        email = self.cleaned_data['email']
        try:
            ad_rep_lead = AdRepLead.objects.get(email=email)
            ad_rep_lead.first_name = \
                self.cleaned_data.get('first_name') or ad_rep_lead.first_name
            ad_rep_lead.last_name = \
                self.cleaned_data.get('last_name') or ad_rep_lead.last_name
            ad_rep_lead.primary_phone_number = \
                self.cleaned_data.get('primary_phone_number') \
                    or ad_rep_lead.primary_phone_number
            ad_rep_lead.consumer_zip_postal = \
                self.cleaned_data['consumer_zip_postal']
            if site.id != 1 or not ad_rep_lead.site:
                ad_rep_lead.site = site
        except AdRepLead.DoesNotExist:
            ad_rep_lead = AdRepLead.objects.create_ad_rep_lead_from_con(
                consumer.id, self.cleaned_data)
        ad_rep_lead.email_subscription.add(5, 6)
        return ad_rep_lead
    
    @staticmethod
    def set_ad_rep(request, ad_rep_lead):
        """ Set ad rep for this ad rep lead. """
        try:
            ad_rep = AdRep.objects.get(id=request.session['ad_rep_id'])
            if ad_rep.rank != 'CUSTOMER':
                AdRepConsumer.objects.create_update_rep(request, 
                    ad_rep_lead.consumer)
                ad_rep_lead.ad_rep = ad_rep
                ad_rep_lead.save()
            else:
                ad_rep = None
        except (KeyError, AdRep.DoesNotExist):
            ad_rep = None
        if not ad_rep:
            try: # Default ad_rep: Alana Lenec
                ad_rep = AdRep.objects.get(firestorm_id=103955)
            except AdRep.DoesNotExist:
                pass
            if ad_rep:
                ad_rep_lead.ad_rep = ad_rep
                ad_rep_lead.save() 
        return ad_rep_lead

    def clean(self):
        """ Clean ConsumerRegistrationForm fields. """
        self.cleaned_data = super(AdRepLeadForm, self).clean()
        if self.data.get('primary_phone_number', None):
            primary_phone_number = \
                self.cleaned_data.get('primary_phone_number', None)
            validate_phone_number(
                self, primary_phone_number, 
                'primary_phone_number', generic=True)
        return self.cleaned_data
       
    def clean_primary_phone_number(self):
        """ Clean phone. """
        primary_phone_number = \
            self.cleaned_data.get('primary_phone_number', None)
        if primary_phone_number:
            return clean_phone_number(primary_phone_number)
        else:
            return primary_phone_number
        
    def save(self, request, redirect_path=None):
        """ Overrides consumer reg form's save method to pass request to 
        the add_or_update_consumer method that is also overridden (in order to
        call add_or_update_ad_rep_lead progressively).
        """
        # Remove non-consumer model values from dict
        ad_rep_lead_dict = {
            'primary_phone_number': 
                self.cleaned_data.pop('primary_phone_number', None)}
        consumer = super(AdRepLeadForm, self).save(request, redirect_path)
        # Re-add non-consumer model values 
        self.cleaned_data.update(ad_rep_lead_dict) 
        ad_rep_lead = self.add_or_update_ad_rep_lead(consumer, self.site)
        ad_rep_lead = self.set_ad_rep(request, ad_rep_lead)
        return ad_rep_lead


class AdRepPhotoUploadForm(forms.Form):
    """ Form for uploading an ad_rep photo."""
    ad_rep_photo = forms.ImageField()
    
    def save(self, request, ad_rep):
        try:
            image = PHOTO_UPLOAD.open_image(temp_image=request.FILES['ad_rep_photo'])            
            image = PHOTO_UPLOAD.check_image_orientation(image)
            square_image = PHOTO_UPLOAD.square_off_image(image)
            rgb_image = PHOTO_UPLOAD.convert_to_rgb(square_image)
            resized_image = PHOTO_UPLOAD.resize_image(rgb_image)
            filename = self.get_image_filename(ad_rep)
            if ad_rep.ad_rep_photo:
                ad_rep.ad_rep_photo.delete()
            PHOTO_UPLOAD.save_image(image=resized_image,
                model_image_field=ad_rep.ad_rep_photo, filename=filename)
        except IOError:
            pass

    @staticmethod
    def get_image_filename(ad_rep):
        """ Build an appropriate filename to save this image file. """
        filename = ''
        if ad_rep.first_name != '' and ad_rep.last_name != '':
            filename = '%s-%s-' % (ad_rep.first_name, ad_rep.last_name)
        elif ad_rep.first_name != '' and ad_rep.last_name == '':
            filename = '%s-' % ad_rep.first_name
        elif ad_rep.first_name == '' and ad_rep.last_name != '':
            filename = '%s-' % ad_rep.last_name
        filename = '%s%s-%s.jpg' % (filename, ad_rep.url, create_unique_datetime_str())
        return filename.lower()
