"""
Models for market app.

Inspired by django.contrib.sites
Differences:
    Site has many app specific fields: directory_name is an important one.
    SITE_ID is not set in settings for the project, but determined on the fly 
    from request.HTTP_HOST in market.middleware.
"""
#pylint: disable=W0613
import logging
from decimal import Decimal
from math import cos, sin, radians
import os

from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.template import Context
from django.template.loader import get_template

from geolocation.models import Coordinate, USCounty, USState, USZip
from geolocation.service import build_zip_geometries, build_city_geometries

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)
LOG.info('Logging Started')


class SiteDeferredManager(models.Manager):
    """ A manager for deferring fields. """
    def get_query_set(self):
        return super(SiteDeferredManager, self).get_query_set().defer(
            'envelope', 'geom', 'point')


class SiteManager(models.GeoManager):
    """ Default manager for Site model. """ 
    def get_current(self):
        """ Get an instance from cache. """
        cache_key = "site-%s" % self.id
        current_site = cache.get(cache_key)
        return current_site

    def cacheable_sites(self):
        """ Returns the Site QuerySet relevant for caching. """
        return self.filter(inactive_flag=False).defer(
            'envelope', 'geom', 'point')

    def set_site_cache(self):
        """ Sets the Site object cache. Sets each site into cache. """
        LOG.debug('SiteManager.set_site_cache')
        cache.set('site-cache', self.cacheable_sites())

    def get_or_set_cache(self):
        """
        Returns the Site object cache (or it's equivalent for a dummy cache).
        """
        LOG.debug('SiteManager.get_or_set_cache')
        site_cache = cache.get('site-cache')
        if site_cache is None:
            site_cache = Site.objects.cacheable_sites()
            self.set_site_cache()
        return site_cache

    @staticmethod
    def get_or_set_site_count():
        """
        Returns the count of sites from  cache, or sets it into cache.
        """
        LOG.debug('SiteManager.get_or_set_site_count')
        key = 'site-count'
        site_count = cache.get(key)
        if site_count is None:
            site_count = Site.objects.cacheable_sites().count()
            cache.set(key, site_count)
        return site_count

    @staticmethod
    def clear_cache():
        """ Clears the Site object cache. """
        cache.delete_many(['site-cache', 'site-state-list', 'site-count'])
    
    @staticmethod
    def clear_geom_caches(site_id):
        """ Clears the caches dependent upon geometry market relationships.
        Note this will not clear the caches for the surrounding close sites.
        """
        cache.delete_many(['site-markers', 'site-%s-counties' % site_id,
            'site-%s-close-sites' % site_id, 'site-%s-geom' % site_id])
        zip_data_file = '%sdynamic/map-data/site-%s-zip-geom-data.txt' \
            % (settings.MEDIA_ROOT, site_id)
        if os.path.exists(zip_data_file):
            os.remove(zip_data_file)

    @staticmethod
    def get_sites_this_zip(code):
        """ Return all the sites related to this zip code. """
        sites = Site.objects.raw("""
            SELECT site.*
            FROM market_site site
            JOIN market_site_us_county s_cn
                ON s_cn.site_id = site.id
            JOIN geolocation_uszip z

                ON z.us_county_id = s_cn.uscounty_id
                WHERE z.code = %s""", [code])
        return sites

