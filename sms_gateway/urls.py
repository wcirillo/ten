""" Urls for sms_gateway app. """

from django.conf.urls.defaults import patterns

from sms_gateway import views

urlpatterns = patterns('',
    (r'^receive-sms/$', views.receive_sms),
    (r'^receive-report/$', views.receive_report),
)
