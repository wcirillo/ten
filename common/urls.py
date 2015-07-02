""" Base urlconf for 10Coupons project """

import os.path

from django.conf.urls.defaults import include, patterns, url
from django.conf import settings
from django.contrib import admin

import nexus

import consumer.views
import subscriber.views

admin.autodiscover()
nexus.autodiscover()

# These are things that *ONLY* appear on default *NON-MARKET* (corporate) site 1
DEFAULT_PATTERNS = patterns('',
    url(r'^(e/$)', 'common.views.force_generic_home', 
        name='force-generic-home-e'),
    url(r'^(?P<msg>[a-z])/$', 'common.views.show_home', name='home'),
    (r'^captain/doc/', include('django.contrib.admindocs.urls')),
    (r'^captain/', include(admin.site.urls)), # Admin url obfiscation.
    (r'^captain/firestorm/', include('firestorm.urls_admin')),
    (r'^nexus/', include(nexus.site.urls)),
    (r'^sms-gateway/', include('sms_gateway.urls')),
    (r'^', include('common.urls_sitemaps')),
    (r'^', include('market.urls')),
    (r'^', include('watchdog.urls')),
    (r'^feed/', include('feed.urls')),
    url(r'^map/(?P<state_name>.*)/$', 'common.views.show_state_markets',
        name='show-state-markets'),
    # coupon-widgets takes input of the form:
    #  widget_type in {businesses, advertisers, markets}
    #  widget_identifier: advertiser.id, business.id, site.directory_name
    #  widget_file: one of the size-bases js templates
    # example:
    #  10coupons.com/coupon-widgets/markets
    #       /hudson-valley/10CouponsWidget300x250.js
    url(r'^media/coupon-widgets/' +
        '(?P<widget_type>.*)/(?P<widget_identifier>.*)/(?P<widget_file>.*)/$',
        'coupon.views.widget_views.create_widget_from_web',
        name='create-widget-from-web'),
    url(r'^media/coupon-widgets/' +
        '(?P<widget_type>.*)/(?P<widget_identifier>.*)/(?P<widget_file>.*)$',
        'coupon.views.widget_views.create_widget_from_web',
        name='create-widget-from-web'),

    # Media partner pages
    url(r'^media-partner-home/$', 
        'common.views.show_media_partner_home', 
        name='media-partner-home'),
    url(r'^inside-radio/$', 'common.views.show_inside_radio', 
        name="inside-radio"),
    url(r'^radio-ink/$', 'common.views.show_radio_ink', 
        name="radio-ink"),
    url(r'^press-release/$', 'common.views.show_press_release', 
        name="press-release"),
    url(r'^broadcaster/info/$', 'common.views.redirect_media_explanation'),
    url(r'^media-partner/info/$', 'common.views.redirect_media_explanation'),
    url(r'^media-partner/half-off/$', 
        'common.views.show_media_partner_half_off', 
        name='media-partner-half-off'), 
    url(r'^map/(?P<state_name>.*)/$', 'common.views.show_state_markets',
        name='show-state-markets'),
    url(r'^map/$', 'common.views.show_site_directory',
        name='site-directory'),
    url(r'^media/dynamic/map-data/(?P<requested_file>[a-zA-Z0-9_.-]+-geoms.txt$)$',
        'market.views.get_or_set_site_geoms', name='get-or-set-site-geoms'),
    url(r'^media/dynamic/map-data/market-geom-markers.txt$', 
        'market.views.get_or_set_market_markers',
        name='get-or-set-market-markers'),
    url(r'^market-zip-search/$', 'common.views.show_market_search',
        name='market-zip-search'),
    url(r'^locate-market-map/$', 'common.views.show_close_markets',
        name='locate-market-map'),
    # Zinnia blog:
    (r'^blog/', include('zinnia.urls')),
    url(r'^test/navigator-location/$',
        'geolocation.views.show_my_location',
        name='test-navigator-coords'),
    url(r'^test/ajax-get-zip/$',
        'geolocation.views.get_my_location',
        name='test-zip-from-coords'),
)

