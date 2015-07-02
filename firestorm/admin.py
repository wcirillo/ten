""" Admin classes for firestorm app of project ten. """
import logging

from django.contrib import admin

from common.custom_format_for_display import format_phone
from firestorm.models import (AdRep, AdRepWebGreeting, AdRepAdvertiser,
    AdRepOrder, AdRepConsumer, AdRepLead, AdRepSite, AdRepUSState,
    BonusPoolAllocation, AdRepCompensation)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

def ad_rep_email(obj):
    """ Return the AdvertiserAdReps email for display and search purposes """
    return '%s' % obj.ad_rep.email

def is_qualified(obj):
    """ Return boolean 'Is this ad rep qualified?' """
    return obj.is_qualified()
is_qualified.boolean = True
is_qualified.short_description = 'Qualified?'

def first_last_name(obj):
    """ Return first, last name of the object. """
    return '%s %s' % (obj.first_name, obj.last_name)
first_last_name.short_description = 'Lead Name'

def ad_rep_lead_phone(obj):
    """ Referring AdRep Phone Number """
    if obj.phone_number is None:
        phone_number = ''
    else:
        phone_number = format_phone(obj.phone_number)
    return "%s" % phone_number
ad_rep_lead_phone.short_description = 'Lead Phone Number'

def site(obj):
    """ Display the site.name of the object """
    return "%s" % (obj.site.name)
site.short_description = 'Site'

def referring_ad_rep_name(obj):
    """ Referring AdRep Name """
    if obj.ad_rep is None:
        ad_rep = ''
    else:
        ad_rep = obj.ad_rep
    return "%s" % ad_rep
referring_ad_rep_name.short_description = 'Ad Rep Name'

def referring_ad_rep_email(obj):
    """ Referring Ad Rep email """
    if obj.ad_rep is None:
        email = ''
    else:
        email = obj.ad_rep.email
    return "%s" % email
referring_ad_rep_email.short_description = 'Ad Rep Email'

def order_create_datetime(obj):
    """ Return the object create datetime. """
    return '%s' % obj.order.create_datetime

def order_promoter_cut_amount(obj):
    """ Return the promoter cut amount for this object. """
    return '%s' % obj.order.promoter_cut_amount

def ad_rep_city_state(obj):
    """ Return the city, state of the ad_rep for this object. """
    return '%s, %s' % (obj.ad_rep.geolocation_object.us_city.name,
        obj.ad_rep.geolocation_object.us_state.abbreviation)

def signup_ip(obj):
    """ Returns the IP from which the consumer signed up. """
    try:
        return obj.consumer.history.all()[0].ip
    except (AttributeError, IndexError):
        return "N/A"


class AdRepWebGreetingInline(admin.StackedInline):
    """ AdRepWebGreeting admin interface class, """
    model = AdRepWebGreeting
    fk_name = "ad_rep"
    extra = 0
    readonly_fields = ('web_greeting',)


class AdRepAdmin(admin.ModelAdmin):
    """ AdRep admin interface class. """
    exclude = ('user_permissions', 'password')
    filter_horizontal = ('email_subscription', 'groups',)
    inlines = [AdRepWebGreetingInline]
    list_display = ('__unicode__', 'firestorm_id', 'rank', 'url',
        'parent_ad_rep', 'site', 'is_emailable', is_qualified, 
        'ad_rep_create_datetime')
    list_filter = ('rank', 'site__name', )
    ordering = ('-firestorm_id',)
    raw_id_fields = ('subscriber',)
    readonly_fields = ('parent_ad_rep', 'firestorm_id', 'email', 'first_name',
        'last_name', 'url', 'company', 'rank', 'mailing_address1',
        'mailing_address2', 'mailing_city', 'mailing_state_province',
        'mailing_zip_postal', 'home_phone_number', 'primary_phone_number',
        'fax_phone_number', 'cell_phone_number',)
    save_on_top = True
    search_fields = ['id', 'email', 'url', 'first_name', 'last_name', 
        'company', 'ad_rep_create_datetime']
    
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AdRepAdmin, self).queryset(request)
        qs = AdRep.objects.select_related().filter(id__in=qs
            ).defer('site__envelope',
                'site__geom',
                'site__point')
        return qs


class AdRepAdvertiserAdmin(admin.ModelAdmin):
    """ AdRepAdvertiser admin interface class. """
    list_display = ('ad_rep', ad_rep_email, 'advertiser')
    list_filter = ('ad_rep__site__name',)
    raw_id_fields = ('ad_rep', 'advertiser',)
    search_fields = ['ad_rep__first_name', 'ad_rep__last_name', 'ad_rep__email',
        'ad_rep__username', 'advertiser__email', 'advertiser__username']
    save_on_top = True

    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AdRepAdvertiserAdmin, self).queryset(request)
        qs = AdRepAdvertiser.objects.select_related().filter(id__in=qs
            ).defer('advertiser__site__envelope',
                'advertiser__site__geom',
                'advertiser__site__point')
        return qs


