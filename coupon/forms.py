""" All forms related to coupons. """
from time import strptime
import logging

from django import forms
from django.conf import settings
from django.contrib.localflavor.us.forms import USStateField
from django.forms.util import ErrorDict, ErrorList
from django.template.defaultfilters import date as date_filter
from django.utils.translation import ugettext_lazy as _

from advertiser.models import Business
from category.models import Category
from common.custom_cleaning import trim_fields_in_form
from common.form_widgets import (CheckboxSelectMultiple, RadioSelect,
    CheckboxInput, USStateSelect)
from coupon.config import IS_REDEEMED_BY_SMS_CHOICES
from coupon.models import DefaultRestrictions
from coupon.service.coupons_service import ALL_COUPONS, SORT_COUPONS
from coupon.service.restrictions_service import COUPON_RESTRICTIONS
from coupon.tasks import record_action_multiple_coupons
from market.service import get_current_site

from haystack.forms import SearchForm
from haystack.query import SearchQuerySet

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class RestrictionsForm(forms.Form):
    """ The Default Restrictions and Custom Restrictions Form. """
    default_restrictions = forms.ModelMultipleChoiceField(
        widget=CheckboxSelectMultiple, 
        queryset=DefaultRestrictions.objects.all().order_by('sort_order'), 
        required=False)
    custom_restrictions = forms.CharField(widget=forms.Textarea(attrs={
        'onkeypress' : "return enforceMaxLength(this,1500,event);",
        'onblur' : "return enforceMaxLength(this,1500,event);"
        }), required=False)
    is_redeemed_by_sms = forms.ChoiceField(
        widget=RadioSelect, 
        choices=IS_REDEEMED_BY_SMS_CHOICES, 
        initial="1")

    def clean(self):
        """ Clean RestrictionsForm fields. """
        self.cleaned_data = trim_fields_in_form(self)
        return self.cleaned_data

    def clean_default_restrictions(self):
        index = 0
        for x in self.cleaned_data['default_restrictions']:
            self.cleaned_data['default_restrictions'][index].restriction = \
                    unicode(x.restriction.strip())
            index += 1
        return self.cleaned_data['default_restrictions']
    
    def clean_custom_restrictions(self):
        self.cleaned_data['custom_restrictions'] = \
            self.cleaned_data.get(
                'custom_restrictions', None).strip()[:1500]
        return self.cleaned_data['custom_restrictions']
    
    def clean_is_redeemed_by_sms(self):
        self.cleaned_data['is_redeemed_by_sms'] = \
            bool(int(self.cleaned_data.get('is_redeemed_by_sms', 1)))
        return self.cleaned_data['is_redeemed_by_sms']

def get_restrictions_initial_data(this_coupon):
    """ Get the initial data for the restrictions form. """
    if not this_coupon['is_redeemed_by_sms']:
        is_redeemed_by_sms = 0
    else:
        is_redeemed_by_sms = 1
    default_restrictions_list = \
        COUPON_RESTRICTIONS.get_default_restrictions_list(
            this_coupon['coupon_id'],
            this_coupon['custom_restrictions'])
    initial_dict = {
                'is_redeemed_by_sms':is_redeemed_by_sms,
                'custom_restrictions':this_coupon['custom_restrictions'],
                'default_restrictions':default_restrictions_list
                }
    return initial_dict


class ValidDaysForm(forms.Form):
    """ The Valid Days Form holds the 7 days of the week checkboxes to build 
    the valid days string when certain checkboxes are check and unchecked. 
    """
    is_valid_monday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_tuesday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_wednesday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_thursday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_friday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_saturday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'weekend'}), required=False)
    is_valid_sunday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'weekend'}), required=False)

def get_valid_days_initial_data(this_coupon):
    """ Build the initial_dict for the ValidDaysForm() """
    initial_dict = {
        'is_valid_monday': this_coupon['is_valid_monday'],
        'is_valid_tuesday': this_coupon['is_valid_tuesday'],
        'is_valid_wednesday': this_coupon['is_valid_wednesday'],
        'is_valid_thursday': this_coupon['is_valid_thursday'],
        'is_valid_friday': this_coupon['is_valid_friday'],
        'is_valid_saturday': this_coupon['is_valid_saturday'],
        'is_valid_sunday': this_coupon['is_valid_sunday'],
    }
    return initial_dict


