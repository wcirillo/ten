""" More urls for coupons. """

from django.conf.urls.defaults import patterns, url

from coupon.views import coupon_views

urlpatterns = patterns('',
    url(r'^$', coupon_views.show_all_coupons, name='all-coupons'),
    url(r'^facebook/$', coupon_views.show_all_coupons_facebook,
        name='all-coupons-facebook'),
    url(r'^(?P<msg>\d+)/$', coupon_views.show_all_coupons,
        name='all-coupons-msg'),
    url(r'^(?P<slug>.*)/(?P<business_id>\d+)/$', 
        coupon_views.show_all_coupons_this_business,
        name="view-all-businesses-coupons"),
)

