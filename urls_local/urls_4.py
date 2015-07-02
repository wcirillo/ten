""" Auto generated urlconf for Capital Area """

from django.conf.urls.defaults import include, patterns

from common.urls import DEFAULT_PATTERNS, GLOBAL_PATTERNS, LOCAL_PATTERNS

urlpatterns = patterns('',
    (r'^', include(DEFAULT_PATTERNS)),
    (r'capital-area/', include(GLOBAL_PATTERNS)),
    (r'capital-area/', include(LOCAL_PATTERNS)),
    # If you add anything here, you are doing it WRONG!!!
)
