""" 
Celery tasks for advertiser.business.location app.
Includes routine for saving geocoded address coordinates.
"""
from decimal import Decimal
import logging

from celery.decorators import task
from django.conf import settings
from django.core.exceptions import ValidationError

from advertiser.models import Location, LocationCoordinate
from email_gateway.send import send_admin_email
from geolocation.geocode_address import GEOCODE_LOCATION

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


@task()
def create_location_coordinate(location_id):
    """ Save lat and long coordinates for this location. """
    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        return
    # Get lat & lon for this location's address.
    try:
        coord = GEOCODE_LOCATION.get_coordinate(location)
    except ValidationError as e:
        # Send email alert.
        if (not settings.ENVIRONMENT['is_test']
        and settings.SEND_GEOCODE_NOTIFICATIONS):
            exception_message = (
            ['Error occurred while generating location coordinates.']
            + e.messages
            + [' Task executed from %s.' % settings.HTTP_PROTOCOL_HOST])
            send_admin_email(context={
                'to_email': [admin[1] for admin in settings.ADMINS],
                'subject': 'Geocoder Task Error',
                'admin_data': exception_message})
        coord = None
    if coord:
        # Save coordinates to LocationCoordinate model.
        new_coords = LocationCoordinate()
        new_coords.location = location
        new_coords.location_longitude = Decimal(coord[0])
        new_coords.location_latitude = Decimal(coord[1])
        new_coords.save()
