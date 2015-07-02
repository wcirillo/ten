"""" Service functions for location of a business of an advertiser. """
from advertiser.models import Location
from common.session import add_update_business_location

def add_location_to_business(request, **kwargs):
    """ Add location to a business in db and session. """
    location_id = None
    if kwargs['location_state_province'] or kwargs['location_city'] \
    or kwargs['location_exchange'] or kwargs['location_area_code'] \
    or kwargs['location_number'] or kwargs['location_description'] \
    or kwargs['location_zip_postal'] or kwargs['location_address1'] \
    or kwargs['location_address2']:
        location = Location(
            business_id=kwargs['business_id'],
            location_address1=kwargs['location_address1'],
            location_address2=kwargs['location_address2'],
            location_city=kwargs['location_city'],
            location_description=kwargs['location_description'],
            location_state_province=kwargs['location_state_province'],
            location_zip_postal=kwargs['location_zip_postal'],
            location_area_code=kwargs['location_area_code'],
            location_exchange=kwargs['location_exchange'],
            location_number=kwargs['location_number'])
        location.save()
        location_id = location.id
        add_update_business_location(request, location)
    return location_id

def update_business_location(request, **kwargs):
    """ Update a specific business location in the db and session """
    location = Location.objects.get(id=kwargs['location_id'])
    location.location_address1 = kwargs['location_address1']
    location.location_address2 = kwargs['location_address2']
    location.location_city = kwargs['location_city']
    location.location_state_province = kwargs['location_state_province']
    location.location_description = kwargs['location_description']
    location.location_zip_postal = kwargs['location_zip_postal']
    location.location_area_code = kwargs['location_area_code']
    location.location_exchange = kwargs['location_exchange']
    location.location_number = kwargs['location_number']
    location.save()
    add_update_business_location(request, location)

def create_location_ids_list(business_loc_ids, location_number_list):
    """ Create a list of dicts with each holding a location_number and a
    location_id to be used when updating locations.
    """
    count = 0
    location_ids_list = []
    while count < len(location_number_list):
        location_item_dict = {'location_id':business_loc_ids[count],
                            'location_number':location_number_list[count]}
        location_ids_list.append(location_item_dict)
        count = count + 1
    return location_ids_list

def get_locations_for_coupons(all_coupons):
    """ List locations for these coupons. """
    location_list = []
    for coupon in all_coupons:
        for location in coupon.location.all().order_by('id'):
            if location not in location_list:
                location_list.append(location)
    return location_list

def get_location_coords_list(locations):
    """
    List all coordinates for this coupon's locations, handles multiple
    coupon's locations.
    """
    location_coords = [] # Create coordinates list for map.
    for location in locations:
        coords = location.get_coords()
        if coords:
            location_coords.append([str(coords[0]), str(coords[1])])
    if len(location_coords) < 1:
        location_coords = None
    return location_coords