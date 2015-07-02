"""Settings for Hudson CI server (must run with no interaction)"""
#pylint: disable=W0401,W0614
from settings.jenkins import *

DATABASES['default'].update({
        'TEST_NAME': 'test_jenkins_ten_stable'
    })

CACHES['default'].update({
    'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    'KEY_PREFIX': 'jenkins_ten_stable'
    })
## Settings for 3rd party apps:
# Settings for Johnny Cache:
JOHNNY_MIDDLEWARE_KEY_PREFIX = 'jc_jenkins_ten_stable'

# Settings for Haystack:
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8800/test-ten-stable'