class Site(models.Model):
    """ Sites are 10LocalCoupons, 10HudsonValleyCoupons etc. """
    domain = models.CharField(_('domain name'), max_length=100,
        unique=True, help_text=_("Ex: '10HudsonValleyCoupons.com'"))
    name = models.CharField(_('market name'), max_length=50, unique=True,
        help_text=_("Used to build the logo 'image'. Example 'Hudson Valley'"))
    short_name = models.CharField(_('short market name'), max_length=22, 
        unique=True, help_text=_('Appears in SMS messages, for example.'))
    region = models.CharField(_('region'), max_length=50,
        help_text=_("Ex: 'Hudson Valley Area'"))
    directory_name = models.CharField(_('directory name'), max_length=50,
        null=True, blank=True, unique=True,
        help_text=_("Ex: 'hudson-valley'"))
    launch_date = models.DateField(_('launch date'), max_length=50, null=True, 
        blank=True)
    base_rate = models.DecimalField(_('base rate'), max_digits=6, 
        decimal_places=0, default=0)
    default_zip_postal = models.CharField(_('Zip/Postal'), max_length=9, 
        null=True, blank=True)
    default_state_province = models.ForeignKey('geolocation.USState', 
        related_name='site', null=True, blank=True)
    market_cities = models.CharField(_('market cities'), max_length=100,
        null=True, blank=True, 
        help_text=_("Ex: 'Poughkeepsie-Newburgh-Middletown'"))
    media_partner_allotment = models.PositiveSmallIntegerField(
        _('media partner allotment'), default=0, 
        help_text=_("""How many free flyer placements allowed per 
            media partner?"""))
    phase = models.PositiveSmallIntegerField(
        _('phase'), default=1, 
        help_text=_('What phase is this market in?'))
    inactive_flag = models.BooleanField(_('inactive flag'), default=False)
    us_state = models.ForeignKey('geolocation.USState', related_name='sites', 
        null=True, blank=True,
        help_text=_("Select this if the market covers an entire state."))
    us_county = models.ManyToManyField('geolocation.USCounty', 
        related_name='sites', null=True, blank=True)
    us_city = models.ManyToManyField('geolocation.USCity',
        related_name='sites', null=True, blank=True, editable=False)
    us_zip = models.ManyToManyField('geolocation.USZip',
        related_name='sites', null=True, blank=True, editable=False)
    coordinate = models.ForeignKey('geolocation.Coordinate',
        related_name='sites', null=True, blank=True, editable=False, 
        help_text='The geographic center of the market, for map rendering')
    envelope = models.GeometryField(srid=4326, null=True, blank=True, 
        editable=False,
        help_text='The four corner points that define this market.')
    geom = models.GeometryField(srid=4326, null=True, blank=True, 
        editable=False,
        help_text='Contains every geometry point defining this market.')
    point = models.PointField(null=True, blank=True, editable=False,
        spatial_index=True, geography=True,
        help_text="The central geographical point within this market.")
    objects = SiteManager()
    admin = SiteDeferredManager()
    
    class Meta:
        ordering = ('id',)
        
    def __unicode__(self):
        return u'%s' % self.name
        
    def save(self, *args, **kwargs):
        """ Saves a site, computes its geographic center, flushes site cache, 
        and creates a URLconf required by market/middleware.py.
        """
        Site.objects.clear_cache()
        # Populate geometry fields, unless coming from admin.
        if not kwargs.get('override_geom_update', None):
            self.update_geometry_fields()
        # Now the site has an id. Generate a urls_local for this site.
        # Unless site one, which is special :D
        if self.id > 1:
            template_ = get_template('urls_local.html')
            content = template_.render(Context({'current_site': self}))
            file_name = '%s/urls_local/urls_%s.py' % (
                settings.PROJECT_PATH, self.id
                )
            file_ = open(file_name, 'w')
            file_.write(content)
            file_.close()
    
    def update_geometry_fields(self, us_county_list=None):
        """ Update geom, point and envelope fields based on county data, the 
        form parameter can come from admin. 
        """
        Site.objects.clear_geom_caches(self.id)
        try: 
            if us_county_list:
                geom = USCounty.objects.filter(
                    id__in=us_county_list).unionagg()
            else:
                geom = self.us_county.all().unionagg()
            point = geom.centroid
            envelope = geom.envelope
            point.y = Decimal(str(point.y)).quantize(Decimal('.0000000001'))
            point.x = Decimal(str(point.x)).quantize(Decimal('.0000000001'))
            try:
                coord = Coordinate.objects.get(
                    latitude=point.y, longitude=point.x)
            except Coordinate.DoesNotExist:
                coord = Coordinate()
                coord.latitude = point.y
                coord.longitude = point.x
                coord.rad_lat = radians(coord.latitude)
                coord.rad_lon = radians(coord.longitude)
                coord.sin_rad_lat = sin(coord.rad_lat)
                coord.cos_rad_lat = cos(coord.rad_lat)
                coord.save()
            self.coordinate = coord
            self.point = point
            self.geom = geom
            self.envelope = envelope
        except (ValueError, AttributeError, KeyError) as error:
            LOG.info('Site %s.save(): %s' % (self.name, error)) 
        super(Site, self).save()
        return self
        
    def close_sites(self, code=None, miles=100, max_results=5):
        """ Return the n closest markets within x miles of this zip, excluding 
        this site, ie: "get sites close to me."
        """
        if not code:
            code = self.default_zip_postal
        sites = None
        try:
            coordinate = USZip.objects.select_related('coordinate').only(
                'coordinate__longitude', 'coordinate__latitude'
                ).get(code=code).coordinate
            _point = Point(coordinate.longitude, coordinate.latitude)
            sites = Site.objects.filter(envelope__distance_lte=(_point, 
                D(mi=miles))).exclude(id=self.id).distance(_point).values(
                'id', 'name', 'directory_name', 'domain', 'default_zip_postal',
                'default_state_province__abbreviation', 
                'default_state_province__name', 'distance').order_by(
                'distance')[:max_results]
        except USZip.DoesNotExist:
            pass
        return sites
   
    def get_name_no_spaces(self):
        """ Return market name with no spaces (for coupon web logo display). """
        name_no_spaces = str(self.name)
        return name_no_spaces.replace(' ', '')

    def get_flyer_recipients(self):
        """ Return lazy query of consumers for this site instance that are 
        emailable and subscribed to receive the weekly email flyer.
        Note: This query is used by Finance to report consumer growth on our 
        sites to Media Partners and should not be changed with confirmation.
        """
        return self.consumers.filter(
            is_emailable=True, email_subscription=1)

    def get_or_set_close_sites(self):
        """ Get close_sites from cache if it exists, or set cache and return.
        """
        close_sites = cache.get("site-%s-close-sites" % self.id)
        if not close_sites:
            close_sites = self.close_sites()
            cache.set(("site-%s-close-sites" % self.id), self.close_sites())
        return close_sites

    def get_or_set_consumer_count(self):
        """ Get count of consumers subscribed to flyer and are emailable for a 
        this site from cache, if cache not yet set, set it and return.
        """
        consumer_count = cache.get("site-%s-consumer-count" % self.id)
        if not consumer_count:
            consumer_count = self.get_flyer_recipients().count()
            cache.set(("site-%s-consumer-count" % self.id), consumer_count)
        return consumer_count
    
    def get_or_set_counties(self):
        """ Get counties from cache if it exists, or set cache and return. """
        counties = cache.get("site-%s-counties" % self.id)
        if not counties:
            counties = self.us_county.values_list('name', flat=True)
            cache.set(("site-%s-counties" % self.id), counties)
        return counties
    
    def get_or_set_geometries(self, region_file_type_extension):
        """  Get zip geometry data from cached file if it exists, or set cached  
        file and return.
        """
        data_filename = '%sdynamic/map-data/site-%s-%s' \
            % (settings.MEDIA_ROOT, self.id, region_file_type_extension)
        if os.path.exists(data_filename):
            data_file = open(data_filename)
            geoms = data_file.read()
        else:
            if 'city' in region_file_type_extension:
                geoms = build_city_geometries(self)
            elif 'zip' in region_file_type_extension:
                geoms = build_zip_geometries(self)
            data_file = open(data_filename, 'w')
            data_file.write(geoms)
        data_file.close()
        return geoms
    
    def get_or_set_geom(self):
        """ Cache this site's geom for future retrieval (from close_sites list
        used for maps). Geom will be retrieved from cache and/or set when
        requested.
        """
        geom = cache.get("site-%s-geom" % self.id)
        if not geom:
            geom = self.set_geom()
        return geom
    
    def set_geom(self):
        """ Set this site geom in cache and return. """
        geom = self.geom
        cache.set(("site-%s-geom" % self.id), geom)
        return geom

    def spot_name(self):
        """ We had to munge the 'short_name' of site to jive with the spot 
        producer's system.  We re-do the munge here to match the current site
        to the proper spot files.
        """
        return str(self.short_name).translate(None, " .-")

    def get_abbreviated_state_province(self):
        """ Return the abbreviated default state/province for this site. 
        
        This syntax is more convoluted then just doing...
        "self.default_state_province.abbreviation"
        ...but allows for deferring of us_state.geom etc.

        Now uses get or set caching methodology.
        """
        abbreviation = cache.get("site-%s-abbreviation" % self.id)
        if not abbreviation:
            try:
                abbreviation = USState.objects.only('id', 'abbreviation').get(
                    id=self.default_state_province_id).abbreviation
            except USState.DoesNotExist:
                abbreviation = ''
            cache.set("site-%s-abbreviation" % self.id, abbreviation)
        return abbreviation
    
    def get_state_division_type(self, plural_form=False):
        """ Return the term used to describe the geographic divisions of the
        default state for this site (county, parish or borough). (Not all sites 
        have states assigned to them (local site 1 and return-path-monitor).
        """
        municipality_division = ''
        if self.default_state_province:
            municipality_division = \
            self.default_state_province.get_municipality_division(plural_form)
        return municipality_division

    def is_geom_in_market(self, this_geom):
        """ Query market geometry to determine if this zip resides within. If no
        results are found, a 0 is returned which will result in an evaluation of
        False. 
        """
        if this_geom:
            return Site.objects.filter(
            id=self.id, geom__contains=this_geom).count()
        else:
            return False


class TwitterAccount(models.Model):
    """ Stores the Twitter account info for each local site """
    site = models.OneToOneField(Site, verbose_name='related market', 
        related_name='twitter_account')
    twitter_name = models.CharField(_('Twitter account name'), max_length=15, 
        unique=True, blank=True, null=True, 
        help_text=_("You'll need to create this account."))
    password = models.CharField(_('Twitter account password'), 
        max_length=25, blank=True, null=True)
    consumer_key = models.CharField(max_length=50, blank=True, null=True, 
        help_text=_("Get it here: http://twitter.com/apps") )
    consumer_secret = models.CharField(max_length=50, blank=True, null=True)
    access_key = models.CharField(max_length=50, blank=True, null=True)
    access_secret = models.CharField(max_length=50, blank=True, null=True)
    
    class Meta:
        """ Override existing Twitter model field names """
        app_label = 'market'
        verbose_name = _('Twitter Account',)
        verbose_name_plural = _('Twitter Accounts',)
    
    def __unicode__(self):
        return self.twitter_name if self.twitter_name else u'%s' % self.id