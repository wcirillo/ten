""" Admin config for coupon app. """
#pylint: disable=W0612,W0613,R0201
from django import forms
from django.contrib import admin
from django.db import connection

from advertiser.models import Location
from common.custom_cleaning import AdminFormClean
from coupon.models import (Action, Coupon, CouponCode, CouponType, Offer,
    Flyer, FlyerCoupon, FlyerSubdivision, FlyerPlacement,
    FlyerPlacementSubdivision, FlyerSubject, Slot, SlotTimeFrame)
from market.models import Site

def make_approved(modeladmin, request, queryset):
    """ Set is_approved for each instance in queryset. """
    queryset.update(is_approved=True)
make_approved.short_description = "Mark these items approved"

def get_data(coupons):
    """ Raw sql pull to populate the coupon admin interface. """
    coupons = tuple(coupons.values_list('id', flat=True))
    if len(coupons) == 0:
        return None
    cursor = connection.cursor()
    cursor.execute("""
SELECT c.id,
    COALESCE(c_a1.count, 0) AS view,
    COALESCE(c_a2.count, 0) AS clicks,
    COALESCE(c_a3.count, 0) AS prints,
    COALESCE(c_a4.count, 0) AS texts,
    COALESCE(c_a11.count, 0) AS blasted
FROM coupon_coupon c
LEFT JOIN coupon_couponaction c_a1
    ON c_a1.coupon_id = c.id
    AND c_a1.action_id = 1
LEFT JOIN coupon_couponaction c_a2
    ON c_a2.coupon_id = c.id
    AND c_a2.action_id = 2
LEFT JOIN coupon_couponaction c_a3
    ON c_a3.coupon_id = c.id
    AND c_a3.action_id = 3
LEFT JOIN coupon_couponaction c_a4
    ON c_a4.coupon_id = c.id
    AND c_a4.action_id = 4
LEFT JOIN coupon_couponaction c_a11
    ON c_a11.coupon_id = c.id
    AND c_a11.action_id = 11
WHERE c.id IN  %s 
GROUP BY c.id, c_a1.count, c_a2.count, c_a3.count, c_a4.count, c_a11.count
        """, [coupons])
    query = cursor.fetchall()
    data = {}
    for row in query:
        data[row[0]] = row[1:]
    return data


class OfferAdmin(admin.ModelAdmin):
    """ Admin config of Offer model. """
    list_display = ('business', 'headline')
    search_fields = ['headline', 'business__business_name',
        'business__advertiser__site__name']
    raw_id_fields = ('business',)
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "business__advertiser__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(OfferAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(OfferAdmin, self).queryset(request)
        qs = Offer.objects.select_related().filter(id__in=qs
            ).defer('business__advertiser__site__envelope', 
                    'business__advertiser__site__geom', 
                    'business__advertiser__site__point')
        return qs


class CouponForm(AdminFormClean):
    """ Coupon Form in the admin. """ 
    def __init__(self, *args, **kwargs):
        """ 
        Customize widgets to show related objects only.
        Better usability, much better performance.
        """
        super(CouponForm, self).__init__(*args, **kwargs)
        try:
            offers = Offer.objects.filter(
                business=self.instance.offer.business
                )
        except AttributeError:
            offers = []
        self.fields['offer'].widget.choices = [
            (choice.id, choice.headline) for choice in offers
            ]
        try:
            locations = Location.objects.filter(
                business=self.instance.offer.business
                )
        except AttributeError:
            locations = []
        self.fields['location'].widget.choices = [
            (choice.id, choice) for choice in locations
            ]


