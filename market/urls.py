""" Urls for the market app of project ten. Redirects for when a site directory
changes.
"""

from django.conf.urls.defaults import patterns, url
from django.views.generic.base import RedirectView

urlpatterns = patterns('',
    url(r'^big-apple/$', RedirectView.as_view(url='/manhattan/')),
    url(r'^central_wisconsin/$', RedirectView.as_view(url='/c-w/')),
    url(r'^coastal/$', RedirectView.as_view(url='/west-palm-beach-boca/')),
    url(r'^detroit/$', RedirectView.as_view(url='/metro-detroit/')),
    url(r'^grand-rapids/$', RedirectView.as_view(url='/west-michigan/')),
    url(r'^new-hampshire/$', RedirectView.as_view(url='/sea-coast/')),
    url(r'^north-country/$', RedirectView.as_view(url='/champlain-valley/')),
    url(r'^motor-city/$', RedirectView.as_view(url='/metro-detroit/')),
    url(r'^west-kentucky/$', RedirectView.as_view(url='/purchase/')),
)
