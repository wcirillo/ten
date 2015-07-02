""" Urls for advertiser app. """

from django.conf.urls.defaults import patterns, url

from advertiser import views

urlpatterns = patterns('',
    url(r'^$', 'advertiser.views.show_advertiser_account', 
        name='advertiser-account'), 
    url(r'^coupon-stats/$', 'advertiser.views.show_coupon_stats', 
        name='coupon-stats'),
    url(r'^sign-in/$', views.redirect_advertiser_sign_in),
    url(r'^sign_in/$', views.redirect_advertiser_sign_in),
    url(r'^register/$', views.redirect_advertiser_reg),
    url(r'^password-help/$', views.redirect_adv_password_help),
    url(r'^faq/$', views.show_advertiser_faq, name='advertiser-faq'),
)

