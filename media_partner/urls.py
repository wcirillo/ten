""" Urls for media_partner app """

from django.conf.urls.defaults import patterns, url

from media_partner import views

SIGNUP_REPORT_PATTERNS = '|'.join([ \
    "last-12-months",
    "last-30-days",
    "since-launch"])

urlpatterns = patterns('',
    url(r'^media-partner/$', views.show_transaction_report,
        name="media-partner-view-report"),
    url(r'^media-partner/consumer-sign-ups/(?P<stype>%s)/$' \
            % SIGNUP_REPORT_PATTERNS,
        views.consumer_acquisition_report,
        name="media-partner-consumer-sign-ups"),
)
