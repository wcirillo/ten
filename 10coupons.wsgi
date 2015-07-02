import os, sys
sys.path.append('/home/django/10coupons/ten')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

#import django.core.handlers.wsgi

#_application = django.core.handlers.wsgi.WSGIHandler()
from django.core.handlers.wsgi import WSGIHandler
_application = WSGIHandler()

def application(environ, start_response): 
    environ['wsgi.url_scheme'] = environ.get('HTTP_X_URL_SCHEME', 'http') 
    return _application(environ, start_response)

