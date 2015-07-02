""" Urls for business app """

from django.conf.urls.defaults import patterns, url

from advertiser.business import views

urlpatterns = patterns('',   
    url(r'^web-snap/(?P<business_id>\d+)/$', views.hit_web_snap, 
        name="web-snap"),    
    url(r'^snappy-all-snappy/$', views.snap_all_businesses, 
        name="snappy-all-snappy"),
    url(r'^edit/(?P<business_id>\d+)/$', views.show_edit_business_profile, 
        name="edit-business-profile"),
    url(r'^r/(?P<coupon_id>\d+)/$', views.click_business_web_url, 
        name="click-business-web_url"),  
)
