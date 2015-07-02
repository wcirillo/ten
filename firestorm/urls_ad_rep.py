""" Urls for the firestorm ad-rep-account """

from django.conf.urls.defaults import patterns, url

from firestorm.views.ad_rep_account_views import AdRepAccount
from firestorm.views.downline_views import AdRepDownline
from firestorm.views.photo_upload_views import AdRepPhotoUpload

urlpatterns = patterns('firestorm.views.ad_rep_account_views',
    url(r'^advertiser-stats/$', 'advertiser_stats', name='advertiser-stats'),
    url(r'^$', AdRepAccount.as_view(), name="ad-rep-account"),
    url(r'^downline-recruits/$', AdRepDownline.as_view(),
        name="ad-rep-downline-recruits"),
    url(r'^photo-upload/$', AdRepPhotoUpload.as_view(),
        name="ad-rep-photo-upload"),
    url(r'^share-links/$', 'show_share_links',
        name='share-links'),
    url(r'^ad-rep-consumers/$', 'ad_rep_consumers',
        name='ad-rep-consumers'),
    url(r'^downline-consumers/(?P<downline_ad_rep_id>\d+)/$',
        'downline_consumers', name='downline-consumers-drill-down'),
    url(r'^downline-consumers/$', 'downline_consumers',
        name='downline-consumers'),
    url(r'^recruitment-ad/$', 'recruitment_assistance',
        name='recruitment-ad'),
    url(r'^web-addresses/$', 'web_addresses',
        name='web-addresses'),
)
