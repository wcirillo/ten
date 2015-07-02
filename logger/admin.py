""" Admin config for logger app """
from logger.models import LogHistory
from django.contrib import admin

from common.custom_cleaning import AdminFormClean

class LogHistoryAdmin(admin.ModelAdmin):
    """ Admin class for Logger """
    list_display = ('logger', 'status', 'execution_date_time')
    actions = None
    form = AdminFormClean
    
    
    
admin.site.register(LogHistory, LogHistoryAdmin)