class EditCouponForm(forms.Form):
    """ The Coupon Edit form.  Used originally for the preview edit coupon. """ 
    def __init__(self, *args, **kwargs):
        """ Dynamically create 10 sets of location fields. """
        super(EditCouponForm, self).__init__(*args, **kwargs)
        count = 1
        while count <= 10:
            self.fields['location_address1_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'25', 'maxlength':'50'}), 
                required=False)    
            self.fields['location_address2_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'25', 'maxlength':'50'}), 
                required=False)
            self.fields['location_city_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'25', 'maxlength':'50'}), 
                required=False)
            self.fields['location_state_province_' + str(count)] = USStateField(
                widget=USStateSelect(attrs={}), required=False)
            self.fields['location_zip_postal_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'6', 'maxlength':'9'}), 
                required=False)
            self.fields['location_description_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'25', 'maxlength':'50'}), 
                required=False)
            self.fields['location_area_code_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'3', 'maxlength':'3'}), 
                required=False)
            self.fields['location_exchange_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'3', 'maxlength':'3'}), 
                required=False)
            self.fields['location_number_' + str(count)] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'4', 'maxlength':'4'}), 
                required=False)
            count += 1

    business_name = forms.CharField(widget=forms.TextInput(
        attrs={'size':'25', 'maxlength':'50'}), 
        error_messages={'required': 'Please supply a Business Name'}
        )
    slogan = forms.CharField(widget=forms.TextInput(
        attrs={'size':'25', 'maxlength':'40'}), 
        required=False
        )
    web_url = forms.CharField(widget=forms.TextInput(
        attrs={'size':'25', 'maxlength':'255'}), 
        required=False
        )
    headline = forms.CharField(widget=forms.TextInput(
        attrs={'size':'25', 'maxlength':'25'}), 
        error_messages={'required': 'Please supply a Coupon Offer'}
        )
    qualifier = forms.CharField(widget=forms.TextInput(
        attrs={'size':'25', 'maxlength':'40'}), 
        required=False
        )

    default_restrictions = forms.ModelMultipleChoiceField(
        widget=CheckboxSelectMultiple, 
        queryset=DefaultRestrictions.objects.all().order_by('sort_order'), 
        required=False)
    custom_restrictions = forms.CharField(widget=forms.Textarea(attrs={
        'onkeypress' : "return enforceMaxLength(this,1500,event);",
        'onblur' : "return enforceMaxLength(this,1500,event);"
        }), required=False)

    is_valid_monday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_tuesday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_wednesday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_thursday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_friday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'monfri'}), required=False)
    is_valid_saturday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'weekend'}), required=False)
    is_valid_sunday = forms.BooleanField(
        widget=CheckboxInput(attrs={'class':'weekend'}), required=False)

    is_redeemed_by_sms = forms.ChoiceField(
        widget=RadioSelect, choices=IS_REDEEMED_BY_SMS_CHOICES)

    expiration_date = forms.CharField(
        widget=forms.HiddenInput(attrs={'maxlength':'10'}))

    def clean(self):
        """ Clean EditCouponForm fields. """
        self.cleaned_data = trim_fields_in_form(self)
        web_url = self.cleaned_data.get('web_url', None)
        if web_url:
            business = Business(web_url=web_url)
            is_url_good = business.clean_web_url()
            if not is_url_good:
                self._errors['web_url'] = ErrorList(["URL not valid"])
        # Clean location fields.
        count = 1
        while count <= 10:
            # Do not use default state if no other address information is 
            # present.
            if not self.cleaned_data['location_address1_' + str(count)] and \
                not self.cleaned_data['location_address2_' + str(count)] and \
                not self.cleaned_data['location_city_' + str(count)] and \
                not self.cleaned_data['location_zip_postal_' + str(count)]:
                self.cleaned_data['location_state_province_' + str(count)] = ""
            count += 1  
        return self.cleaned_data

    def clean_custom_restrictions(self):
        """ Clean custom restrictions. """
        self.cleaned_data['custom_restrictions'] = \
            self.cleaned_data.get(
                'custom_restrictions', None).strip()[:1500]
        return self.cleaned_data['custom_restrictions']

    def clean_web_url(self):
        """ Clean web_url field in form. """
        self.cleaned_data['web_url'] = self.cleaned_data.get(
            'web_url', None).strip()
        if self.cleaned_data['web_url'] != '' \
        and self.cleaned_data['web_url'][:7] != 'http://':
            self.cleaned_data['web_url'] = 'http://%s' % (
                self.cleaned_data['web_url'])
        return self.cleaned_data['web_url']


