""" Auto generated urlconf for Hudson Valley """

from django.conf.urls.defaults import include, patterns

from common.urls import DEFAULT_PATTERNS, GLOBAL_PATTERNS, LOCAL_PATTERNS

urlpatterns = patterns('',
    (r'^', include(DEFAULT_PATTERNS)),
    (r'hudson-valley/', include(GLOBAL_PATTERNS)),
    (r'hudson-valley/', include(LOCAL_PATTERNS)),
    # If you add anything here, you are doing it WRONG!!!
)
