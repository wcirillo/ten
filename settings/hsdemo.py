"""
Production environment settings for ten project. Organized with Django first,
then ten, then 3rd party.
"""
#pylint: disable=W0401,W0614
from settings.common import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

EMAIL_HOST = 'localhost'

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'ten_hsdemo',
        'USER': 'ten_hsdemo_user',
        'PASSWORD': 'l-u0tkPgIaRRXWZR7GKJUqO0ZjRywkJqm0EXkID6tLG',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

ADMINS = (
     ('Jeremy Price', 'jeremy@10coupons.com'),
)
MANAGERS = ADMINS

FIRESTORM_LIVE = False
DEMO = True

### Settings below here are *NOT* django settings.
## Settings for ten project:
NOTIFY_COMPLETED_SALE_LIST = ['sale-announce-all-10coupons@strausdigital.com']
NOTIFY_FLYER_SEND_REPORT = [
    'jeremy@10coupons.com',
    'steve@10coupons.com',
    'eric@10coupons.com',
    'courtney@10coupons.com',
    'scott@10coupons.com',
    'william@10coupons.com',
    ]
NOTIFY_WARM_LEADS_REPORT = [
    'jeremy@10coupons.com', 
    'scarlin@10coupons.com',
    'eric@10coupons.com',
    ]

STATIC_URL = 'https://demo.10coupons.com/media/'

WARM_LEADS_BCC = []

SEND_SALE_NOTIFICATIONS = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

## Settings for 3rd party apps:

# Settings for SugarCRM: sync of business data 
SUGAR_SYNC_MODE = False

# Solr settings.
INSTALLED_APPS += ('haystack',)
HAYSTACK_SITECONF = 'common.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8800/solr'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = 'https://demo.10coupons.com/media/'
STATIC_URL = 'https://demo.10coupons.com/media/'

HTTP_HOST = 'demo.10coupons.com'
HTTP_PROTOCOL_HOST = "http://demo.10coupons.com"
HTTPS_PROTOCOL_HOST = "https://demo.10coupons.com"

