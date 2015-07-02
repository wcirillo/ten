""" Models for geolocation app. """

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.core.exceptions import ValidationError


class Coordinate(models.Model):
    """
    Relevant unique lat and long points. There are far fewer of these than 
    postal codes.
    """
    id = models.AutoField(primary_key=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    rad_lat = models.FloatField()
    rad_lon = models.FloatField()
    sin_rad_lat = models.FloatField()
    cos_rad_lat = models.FloatField()
    
    def __unicode__(self):
        return u'%s, %s' % (self.latitude, self.longitude)
        
    def delete(self):
        raise ValidationError('Coordinate cannot be deleted.')


class USState(models.Model):
    """ States in the United States. """
    id = models.AutoField(primary_key=True)
    name = models.CharField(unique=True, max_length=24)
    abbreviation = models.CharField(unique=True, max_length=2)
    geom = models.MultiPolygonField(srid=4326, null=True)
    objects = models.GeoManager()
    
    class Meta:
        ordering = ('name',)
        verbose_name = "US State"
        verbose_name_plural = "US States"

    def __unicode__(self):
        return u'%s' % self.name
        
    def save(self):
        raise ValidationError('USState cannot be saved.')
        
    def delete(self):
        raise ValidationError('USState cannot be deleted.')
    
    def get_municipality_division(self, plural_form=False):
        """ 
        Return relevant municipality division terminology for what equates to a
        county in New York. 
        """
        if self.abbreviation not in ('AK', 'LA'):
            # Handle popular requests first.
            return plural_form and 'counties' or 'county'
        else:
            if self.abbreviation == 'AK':
                return plural_form and 'boroughs' or 'borough'
            elif self.abbreviation == 'LA':
                return plural_form and 'parishes' or 'parish'

    
class USCounty(models.Model):
    """ Counties, LA parishes, and Alaskan boroughs and census areas. """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=25)
    us_state = models.ForeignKey(USState, related_name='us_counties')
    geom = models.MultiPolygonField(srid=4326, null=True)
    objects = models.GeoManager()
    
    class Meta:
        ordering = ('us_state', 'name')
        verbose_name = "US County"
        verbose_name_plural = "US Counties"

    def __unicode__(self):
        return u'%s, %s' % (self.name, self.us_state.name)
        
    def save(self):
        raise ValidationError('USCounty cannot be saved.')
        
    def delete(self):
        raise ValidationError('USCounty cannot be deleted.')


class USCity(models.Model):
    """ US Cities, Towns and Villages. """
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=33)
    coordinate = models.ForeignKey(Coordinate, related_name='us_cities')
    us_county = models.ForeignKey(USCounty, related_name='us_cities')
    us_state = models.ForeignKey(USState, related_name='us_cities')
    geom = models.MultiPolygonField(srid=4326, null=True)
    objects = models.GeoManager()
    
    class Meta:
        ordering = ('us_state', 'name')
        verbose_name = "US City"
        verbose_name_plural = "US Cities"

    def __unicode__(self):
        return u'%s, %s' % (self.name, self.us_state)
        
    def save(self):
        raise ValidationError('USCity cannot be saved.')
        
    def delete(self):
        raise ValidationError('USCity cannot be deleted.')


class USZipManager(models.GeoManager):
    """ Manager for USZip. Note its GeoManager. """
    def get_zips_this_site(self, site):
        """
        Return all the zips related to this site. The unions commented out are
        for when we need to support markets that are statewide, or are by city
        or by zip. Note: does not return model instances.
        """
        zips = self.raw("""
            SELECT z.id, z.code
            FROM geolocation_uszip z
            JOIN market_site_us_county s_cn
                ON s_cn.uscounty_id = z.us_county_id
            WHERE s_cn.site_id = %s
            """, [site.id])
        return zips
    
    @classmethod
    def get_zip_this_coordinate(cls, lat, lon):
        """ Return zipcode encasing this latitude-longitude coordinate. """
        us_zip = None
        if lat and lon:
            origin = Point(float(lon), float(lat))
            try:
                us_zip = USZip.objects.filter(geom__contains=origin)[0]
            except IndexError:
                pass
        return us_zip


class USZip(models.Model):
    """ 5 digit US Zip Codes. """
    id = models.AutoField(primary_key=True)
    code = models.CharField(unique=True, max_length=5)
    coordinate = models.ForeignKey(Coordinate, related_name='us_zips', 
        null=True, blank=True, default=1)
    us_city = models.ForeignKey(USCity, related_name='us_zips')
    us_county = models.ForeignKey(USCounty, related_name='us_zips')
    us_state = models.ForeignKey(USState, related_name='us_zips')
    geom = models.MultiPolygonField(srid=4326, null=True)
    objects = USZipManager()
    
    class Meta:
        ordering = ('code',)
        verbose_name = "US Zip Code"
        verbose_name_plural = "US Zip Codes"

    def __unicode__(self):
        return u'%s' % self.code
        
    def save(self):
        raise ValidationError('USZip cannot be saved.')
        
    def delete(self):
        raise ValidationError('USZip cannot be deleted.')
