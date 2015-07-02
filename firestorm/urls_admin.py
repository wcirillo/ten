""" Urls for custom admin pages. """
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('firestorm.views.ad_rep_account_views',
    url(r'^ad-rep-consumers/(?P<ad_rep_id>\d+)/$',
        'admin_ad_rep_consumers', name='admin-ad-rep-consumers'),
    url(r'^downline-consumers/(?P<ad_rep_id>\d+)/(?P<downline_ad_rep_id>\d+)/$',
        'admin_downline_consumers', name='admin-downline-consumers-drill-down'),
    url(r'^downline-consumers/(?P<ad_rep_id>\d+)/$',
        'admin_downline_consumers', name='admin-downline-consumers'),
    url(r'^recruitment-ad/(?P<ad_rep_id>\d+)/$', 'admin_recruitment_assistance',
        name='admin-recruitment-ad'),
    url(r'^web-addresses/(?P<ad_rep_id>\d+)/$', 'admin_web_addresses',
        name='admin-web-addresses'),
    url(r'^advertiser-stats/(?P<ad_rep_id>\d+)/$', 'admin_advertiser_stats',
        name='admin-advertiser-stats')
)
