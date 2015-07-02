""" Auto generated urlconf for Puerto Rico """

from django.conf.urls.defaults import include, patterns

from common.urls import DEFAULT_PATTERNS, GLOBAL_PATTERNS, LOCAL_PATTERNS

urlpatterns = patterns('',
    (r'^', include(DEFAULT_PATTERNS)),
    (r'puerto-rico/', include(GLOBAL_PATTERNS)),
    (r'puerto-rico/', include(LOCAL_PATTERNS)),
    # If you add anything here, you are doing it WRONG!!!
)
