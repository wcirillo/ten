""" Forms for a business of an advertiser. """

from django import forms
from django.forms.util import ErrorList

from advertiser.models import Business, BusinessProfileDescription
from category.models import Category
from common.form_widgets import CheckboxInput
from common.custom_cleaning import trim_fields_in_form

class WebURLForm(forms.ModelForm):
    """ Business Web Url CREATION """
    class Meta:
        model = Business
        fields = ('web_url',)
        widgets = {
            'web_url': forms.TextInput(attrs={
                'size':'35',
                'maxlength':'255',
                'tabindex':'1'}),
        }
    
    def clean(self):
        """ Form clean method """
        self.cleaned_data = trim_fields_in_form(self)
        cleaned_data = self.cleaned_data
        web_url = cleaned_data.get('web_url', None)
        if web_url:
            if web_url[:7] != 'http://':
                web_url = 'http://%s' % web_url
            business = Business(web_url=web_url)
            is_url_good = business.clean_web_url()
            if not is_url_good:
                self._errors['web_url'] = ErrorList(["URL not valid"])
            cleaned_data['web_url'] = web_url
        return cleaned_data
        
        
class EditBusinessProfileForm(forms.Form):
    """ Form for editing a business profile. """
    slogan = forms.CharField(widget=forms.TextInput(
        attrs={'size':'40', 'maxlength':'40', 'tabindex':'2'}), 
        required=False
        )
    business_description = forms.CharField(widget=forms.Textarea, 
        max_length=2500, required=False)
    show_web_snap = forms.BooleanField(widget=CheckboxInput(), required=False)
    show_map = forms.BooleanField(widget=CheckboxInput(), required=False)
    category = forms.ChoiceField(label="Category", choices=(),
        widget=forms.Select(attrs={'class':'selector'}))

    def __init__(self, *args, **kwargs):
        super(EditBusinessProfileForm, self).__init__(*args, **kwargs)
        choices = [(cat.id, unicode(cat)) for cat in Category.objects.all()]
        self.fields['category'].choices = choices
        
    def clean(self):
        """ Form clean method. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data
    
    def clean_show_web_snap(self):
        """ Clean the show_web_snap flag. """
        self.cleaned_data['show_web_snap'] = self.cleaned_data.get(
                                                        'show_web_snap', False)
        return self.cleaned_data['show_web_snap']
    
    def clean_show_map(self):
        """ Clean the show_map flag. """
        self.cleaned_data['show_map'] = self.cleaned_data.get('show_map', False)
        return self.cleaned_data['show_map']


def get_edit_profile_form_init_data(business):
    """ Pre-populate the edit business profile form if possible. """
    initial_data = {'slogan': business.slogan,
                'show_web_snap': business.show_web_snap,
                'show_map': business.show_map,
                'category': (business.categories.values_list(
                                                'id', flat=True) or [7])[0]}
    try:
        business_profile_description = BusinessProfileDescription.objects.get(
                business=business
            )
        initial_data['business_description'] = \
            business_profile_description.business_description
    except BusinessProfileDescription.DoesNotExist:
        pass
    return initial_data
