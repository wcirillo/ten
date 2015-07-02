""" Admin UI for the email_gateway app of project ten. """

from django.contrib import admin

from common.custom_cleaning import AdminFormClean
from email_gateway.models import Email

class EmailAdmin(admin.ModelAdmin):
    """ Admin manager to manage email class."""
    form = AdminFormClean
    list_display = ('subject', 'send_status', 'send_datetime', 'num_recipients')
    readonly_fields = ('num_recipients',)

admin.site.register(Email, EmailAdmin)
