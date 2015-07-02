"""Settings for Hudson CI server (must run with no interaction)"""
#pylint: disable=W0401,W0614
from settings.dev import *

DATABASES['default'].update({
        'TEST_NAME': 'test_jenkins_ten'
    })

# Dump logs in workspace
LOG_PATH = os.path.join(PROJECT_PATH, "..")

CACHES['default'].update({
    'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    'KEY_PREFIX': 'jenkins_ten'
    })
### Settings below here are *NOT* django settings.
## Settings for ten project:
ENVIRONMENT = {
    'environment': 'test',
    'is_test': True
}
# Makes tests much faster:
SEARCH_REALTIME = False

# LIVE_EMAIL_DOMAIN contains list of deliverable domains, empty would be all.
LIVE_EMAIL_DOMAINS = []

## Settings for 3rd party apps:
# Settings for Johnny Cache:
JOHNNY_MIDDLEWARE_KEY_PREFIX = 'jc_jenkins_ten'

# Settings for unittest-xml-reporting
TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
TEST_OUTPUT_VERBOSE = True
TEST_OUTPUT_DESCRIPTIONS = True
TEST_OUTPUT_DIR = 'xmlrunner'

# Settings for Celery:
CELERY_ALWAYS_EAGER = True

# Settings for Haystack:
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8800/test-ten'
