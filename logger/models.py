""" Models for the logger app. """
from datetime import datetime
from django.core.exceptions import ValidationError
from django.db import models


class LogHistory(models.Model):
    """ Stores log history of custom actions and events. """
    logger = models.CharField('Logging Class Module or Task', max_length=200)
    execution_date_time = models.DateTimeField('Datetime of Execution', 
        default=datetime.now)
    status = models.CharField('Status of Log Action', max_length=150, 
        null=False, blank=False)
    detail_dict = models.TextField('Dict of keys for debug or explanation.', 
        max_length=2000, null=True, blank=True)
    
    def __unicode__(self):
        return self.logger

    class Meta:
        verbose_name = 'Database Log'
        verbose_name_plural = 'Database Logs'
        get_latest_by = 'execution_date_time'
            
    def delete(self):
        raise ValidationError('Cannot delete log history.')
    
    def save(self, *args, **kwargs):
        super(LogHistory, self).save(*args, **kwargs)  
        return self