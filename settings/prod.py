"""
Production environment settings for ten project. Organized with Django first,
then ten, then 3rd party.
"""
#pylint: disable=W0401,W0614
from settings.common import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

EMAIL_HOST = 'localhost'

CACHES = {
    'default': {
        'BACKEND': 'johnny.backends.memcached.MemcachedCache',
        'LOCATION': 'hsmemcache01.10coupons.prod:11211',

        'JOHNNY_CACHE': True,
        }
}

FIRESTORM_LIVE = True

### Settings below here are *NOT* django settings.
## Settings for ten project:
NOTIFY_AD_REP_LEAD = [
    'dennis@strausdigital.com', 'eric@strausdigital.com', 
    'alana@strausdigital.com', 'william@strausdigital.com'
    ]
NOTIFY_COMPLETED_SALE_LIST = ['sale-announce-all-10coupons@strausdigital.com']
NOTIFY_CONSUMER_UNQUALIFIED_REPORT = ['dbenedetto@strausdigital.com', 
    'scott@strausdigital.com']
NOTIFY_EVERYONE = ['everyone@strausdigital.com']
NOTIFY_FLYER_SEND_REPORT = [
    'jeremy@10coupons.com',
    'steve@10coupons.com',
    'eric@10coupons.com',
    'courtney@10coupons.com',
    'scott@10coupons.com',
    'william@10coupons.com',
    'danielle@10coupons.com',
    ]
NOTIFY_WARM_LEADS_REPORT = [
    #'bob@strausdigital.com', 
    'jeremy@10coupons.com', 
    'scarlin@10coupons.com',
    'eric@10coupons.com',
    ]

SEND_SALE_NOTIFICATIONS = True

# Settings for SugarCRM: sync of business data
SUGAR_SYNC_MODE = True

## Settings for 3rd party apps:
# Settings for Celery:
CELERY_ALWAYS_EAGER = False
BROKER_HOST = "celery01.10coupons.prod"


## Settings for 3rd party apps:
# Settings for Haystack:
HAYSTACK_SOLR_URL = 'http://hssearch01:8800/solr'

#Point to celery server
BROKER_HOST = "celery01.10coupons.prod"

#MIDDLEWARE_CLASSES += (
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
#)
#INTERNAL_IPS = ('173.220.217.195','173.220.217.194',)

