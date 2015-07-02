""" Admin config for advertiser app. """
#pylint: disable=W0612,R0201

from django.contrib import admin
from django.db import connection

from common.custom_cleaning import AdminFormClean
from advertiser.models import (Advertiser, BillingRecord, Business, Location,
    BusinessProfileDescription)
from coupon.models import Offer
from market.models import Site


class BusinessInline(admin.StackedInline):
    """ Business has Advertiser FK. """
    model = Business
    fk_name = "advertiser"
    extra = 0  
    
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(BusinessInline, self).queryset(request)
        qs = Business.objects.select_related().filter(id__in=qs
            ).defer('advertiser__site__envelope', 
                'advertiser__site__geom',
                'advertiser__site__point')
        return qs 


class LocationInline(admin.StackedInline):
    """ Location has Business FK. """
    model = Location
    fk_name = "business"
    extra = 0
    
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(LocationInline, self).queryset(request)
        qs = Location.objects.select_related().filter(id__in=qs
            ).defer('business__advertiser__site__envelope', 
                'business__advertiser__site__geom',
                'business__advertiser__site__point')
        return qs 


class BillingRecordInline(admin.StackedInline):
    """ BillingRecord has Business FK. """
    model = BillingRecord
    fk_name = "business"
    extra = 0
    
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(BillingRecordInline, self).queryset(request)
        qs = BillingRecord.objects.select_related().filter(id__in=qs
            ).defer('business__advertiser__site__envelope', 
                'business__advertiser__site__geom',
                'business__advertiser__site__point')
        return qs 


class OfferInline(admin.StackedInline):
    """ Offer has Business FK. """
    model = Offer
    fk_name = "business"
    extra = 0
    
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(OfferInline, self).queryset(request)
        qs = Offer.objects.select_related().filter(id__in=qs
            ).defer('business__advertiser__site__envelope',
                'business__advertiser__site__geom',
                'business__advertiser__site__point')
        return qs 


class BusinessProfileDescriptionInline(admin.StackedInline):
    """ Location has Business FK. """
    model = BusinessProfileDescription
    fk_name = "business"
    extra = 0  
    
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(BusinessProfileDescriptionInline, self).queryset(request)
        qs = BusinessProfileDescription.objects.select_related(
            ).filter(id__in=qs
            ).defer('business__advertiser__site__envelope',
                'business__advertiser__site__geom',
                'business__advertiser__site__point')
        return qs 
    
def get_advertiser_data(advertisers):
    """ Select custom data to appear in advertiser change list. """
    advertisers = tuple(advertisers.values_list('id', flat=True))
    cursor = connection.cursor()
    cursor.execute("""
        SELECT a.consumer_ptr_id, b.business_name
        FROM advertiser_advertiser a
        LEFT JOIN advertiser_business b
            ON b.advertiser_id = a.consumer_ptr_id
        WHERE a.consumer_ptr_id IN  %s 
        ORDER BY a.consumer_ptr_id
                """, [advertisers])
    query = cursor.fetchall()
    data = {}
    for row in query:
        try:
            data[row[0]]
        except KeyError:
            data[row[0]] = []
        data[row[0]].append(row[1])
    return data


