# Django settings for ten project *DEV ENVIRONMENT ONLY*

from settings.common import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG
CELERY_ALWAYS_EAGER = True
LOG_PATH = '/var/log/django'

#DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABASE_NAME = 'ten'             # Or path to database file if using sqlite3.
#DATABASE_USER = 'wcirillo'             # Not used with sqlite3.
#DATABASE_PASSWORD = '1010wins'         # Not used with sqlite3.
#DATABASE_HOST = '127.0.0.1'             # Set to empty string for localhost. Not used with sqlite3.
#DATABASE_PORT = '5432'             # Set to empty string for default. Not used with sqlite3.

DATABASES['default'].update({
        'USER': 'wcirillo',
        'PASSWORD': '1010wins',
        'HOST': '127.0.0.1',
        'PORT': '5432'
    })

#DATABASES['default'].update({
#	'TEST_NAME': 'wild_will', # Make this name unique to you!
#	'PASSWORD': 'RRXWZR7GKJUqO0ZjRywkJqm', # Use the password from dev.py!
#	'HOST': 'sdm-devdb01', # Use the host from dev.py!
#	'PORT': '5432'
#	})

ADMINS = (
     ('William Cirillo', 'william@strausdigital.com')     
)

NOTIFY_EVERYONE = ['william@strausdigital.com']

#EMAIL_HOST = 'localhost'
EMAIL_PORT = 587

CONTEST_START_DATE = '2010-12-14'
CONTEST_END_DATE = '2012-04-30'
#CELERYD_LOG_FILE = '/var/log/celery/celery.log'
#CELERYD_LOG_LEVEL = 'INFO'
USE_I18N = True

TEMPLATE_DEBUG = True

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

#--------------------------------------
#To activate Debug ToolBar
# 1.) Comment out the INTERNAL_IPS line of code below.
# 2.) Set INTERCEPT_REDIRECTS == True
#--------------------------------------
INTERNAL_IPS = ([])
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}
#--------------------------------------

HTTP_HOST = 'local.10coupons.com'
HTTP_PROTOCOL_HOST = "http://local.10coupons.com"

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'sc=xxq-@2y$2&=wt!7q(d6+(jf3fy=5(ura)6-m4u5y0g^l*j5'

STATIC_DOC_ROOT = '/home/wcirillo/djcode/ten/media'
STATIC_URL = "http://local.10coupons.com/media//"

MEDIA_URL = 'http://local.10coupons.com/media/'
## Settings for ten project:
ENVIRONMENT = {
    'environment': 'local',
    'is_test': False
}

# Disable caching for dev purposes.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
}

#CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
#         'LOCATION': 'ten'
#     }
#}

# Or, if this was dev environment...
CACHE_BACKEND =    'dummy://'

# Makes tests much faster:
SEARCH_REALTIME = True

# Settings for unittest-xml-reporting (just like Jenkins)
#TEST_RUNNER = 'xmlrunner.extra.djangotestrunner.XMLTestRunner'
#TEST_OUTPUT_VERBOSE = True
#TEST_OUTPUT_DESCRIPTIONS = True
#TEST_OUTPUT_DIR = 'xmlrunner'