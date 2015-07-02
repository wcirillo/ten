""" Models for sms_gateway """

import datetime
import logging

from django.core.exceptions import ValidationError
from django.db import models

from common.custom_cleaning import clean_phone_number
from subscriber.models import MobilePhone

from sms_gateway import config

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)
LOG.info('Logging Started')

BITS_CHOICES = (
        (7, '7bit text'),
        (8, '8bit hex-encoded data'),
        (16, 'best-effort 7bit text representation of the unicode message'),
    )

SPLIT_CHOICES = (
        (0, """Don't split long messages. Messages > 160 characters will be 
            rejected."""),
        (1, 'Split messages using "..." (Maximum of 5 messages once split)'),
        (2, """SMS Concatenation (w. UDH header) - not supported by all phones 
            (Maximum of 4 messages once split)"""),
        (3, """Split messages into multiple 160 character messages (Maximum of 
            5 messages once split)"""),
    )

STATUS_CHOICES = (
        ('DELIVERED', 'DELIVERED'),
        ('FAILED', 'FAILED'),
        ('BUFFERED', 'BUFFERED'),
        ('REJECTED', 'REJECTED'),
        ('NONE/BUFFERED', 'NONE/BUFFERED'),
    )
    
STATUS_HELP_TEXT = """
DELIVERED = SMS delivered to handset.
FAILED = SMS delivery has failed.
BUFFERED = Mobile Network is continuing delivery attempts of the SMS, however 
        delivery has not been successful yet. This will continue throughout 
        the validity period of the SMS, assuming the message has not yet been 
        DELIVERED or FAILED.
REJECTED = Mobile Network has rejected the SMS, and delivery has not been 
        attempted.
NONE/BUFFERED = Out of coverage, phone turned off and operator retrying for 
        duration of validity period.
"""

RESPONSE_DIRECTION_CHOICES = (
        ('in', 'The subscriber responds to us'),
        ('out', 'We respond to the subscriber'),
    )


class SMSMessage(models.Model):
    """
    Generic class describing all SMS messages, sent or received.
    smsto *or* smsfrom will be config.SMS_SHORT_CODE. The other will
    be a mobile_phone. We retain the phone number itself with message here,
    as well as relate it to subscriber.MobilePhone, in case the user changes 
    their phone number.
    """
    smsid = models.BigIntegerField('SMS ID', blank=True, null=True, 
        help_text='Unique id for this message in EzTexting sytem')
    smsto = models.CharField('SMS to', max_length=16, 
        help_text='The phone number (or shortcode) this sms is to')
    smsfrom = models.CharField('SMS from', max_length=16, blank=True, 
        null=True, help_text='The phone number this sms is from')
    mobile_phone = models.ForeignKey('subscriber.MobilePhone', null=True,
        related_name='sms_messages', editable=False)
    note = models.CharField('note', max_length=160, blank=True, null=True,
        help_text="""Note that will be stored in the billing record
        (maximum 160 characters)""")
    subaccount = models.CharField(max_length=10, blank=True, null=True, 
        help_text="""Sub account that will be stored in the billing record
        (maximum 10 characters)""")
    report = models.PositiveSmallIntegerField('report flag', max_length=1, 
        default=0, blank=True, null=True, 
        help_text="""
        Flags for delivery reports (These are bit fields, 
        ie: report=7 enabled all reports - default=0): 
            Bit 1 - Enable intermediate delivery reports 
            Bit 2 - Enable success delivery reports
            Bit 3 - Enable failure delivery reports""")
    vp = models.PositiveSmallIntegerField('validity period', 
        blank=True, null=True, 
        help_text = """Validity period for the message, in seconds. How long
        should they keep trying to send the sms.""")

    def __unicode__(self):
        return u'%s' % self.smsid
        
    class Meta:
        ordering = ('smsid',)
        verbose_name = 'SMS Message'
        verbose_name_plural = 'SMS Messages'

    def save(self, *args, **kwargs):
        """
        Clean and save, relating this message to a mobile phone if it exists.
        """
        self.smsto = clean_phone_number(self.smsto)
        self.smsfrom = clean_phone_number(self.smsfrom)
        try:
            mobile_phone = MobilePhone.objects.get(
                mobile_phone_number=self.smsto
                )
        except MobilePhone.DoesNotExist:
            try:
                mobile_phone = MobilePhone.objects.get(
                    mobile_phone_number=self.smsfrom
                    )
            except MobilePhone.DoesNotExist:
                mobile_phone = False
        if mobile_phone:
            self.mobile_phone = mobile_phone  
        super(SMSMessage, self).save(*args, **kwargs)


