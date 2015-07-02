""" Urls for watchdog app. """

from django.conf.urls.defaults import url, patterns

urlpatterns = patterns('watchdog',
    url(r'^site-health/(?P<action>.+)/(?P<data>.+)/$', 'views.site_health',
        name='site_health'),
    url(r'^blast-effects/(?P<sitenum>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/$', 
        'views.get_blast_effect_before', name='get_blast_effect_before'),
    url(r'^blast-effects/(?P<sitename>.+)/(?P<date>\d{4}-\d{2}-\d{2})/$', 
        'views.get_blast_effect_before', name='get_blast_effect_before'),
    
    )

