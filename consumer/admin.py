""" Admin config for consumer app. """
#pylint: disable=W0612,R0201
from itertools import groupby
from operator import itemgetter

from django.contrib.auth.admin  import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin
from django.db import connection

from common.custom_cleaning import AdminFormClean
from consumer.models import (Consumer, EmailSubscription, BadUserPattern,
    UnEmailableReason, SalesRep)
from market.models import Site

def get_data(consumers):
    """
    Raw sql pull to populate the consumer change list. This will have one row
    per consumer per email subscription.
    Because consumers is a lazy query, there could be a consumer in the final
    result set that was not passed into this.
    """
    consumers = tuple(consumers.values_list('id', flat=True))
    if len(consumers) == 0:
        return None
    cursor = connection.cursor()
    cursor.execute("""
    SELECT c.user_ptr_id, m.domain, a.consumer_ptr_id,
        MIN(p.mobile_phone_number) AS "mobile_phone_number",
        es.email_subscription_name
    FROM consumer_consumer c
    LEFT JOIN market_site m
        ON m.id = c.site_id
    LEFT JOIN advertiser_advertiser a
        ON a.consumer_ptr_id = c.user_ptr_id
    LEFT JOIN subscriber_subscriber s
        ON s.id = c.subscriber_id
    LEFT JOIN subscriber_mobilephone p
        ON p.subscriber_id = s.id
    -- m2m rel:
    LEFT JOIN consumer_consumer_email_subscription e
        ON e.consumer_id = c.user_ptr_id
    LEFT JOIN consumer_emailsubscription es
        ON es.id = e.emailsubscription_id
    WHERE c.user_ptr_id IN  %s
    GROUP BY c.user_ptr_id, m.domain, a.consumer_ptr_id,
        es.email_subscription_name
    ORDER BY c.user_ptr_id
    """, [consumers])
    query = cursor.fetchall()
    # Populate a dictionary where key will be consumer.id.
    # Collapse multiple rows for same consumer.
    data = {}
    # Each dictionary row will be a three tuple, and a list.
    # Ex: 34: ((u'Hudson Valley', 34, u'8455552001'), [None])
    for row in query:
        data[row[0]] = (row[1:4]) 
    for key, group in groupby(query, key=itemgetter(0)):
        data[key] = data[key], map(itemgetter(4), group)
    return data


class ConsumerAdmin(UserAdmin):
    """ Admin manager for Consumer model, which subclasses User """
    def __init__(self, *args, **kwargs):
        super(ConsumerAdmin, self).__init__(*args, **kwargs)
        fields = list(UserAdmin.fieldsets[0][1]['fields'])
        fields.append('site')
        fields.append('is_email_verified')
        fields.append('consumer_zip_postal')
        fields.append('subscriber')
        fields.append('is_emailable')  
        fields.append('nomail_reason')
        fields.append('email_hash')
        fields.append('email_subscription')
        UserAdmin.fieldsets[0][1]['fields'] = fields
        
    ordering = ['-consumer_create_datetime']
    date_hierarchy = 'consumer_create_datetime'
    filter_horizontal = ('nomail_reason', 'email_subscription', 'groups',)
    list_display = ('email_trimmed', 'is_advertiser', 'mobile_phone', 
                    'consumer_zip_postal', 'is_verified', 'is_emailable',
                    'email_subscriptions', 'consumer_site', 'registered')
    list_filter = ('consumer_create_datetime', 'site__name',)
    raw_id_fields = ('subscriber',)
    save_on_top = True
    search_fields = ['id', 'email', 'username', 'consumer_zip_postal',
        'consumer_create_datetime', ]
    form = AdminFormClean
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "site":
            kwargs["queryset"] = Site.objects.defer('envelope', 'geom', 'point')
        return super(ConsumerAdmin, self).formfield_for_foreignkey(
            db_field, request, **kwargs)
        
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(ConsumerAdmin, self).queryset(request)
        qs = Consumer.objects.select_related().filter(id__in=qs
            ).defer('site__envelope', 'site__geom', 'site__point')
        self.data = get_data(qs)
        return qs 

    def is_verified(self, obj):
        """ Has the email address been verified? """
        return obj.is_email_verified
    is_verified.boolean = True
    is_verified.short_description = 'Ver?'
    
    def is_advertiser(self, obj):
        """ Is the consumer an advertiser? """
        try:
            datum = self.data[obj.id][0][1]
        except KeyError:
            datum = None
        return bool(datum)
    is_advertiser.boolean = True
    is_advertiser.short_description = u'Advertiser?' 
    
    def consumer_site(self, obj):
        """ What site is the consumer related to? """
        try:
            datum = self.data[obj.id][0][0]
        except KeyError:
            datum = None
        return datum
    consumer_site.short_description = u'Site' 
    
    def email_trimmed(self, obj):
        """ Email shortened for better display. """
        email_trimmed = obj.email[0:40]
        if len(email_trimmed) == 40:
            email_trimmed = '%s...' % email_trimmed
        return ("%s" % (email_trimmed))
    email_trimmed.admin_order_field = 'email'
    email_trimmed.short_description = 'Email'

    def registered(self, obj):
        """ Pretty date formatting on create date. """
        return obj.consumer_create_datetime.strftime('%b %d %Y %H:%M')
    registered.admin_order_field = 'consumer_create_datetime'
    
    def mobile_phone(self, obj):
        """ What mobile phone, if any, do we have for this subscriber? """
        try:
            datum = self.data[obj.id][0][2]
        except KeyError:
            datum = None
        if datum == None:
            datum = ''
        return ("%s" % (datum))
    mobile_phone.short_description = 'Subscriber?'
    
    def email_subscriptions(self, obj):
        """ What email subscriptions does the consumer have? """
        try:
            datum = ', '.join(self.data[obj.id][1])
        except (TypeError, KeyError):
            datum = ''
        return ("%s" % (str(datum)))
    email_subscriptions.short_description = 'subs'


class SalesRepAdmin(admin.ModelAdmin):
    """ admin manager to manage sales reps"""
    raw_id_fields = ('consumer',)
    form = AdminFormClean

admin.site.unregister(User)
admin.site.register(Consumer, ConsumerAdmin)
admin.site.register(EmailSubscription)
admin.site.register(BadUserPattern)
admin.site.register(UnEmailableReason)
admin.site.register(SalesRep, SalesRepAdmin)
