""" Views for market app. """
#pylint: disable=W0613
from django.http import HttpResponse

from market.models import Site
from market.service import get_or_set_site_markers

def get_or_set_site_geoms(request, requested_file):
    """ 
    Return txt data file of all zip geometries for this site in 900913
    projection. 
    """
    if 'zip-geoms.txt' in requested_file:
        region_file_type_extension = 'zip-geoms-data.txt'
    elif 'city-geoms.txt' in requested_file:
        region_file_type_extension = 'city-geoms-data.txt'
    try:
        site_name = requested_file.replace('-zip-geoms.txt','').replace('-city-geoms.txt','').lower()
        site = Site.objects.get(directory_name=site_name)
        geom_data = site.get_or_set_geometries(region_file_type_extension)
    except Site.DoesNotExist:
        geom_data = 'Error: %s is invalid for this feature.' % site_name
    
    return HttpResponse(geom_data, mimetype='text/plain')

def get_or_set_market_markers(request):
    """ 
    Return txt data file of all marker points for map disply. 
    """
    return HttpResponse(str(get_or_set_site_markers()))
