""" Custom cleaning for ten project. """
import re

from django.core import validators
from django import forms
from django.forms.util import ErrorList


def check_field_length(self, field_name):
    """ Ensure form fields length is within constraints. (IE Mobile browser
    7.0 ignores form attribute and causes database error when field value is 
    too long.
    """
    try:
        max_length = int(self.fields[field_name].widget.attrs.get('maxlength'))
    except (AttributeError, TypeError):
        max_length = None
    if max_length and len(self.cleaned_data[field_name]) > max_length:
        self.errors[field_name] = ErrorList(
            ["Please limit this field to %s characters" % max_length])

def clean_email_form_field(form):
    """ Email clean method for form. """
    form.cleaned_data['email'] = \
        form.cleaned_data.get('email', None).strip().lower()
    if form.cleaned_data['email']:
        validators.validate_email(form.cleaned_data['email'])            
    else:
        form.errors['email'] = ErrorList(["Enter an Email Address."]) 
    return form.cleaned_data['email']

def clean_phone_number(phone_number):
    """ Remove common punctuation marks from a phone_number and take right most
    ten digits. 
    """
    return strip_to_numbers(phone_number or '')[-10:]
 
def strip_to_numbers(number):
    """ 
        Extract number from string. 
        Runs an average of 0.000006906 seconds per execution.
    """
    result = ''
    return result.join(re.findall('(\d+)', number))

def trim_fields_in_form(form):
    """ Trim space off each form field value. """
    cleaned_data = form.cleaned_data
    for field in form.fields:
        try:
            if type(cleaned_data[field]).__name__ in ('str', 'unicode'):
                cleaned_data[field] = form.cleaned_data.get(field).strip()
                check_field_length(form, field)

        except KeyError:
            # Field is None, can't strip, continue. 
            cleaned_data[field] = None
    return cleaned_data

class AdminFormClean(forms.ModelForm):
    """ Base class to use to add a generic clean method to admin forms. """
    def clean(self):
        """ Trim all fields in form. """
        self.cleaned_data = trim_fields_in_form(self)
        super(AdminFormClean, self).clean()
        return self.cleaned_data