class CouponAdmin(admin.ModelAdmin):
    """ Admin config for coupon model. """
    actions = [make_approved]
    date_hierarchy = 'start_date'
    filter_horizontal = ('location', 'redemption_method', 
        'default_restrictions',)
    form = CouponForm
    list_display = ('offer', 'business', 'coupon_type', 'advertiser_site', 
        'start_date', 'expiration_date', 'approved', 'metrics')
    list_filter = ('start_date', 'coupon_type', 'is_approved')
    search_fields = ['id', 'offer__headline', 'offer__business__business_name',
        'offer__business__advertiser__site__name']
    save_on_top = True
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "offer__business__advertiser__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(CouponAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        coupons = super(CouponAdmin, self).queryset(request)
        self.data = get_data(coupons)
        return coupons.select_related('offer', 'offer__business', 'coupon_type',
            'offer__business__advertiser__site__name'
            ).defer('offer__business__advertiser__site__geom', 
                    'offer__business__advertiser__site__envelope', 
                    'offer__business__advertiser__site__point')

    def approved(self, obj):
        """ Long way to get a short description. """
        return bool(obj.is_approved)
    approved.boolean = True
    approved.short_description = u'Ap?'
        
    def business(self, obj):
        """ The business this coupon is for. """
        business = obj.offer.business
        return ("%s" % (business))
    business.admin_order_field = 'offer__business__business_name'
        
    def advertiser_site(self, obj):
        """ The site the advertiser is related to. """
        advertiser_site = obj.offer.business.advertiser.site.name
        return ("%s" % (advertiser_site))
    advertiser_site.admin_order_field = 'offer__business__advertiser__site__name'
                
    def metrics(self, obj):
        """ Display various coupon action datapoints. """
        if obj.coupon_type.id in (1, 7) :
            return ""
        try:
            row = self.data[obj.id]
        except KeyError:
            row = ('', '', '', '', '')
        return ("%s / %s / %s / %s / %s" % 
            (row[0], row[1], row[2], row[3], row[4]))
    metrics.short_description = u'View/Click/Print/SMS/Blast'