class SearchCouponForm(SearchForm):
    """ Search form for coupons with category filter. """
    category_choices = [ ('0', 'Search all categories')]
    category_choices.extend(
        [(category.id, category.name) for category in Category.objects.all()])

    cat = forms.ChoiceField(
        required=False,
        label=_('Category'),
        choices=category_choices,
        widget=forms.Select(attrs={'class':'dropdown'})
        )

    def __init__(self, *args, **kwargs):
        self.selected_categories = kwargs.pop("selected_categories", [])
        # These two vars are used by the template:
        self.query_string_not_found = False
        self.category_not_found = False
        self.suggestion = None
        self.sqs = [] # This is the result set that will be returned.
        super(SearchCouponForm, self).__init__(*args, **kwargs)

    def clean_cat(self):
        """ Clean user submitted categories. """
        if not self.cleaned_data.get('cat', None) \
        or self.cleaned_data['cat'] == '0':
            self.cleaned_data['cat'] = ''
        return self.cleaned_data['cat']

    def process_search(self, request):
        """ Perform search query from form. """
        cat = self.cleaned_data['cat']
        search_query = self.cleaned_data['q']
        if cat != '' or search_query != '':
            self.set_search_query_set(request)
            if cat != '' and search_query != '':
                self.search_category_and_query()
            elif cat != '':
                self.search_category_only()
            else:
                self.search_query_string_only()
            coupons = self.intersect_index_and_db_results(request)
        else:
            coupons = self.no_query_found(request)
        return coupons, self.suggestion

    def set_search_query_set(self, request):
        """ Set searchqueryset, a QuerySet from solr, defaulting to all coupons
        for this site. If there was a previous search with valid results,
        set it to that.
        """
        self.searchqueryset = request.POST.get('searchqueryset', None)
        if not self.searchqueryset:
            self.searchqueryset = SearchQuerySet().filter(
                site_id=get_current_site(request).id)
        return

    def search_category_and_query(self):
        """ Search both the category and the query string. """
        self.search_category()
        if self.category_not_found:
            self.query_string_not_found = True
            self.sqs = self.searchqueryset
            self.suggestion = self.grab_suggestion()
        else:
            self.search_query_string()
            if self.query_string_not_found:
                self.sqs = self.searchqueryset
                self.suggestion = self.grab_suggestion()
        return

    def search_category_only(self):
        """ Search the category only. """
        self.search_category()
        if self.category_not_found:
            self.sqs = self.searchqueryset
            self.suggestion = self.grab_suggestion()
        return

    def search_query_string_only(self):
        """ Search the query string only. """
        self.search_query_string()
        if self.query_string_not_found:
            self.sqs = self.searchqueryset
            self.suggestion = self.grab_suggestion()
        return

    def search_query_string(self):
        """ Search against the query string. """
        self.sqs = self.search()
        if not len(self.sqs):
            self.query_string_not_found = True
        else:
            self.searchqueryset = self.sqs
        return

    def search_category(self):
        """ Search against the selected category. """
        self.sqs = self.searchqueryset.filter(
            categories=self.cleaned_data['cat'])
        if not len(self.sqs):
            self.category_not_found = True
        else:
            self.searchqueryset = self.sqs
        return
            
    def intersect_index_and_db_results(self, request):
        """ Take the searchqueryset results after searching against category and
        query_string and intersect those results with the db """
        LOG.debug('searchqueryset: %s' % self.searchqueryset)
        searchqueryset_ids = [
            int(result.pk) for result in self.sqs if result is not None]
        LOG.debug('searchqueryset_ids: %s' % searchqueryset_ids)
        # Filter results against coupons that are eligible for display on 
        # the site.
        coupon_ids = ALL_COUPONS.get_all_coupons(get_current_site(request))[1]
        LOG.debug('coupon_ids: %s' % coupon_ids)
        good_ids = set(coupon_ids).intersection(set(searchqueryset_ids))
        LOG.debug('good_ids: %s' % good_ids)
        sorted_coupon_ids, coupons = SORT_COUPONS.sorted_coupons(good_ids)
        ALL_COUPONS.join_coupon_with_locations(sorted_coupon_ids, coupons)
        LOG.debug('coupons: %s' % coupons)
        return coupons

    def no_query_found(self, request):
        """ Determines the behavior when no query was found. """
        all_coupons, coupon_ids = ALL_COUPONS.get_all_coupons(
            get_current_site(request))
        record_action_multiple_coupons.delay(action_id=1,
            coupon_ids=tuple(coupon_ids))
        return all_coupons
    
    def grab_suggestion(self):
        """  Return a suggestion since these results did not return anything. """
        if getattr(settings, 'HAYSTACK_INCLUDE_SPELLING', False):
            return self.get_suggestion()