class AdvertiserAdmin(admin.ModelAdmin):
    """ Advertiser Admin Interface. """
    inlines = [
        BusinessInline
    ]
    date_hierarchy = 'advertiser_create_datetime'
    exclude = ('approval_count', 'user_permissions', 'password')
    filter_horizontal = ('email_subscription', 'groups',)
    list_display = ('email_trimmed', 'business_name', 
        'site', 'is_emailable', 
        'registered')
    list_filter = ('advertiser_create_datetime', 'site__name',)
    raw_id_fields = ('subscriber',)
    search_fields = ['id', 'email', 'username']
    save_on_top = True
    
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(AdvertiserAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AdvertiserAdmin, self).queryset(request).defer(
             'site__envelope', 'site__geom', 'site__point')
        self.data = get_advertiser_data(qs)
        return qs
        
    def email_trimmed(self, obj):
        """ Returns email shortened if necessary. """
        if obj.email:
            email_trimmed = obj.email[0:40]
            if len(email_trimmed) == 40:
                email_trimmed = '%s...' % email_trimmed
        else:
            email_trimmed = obj.id
        return ('%s' % (email_trimmed))
    email_trimmed.admin_order_field = 'email'
    email_trimmed.short_description = 'email'
    
    def business_name(self, obj):
        """ A list of businesses of this advertiser. """
        try:
            business_name_list = ", ".join(self.data[obj.id])
        except TypeError:
            business_name_list = ''
        return business_name_list

    def registered(self, obj):
        """ Pretty date. """
        return obj.advertiser_create_datetime.strftime('%b %d %Y %H:%M')
    registered.admin_order_field = 'advertiser_create_datetime'


def get_business_data(businesses):
    """ Return custom data to appear in business change list. """
    businesses = tuple(businesses.values_list('id', flat=True))
    cursor = connection.cursor()
    cursor.execute("""
        SELECT b.id, c.name
        FROM advertiser_business b
        LEFT JOIN advertiser_business_categories bc
            ON bc.business_id = b.id
        LEFT JOIN category_category c
            ON c.id = bc.category_id
        WHERE b.id IN  %s 
        ORDER BY b.id
                """, [businesses])
    query = cursor.fetchall()
    data = {}
    for row in query:
        if not row[0] in data:
            data[row[0]] = []
        data[row[0]].append(row[1])
    return data


class BusinessAdmin(admin.ModelAdmin):
    """ Business Admin Interface. """
    inlines = [
        OfferInline,
        LocationInline,
        BillingRecordInline,
        BusinessProfileDescriptionInline
    ]
    filter_horizontal = ('categories',)
    list_display = ('business_name', 'category_list', 'advertiser',)
    search_fields = ['id', 'business_name', 'advertiser__email',]
    raw_id_fields = ('advertiser',)
         
    form = AdminFormClean
    save_on_top = True
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "advertiser__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(BusinessAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(BusinessAdmin, self).queryset(request).defer(
            'advertiser__site__envelope', 'advertiser__site__geom', 
             'advertiser__site__point')
        self.data = get_business_data(qs)
        return qs
    
    def category_list(self, obj):
        """ A list of categories of this business. """
        try:
            category_list = ", ".join(self.data[obj.id])
        except TypeError:
            category_list = ''
        return category_list
    category_list.admin_order_field = 'categories'


class BillingRecordAdmin(admin.ModelAdmin):
    """ BillingRecord Admin Interface. """
    list_display = ('business', 'billing_address1', 'billing_city', 
        'billing_state_province')
    search_fields = ['business__business_name',]
    raw_id_fields = ('business',)
    
    form = AdminFormClean
    save_on_top = True
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "business__advertiser__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(BillingRecordAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(BillingRecordAdmin, self).queryset(request).defer(
            'business__advertiser__site__envelope', 
            'business__advertiser__site__geom', 
            'business__advertiser__site__point')
        return qs


class LocationAdmin(admin.ModelAdmin):
    """ Location Admin Interface. """
    list_display = ('id', 'business_name', '__unicode__')
    search_fields = ['business__business_name', 'location_url', 
        'location_address1', 'location_address2', 'location_city',
        'location_description']
    raw_id_fields = ('business',)
    
    form = AdminFormClean
    save_on_top = True
    
    def business_name(self, obj):
        """ Business name this location belongs to. """
        return obj.business.business_name

admin.site.register(Advertiser, AdvertiserAdmin)
admin.site.register(Business, BusinessAdmin)
admin.site.register(BillingRecord, BillingRecordAdmin)
admin.site.register(Location, LocationAdmin)
