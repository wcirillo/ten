""" Admin config overrides for third party apps. """
from django.contrib import admin

from zinnia.models import Entry
from zinnia.admin.entry import EntryAdmin

class CustomEntryAdmin(EntryAdmin):
    """ Exclude authors from the list filter. """
    list_filter = list(EntryAdmin.list_filter)
    list_filter.remove('authors')
    list_filter = tuple(list_filter) 

admin.site.unregister(Entry)
admin.site.register(Entry, CustomEntryAdmin)

