""" Urls for coupon app. """

from django.conf.urls.defaults import patterns, url

from coupon import views

urlpatterns = patterns('',
    url(r'^coupon/view-coupons/$', views.redirect_show_all_offers, 
        name="view-all-offers"),
    # Old url redirects to new:
    url(r'^coupon/business/(?P<slug>.*)/(?P<coupon_id>\d+)/$', 
        views.redirect_view_single_coupon, name="redirect-view-single-coupon"),
    url(r'^coupon-(?P<slug>.*)/(?P<coupon_id>\d+)/$', 
        views.show_single_coupon, name="view-single-coupon"),
    url(r'^coupon/sms/(?P<coupon_id>\d+)/$', views.show_send_sms_single_coupon, 
        name="show-send-sms-single-coupon"),
    url(r'^email/coupon/(?P<coupon_id>\d+)/$', views.show_email_coupon, 
        name="show-email-coupon"),
    url(r'^coupon/send/sms/(?P<coupon_id>\d+)/$', views.send_sms_single_coupon,
        name="send-sms-single-coupon"),
    url(r'^coupon/(?P<coupon_id>\d+)/$', views.print_single_coupon, 
        name="print-single-coupon"),
    url(r'^coupon/window-display/(?P<coupon_id>\d+)/$', views.window_display, 
        name="window-display"),
    url(r'^coupon/redir/(?P<coupon_id>\d+)/$',
        views.external_click_coupon, name="external-click-coupon"),
    url(r'^coupon/flyer-view/business/(?P<slug>.*)/(?P<coupon_id>\d+)/(?P<consumer_email_hash>.*)/$',
        views.flyer_click_show_single_coupon, name="flyer-view-single-coupon"),
    url(r'^coupon/flyer/(?P<coupon_id>\d+)/(?P<payload>.*)/$',
        views.flyer_click_coupon, name="flyer-click"),
    url(r'^coupon-(?P<slug>.*)/(?P<coupon_id>\d+)/(?P<code>[A-Z2-9]{6})/$',
        views.scan_coupon_qr_code, name="qr-code-view-single-coupon"),
    url(r'^edit-coupon/(?P<coupon_id>\d+)/$', views.show_edit_coupon, 
        name="edit-coupon"),
    url(r'^coupon/tweet/(?P<coupon_id>\d+)/$', views.tweet_coupon, 
        name="tweet-coupon"),    
    url(r'^coupon/tweet/(?P<coupon_id>\d+)/(?P<textflag>\d)/$', 
        views.tweet_coupon, name="tweet-coupon"), 
    url(r'^coupon/facebook/(?P<coupon_id>\d+)/$', 
        views.facebook_coupon, name="facebook-coupon"),     
)

