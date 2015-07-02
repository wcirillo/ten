""" These views are called only by EZTexting (and our unit tests). """
import dateutil
import logging

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseBadRequest

from subscriber.models import Carrier

from sms_gateway import config
from sms_gateway.models import SMSMessageReceived, SMSReport
from sms_gateway.service import BadRequestError, get_sms_from_request

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def receive_sms(request):
    """ Receive a text messages from EZTexting. Texting to 71010 comes in here.
    """
    if request.method != 'GET':
        LOG.error('receive_sms attempt with method "%s"' % request.method)
        return HttpResponseBadRequest(content='Bad request')
    # Very hard to test with, so only use in prod:
    if settings.DEBUG == False \
    and request.META['REMOTE_ADDR'] not in config.SMS_ALLOWED_IPS:
        LOG.error('receive_sms from not permitted IP %s' 
            % request.META['REMOTE_ADDR'])
        return HttpResponseBadRequest
    try:
        sms = get_sms_from_request(request)
    except BadRequestError:
        return HttpResponseBadRequest(content='Bad request')
    try:
        Carrier.objects.get(carrier=sms.network)
        LOG.debug('receive_sms knows carrier %s' % sms.network)
    except Carrier.DoesNotExist:
        LOG.error('receive_sms with unknown carrier %s' % sms.network)
    LOG.debug('receive_sms sms: %s' % sms.__dict__)
    # Did we already receive this message?
    try:
        sms = SMSMessageReceived.objects.get(smsid=request.GET.get('smsid'))
        LOG.debug('receive_sms found matching smsid: %s' % sms.id)
    except SMSMessageReceived.MultipleObjectsReturned:
        LOG.info('receive_sms repeat sms received for smsid %s' 
            % request.GET.get('smsid'))
    except SMSMessageReceived.DoesNotExist:
        # We didn't get this message yet. Store it.
        try:
            sms.full_clean()
        except ValidationError, e:
            LOG.error(e.messages)
            # Don't log smsfrom; private data.
            sms.smsfrom = 'nnnnnn' + sms.smsfrom[-4:]
            LOG.error('receive_sms not saved: %s' % sms.__dict__)
            return HttpResponseBadRequest(content='Bad request')
        sms.save()
        LOG.info('receive_sms saved new smsid %s' % sms.smsid)
    return HttpResponse("OK")

def receive_report(request):
    """ After we send a text message through EZTexting, they'll send us a report
    about whether it was delivered or not, through this.
    """
    LOG.debug('receive_report began')
    if request.method != 'GET':
        LOG.error('receive_report attempt with method "%s"' % request.method)
        return HttpResponseBadRequest(content='Bad request')
    # This is very hard to test with, so only use in prod:
    if settings.DEBUG == False:
        if request.META['REMOTE_ADDR'] not in config.SMS_ALLOWED_IPS:
            LOG.error('receive_report from not permitted IP %s' 
                % request.META['REMOTE_ADDR'])
            return HttpResponseBadRequest(content='Bad request')
    if len(request.GET) < 4:
        LOG.error('receive_report attempt with parameter count %s' 
            % len(request.GET))
        return HttpResponseBadRequest(content='Bad request')
    sms_report = SMSReport(
                    smsfrom=request.GET['smsfrom'],
                    smsdate=request.GET['smsdate'],
                    smsmsg = request.GET['smsmsg'])
    try:
        sms_report.smsdate = dateutil.parser.parse(sms_report.smsdate)
    except ValueError:
        sms_report.smsdate = dateutil.parser.parse(sms_report.smsdate[:10])
    # Don't log mobile_phone_number; it is private data.
    LOG.debug('receive_report smsfrom nnn-%s smsdate %s smsmsg %s'
        % (sms_report.smsfrom[-4:], sms_report.smsdate, sms_report.smsmsg))
    try:
        sms_report.clean()
    except ValidationError, e:
        LOG.error(' '.join(e.messages))
        sms_report.smsfrom = 'nnnnnn' + sms_report.smsfrom[-4:]
        LOG.error('receive_report not saved: %s' % sms_report.__dict__)
        return HttpResponseBadRequest(content='Bad request')
    sms_report.save()
    LOG.info('receive_report saved new smsid %s' % sms_report.smsid)
    return HttpResponse("OK")
