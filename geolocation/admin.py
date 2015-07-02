""" Admin config for geolocation app """

from django.contrib.gis import admin

from common.custom_cleaning import AdminFormClean
from geolocation.models import USState, USCounty, USZip


class USStateAdmin(admin.OSMGeoAdmin):
    """ Admin for US State """
    modifiable = False
    search_fields = ['name',]
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(USStateAdmin, self).queryset(request)
        self.data = USState.objects.select_related().filter(id__in=qs
            ).defer('geom')
        return self.data

    def has_delete_permission(self, request, obj=None):
        return False

class USCountyAdmin(admin.OSMGeoAdmin):
    """ Admin for US County """
    modifiable = False
    search_fields = ['name',]
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(USCountyAdmin, self).queryset(request)
        self.data = USCounty.objects.select_related().filter(id__in=qs
            ).defer('geom', 'us_state__geom')
        return self.data

    def has_delete_permission(self, request, obj=None):
        return False

class USZipAdmin(admin.OSMGeoAdmin):
    """ Admin for US Zip """
    exclude = ('coordinate', 'us_city', 'us_county', 'us_state')
    modifiable = False
    search_fields = ['code',]
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(USZipAdmin, self).queryset(request)
        self.data = USZip.objects.select_related().filter(id__in=qs
            ).defer('geom')
        return self.data

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(USState, USStateAdmin)
admin.site.register(USCounty, USCountyAdmin)
admin.site.register(USZip, USZipAdmin)