class AddFlyerDatesForm(forms.Form):
    """ The Add Flyer Dates Form. """

    subdivision_consumer_count = forms.IntegerField(widget=forms.HiddenInput(), 
        required=False, initial=0)

    def __init__(self, available_flyer_dates_list, 
        subdivision_consumer_count=None, checked_data=None, *args, **kwargs):
        """ Dynamically create 10 sets of location fields. """
        super(AddFlyerDatesForm, self).__init__(*args, **kwargs)
        if checked_data:
            self.fields['subdivision_consumer_count'].initial = \
            checked_data.get('subdivision_consumer_count', 0)
        else:
            self.fields['subdivision_consumer_count'].initial = \
                subdivision_consumer_count
        for flyer_month in available_flyer_dates_list:
            for week in flyer_month['weeks']:
                attrs = {'value': week['send_date']}
                if not week['date_is_available']:
                    attrs['disabled'] = 'disabled'
                if checked_data:
                    if '%s' % date_filter(week['send_date'], 'F j'
                            ) in checked_data:
                        attrs['checked'] = 'checked'
                else:    
                    if week['checked'] and week['date_is_available']:
                        attrs['checked'] = 'checked'
                self.fields['%s' % date_filter(
                    week['send_date'], 'F j')] = forms.ChoiceField(
                        widget=CheckboxInput(
                            attrs=attrs,
                            check_test=True),
                        initial=week['send_date'],
                        label = '%s' % date_filter(week['send_date'], 'F j'),
                        required=False)

    def clean_dynamic_fields(self, post_data):
        """ Clean method for this form. """
        selected_flyer_list = []
        self.cleaned_data = {}
        self._errors = ErrorDict()
        for field in self.fields: 
            if field in post_data and field != 'subdivision_consumer_count':
                try:
                    strptime(post_data[field], "%Y-%m-%d")
                    selected_flyer_list.append(post_data[field])
                except ValueError:
                    pass
        try:
            if int(self.fields['subdivision_consumer_count'].initial) < 1:
                # Abort transaction.
                raise forms.ValidationError(
                    _("Flyer Purchases are currently unavailable."))
        except (TypeError, ValueError):
            raise forms.ValidationError(
                    _("Flyer Purchase unavailable."))
        if not selected_flyer_list:
            self._errors['non_field_error'] = ErrorList(
                    ["You must choose at least one date to send out a flyer."])
        else:
            self.cleaned_data = {'flyer_dates_list':selected_flyer_list}
        return self

    def custom_is_valid(self, post_data):
        """ Custom is_valid form method to build cleaned_data and errors then 
        return a boolean deeming the validity of the form.
        """
        self.clean_dynamic_fields(post_data)
        is_valid = True
        if self._errors or not self.cleaned_data:
            is_valid = False
        return is_valid


class AddFlyerByMapForm(forms.Form):
    """ The Add Flyer By Map Form. """
    def __init__(self, county_dict, *args, **kwargs):
        super(AddFlyerByMapForm, self).__init__(*args, **kwargs)

        for county in county_dict:
            county_underscore = county['county'].replace(" ", "_")
            attrs = {
                'class': "county county_%s" % county_underscore,
                'id': "id_%s_%s" % (county['county_id'], county['county_count'])
                }
            self.fields['county_%s' % county_underscore] = forms.ChoiceField(
                widget=CheckboxInput(attrs=attrs, check_test=True),
                initial=county_underscore,
                label = county['county'],
                required=False)
            for city in county['cities']:
                city_underscore = city['city'].replace(" ", "_")
                for _zip in city['zips']:
                    self.fields['zip_%s' % _zip['zip']] = forms.IntegerField(
                        widget=forms.HiddenInput(
                        attrs={'class': "zip region_%s region_%s zip_%s" % (
                                county_underscore,
                                city_underscore,
                                _zip['zip']),
                            'id': "id_%s_%s" % (
                                _zip['zip_id'], _zip['zip_count'])}),
                    required=False, initial=_zip['zip'])

        self.fields['county_array'] = forms.CharField(widget=forms.HiddenInput(), 
            required=False)
        self.fields['zip_array'] = forms.CharField(widget=forms.HiddenInput(), 
            required=False)
        self.fields['subdivision_consumer_count'] = forms.IntegerField(
            widget=forms.HiddenInput(
                attrs={'class':"subdivision_consumer_count"}), 
        required=False, initial=0)
        
    def clean_dynamic_fields(self, post_data):
        """ Clean method for this form. """
        self.cleaned_data = {}
        self._errors = ErrorDict()
        county_array = post_data['county_array'].split(",")
        zip_array = post_data['zip_array'].split(",")
        if county_array[0] is u'':
            county_array.pop(0)
        if zip_array[0] is u'':
            zip_array.pop(0)
        county_array = [int(county) for county in county_array]
        zip_array = [int(_zip) for _zip in zip_array]
        subdivision_consumer_count = post_data['subdivision_consumer_count']
        self.cleaned_data = {
            'subdivision_consumer_count':subdivision_consumer_count,
            'zip_array':tuple(zip_array),
            'county_array':tuple(county_array)}
        return self

    def custom_is_valid(self, post_data):
        """ Custom is_valid form method to build cleaned_data and errors, then 
        return a boolean deeming the validity of the form.
        """
        self.clean_dynamic_fields(post_data)
        is_valid = True
        if self._errors or not self.cleaned_data:
            is_valid = False
        return is_valid


