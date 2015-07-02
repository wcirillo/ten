""" Models of watchdog app. """

from django.db import models

class SiteHealth(models.Model):
    """ A model for storing a history of site health. """
    datestamp = models.DateTimeField(auto_now_add=False)
    extra = models.CharField(max_length=20)

