""" The url for the sitemap. """

from django.conf.urls.defaults import patterns

from common.sitemaps import SITEMAPS

urlpatterns = patterns('',
    (r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', 
        {'sitemaps': SITEMAPS})
)

