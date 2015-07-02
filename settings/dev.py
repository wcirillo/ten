"""
Development environment settings for ten project. Organized with Django first,
then ten, then 3rd party.
"""
#pylint: disable=W0401,W0614
from settings.common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES['default'].update({
        'HOST': 'sdm-devdb01',
        'PORT': '',
        'PASSWORD': 'RRXWZR7GKJUqO0ZjRywkJqm',
    })

MEDIA_URL = "http://dev.10coupons.com/media/"
STATIC_URL = MEDIA_URL

# Necessary hack to have dev server serve media files
STATIC_DOC_ROOT = ''

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

### Settings below here are *NOT* django settings.
## Settings for     ten project:
HTTP_HOST = 'dev.10coupons.com'
HTTP_PROTOCOL_HOST = "http://dev.10coupons.com"
SEND_SALE_NOTIFICATIONS = False

# LIVE_EMAIL_DOMAIN contains list of deliverable domains, empty would be all.
LIVE_EMAIL_DOMAINS = ['@strausdigital.com', '@10coupons.com']

## Settings for 3rd party apps:
# Settings for Haystack:
HAYSTACK_SOLR_URL = 'http://solr-dev.10coupons.com:8800/solr'

# Settings for Debug Toolbar:
# Steve  wants to see dev debug.
INTERNAL_IPS = ('127.0.0.1', '192.168.88.107', '192.168.88.106')

## Settings for ten project:
ENVIRONMENT = {
    'environment': 'dev',
    'is_test': True,
    'use_geo_method': 'static'
}
