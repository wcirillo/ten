""" admin module for the feed app """

from django.contrib import admin
from feed.models import FeedProvider, FeedCoupon, FeedRelationship

class FeedProviderAdmin(admin.ModelAdmin):
    """ admin manager for feed providers """
    list_display = ('name', 'feed_url', 'advertiser',)
    raw_id_fields = ('advertiser',)
    search_fields = ('name',)
    

class FeedCouponAdmin(admin.ModelAdmin):
    """ admin manager for feed coupons """
    list_display = ('external_id', 'business_name', 'start_date', 
        'expiration_date', 'feed_provider', 'modified_datetime')
    ordering = ('feed_provider', 'expiration_date',)
    search_fields = ('external_id', 'business_name',)

class FeedRelationshipAdmin(admin.ModelAdmin):
    """ admin manager for feed relationships """
    list_display = ('feed_provider', 'feed_coupon', 'coupon', 
        'modified_datetime',)
    raw_id_fields = ('feed_provider', 'feed_coupon', 'coupon',)
    search_fields = ('feed_provider',)
    
admin.site.register(FeedProvider, FeedProviderAdmin)
admin.site.register(FeedCoupon, FeedCouponAdmin)
admin.site.register(FeedRelationship, FeedRelationshipAdmin)