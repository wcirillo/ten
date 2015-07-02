""" Django settings for ten project. Organized with native Django settings
first, then settings specific to project ten, then 3rd party apps.
"""
import os.path
import djcelery

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'ten',
        'USER': 'ten_user',
        'PASSWORD':
            'wP18-2yk04S7l-u0tkPgIaRRXWZR7GKJUqO0ZjRywkJqm0EXkID6tLGFl3Gv4yGr',
        'HOST': 'hsdb01',
        'PORT': '5432'
    }
}

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HASH_SALT = 'SDMSalt'
EMAIL_HOST = 'smtp01.strausdigital.com'

SESSION_COOKIE_AGE = 60 * 60 * 24

PROJECT_PATH = os.path.abspath(os.path.split(os.path.split(__file__)[0])[0])

LOGIN_URL = '/sign-in/'

ADMINS = (
     ('Steve Bywater', 'steve@strausdigital.com'),
     ('William Cirillo', 'william@strausdigital.com'),
     ('Jeremy Price', 'jeremy@10coupons.com'),
     ('Vincent Santaiti', 'vsantaiti@strausdigital.com'),
     ('Dennis Benedetto', 'dbenedetto@strausdigital.com'),
)
MANAGERS = ADMINS

FIRESTORM_LIVE = False
DEMO = False # demo server

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
MEDIA_ROOT = PROJECT_PATH + '/media/'
IMAGES = MEDIA_ROOT + '/images/'
# These should be 'http'; common.context_processors.safe_urls will make a secure
# version from these.
MEDIA_URL = 'http://10static.com/media/'
STATIC_URL = MEDIA_URL

# This is deprecated in django 1.4 but required by Zinnia:
ADMIN_MEDIA_PREFIX = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'sc=xxq-@2y$2&=wt!7q(d6+(jf3fy=5(ura)6-m4u5y0g^l*j5'

AUTHENTICATION_BACKENDS = (
    'common.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.csrf',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'common.context_processors.current_session',
    'common.context_processors.current_site',
    'common.context_processors.current_url_no_subdomain',
    'common.context_processors.page_locale',
    'common.context_processors.safe_urls',
    'common.contest.contest_is_running',
    'firestorm.context_processors.referring_ad_rep',
    'zinnia.context_processors.media',
    'zinnia.context_processors.version',
)

MIDDLEWARE_CLASSES = (
    'johnny.middleware.LocalStoreClearMiddleware',
    'johnny.middleware.QueryCacheMiddleware',
    'django.middleware.cache.UpdateCacheMiddleware', # Keep as first in list
    'market.middleware.URLHandlerMiddleware',
    'django.middleware.gzip.GZipMiddleware', # Compresses ASCII on way out.
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware', # Keep as last in lists.
)

CACHES = {
    'default': {
        'BACKEND': 'johnny.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'JOHNNY_CACHE': True,
        }
}
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

ROOT_URLCONF = 'common.urls'

TEMPLATE_DIRS = ()
for root, dirs, files in os.walk(PROJECT_PATH):
    if 'templates' in dirs:
        TEMPLATE_DIRS = TEMPLATE_DIRS + (os.path.join(root, 'templates'),)

DJANGO_APPS = (    
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.gis',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.sitemaps',
    'django.contrib.sites',
    'django.contrib.comments',
    'django.contrib.staticfiles',
)

THIRD_PARTY_APPS = (
    'debug_toolbar',
    'django_extensions',
    'djcelery',
    'haystack', # For full text search
    'gargoyle', # Feature switcher
    'mptt',
    #'nexus', # Admin customizer used by gargoyle.
    'tagging',
    'south',
    'zinnia',
)

TEN_COUPON_APPS = (
    'advertiser',
    'category',
    'common',
    'consumer',
    'coupon',
    'ecommerce',
    'email_gateway',
    'feed',
    'firestorm',
    'geolocation',
    'logger',
    'market',
    'media_partner',
    'sms_gateway',
    'subscriber',
    'watchdog',
)

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + TEN_COUPON_APPS

# Settings for logging:
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
                '%(asctime)s %(name)s %(levelname)s %(module)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/django.log',
            'maxBytes': 20000000,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
        'db_backend': {
            'level': 'INFO',
            'class':'logger.handler.DatabaseHandler',
            'formatter': 'verbose'
       }
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request':{
            'handlers': ['file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'ten':{
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
            'disabled': False
        },
        'db_logger':{
            'handlers': ['db_backend'],
            'level': 'INFO',
            'propagate': False,
            'disabled': False
        }
    }
}

CSRF_FAILURE_VIEW = 'common.views.show_csrf_error'

