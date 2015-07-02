""" Forms for business locations model """

from django import forms
from django.contrib.localflavor.us.forms import USStateField

from advertiser.business.location.service import (update_business_location,
    add_location_to_business)
from common.custom_cleaning import trim_fields_in_form
from common.form_widgets import USStateSelect
from common.session import add_location_id_to_coupon, parse_curr_session_keys

class CreateLocationForm(forms.Form):
    """ Create a location. """
    def __init__(self, site=None, *args, **kwargs):
        super(CreateLocationForm, self).__init__(*args, **kwargs)
        count = 1
        while count <= 10:        
            self.fields['location_address1_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                    attrs={'class':'form_location', 'alt':'address1', 
                           'size':'35', 'maxlength':'50', 'tabindex':'2'}), 
                required=False
                )
            self.fields['location_address2_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                    attrs={'class':'form_location', 'alt':'address2', 
                           'size':'35', 'maxlength':'50', 'tabindex':'3'}), 
                required=False
                )
            self.fields['location_city_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                attrs={'class':'form_city', 'alt':'city', 
                       'size':'35', 'maxlength':'50', 'tabindex':'4'}), 
                required=False
                )
            self.fields['location_state_province_' + str(count)] = USStateField(
                widget=USStateSelect(
                    attrs={'class':'form_state_province', 'alt':'state', 
                           'tabindex':'5'}, site=site), 
                required=False
                )
            self.fields['location_zip_postal_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                    attrs={'class':'form_location', 'alt':'zip_postal', 
                           'size':'10', 'maxlength':'9', 'tabindex':'6'}), 
                required=False
                )
            self.fields['location_area_code_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                    attrs={'class':'form_phone', 'alt':'area_code', 
                           'size':'3', 'maxlength':'3', 'tabindex':'7'}), 
                required=False
                )
            self.fields['location_exchange_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                    attrs={'class':'form_phone', 'alt':'exchange', 
                           'size':'3', 'maxlength':'3', 'tabindex':'8'}),
                required=False
                )
            self.fields['location_number_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                    attrs={'class':'form_phone', 'alt':'number', 
                           'size':'6', 'maxlength':'4', 'tabindex':'9'}), 
                required=False
                )
            self.fields['location_description_' + str(count)] = forms.CharField(
                widget=forms.TextInput(
                    attrs={'class':'form_location', 'alt':'description', 
                           'size':'35', 'maxlength':'50', 'tabindex':'10'}), 
                required=False
                )
            count += 1


    def clean(self):
        """ Clean state_province field of default if no other address info
        present.
        """
        self.cleaned_data = trim_fields_in_form(self)
        count = 1
        while count <= 10:
            if not self.cleaned_data['location_address1_' + str(count)] and \
            not self.cleaned_data['location_address2_' + str(count)] and \
            not self.cleaned_data['location_city_' + str(count)] and \
            not self.cleaned_data['location_zip_postal_' + str(count)]:
                self.cleaned_data['location_state_province_' + str(count)] = ''
            count = count + 1  
        return self.cleaned_data
    
    def locations_posted(self):
        """ Build a location_number_list of all the location dynamic numbers 
        that got POSTed with data in those specific field. So if location_1 and 
        location_3 on the location form are the only locations that have info 
        filled into them, the location_number_list will == [1, 3].  
        location_count == 2.
        """
        location_count = 0
        location_number_list = []
        count = 1
        while count <= 10:
            location_address1 = self.cleaned_data[
                                        'location_address1_' + str(count)]
            location_address2 = self.cleaned_data[
                                        'location_address2_' + str(count)]
            location_city = self.cleaned_data[
                                        'location_city_' + str(count)]
            location_description = self.cleaned_data[
                                        'location_description_' + str(count)]
            location_state_province = self.cleaned_data[
                                        'location_state_province_' + str(count)]
            location_zip_postal = self.cleaned_data[
                                        'location_zip_postal_' + str(count)]
            location_area_code = self.cleaned_data[
                                        'location_area_code_' + str(count)]
            location_exchange = self.cleaned_data[
                                        'location_exchange_' + str(count)]
            location_number = self.cleaned_data[
                                        'location_number_' + str(count)]
            if (location_address1 
            or location_address2 
            or location_city 
            or location_description 
            or location_state_province 
            or location_zip_postal 
            or location_area_code 
            or location_exchange 
            or location_number):
                location_count = location_count + 1
                location_number_list.append(count)
            count = count + 1
        return location_count, location_number_list
    
    def add_business_coupon_locations(self, request, coupon):
        """ Add locations to a coupon for the first time. For every location on
        the create_location form, add it to the coupons location_list to be 
        added to the coupon. 
        """
        location_list = []
        count = 1
        while count <= 10:
            location_address1 = self.cleaned_data[
                                        'location_address1_' + str(count)]
            location_address2 = self.cleaned_data[
                                        'location_address2_' + str(count)]
            location_city = self.cleaned_data[
                                        'location_city_' + str(count)]
            location_description = self.cleaned_data[
                                        'location_description_' + str(count)]
            location_state_province = self.cleaned_data[
                                        'location_state_province_' + str(count)]
            location_zip_postal = self.cleaned_data[
                                        'location_zip_postal_' + str(count)]
            location_area_code = self.cleaned_data[
                                        'location_area_code_' + str(count)]
            location_exchange = self.cleaned_data[
                                        'location_exchange_' + str(count)]
            location_number = self.cleaned_data[
                                        'location_number_' + str(count)]
            if (location_address1 
            or location_address2 
            or location_city 
            or location_description 
            or location_state_province 
            or location_zip_postal 
            or location_area_code 
            or location_exchange 
            or location_number):
                location_id = add_location_to_business(request, 
                business_id=coupon.offer.business.id,
                location_address1=location_address1,
                location_address2=location_address2,
                location_city=location_city,
                location_description=location_description,
                location_state_province=location_state_province,
                location_zip_postal=location_zip_postal,
                location_area_code=location_area_code,
                location_exchange=location_exchange,
                location_number=location_number)
                location_list.append(location_id)
                add_location_id_to_coupon(request, location_id)
            count = count + 1
        coupon.location = location_list
       
    def update_all_business_locations(self, request, location_ids_list):
        """ Update all business locations with all the info  that just got
        posted. 
        """
        for location_ids_dict in location_ids_list:
            location_number = location_ids_dict['location_number']
            location_address1 = self.cleaned_data[
                            'location_address1_' + str(location_number)]
            location_address2 = self.cleaned_data[
                            'location_address2_' + str(location_number)]
            location_city = self.cleaned_data[
                            'location_city_' + str(location_number)]
            location_description = self.cleaned_data[
                            'location_description_' + str(location_number)]
            location_state_province = self.cleaned_data[
                            'location_state_province_' + str(location_number)]
            location_zip_postal = self.cleaned_data[
                            'location_zip_postal_' + str(location_number)]
            location_area_code = self.cleaned_data[
                            'location_area_code_' + str(location_number)]
            location_exchange = self.cleaned_data[
                            'location_exchange_' + str(location_number)]
            location_number = self.cleaned_data[
                            'location_number_' + str(location_number)]
            update_business_location(request=request, 
                location_id=location_ids_dict['location_id'],
                location_address1=location_address1,
                location_address2=location_address2,
                location_city=location_city,
                location_description=location_description,
                location_state_province=location_state_province,
                location_zip_postal=location_zip_postal,
                location_area_code=location_area_code,
                location_exchange=location_exchange,
                location_number=location_number)
            
    def create_business_locations(self, request, coupon, add_loc_number_list):
        """ Pass in a list of location_number's which got posted on the 
        create_location_form that we should add to the business in the database
        and the session.
        """
        for location_number in add_loc_number_list:
            location_address1 = self.cleaned_data[
                            'location_address1_' + str(location_number)]
            location_address2 = self.cleaned_data[
                            'location_address2_' + str(location_number)]
            location_city = self.cleaned_data[
                            'location_city_' + str(location_number)]
            location_description = self.cleaned_data[
                            'location_description_' + str(location_number)]
            location_state_province = self.cleaned_data[
                            'location_state_province_' + str(location_number)]
            location_zip_postal = self.cleaned_data[
                            'location_zip_postal_' + str(location_number)]
            location_area_code = self.cleaned_data[
                            'location_area_code_' + str(location_number)]
            location_exchange = self.cleaned_data[
                            'location_exchange_' + str(location_number)]
            location_number = self.cleaned_data[
                            'location_number_' + str(location_number)]
            location_id = add_location_to_business(request, 
                    business_id=coupon.offer.business_id,
                    location_address1=location_address1,
                    location_address2=location_address2,
                    location_city=location_city,
                    location_description=location_description,
                    location_state_province=location_state_province,
                    location_zip_postal=location_zip_postal,
                    location_area_code=location_area_code,
                    location_exchange=location_exchange,
                    location_number=location_number)
            coupon.location.add(location_id)
            add_location_id_to_coupon(request, location_id)

def get_location_initial_dict(request):
    """ Populate the initial dict for the locations form with this coupons
    locations.
    """
    session_dict = parse_curr_session_keys(request.session, ['this_business'])
    location_initial_dict = {}
    count = 0
    while count < len(session_dict['this_business']['location']): 
        this_location = session_dict['this_business']['location'][count]
        
        location_initial_dict.update({
            'location_address1_' + str(count+1):this_location[
                                                    'location_address1'],
            'location_address2_' + str(count+1):this_location[
                                                    'location_address2'],
            'location_city_' + str(count+1):this_location[
                                                    'location_city'],
            'location_state_province_' + str(count+1):this_location[
                                                    'location_state_province'],
            'location_zip_postal_' + str(count+1):this_location[
                                                    'location_zip_postal'],
            'location_description_' + str(count+1):this_location[
                                                    'location_description'],
            'location_area_code_' + str(count+1):this_location[
                                                    'location_area_code'],
            'location_exchange_' + str(count+1):this_location[
                                                    'location_exchange'],
            'location_number_' + str(count+1):this_location[
                                                    'location_number']})
        count = count + 1
    return location_initial_dict