class SMSMessageSent(SMSMessage):
    """
    Text messages sent by us to Subscribers. Subclass of SMSMessage.
    """
    # The following are all from the API 
    # (and so don't follow python naming conventions):
    smsmsg = models.TextField('sms message', max_length=800)
    flash = models.BooleanField(default=0, 
        help_text="""Flash messages are possible on some of the US carriers, 
        however it is not very well supported or reliable. They are definitely 
        not supported on the CDMA carriers and probably only a few of the GSM 
        ones, so we'd recommend you not use this option.""")
    split = models.PositiveSmallIntegerField(max_length=1, default=0, 
        choices=SPLIT_CHOICES)
    smsudh = models.CharField('user data header (UDH)', blank=True, null=True, 
        max_length=20, 
        help_text="""Hex encoded. This is used for sending enhanced messages 
            or the concatenated messages enabled with split=2""")
    # End API specific fields.
    sent_datetime = models.DateTimeField('date/time sent', 
        auto_now_add=True)

    class Meta:
        verbose_name = 'SMS Message Sent'
        verbose_name_plural = 'SMS Messages Sent'

    def body_callback(self, buf):
        """ Used by Curl to recieve response buffer."""
        self.content += buf
        
    def clean(self, *args, **kwargs):
        super(SMSMessageSent, self).clean(*args, **kwargs)
        split = self.split
        smsmsg = self.smsmsg
        smsudh = self.smsudh
        if split == '':
            split = 0
        if split == 0:
            if len(smsmsg) > 160:
                raise ValidationError("""If split is set to 0 then the max 
                length is 160 characters (one message = 160 charcters)""")
            elif split == 1:
                if len(smsmsg) > 788:
                    raise ValidationError("""If split is set to 1 then the max 
                    length is 788 characters (five messages = 5*160 characters 
                    - 4*3 characters for the "..." splitting them)""")
            elif split == 2:
                if smsudh == None or smsudh == '':
                    raise ValidationError('If split is 2 then UDH is required')
                elif len(smsmsg) > 612:
                    raise ValidationError("""If split is set to 2 then the max 
                    length is 640 characters (four messages = 4*153 characters.
                    A UDH header will get attached automagically)""")
            elif split == 3:
                if len(smsmsg) > 800:
                    raise ValidationError("""If split is set to 3 then the max 
                    length is 800 characters (five messages = 5*160 characters)
                    """)
                else:
                    raise ValidationError('Split must be 0,1,2 or 3.')        
        return


class SMSMessageReceived(SMSMessage):
    """
    Text messages that were received by us from Subscribers.
    """
    # The following are all from the API 
    # (and so don't follow python naming conventions):
    smsdate = models.DateTimeField('sms date from API')
    network = models.CharField(blank=True, null=True, max_length=20,
        help_text='Required for messages to shortcodes.') 
    smsmsg = models.CharField('message body', max_length=160)
    bits = models.PositiveSmallIntegerField('bits', max_length=2, 
        choices=BITS_CHOICES, default=7,
        help_text='Describes the content of message body')
    smsc = models.CharField(blank=True, null=True, max_length=20)
    smsudh = models.CharField('user data header (UDH)', blank=True, null=True, 
        max_length=20, 
        help_text="""Hex encoded. This is used for sending enhanced messages 
            or the concatenated messages enabled with split=2""")
    smsucs2 = models.CharField(blank=True, null=True, max_length=20, 
        help_text="""This is hex encoded UCS-2 encoded characters, for use 
            when sending in language encodings not natively supported by 
            SMS""")
    # End API specific fields
    # subscriber = models.ForeignKey(Subscriber)
    received_datetime = models.DateTimeField('date/time received', 
        auto_now_add=True)
    response = models.ManyToManyField(SMSMessageSent, 
        related_name='sms_messages_received', through='SMSResponse')

    class Meta:
        ordering = ('smsid',)
        verbose_name = 'SMS Message Received'
        verbose_name_plural = 'SMS Messages Received'

    def save(self, *args, **kwargs):
        #pylint: disable=W0404
        from sms_gateway.tasks import process_received_sms

        super(SMSMessageReceived, self).save(*args, **kwargs)
        process_received_sms.delay(self)

    def clean(self, *args, **kwargs):
        super(SMSMessageReceived, self).clean(*args, **kwargs)
        smsdate = self.smsdate
        # If the date time specified is not well formed, change it to now.
        if not isinstance(smsdate, datetime.datetime):
            self.smsdate = datetime.datetime.now()
        if self.smsto == config.SMS_SHORT_CODE:
            if self.network == None or self.network == '':
                raise ValidationError("""Network is required for messages 
                    to shortcodes""")
        return


