""" Urls for feed app of project ten. """

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('feed.views',
    url(r'^shooger.xml$', 'show_shooger_coupon_feed'),
    url(r'^generic-xml/$', 'show_generic_coupon_feed',
        name='show-generic-coupon-feed'),
)
