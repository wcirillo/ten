""" Views for geolocation app in project ten. """

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from geolocation.models import USZip


def show_my_location(request):
    """ Show the latitude and longitude coordinates of my current location
    given to me through Ajax, (prototype should be removed after implemented).
    """
    context_instance_dict = {'js_my_location': 1}
    return render_to_response(
        'demo/display_my_location.html',
        context_instance=RequestContext(request, context_instance_dict))

def get_my_location(request):
    """ Get the zip found containing the latitude and longitude coordinates of
    my current location given to me from the end user's browser.
    """
    lon = request.GET.get('lon', False)
    lat = request.GET.get('lat', False)
    return HttpResponse(str(USZip.objects.get_zip_this_coordinate(lat, lon)))
