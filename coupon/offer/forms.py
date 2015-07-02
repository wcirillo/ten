""" Forms for offers of a business. """

from django import forms

from category.models import Category
from common.custom_cleaning import trim_fields_in_form


class CreateOfferForm(forms.Form):
    """ The create offer form. """
    headline = forms.CharField(widget=forms.TextInput(
            attrs={'size':'25', 'maxlength':'25', 'tabindex':'1'}
        ), 
        error_messages={'required': 'Please supply a Coupon Offer'})
    qualifier = forms.CharField(widget=forms.TextInput(
            attrs={'size':'35', 'maxlength':'40', 'tabindex':'2'}
        ), 
        required=False)
    expiration_date = forms.CharField(widget=forms.HiddenInput(
        attrs={'maxlength':'10'}))
    category = forms.ChoiceField(label="Category", choices=(),
        widget=forms.Select(attrs={'class':'selector'}),
        error_messages={'required': 'Please select a category'})

    def __init__(self, *args, **kwargs):
        super(CreateOfferForm, self).__init__(*args, **kwargs)
        choices = [(cat.id, unicode(cat)) for cat in Category.objects.all()]
        self.fields['category'].choices = choices
       
    def clean(self):
        """ Clean CreateOfferForm fields. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data