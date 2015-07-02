""" Admin config for subscriber app. """
#pylint: disable=W0612,R0201
from django.contrib import admin

from common.custom_cleaning import AdminFormClean
from market.models import Site
from subscriber.models import Subscriber, MobilePhone, Carrier, SMSSubscription

class SubscriberAdmin(admin.ModelAdmin):
    """ Admin config for Subscriber model. """
    date_hierarchy = 'subscriber_create_datetime'
    list_display = ('mobile_phone', 'carrier', 'sms_subscriptions', 
        'subscriber_zip_postal','site', 'registered')
    list_filter = ('subscriber_create_datetime', 'site__name',)
    filter_horizontal = ('sms_subscription',)
    search_fields = ['mobile_phones__mobile_phone_number', 
        'mobile_phones__carrier__carrier_display_name', 
        'subscriber_zip_postal', 
        'subscriber_create_datetime']
    form = AdminFormClean
    
    def mobile_phone(self, obj):
        """ Displays one mobile phone of the subscriber. """
        try:
            mobile_phone = obj.mobile_phones.all()[0]
        except IndexError:
            mobile_phone = None
        return mobile_phone    
    mobile_phone.admin_order_field = 'mobile_phones__mobile_phone_number'
    
    def carrier(self, obj):
        """ Displays the carrier of a phone of the subscriber. """
        try:
            carrier = obj.mobile_phones.all()[0].carrier
        except IndexError:
            carrier = None
        return carrier
    carrier.admin_order_field = 'mobile_phones__carrier'
    
    def sms_subscriptions(self, obj):
        """ Returns a list of sms_subscriptions for this user, as a string. """
        count = 0
        subscriptions = ''
        subscriber_sms_subscriptions = SMSSubscription.objects.filter(
            subscribers=obj.id
            )
        if subscriber_sms_subscriptions:
            for subscription in subscriber_sms_subscriptions:
                count = count + 1
                subscriptions = subscriptions + \
                    subscription.sms_subscription_name
                if count != len(subscriber_sms_subscriptions):
                    subscriptions = subscriptions + ' - '
        return subscriptions
        
    def registered(self, obj):
        """ Pretty date. """
        return obj.subscriber_create_datetime.strftime('%b %d %Y %H:%M')
    registered.admin_order_field = 'subscriber_create_datetime'
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(SubscriberAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(SubscriberAdmin, self).queryset(request)
        qs = Subscriber.objects.select_related().filter(id__in=qs
            ).defer('site__envelope', 'site__geom', 'site__point')
        return qs


class MobilePhoneAdmin(admin.ModelAdmin):
    """ Admin config for MobilePhone model. """
    list_display = ('id', 'mobile_phone_number', 'is_verified', 'carrier')
    list_filter = ('carrier',)
    search_fields = ['mobile_phone_number']
    raw_id_fields = ("subscriber",)
    form = AdminFormClean
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(MobilePhoneAdmin, self).queryset(request)
        self.data = MobilePhone.objects.select_related().filter(id__in=qs
            ).defer('subscriber__site__envelope', 'subscriber__site__geom', 
                    'subscriber__site__point')
        return self.data

class CarrierAdmin(admin.ModelAdmin):
    """ Admin config for Carrier model. """
    list_display = ('id', 'carrier_display_name',)
    list_filter = ('is_major_carrier',)
    form = AdminFormClean
    ordering = ('-is_major_carrier', 'carrier_display_name')
    search_fields = ['carrier', 'carrier_display_name']
    
admin.site.register(Subscriber, SubscriberAdmin)
admin.site.register(MobilePhone, MobilePhoneAdmin)
admin.site.register(Carrier, CarrierAdmin)
admin.site.register(SMSSubscription)