class SMSReport(models.Model):
    """ The delivery report of a sent message """
    # The following are all from the API 
    # (and so don't follow python naming conventions):
    smsfrom = models.CharField('SMS from', max_length=16,
        help_text="""The number that was used as smsto in the message that 
        triggered the report.""")
    smsdate = models.DateTimeField('The date/time of the delivery report.')
    smsmsg = models.CharField('message body', max_length=160,
        help_text="""Derive smsid and status from smsmsg in the form: 
        "REPORT+{SMSID}+{STATUS}" """)
    reason = models.CharField(max_length=10, 
        help_text='Detailed delivery report reason code, in hex')
    smsid = models.ForeignKey(SMSMessageSent, related_name='sms_reports', 
        help_text='unique id for the message this report is about')
    status = models.CharField(max_length='14', choices=STATUS_CHOICES, 
        help_text=STATUS_HELP_TEXT)

    class Meta:
        ordering = ('smsid',)
        verbose_name = 'SMS Report'
        verbose_name_plural = 'SMS Reports'

    def __unicode__(self):
        return u'%s' % self.smsid

    def clean(self):
        """
        Cleans incoming report data prior to saving it.
        Derive smsid and status from smsmsg in the form: 
            "REPORT+<SMSID>+<STATUS>"
        Ex: https://server.com/drpt.cgi?smsfrom=447931123456&smsmsg=REPORT+1721
        8733+DELIVERED&smsto=913&shortcode=913&smsid=17221293&smsdate=2002-04-3
        0+21%3A58%3A00&reason=135915161
        """
        smsmsg = self.smsmsg        
        # Depending on how this clean method is called, the plus symbol may
        # have already been translated to a space.
        split_msg = smsmsg.split(' ')
        try:
            split_msg[1]
        except IndexError:
            split_msg = smsmsg.split('+')
        string_smsid = split_msg[1]
        self.status = split_msg[2]
        LOG.debug('string_smsid: %s' % string_smsid)
        LOG.debug('self.status: %s' % self.status)
        try:
            # Only want one record returned
            self.smsid = SMSMessageSent.objects.filter(smsid=string_smsid)[0]
        except IndexError:
            raise ValidationError('Report must be for a sent message.')
        return self


class SMSResponse(models.Model):
    """
    Stores a relationship between messages we send and messages we receive. 
    This is a two-way relationship. Here are three examples of response 
    relationships:
        Subscriber sends 'pizza' and we respond 'send us your zip.'
        Subscriber sends '12601' and we respond with a coupon.    
        We send a coupon and subscriber responds 'stop.'
    """
    sent = models.ForeignKey(SMSMessageSent, related_name='sms_responses')
    received = models.ForeignKey(SMSMessageReceived, 
        related_name='sms_responses')
    response_direction = models.CharField(max_length=3, 
        choices=RESPONSE_DIRECTION_CHOICES) 
    is_opt_out = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'SMS Response'
        verbose_name_plural = 'SMS Responses'
            
    def __unicode__(self):
        return u'%s' % self.sent
