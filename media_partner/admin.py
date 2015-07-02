""" Admin config for media_partner app. """

from django.contrib import admin

from common.custom_cleaning import AdminFormClean
from media_partner.models import (MediaPartner, MediaGroup, Affiliate,
    MediaPieShare, Medium, Outlet)
from market.models import Site


def media_groups(obj):
    """ Return a pretty list of groups to which a partner belongs. """
    groups = ''
    for group in obj.media_groups.all():
        if groups:
            groups = "%s, %s" % str(group.name)
        else:
            groups = str(group.name)
    return groups


class MediaPartnerForm(AdminFormClean):
    """ Form for admin MediaPartner display and cleaning. """
    class Meta:
        model = MediaPartner


class MediaPartnerAdmin(admin.ModelAdmin):
    """ Admin config for MediaPartner model. """
    list_display = ('email', media_groups, 'site', 'is_emailable')
    list_filter = ('email', 'consumer_create_datetime', 'site__name', 
        'is_emailable')
    search_fields = ['email', 'username']
    save_on_top = True
    form = MediaPartnerForm
    raw_id_fields = ('site',)
    exclude = ('user_permissions', 'password', 'subscriber', 'geolocation_type',
        'geolocation_id')


    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(MediaPartnerAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(MediaPartnerAdmin, self).queryset(request)
        qs = MediaPartner.objects.filter(id__in=qs
            ).defer('site__envelope', 'site__geom', 'site__point')
        return qs


class MediaGroupAdmin(admin.ModelAdmin):
    """ Admin config for MediaGroup model. """
    list_display = ('name', 'contact_name', 'contact_phone', 'contact_email')
    filter_horizontal = ('media_group_partner',)
    save_on_top = True
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "media_group_partner__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(MediaGroupAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(MediaGroupAdmin, self).queryset(request)
        return MediaGroup.objects.filter(id__in = qs
            ).defer('media_group_partner__site__envelope', 
                    'media_group_partner__site__geom', 
                    'media_group_partner__site__point')


class AffiliateAdmin(admin.ModelAdmin):
    """ Admin config for Affiliate model. """
    list_display = ('name', 'medium', 'media_group', 'site',  'free_coupons', 
        'contact_name', 'contact_phone', 'contact_email')
    filter_horizontal = ('affiliate_partner',)
    list_filter = ('name', 'medium', 'media_group', 'free_coupons', 
        'site__name')
    search_fields = ['name', 'medium__name', 'media_group__name', 
        'contact_name', 'contact_phone', 'contact_email']
    save_on_top = True
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(AffiliateAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AffiliateAdmin, self).queryset(request)
        return Affiliate.objects.filter(id__in = qs
            ).defer('site__envelope', 'site__geom', 'site__point')


class MediaPieShareAdmin(admin.ModelAdmin):
    """ Admin config for MediaPieShare model. """
    date_hierarchy = 'start_date'
    list_display = ('affiliate', 'site', 'share', 'start_date', 
        'end_date')
    list_filter = ('affiliate', 'end_date', 'start_date', 'site__name')
    search_fields = ['affiliate']
    save_on_top = True
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(MediaPieShareAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(MediaPieShareAdmin, self).queryset(request)
        self.data = MediaPieShare.objects.filter(id__in=qs
            ).defer('site__envelope', 'site__geom', 'site__point')
        return self.data


class OutletAdmin(admin.ModelAdmin):
    """ Admin config for Outlet model. """
    list_display = ('name', 'affiliate', 'band', 'frequency', 'format', 
        'slogan', 'website', 'logo')
    search_fields = ('name', 'band', 'frequency')
    save_on_top = True
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "affiliate__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(OutletAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(OutletAdmin, self).queryset(request)
        self.data = Outlet.objects.filter(id__in=qs
            ).defer('affiliate__site__envelope', 
                    'affiliate__site__geom', 
                    'affiliate__site__point')
        return self.data

admin.site.register(MediaPartner, MediaPartnerAdmin)    
admin.site.register(MediaGroup, MediaGroupAdmin)
admin.site.register(Affiliate, AffiliateAdmin)
admin.site.register(MediaPieShare, MediaPieShareAdmin)
admin.site.register(Medium)
admin.site.register(Outlet, OutletAdmin)
