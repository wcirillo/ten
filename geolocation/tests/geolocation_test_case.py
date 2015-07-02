""" A TestCase for many unit tests of the geolocation app. """

from django.conf import settings
from django.test import TestCase


class GeoTestCase(TestCase):
    """ Employ common methods for geolocation tests derived from TestCase.
    TEST_MODE switches geocoder between Google and OpenStreetMap.
    """

    def setUp(self):
        """ Set TEST_MODE from config. """
        TestCase.setUp(self)
        self.original_celery_always_eager = settings.CELERY_ALWAYS_EAGER
        settings.CELERY_ALWAYS_EAGER = True

    def tearDown(self):
        """ Reset TEST_MODE to original. """
        TestCase.tearDown(self)
        settings.CELERY_ALWAYS_EAGER = self.original_celery_always_eager
