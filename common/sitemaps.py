""" Util for building a sitemap for project ten. """
import datetime

from django.contrib.sitemaps import Sitemap
from django.core.urlresolvers import reverse

from advertiser.models import Business
from coupon.models import Coupon
from market.models import Site

from zinnia.sitemaps import EntrySitemap


class DefaultNamedURLSitemap(Sitemap):
    """ Given a set of named URLs, returns sitemap items for each. """
    changefreq = 'monthly'
    lastmod = datetime.datetime.now()
    
    def __init__(self, names):
        self.names = names
        self.priority = 0.1
        Sitemap.__init__(self)

    def items(self):
        return self.names

    @classmethod
    def location(cls, obj):
        return reverse(obj)


class LocalNamedURLSitemap(Sitemap):
    """ 
    A Sitemap for named urls that only exist on local market sites. 
    
    Since we don't want multiples of each indexed, site 2 is the canonical
    version.
    """
    changefreq = 'monthly'
    lastmod = datetime.datetime.now()
    
    def __init__(self, names):
        self.names = names
        self.priority = 0.1
        self.path = '/%s' % Site.objects.get(id=2).directory_name
        Sitemap.__init__(self)

    def items(self):
        return self.names

    def location(self, obj):
        return '%s%s' % (self.path, reverse(obj)) 


class LocalHomePagesMap(Sitemap):
    """ Sitemap for all local homepages. """
    changefreq = 'weekly'
    priority = 1.0
    lastmod = datetime.datetime.now()
    
    page_dict = {}
    # Filtering here would cause an extra hit:
    sites = Site.objects.get_or_set_cache() 
    for site in sites:
        if site.id > 1:
            page_dict[site.name] = '/%s/' % site.directory_name
        
    def items(self):
        return self.page_dict.keys()
        
    def location(self, url):
        return self.page_dict[url]


class CouponsMap(Sitemap):
    """ Sitemap for coupons. """
    changefreq = 'weekly'
    priority = 0.9
    
    @classmethod
    def location(cls, obj):
        path = obj.get_site().directory_name
        if len(path) > 1:
            path = '/%s' % path     
        return '%s%s' % (path, reverse('view-single-coupon', kwargs={
            'slug': obj.slug(),
            'coupon_id': obj.id
            }))
    
    @classmethod
    def items(cls):
        return Coupon.current_coupons.all()
    
    @classmethod
    def lastmod(cls, obj):
        """ When was this item last modified? """
        return obj.coupon_modified_datetime


class BusinessMap(Sitemap):
    """ Sitemap for 'all coupons this business' pages. """
    changefreq = 'weekly'
    priority = 0.9
    
    @classmethod
    def location(cls, obj):
        url_site_id = obj.advertiser.site.id
        if url_site_id == 1:
            url_site_id = 2
        path = Site.objects.only('directory_name').get(
            id=url_site_id).directory_name
        return '/%s%s' % (path, reverse('view-all-businesses-coupons', kwargs={
            'slug': obj.slug(),
            'business_id': obj.id
            }))
    
    @classmethod
    def items(cls):
        return Business.objects.distinct().filter(
            offers__coupons__is_approved=True, 
            offers__coupons__start_date__lt=datetime.datetime.now(),
            offers__coupons__expiration_date__gt=datetime.datetime.now())
        
    @classmethod
    def lastmod(cls, obj):
        """ When was this item last modified? """
        return obj.business_modified_datetime

SITEMAPS = {
    'local_home_pages': LocalHomePagesMap,
    'default_named_pages': DefaultNamedURLSitemap([
        'media-partner-home',
        'inside-radio',
        'radio-ink',
        'press-release',
        'media-partner-half-off',
        'site-directory',
        ]),
    'local_named_pages': LocalNamedURLSitemap([
        'contact-us',
        'help',
        'how-it-works',
        'sample-flyer',
        'who-we-are',
        ]),
    'coupon': CouponsMap,
    'business': BusinessMap,
    'blog': EntrySitemap,
}
