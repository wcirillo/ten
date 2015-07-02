""" Admin config for sms_gateway """
#pylint: disable=R0201
from django.contrib import admin

from sms_gateway.models import (SMSMessage, SMSMessageSent, SMSMessageReceived,
    SMSResponse, SMSReport)


class SMSMessageAdmin(admin.ModelAdmin):
    """ Admin config for SMSMessage model. """
    exclude = ('note', 'subaccount', 'report', 'vp')
    list_display = ('smsid', 'smsto', 'smsfrom', 'message', 'date')
    ordering = ('-smsid',)
    search_fields = ['smsfrom', 'smsmessagesent__smsmsg', 
        'smsmessagereceived__smsmsg']
    
    def queryset(self, request):
        """ Customizes the queryset for improved performance. """
        qs = super(SMSMessageAdmin, self).queryset(request)
        return qs.select_related('smsmessagesent', 'smsmessagereceived')

    def message(self, obj):
        """ The contents of the message. """
        message = obj.smsmessagesent
        if message is None:
            message = obj.smsmessagereceived
        return message.smsmsg
        
    def date(self, obj):
        """ The date of the message. """
        message = obj.smsmessagesent
        if message is None:
            date = obj.smsmessagereceived.received_datetime
        else:
            date = message.sent_datetime
        return date.strftime('%b %d %Y %H:%M')


class SMSMessageReceivedAdmin(admin.ModelAdmin):
    """ Admin config for SMSMessageReceived model. """
    date_hierarchy = 'smsdate'
    exclude = ('note', 'subaccount', 'report', 'vp', 'smsc', 'smsudh', 'bits')
    list_display = ('smsid', 'smsfrom', 'smsmsg', 'smsdate')
    list_filter = ('smsdate', 'network')
    ordering = ('-smsdate',)
    search_fields = ['smsid', 'smsfrom', 'smsmsg']


class SMSMessageSentAdmin(admin.ModelAdmin):
    """ Admin config for SMSMessageSent model. """
    date_hierarchy = 'sent_datetime'
    exclude = ('note', 'subaccount', 'report', 'vp', 'smsudh', 'flash', 'split')
    list_display = ('smsid', 'smsto', 'smsmsg', 'sent_datetime')
    list_filter = ('sent_datetime',)
    ordering = ('-sent_datetime',)
    search_fields = ['smsto', 'smsmsg']


class SMSReportAdmin(admin.ModelAdmin):
    """ Admin config for SMSReport model. """
    actions = None
    date_hierarchy = 'smsdate'
    list_display = ('smsid', 'smsfrom', 'status', 'smsdate')
    list_filter = ('smsdate', 'status')
    ordering = ('-smsdate',)
    search_fields = ['smsfrom']
    raw_id_fields = ('smsid',)


class SMSResponseAdmin(admin.ModelAdmin):
    """ Admin config for SMSResponse model. """  
    actions = None
    list_display = ('id', 'received_date_time', 'received_message',
                    'sent_message', 'response_direction', 'is_opt_out')
    search_fields = ['received__smsfrom', 'sent__smsto', 'received__smsmsg']
    raw_id_fields = ('received', 'sent')
    
    def received_date_time(self, obj):
        """ Pretty formatting of date received."""
        received_date_time = obj.received.received_datetime
        return "%s" % received_date_time

    def received_message(self, obj):
        """ Pretty formatting of received message. """
        received_message = obj.received.smsmsg
        if len(received_message) > 40:
            received_message = "%s..." % received_message[:40]
        return "%s" % received_message

    def sent_message(self, obj):
        """ Pretty formatting of sent message. """
        sent_message = obj.sent.smsmsg
        if len(sent_message) > 60:
            sent_message = "%s..." % sent_message[:60]
        return "%s" % sent_message

admin.site.register(SMSMessage, SMSMessageAdmin)
admin.site.register(SMSMessageReceived, SMSMessageReceivedAdmin)
admin.site.register(SMSMessageSent, SMSMessageSentAdmin)
admin.site.register(SMSReport, SMSReportAdmin)
admin.site.register(SMSResponse, SMSResponseAdmin)
