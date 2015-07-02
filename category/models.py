""" Models for category app. """

from django.db import models

class Category(models.Model):
    """ Category model. Businesses have m2m relation to Category. """
    name = models.CharField(max_length=50)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

