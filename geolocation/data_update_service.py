""" Service functions for building out the data in models of the geolocation app.
"""
from math import cos, sin, radians
from decimal import Decimal

from django.db import connection, transaction
from django.contrib.gis.geos import GEOSGeometry

from geolocation.models import Coordinate

def update_city_coords():
    """ Update geolocation_uscity records with valid coordinates. Creates coords
    if they do not exist.
    """
    cursor = connection.cursor()
    cursor_insert = connection.cursor()
    cursor.execute("""
        SELECT id, ST_AsText(ST_Centroid(geom)) "point"
        FROM prep_city_fix
        WHERE coordinate_id IS NULL and geom IS NOT NULL
    """)
    for city in cursor:
        point = GEOSGeometry(city[1])
        point.y = Decimal(str(point.y)).quantize(Decimal('.0000000001'))
        point.x = Decimal(str(point.x)).quantize(Decimal('.0000000001'))
        try:
            coord = Coordinate.objects.get(
                latitude=point.y, longitude=point.x)
        except Coordinate.DoesNotExist:
            coordinate = Coordinate()
            coordinate.latitude = point.y
            coordinate.longitude = point.x
            coordinate.rad_lat = radians(coordinate.latitude)
            coordinate.rad_lon = radians(coordinate.longitude)
            coordinate.sin_rad_lat = sin(coordinate.rad_lat)
            coordinate.cos_rad_lat = cos(coordinate.rad_lat)
            coordinate.save()
            coord = Coordinate.objects.get(
                latitude=point.y, longitude=point.x)
        cursor_insert.execute("""
        UPDATE prep_city_fix
        SET coordinate_id = %s
        WHERE id = %s and coordinate_id is null;
        """ % (coord.id, city[0]))
        transaction.commit_unless_managed()
