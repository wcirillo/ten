""" Admin config for market app. """
#pylint: disable=W0612,R0201

from django.contrib import admin
from django.contrib.sites.models import Site as ContribSite # no name collision

from common.custom_cleaning import AdminFormClean
from ecommerce.service.calculate_current_price import calculate_current_price
from ecommerce.templatetags.currency import currency
from geolocation.models import USCounty, USState
from market.models import Site, TwitterAccount


class SiteInline(admin.StackedInline):
    """ Site Inline class for the Site admin"""
    model = Site
    extra = 0
    form = AdminFormClean


class SiteForm(AdminFormClean):
    """ Filters counties to this site's default state, for performance."""
    def __init__(self, *args, **kwargs):
        super(SiteForm, self).__init__(*args, **kwargs)
        us_counties = USCounty.objects.select_related(
                'us_state__abbreviation'
            ).all().only('id', 'name', 'us_state__abbreviation')
        self.fields['us_county'].widget.choices = [
            (choice.id, 
            u'%s, %s' % (choice.name, choice.us_state.abbreviation)
            ) for choice in us_counties
            ]
        us_states = USState.objects.only('id', 'name')
        us_state_choices = [('','---')]
        for state in us_states:
            us_state_choices.append((state.id, state.name))
        self.fields['default_state_province'].widget.choices = us_state_choices
        self.fields['us_state'].widget.choices = us_state_choices


class SiteAdmin(admin.ModelAdmin):
    """ Admin config for Site model. """
    filter_horizontal = ('us_county',)
    form = SiteForm
    list_display = ('domain', 'name', 'phase', 'consumer_count',
        'flyer_rate',)
    list_filter = ('base_rate', 'default_state_province__name',)
    ordering = ('id',)
    prepopulated_fields = {"directory_name": ("name",), "domain":("name",)}
    search_fields = ('domain', 'name',)
    
    class Meta:
        model = Site
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(SiteAdmin, self).queryset(request)
        qs = Site.admin.select_related().filter(id__in=qs)
        ordering = self.ordering or ()
        if ordering:
            qs = qs.order_by(*ordering)
        return qs 
        
    def consumer_count(self, obj):
        """ Count of consumers related to this site. """
        return obj.get_or_set_consumer_count()

    consumer_count.short_description = 'Consum'
        
    def flyer_rate(self, obj):
        """ Price of flyer placement on this site. """
        return currency(calculate_current_price(1, obj,
            obj.get_or_set_consumer_count()))
    flyer_rate.short_description = 'Flyer $'
    
    def save_model(self, request, obj, form, change):
        """ Save Site model changes. """
        override = False
        if obj.id > 1:
            obj = obj.update_geometry_fields(form.cleaned_data['us_county'])
            override = True
        initial_id = obj.id
        obj.save(override_geom_update=override)
        if initial_id != obj.id:
            # New site just created, geometries have to be updated after site exists.
            obj.update_geometry_fields(form.cleaned_data['us_county'])


class TwitterAccountAdmin(admin.ModelAdmin):
    """ Admin config for Twitter model. """
    list_display = ('twitter_name', 'site_name', 'is_auto_tweet_setup')
    ordering = ('twitter_name',)
    search_fields = ('twitter_name', 'site__name')
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(TwitterAccountAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(TwitterAccountAdmin, self).queryset(request)
        qs = TwitterAccount.objects.select_related().filter(id__in=qs
            ).defer('site__envelope', 'site__geom', 'site__point')
        return qs 
    
    def site_name(self, obj):
        """ The site for this Twitter Account """
        site = obj.site
        return ("%s" % (site.name))
    site_name.admin_order_field = 'site__name'
    
    def is_auto_tweet_setup(self, obj):
        """ If all 4 keys are setup for auto Tweet approved coupon, 
        return True else False 
        """
        setup = False
        if obj.consumer_key and obj.consumer_secret and \
            obj.access_key and obj.access_secret and \
            obj.consumer_key != '' and obj.consumer_secret != '' and \
            obj.access_key != '' and obj.access_secret != '':
            setup = True
        return bool(setup)
    is_auto_tweet_setup.boolean = True
    is_auto_tweet_setup.short_description = u'Is auto tweet setup?'


admin.site.unregister(ContribSite)
admin.site.register(Site, SiteAdmin)
admin.site.register(TwitterAccount, TwitterAccountAdmin)
