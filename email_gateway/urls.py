""" Urls for email_gateway app. """

from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('email_gateway',
    url(r'^opt-out/(?P<email_hash>.{1,42})/(?P<listid>.{5})/$', 'views.opt_out',
        name='optout_deprecated'),
    url(r'^opt-out/(?P<email_hash>.{1,42})/$', 'views.opt_out_nochoice',
            name='optout_deprecated'),
    url(r'^opt-out/(?P<payload>.+)/(?P<listid>.{5})/$',
        'views.opt_out_payload', name='optout_deprecated2'),
    url(r'^opt-out/(?P<payload>.+)/$', 
        'views.opt_out_payload', name='optout_deprecated2'),
    url(r'^opt-out-list/(?P<payload>.+)/$',
        'views.opt_out_payload', name='opt_out'),
    url(r'^subscribe-consumer/(?P<payload>.+)/$',
        'views.email_verify_consumer', name='email_verify_consumer'),
    url(r'^add-subscriber/(?P<payload>.+)/$',
        'views.email_add_subscriber', name='add_subscriber'),
    # This is an extra url to catch the /hudson-valley/capital-area/ signup 
    # redirect issue.
    url(r'^.+/subscribe-consumer/(?P<payload>.+)/$', 
        'views.email_verify_consumer'),
    # Getting sessions built from email links
    url(r'^i/(?P<payload>.+)/(?P<redir_path>.+)$', 
        'views.email_link_redirect', name='email-link-redirect'),
    url(r'^report-bouncing/(?P<email_string>.+)/(?P<nomail_reason>\d{1,2})/$', 
        'views.remote_bounce_report', name='report-bouncing'),
    # second report bouncing for new type -- reporting type of email in spam complaints
    url(r'^report-spam/(?P<email_string>.+)/(?P<nomail_reason>\d{1,2})/(?P<email_type>.+)/$', 
        'views.remote_bounce_report', name='report-spam'),
    url(r'^reverify-email/(?P<email_string>.+)/$', 
        'views.catch_reverify_email', name='re-verify'),
    url(r'^login-ad-rep/(?P<payload>.+)/$', 'views.login_ad_rep_from_email',
        name='login-ad-rep-from-email'),
    url(r'^login-advertiser/(?P<payload>.+)/$',
        'views.login_advertiser_from_email', 
        name='login-advertiser-from-email'),
    url(r'^password-reset/(?P<email_token>.+)/$',
        'views.reset_password_from_email', name='reset-password-from-email'),
    url(r'^sale-redirect/(?P<payload>.+)/(?P<promo_code>.+)/(?P<product_id>.+)/(?P<item_id>.+)/$',
        'views.sale_redirect_with_session', name='sale-redirect-with-promo'),
    url(r'^sale-redirect/(?P<payload>.+)/(?P<product_id>.+)/(?P<item_id>.+)/$',
        'views.sale_redirect_with_session', name='sale-redirect'),
    url(r'^sale-redirect/(?P<payload>.+)/(?P<promo_code>.+)/$',
        'views.sale_redirect_with_session', name='sale-redirect-with-promo'),
    url(r'^sale-redirect/(?P<payload>.+)/$',
        'views.sale_redirect_with_session', name='sale-redirect'),
        
)