# These are things that *ONLY* appear on local market sites.
LOCAL_PATTERNS = patterns('',
    # Common pages:
    url(r'^help/$', 'common.views.show_help', name='help'),
    url(r'^sample-flyer/$', 'common.views.show_sample_flyer', 
        name='sample-flyer'),
    url(r'^contact-us/$', 'common.views.show_contact_us', 
        name='contact-us'),
    url(r'^map/$', 'common.views.show_map_market_counties',
        name='show-counties-in-market'),
    url(r'^map/consumers/$', 'common.views.show_consumer_map',
        name='show-consumer-map'),
    url(r'^rules/$', 'common.views.show_contest_rules', 
        name='contest-rules'),
    # Added additional contest-rules catch to deal with cross-site url issue 
    # on signup:
    url(r'^.+/rules/$', 'common.views.show_contest_rules'),
    url(r'^widgets/$', 'common.views.show_widgets', name='widgets'),
    url(r'^loader/(?P<page_to_load>.*)/$', 'common.views.loader', 
        name='loader'),
    # Generic processes (multiple user types):
    url(r'^password-set/','common.views.set_password', name='set-password'),
    url(r'^subscribe/$', 'common.views.show_opt_in_opt_out', name='subscribe'),
    # Consumer pages:
    url(r'^local-coupons/$', consumer.views.redirect_consumer_registration, 
        name='consumer-registration'),
    url(r'^consumer-registration-confirmation/$',
        consumer.views.consumer_reg_confirmation,
        name='consumer-registration-confirmation'),
    url(r'^email-coupon-confirmation/(?P<coupon_id>\d+)/$',
        consumer.views.consumer_reg_confirmation,
        name='email-coupon-confirmation'),
    # Subscriber pages:
    url(r'^mobile-coupons/$', subscriber.views.show_subscriber_registration, 
        name='subscriber-registration'),
    url(r'^mobile-phone-registration-confirmation/$', 
        subscriber.views.subscriber_reg_confirmation, 
        name='subscriber-registration-confirmation'),
    url(r'^registration-confirmation/$', 
        subscriber.views.con_sub_reg_confirmation, 
        name='con-sub-reg-confirmation'),
    url(r'^mobile-coupons/sign-out/$', 'subscriber.views.log_out_subscriber', 
        name='log-out-subscriber-registration'),
    # Advertiser pages:
    (r'^advertiser/', include('advertiser.urls')),
    url(r'^advertiser-sign-in/$', 'common.views.show_advertiser_sign_in', 
        name="advertiser-sign-in"),
    url(r'^fresh-sign-in/$', 'common.views.sign_out', 
        name="clean-sign-in"),
    # Business pages:
    (r'^business/', include('advertiser.business.urls')),
    # Media partner pages:
    (r'^', include('media_partner.urls')),
    url(r'^media-partner-sign-in/$', 'common.views.show_media_partner_sign_in',
        name="media-partner-sign-in"),
    url(r'^reports/sign-in/$', 'common.views.redirect_media_partner_sign_in'),
    url(r'^spots/$', 'common.views.show_spots', name="show-spots"),
    # Other includes:
    (r'^', include('coupon.urls')),
    (r'^ad-rep/', include('firestorm.urls_ad_rep')),
    (r'^coupons/', include('coupon.urls_coupons')),
    (r'^create-coupon/', include('coupon.urls_create_coupon')),
    (r'^ecommerce/', include('ecommerce.urls')),
    # Because this includes a wild-card url handler, it *must* be last:
    (r'^', include('firestorm.urls')),
)

# Urls that exist on local market sites and the default site = 1.
GLOBAL_PATTERNS = patterns('',
    # Home
    url(r'^$', 'common.views.show_home', name='home'),
    url(r'^e/$', 'common.views.force_generic_home', name='force-generic-home'),
    url(r'^about-us/$', 'common.views.show_who_we_are', name='who-we-are'),
    url(r'^how-it-works/$', 'common.views.show_how_it_works',
        name='how-it-works'),
    url(r'^terms-of-use/$', 'common.views.show_terms_of_use',
        name='terms-of-use'),
    url(r'^privacy-policy/$', 'common.views.show_privacy_policy',
        name='privacy-policy'),
    url(r'^media-partner/info/$', 'common.views.redirect_media_explanation'),
    url(r'^site-directory/$', 'common.views.redirect_site_directory',
        name='redirect-site-directory'),

    # Generic processes (multiple user types)
    url(r'^sign-in/$', 'common.views.show_sign_in', name="sign-in"),
    url(r'^sign-out/$', 'common.views.sign_out', name="sign-out"),
    url(r'^password-help/$', 'common.views.show_forgot_password',
        name='forgot-password'),
    url(r'^opt-out-confirmation/$', 'common.views.opt_out_confirmation',
        name='opt-out-confirmation'),
    url(r'^opt-out-confirmation/(?P<listid>.{5})/$', 
        'common.views.opt_out_confirmation', name='opt-out-confirmation'),
    url(r'^opt-out-confirmation/(?P<payload>.+)/$', 
        'common.views.opt_out_confirmation', name='opt-out-confirmation'),
    url(r'^unsubscribe/$', 'common.views.show_opt_in_opt_out',
        name='unsubscribe'),
    (r'^', include('email_gateway.urls')),
)

# Just initialize the list:
urlpatterns = patterns('',
    # If you add anything here, you are doing it WRONG!!!
)

# Break this out for urls of local market sites and multilanguage support.
# This is for default languge, which doen't get a custom directory
#for i in range(1, len(site_cache)):
#    this_dir = site_cache[i].directory_name
#    urlpatterns += patterns('',
#        (r'^' + this_dir + '/', include(LOCAL_PATTERNS)),
#        (r'^' + this_dir + '/', include(GLOBAL_PATTERNS)),
#    )

#for n in config.supported_i18n:
#    urlpatterns += patterns(n,
#        (r'^' + n + '/', include(LOCAL_PATTERNS)),
#        (r'^' + n + '/', include(GLOBAL_PATTERNS)),
#    )

#    for i in range(1, len(config.site_cache)):
#        this_dir = config.site_cache[i].directory_name
#        urlpatterns += patterns('',
#            (r'^' + n + '/' + this_dir + '/', include(LOCAL_PATTERNS)),
#            (r'^' + n + '/' + this_dir + '/', include(GLOBAL_PATTERNS)),
#        )

urlpatterns += patterns('',
    (r'^', include(DEFAULT_PATTERNS)),
    (r'^', include(GLOBAL_PATTERNS)),
    (r'^', include(LOCAL_PATTERNS)),
    # If you add anything here, you are doing it WRONG!!!
)
# DEV ONLY hack for displaying media files from django development server 
# (manage.py runserver)
if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(.*)$', 'django.views.static.serve', 
            kwargs={
                'document_root': os.path.join(settings.PROJECT_PATH, 'media')
                }
            ),
    )
