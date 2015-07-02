"""
Views for widgets of coupon app.
"""
#pylint: disable=W0613
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404

from advertiser.models import Advertiser, Business
from market.models import Site
from coupon.tasks import CreateWidget


def create_widget_from_web(request, widget_type, widget_identifier, 
    widget_file):
    """ Vet the input and return the widget. """
    if widget_type == 'advertisers':
        type_instance = get_object_or_404(Advertiser, pk=widget_identifier)
    elif widget_type == 'businesses':
        type_instance = get_object_or_404(Business, pk=widget_identifier)
    elif widget_type == 'markets':
        type_instance = get_object_or_404(Site,
            directory_name=widget_identifier)
    else:
        raise Http404
    response = CreateWidget().run(type_instance, template=widget_file)
    if not response:
        raise Http404
    return HttpResponse(response) 