class CouponCodeAdmin(admin.ModelAdmin):
    """ Admin config for CouponCode model. """
    list_display = ('code', 'coupon',)
    raw_id_fields = ('coupon',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "coupon__offer__business__advertiser__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(CouponCodeAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(CouponCodeAdmin, self).queryset(request)
        qs = CouponCode.objects.select_related().filter(id__in=qs
            ).defer('coupon__offer__business__advertiser__site__envelope', 
                    'coupon__offer__business__advertiser__site__geom', 
                    'coupon__offer__business__advertiser__site__point')
        return qs   


class FlyerCouponInline(admin.StackedInline):
    """ Inline for relating coupons to flyers. """
    model = FlyerCoupon
    extra = 0
    max_num = 10
    raw_id_fields = ("coupon",)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "flyer__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(FlyerCouponInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(FlyerCouponInline, self).queryset(request)
        qs = FlyerCoupon.objects.select_related().filter(id__in=qs).defer(
            'flyer__site__envelope', 'flyer__site__geom', 'flyer__site__point')
        return qs


class FlyerAdmin(admin.ModelAdmin):
    """ Admin config of Flyer model. """
    actions = [make_approved]
    date_hierarchy = 'send_date'
    inlines = [FlyerCouponInline,]
    list_display = ('__unicode__', 'send_date', 'send_status', 'is_approved', 
        'num_consumers')
    list_filter = ('send_date', 'send_status', 'is_approved', 
        'site__name')
    list_select_related = True
    save_on_top = True
    form = AdminFormClean

    def created(self, obj):
        """ Pretty date. """
        return obj.create_datetime.strftime('%b %d %Y %H:%M')
    created.admin_order_field = 'create_datetime'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(FlyerAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(FlyerAdmin, self).queryset(request)
        self.data = Flyer.objects.select_related().filter(id__in=qs).defer(
            'site__geom', 'site__envelope', 'site__point')
        return self.data


class FlyerSubjectAdmin(admin.ModelAdmin):
    """ Admin config for FlyerSubject model. """
    date_hierarchy = 'send_date'
    list_display = ('week', 'send_date', 'title')
    list_select_related = True
    form = AdminFormClean


class FlyerSubdivisionAdmin(admin.ModelAdmin):
    """ Admin config for FlyerSubdivision model. """
    list_display = ('id', 'flyer', 'geolocation_object')
    list_select_related = True
    readonly_fields = ('geolocation_object',)    


class FlyerPlacementSubdivisionAdmin(admin.ModelAdmin):
    """ Admin config for FlyerPlacementSubdivision model. """
    list_display = ('id', 'flyer_placement', 'geolocation_object')
    list_select_related = True
    readonly_fields = ('geolocation_object',)


class FlyerPlacementSubdivisionInline(admin.StackedInline):
    """ Inline for relating coupons to flyers. """
    model = FlyerPlacementSubdivision
    extra = 1
    readonly_fields = ('geolocation_object',)


class FlyerPlacementAdmin(admin.ModelAdmin):
    """ Admin config for FlyerPlacement model. """
    inlines = [FlyerPlacementSubdivisionInline,]
    list_display = ('site', 'send_date', 'slot')
    list_filter = ('site__name', 'send_date')


class SlotTimeFrameInline(admin.StackedInline):
    """ Slot Inline class for the Slot admin"""
    model = SlotTimeFrame
    extra = 0
    raw_id_fields = ("coupon",)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "slot__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(SlotTimeFrameInline, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(SlotTimeFrameInline, self).queryset(request)
        qs = SlotTimeFrame.objects.select_related().filter(id__in=qs
            ).defer('slot__site__envelope', 
                    'slot__site__geom', 'slot__site__point')
        return qs  


class SlotTimeFrameForm(forms.ModelForm):
    """ SlotTimeFrame change form in the admin. """
    def __init__(self, *args, **kwargs):
        super(SlotTimeFrameForm, self).__init__(*args, **kwargs)
        try:
            coupons = Coupon.objects.filter(
                offer__business=self.instance.slot.business
                ).defer('offer__business__advertiser__site__envelope',
                        'offer__business__advertiser__site__geom',
                        'offer__business__advertiser__site__point')
        except AttributeError:
            coupons = []
        except Slot.DoesNotExist:
            coupons = Coupon.objects.all().defer(
                        'offer__business__advertiser__site__envelope',
                        'offer__business__advertiser__site__geom',
                        'offer__business__advertiser__site__point')
        self.fields['coupon'].widget.choices = [
            (choice.id, choice.offer) for choice in coupons
            ]


class SlotTimeFrameAdmin(admin.ModelAdmin):
    """ Admin config for SlotTimeFrame. """
    date_hierarchy = 'start_datetime'
    form = SlotTimeFrameForm
    list_display = ('id', 'slot_site', 'slot_business', 'coupon_offer', 
        'start_datetime', 'end_datetime')
    list_filter = ('slot__site__name',)
    raw_id_fields = ("coupon", "slot")
    search_fields = ['id', 'coupon__offer__headline', 
        'coupon__offer__business__business_name', 'slot__site__name']

    def slot_site(self, obj):
        """ The site the slot is related to. """
        slot_site = obj.slot.site.name
        return ("%s" % (slot_site))
    slot_site.admin_order_field = 'slot__site__name'

    def slot_business(self, obj):
        """ The business the slot is related to. """
        slot_business = obj.slot.business.business_name
        return ("%s" % (slot_business))
    slot_business.admin_order_field = 'slot__business__business_name'
    
    def coupon_offer(self, obj):
        """ The offer the slot timeframe is related to. """
        coupon_offer = obj.coupon.offer.headline
        return ("%s" % (coupon_offer))
    coupon_offer.admin_order_field = 'coupon__offer__headline'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "slot__site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(SlotTimeFrameAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)        

    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(SlotTimeFrameAdmin, self).queryset(request)
        self.data = SlotTimeFrame.objects.select_related().filter(id__in=qs
            ).defer('slot__site__envelope', 
            'slot__site__geom', 'slot__site__point')
        return self.data


class SlotAdmin(admin.ModelAdmin):
    """ Admin config for Slot model. """
    date_hierarchy = 'start_date'
    inlines = [SlotTimeFrameInline,]
    list_display = ('id', 'site', 'business', 'renewal_rate', 'is_autorenew',
        'start_date', 'end_date')
    list_filter = ('site__name',)
    search_fields = ['id', 'business__business_name', 'site__name']
    raw_id_fields = ('business', 'parent_slot')
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(SlotAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(SlotAdmin, self).queryset(request)
        self.data = Slot.objects.select_related().filter(id__in=qs).defer(
            'site__envelope', 'site__geom', 'site__point')
        return self.data
 
admin.site.register(Action)    
admin.site.register(Coupon, CouponAdmin)
admin.site.register(CouponCode, CouponCodeAdmin)
admin.site.register(CouponType)
admin.site.register(Offer, OfferAdmin)
admin.site.register(Flyer, FlyerAdmin)
admin.site.register(FlyerSubject, FlyerSubjectAdmin)
admin.site.register(FlyerSubdivision, FlyerSubdivisionAdmin)
admin.site.register(FlyerPlacement, FlyerPlacementAdmin)
admin.site.register(FlyerPlacementSubdivision, FlyerPlacementSubdivisionAdmin)
admin.site.register(Slot, SlotAdmin)
admin.site.register(SlotTimeFrame, SlotTimeFrameAdmin)