### Settings below here are *NOT* django settings.
## Settings for ten project:
ENVIRONMENT = {
    'environment': 'prod',
    'is_test': False
}

MAIN_NUMBER = '800-581-3380'
CONTEST_START_DATE = '2010-12-20'
CONTEST_END_DATE = '2012-12-30'
HTTP_HOST = '10coupons.com'
HTTP_PROTOCOL_HOST = "http://10coupons.com"
HTTPS_PROTOCOL_HOST = "https://10coupons.com"
LOG_PATH = '/var/log/django'
# Search indexes updated in real time:
SEARCH_REALTIME = True
# Notification lists for various events:

# LIVE_EMAIL_DOMAIN contains list of deliverable domains, empty would be all.
LIVE_EMAIL_DOMAINS = [] # Populated in jenkins, local and dev.

NOTIFY_ABANDONED_COUPONS_REPORT = ['jeremy@strausdigital.com', 
    'dbenedetto@strausdigital.com']
NOTIFY_AD_REP_LEAD = ['dennis@strausdigital.com', 'scott@strausdigital.com']
NOTIFY_AD_REP_ENROLLED = ['danielle@strausdigital.com', 
    'dbenedetto@strausdigital.com']
NOTIFY_COMPLETED_SALE_LIST = ['jeremy@strausdigital.com']
NOTIFY_CONSUMER_PROSPECTS_REPORT = ['jeremy@strausdigital.com']
NOTIFY_CONSUMER_UNQUALIFIED_REPORT = ['dbenedetto@strausdigital.com', 
    'scott@strausdigital.com']
NOTIFY_EVERYONE = ['william@strausdigital.com']
NOTIFY_FLYER_SEND_REPORT = ['jeremy@strausdigital.com']
SEND_GEOCODE_NOTIFICATIONS = True # Turn off if they happen too often.
GEOCODER_AGENT = 'geocode@10coupons.com'
# Must be defined
COLDCALL_LEADS_BCC = []

SEND_SALE_NOTIFICATIONS = False # Override this in settings.prod.

#Where to find the widgets
WIDGET_PATH = os.path.join(PROJECT_PATH, 'media', 'coupon-widgets')

#Where to find spots relative to the project 
SPOT_PATH = os.path.join('media', 'spots')

# Settings for SugarCRM: sync of business data 
SUGAR_SYNC_MODE = False

## Settings for 3rd party apps and packages:
# Settings for Johnny Cache:
JOHNNY_MIDDLEWARE_KEY_PREFIX = 'jc_ten'
MAN_IN_BLACKLIST = ('django_session', 'coupon_couponaction',
    'djcelery_taskstate', 'logger_loghistory')

# ESAPI uses KeyCzar:
ENCRYPTED_FIELD_KEYS_DIR = '/etc/esapi/keyring/symmetric/'

# Settings for Celery:
djcelery.setup_loader()
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 5672
BROKER_VHOST = "ten_vhost"
BROKER_USER = "ten_rabbit_user"
BROKER_PASSWORD = "snerfmorger"
CELERY_RESULT_BACKEND = "amqp"
CELERY_AMQP_TASK_RESULT_EXPIRES = 60
CELERY_IMPORTS = (
    "advertiser.business.location.tasks",
    "advertiser.business.tasks",
    "coupon.tasks",
    "email_gateway.tasks",
    "firestorm.tasks",
    "feed.tasks",
    "sms_gateway.tasks",
)
CELERYBEAT_SCHEDULER = 'djcelery.schedulers.DatabaseScheduler'
CELERY_SEND_TASK_ERROR_EMAILS = True
CELERY_DISABLE_RATE_LIMITS = True
CELERYD_LOG_LEVEL = "DEBUG"
# Toggle use of celery(rabbit)... False=yes, True=no
CELERY_ALWAYS_EAGER = False
#CELERYBEAT_SCHEDULE_FILENAME = /tmp/schedule.tmp
#CELERYBEAT_SCHEDULE = {
#    "run-daily-at-midnight": {
#        "task": "tasks.expire_slot_time_frames",
#        "schedule": crontab(minute=0, hour=0),
#    },
#

# Settings for Haystack:
HAYSTACK_SITECONF = 'common.search_sites'
HAYSTACK_SEARCH_ENGINE = 'solr'
HAYSTACK_SOLR_URL = 'http://127.0.0.1:8800/solr'
HAYSTACK_INCLUDE_SPELLING = True

# Settings for Debug Toolbar:
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}
DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)
INTERNAL_IPS = ('127.0.0.1')

# Settings for South:
SOUTH_TESTS_MIGRATE  = False

# Settings for Zinnia:
ZINNIA_MEDIA_URL = '/media/zinnia/'