class AddFlyerByListForm(forms.Form):
    """ The Add Flyer By List Form. """
    def __init__(self, county_dict, *args, **kwargs):
        super(AddFlyerByListForm, self).__init__(*args, **kwargs)

        for county in county_dict:
            county_underscore = county['county'].replace(" ", "_")
            attrs = {'class':"county county_%s" % county_underscore,
                     'id':"id_%s_%s" % (county['county_id'],
                                        county['county_count'])}
            self.fields['county_%s' % county_underscore] = forms.ChoiceField(
                widget=CheckboxInput(
                    attrs=attrs,
                    check_test=True),
                initial=county_underscore,
                label = '%s' % (county['county']),
                required=False)
            
            for city in county['cities']:
                if len(city['zips']) is 1:
                    city_underscore = city['city'].replace(" ", "_")
                    self.fields['city_%s' % city_underscore] = \
                        forms.ChoiceField(
                            widget=forms.CheckboxInput(
                                attrs={'class': "city region_%s city_%s" % (
                                        county_underscore,
                                        city_underscore),
                                   'id': "id_%s_%s" % (city['city_id'],
                                        city['city_count'])},
                                check_test=True),
                            required=False,
                            label = '%s %s' % (city['city'],
                                city['zips'][0]['zip']),
                            initial=city_underscore)
                else:
                    city_underscore = city['city'].replace(" ", "_")
                    self.fields['city_%s' % city_underscore] = \
                        forms.ChoiceField(
                            widget=forms.CheckboxInput(
                                attrs={'class': "city region_%s city_%s" % (
                                        county_underscore,
                                        city_underscore),
                                    'id': "id_%s_%s" % (city['city_id'],
                                        city['city_count'])},
                                check_test=True),
                            required=False,
                            label = '%s' % (city['city']),
                            initial=city_underscore)
                    for _zip in city['zips']:
                        self.fields['zip_%s' % _zip['zip']] = forms.ChoiceField(
                            widget=forms.CheckboxInput(
                                attrs={'class':
                                    "zip region_%s region_%s zip_%s" % (
                                        county_underscore,
                                        city_underscore,
                                        _zip['zip']),
                                   'id':"id_%s_%s" % (_zip['zip_id'], 
                                        _zip['zip_count'])},
                                check_test=True),
                            required=False,
                            label = '%s' % (_zip['zip']),
                            initial=_zip['zip'])
        self.fields['county_array'] = forms.CharField(
            widget=forms.HiddenInput(), required=False)
        self.fields['zip_array'] = forms.CharField(widget=forms.HiddenInput(), 
            required=False)
        self.fields['subdivision_consumer_count'] = forms.IntegerField(
            widget=forms.HiddenInput(
                attrs={'class':"subdivision_consumer_count"}), 
        required=False, initial=0)
        
    def clean_dynamic_fields(self, post_data):
        """ Clean method for this form. """
        self.cleaned_data = {}
        self._errors = ErrorDict()
        county_array = post_data['county_array'].split(",")
        zip_array = post_data['zip_array'].split(",")
        if county_array[0] is u'':
            county_array.pop(0)
        if zip_array[0] is u'':
            zip_array.pop(0)
        county_array = [int(county) for county in county_array]
        zip_array = [int(_zip) for _zip in zip_array]
        subdivision_consumer_count = post_data['subdivision_consumer_count']
        self.cleaned_data = {
            'subdivision_consumer_count':subdivision_consumer_count,
            'zip_array':tuple(zip_array),
            'county_array':tuple(county_array)}
        return self

    def custom_is_valid(self, post_data):
        """ Custom is_valid form method to build cleaned_data and errors, then 
        return a boolean deeming the validity of the form.
        """
        self.clean_dynamic_fields(post_data)
        is_valid = True
        if self._errors or not self.cleaned_data:
            is_valid = False
        return is_valid