class AdRepOrderAdmin(admin.ModelAdmin):
    """ AdRepOrder admin interface class. """
    list_display = ('order', 'ad_rep', ad_rep_email, order_promoter_cut_amount,
        order_create_datetime)
    list_filter = ('order__create_datetime',)
    raw_id_fields = ('ad_rep', 'order',)
    readonly_fields = ('firestorm_order_id',)
    search_fields = ['ad_rep__first_name', 'ad_rep__last_name', 'ad_rep__email',
        'ad_rep__username', 'order__invoice']

    save_on_top = True

    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AdRepOrderAdmin, self).queryset(request)
        qs = AdRepOrder.objects.select_related().filter(id__in=qs
            ).defer('ad_rep__site__envelope',
                'ad_rep__site__geom',
                'ad_rep__site__point')
        return qs


class AdRepConsumerAdmin(admin.ModelAdmin):
    """ AdRepConsumer admin interface class. """
    list_display = ('ad_rep', ad_rep_email, 'consumer', signup_ip)
    raw_id_fields = ('ad_rep', 'consumer',)
    search_fields = ['ad_rep__first_name', 'ad_rep__last_name', 'ad_rep__email',
        'ad_rep__username', 'consumer__email', 'consumer__username']
    
    save_on_top = True
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AdRepConsumerAdmin, self).queryset(request)
        qs = AdRepConsumer.objects.select_related().filter(id__in=qs
            ).defer('consumer__site__envelope',
                'consumer__site__geom',
                'consumer__site__point')
        return qs


class AdRepLeadAdmin(admin.ModelAdmin):
    """ AdRep admin interface class. """
    date_hierarchy = 'create_datetime'
    exclude = ('user_permissions', 'password')
    filter_horizontal = ('email_subscription', 'groups',)
    list_display = ('__unicode__', first_last_name, ad_rep_lead_phone, site,
        referring_ad_rep_name, referring_ad_rep_email)
    list_filter = ('site__name', )
    raw_id_fields = ('subscriber',)
    search_fields = ['id', 'email', 'first_name', 'last_name']
    save_on_top = True

    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AdRepLeadAdmin, self).queryset(request)
        qs = AdRepLead.objects.select_related().filter(id__in=qs
            ).defer('site__envelope',
                'site__geom',
                'site__point')
        return qs

class AdRepLeadProxy(AdRepLead):
    """ An empty proxy subclass for allowing another admin interface to
    AdRepLead.
    """
    class Meta:
        verbose_name = 'Ad Rep Lead'
        verbose_name_plural = 'Ad Rep Leads - Long Form'
        proxy = True

class AdRepLeadAlternateAdmin(AdRepLeadAdmin):
    """ An alternate admin interface for AdRepLead highlighting the important
    info Eric needs to smile and dial.
    """
    list_display = (first_last_name, 'create_datetime', ad_rep_lead_phone, site,
        'right_person_text')
    list_filter = ()


class AdRepSiteAdmin(admin.ModelAdmin):
    """ AdRepSite admin interface class. """
    list_display = ('__unicode__', 'ad_rep', 'site')

    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(AdRepSiteAdmin, self).queryset(request)
        qs = AdRepSite.objects.select_related().filter(
            id__in=qs).defer('site__envelope', 'site__geom', 'site__point')
        return qs


class AdRepUSStateAdmin(admin.ModelAdmin):
    """ AdRepUSState admin interface class. """
    list_display = ('__unicode__', 'ad_rep', 'us_state')


class BonusPoolAllocationAdmin(admin.ModelAdmin):
    """ AdRep admin interface class. """
    actions = None
    date_hierarchy = 'create_datetime'
    list_display = ('id', 'ad_rep_order', 'ad_rep', 'amount', ad_rep_city_state,
        'create_datetime')
    readonly_fields = ('ad_rep_order', 'ad_rep', 'amount', 'consumer_points',
        'create_datetime')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AdRepCompensationAdmin(admin.ModelAdmin):
    """ AdRepCompensation admin interface. """
    actions = None
    date_hierarchy = 'create_datetime'
    list_display = ('id', 'ad_rep_order', 'ad_rep', 'amount', 'child_ad_rep',
        'create_datetime')
    list_filter = ('create_datetime',)
    readonly_fields = ('ad_rep_order', 'ad_rep', 'amount', 'child_ad_rep',
        'create_datetime')
    search_fields = ['ad_rep_order__order__invoice']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

admin.site.register(AdRep, AdRepAdmin)
admin.site.register(AdRepAdvertiser, AdRepAdvertiserAdmin)
admin.site.register(AdRepOrder, AdRepOrderAdmin)
admin.site.register(AdRepConsumer, AdRepConsumerAdmin)
admin.site.register(AdRepLead, AdRepLeadAdmin)
admin.site.register(AdRepLeadProxy, AdRepLeadAlternateAdmin)
admin.site.register(AdRepSite, AdRepSiteAdmin)
admin.site.register(AdRepUSState, AdRepUSStateAdmin)
admin.site.register(BonusPoolAllocation, BonusPoolAllocationAdmin)
admin.site.register(AdRepCompensation, AdRepCompensationAdmin)
