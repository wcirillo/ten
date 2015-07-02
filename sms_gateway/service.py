""" Service methods for sms_gateway app """

import logging
import pycurl

from django.core.exceptions import ValidationError
from django.template import Context
from django.template.loader import get_template
from django.utils.http import urlquote

from common.contest import check_contest_is_running
from common.custom_format_for_display import format_phone
from common.utils import CurlBuffer, replace_problem_ascii
from consumer.models import Consumer
from email_gateway.send import send_email
from market.models import Site
from sms_gateway import config
from sms_gateway.models import SMSMessageReceived, SMSMessageSent, SMSResponse
from subscriber.models import Carrier, MobilePhone, Subscriber
from subscriber.service import add_update_subscriber

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class BadRequestError(Exception):
    """ An exception for raising Bad Request http response. """
    pass

def get_sms_from_request(request):
    """ Return an SMSMessageReceived object from a request. """
    sms = SMSMessageReceived()
    # These fields are mandatory:
    for field in ('smsto', 'smsfrom', 'smsdate', 'smsid', 'smsmsg', 'bits'):
        try:
            setattr(sms, field, request.GET[field])
        except KeyError:
            # Don't log smsfrom: private data:
            log_copy = request.GET.copy()
            if log_copy['smsfrom']:
                log_copy['smsfrom'] = 'nnnnnn' + log_copy['smsfrom'][-4:]
            LOG.error('receive_sms did not get required param %s' % log_copy)
            raise BadRequestError
    # These fields are optional:
    for field in ('smsfrom', 'note', 'subaccount', 'report', 'vp', 'network',
        'smsudh', 'smsc', 'smsucs2'):
        try:
            setattr(sms, field, request.GET[field])
        except KeyError:
            setattr(sms, field, None)
    # If the phone number is longer than 10 digits, strip the first numbers.
    # Ex: 18455551234 --> 8455551234
    LOG.debug('receive_sms received param %s' % sms.smsfrom)
    sms.smsfrom = sms.smsfrom[-10:]
    LOG.debug('receive_sms trimmed param now %s' % sms.smsfrom)
    # If someone sends a text with a blank sms, change to a space so it can be
    # saved.
    if sms.smsmsg == '':
        sms.smsmsg = ' '
    # Cingular customers receive SMS at AT&T:
    if sms.network == 'CINGULARUS':
        sms.network = 'ATTUS'
        LOG.debug('receive_sms switched CINGULARUS to ATTUS')
    # Note field name inconsistency between API and us:
    # Convert smsucs2 from hex:
    if sms.smsucs2:
        sms.smsucs2 = sms.smsucs2.decode('hex')[:20]
    return sms

def curl_sms(sms, query_string):
    """
    Perform curl to EZTexting API.
    """
    # url can't be Unicode.
    url = str('%s%s' % (config.SMS_SEND_URL, query_string))
    LOG.debug('send_sms url: %s' % url)
    curl_buffer = CurlBuffer()
    curl = pycurl.Curl()
    curl.setopt(curl.VERBOSE, config.SMS_CURL_VERBOSITY)
    curl.setopt(curl.WRITEFUNCTION, curl_buffer.body_callback)
    curl.setopt(curl.URL, url)
    # Send the message.
    curl.perform() 
    if curl.getinfo(curl.HTTP_CODE) != 200:
        LOG.error('send_sms bad status code returned %s' 
            % curl.getinfo(curl.HTTP_CODE))
        LOG.error('sms: %s' % sms.__dict__)
    else:
        LOG.debug('send_sms received valid response. content: %s' 
            % curl_buffer.content)
        sms.smsid = curl_buffer.content.rstrip()
    curl.close()
    return sms

def send_sms(template, smsto, smsfrom=config.SMS_SHORT_CODE, context=None, 
    smsmsg=None):
    """
    Create an SMSMessageSent instance, make a request of the EzTexting API, 
    receive a response from EzTexting, and save it, returning the smsid, which
    is the unique identifier of it from EzTexting. If test mode is configured, 
    it does not contact EzTexting but computes next smsid.
    
    Requires *either*:
        - a template (from which an smsmsg will be generated) 
        - an smsmsg
    
    Variable names that are not nice match the EZTexting API.
    These variables that EZTexting supports are not used by project 10 
    (revert to -r 4829 to see removed code):
        vp
        smsudh
        split
        flash
        bits
        subaccount
        note
    """
    # Build smsmsg out of template and context passed in.
    if template:
        # Render the template.
        if context is None:
            context = {}
        # Contest logic.
        context.update({'contest_is_running': check_contest_is_running()})
        templ = get_template(template)
        LOG.debug('send_sms context %s' % context)
        # Trim trailing newline.
        smsmsg = templ.render(Context(context))[:-1]
    # Strip. Replace smart quotes etc. Remove extra internal whitespace.
    smsmsg = replace_problem_ascii(smsmsg.strip()).replace('  ', ' ')
    LOG.debug('send_sms smsmsg %s' % smsmsg)
    # smsmsg will be stored in our database. Encode a version for delivery.
    # Fix for &
    smsmsg_encoded = urlquote(smsmsg).replace('%26amp%3B', '%26')
    LOG.debug('send_sms smsmsg_encoded %s' % smsmsg_encoded)
    # smsto must be a MobilePhone
    try:
        carrier = MobilePhone.objects.select_related(
            'carrier').get(mobile_phone_number=smsto).carrier
    except MobilePhone.DoesNotExist: 
        error_message = 'send_sms failed: no MobilePhone %s' % smsto
        LOG.error(error_message)
        raise ValidationError(error_message)
    # We must have a username and password for this Carrier
    if not carrier.user_name or not carrier.password:
        error_message = ('send_sms failed: no carrier credentials for %s' %
            carrier.carrier_display_name)
        LOG.error(error_message)
        raise ValidationError(error_message)
    # Build a query string out of allowed inputs:
    # Note: prepending 1 to the outgoing phonenumber here only.
    # report = 7 because we always want delivery notification.
    query_string = '?user=%s&pass=%s&smsto=1%s&smsfrom=%s&smsmsg=%s&%s' % (
        carrier.user_name, carrier.password, smsto, smsfrom, smsmsg_encoded,
        'report=7')
    sms = SMSMessageSent(smsto=smsto, smsfrom=smsfrom, smsmsg=smsmsg)
    if config.TEST_MODE:
        LOG.warning('In TEST_MODE! sms not really sent!!')
        try:
            sms_sent = SMSMessageSent.objects.latest('smsid')
            sms.smsid = sms_sent.smsid + 1
        except SMSMessageSent.DoesNotExist:
            # No messages so far!
            sms.smsid = 1
    else:
        sms = curl_sms(sms, query_string)
    LOG.debug('send_sms smsid: %s' % sms.smsid)
    LOG.info('send_sms successfully sent smsid %s' % sms.smsid)
    LOG.debug('send_sms sms: %s' % sms.__dict__)
    try:
        sms.full_clean()
    except ValidationError, exception:
        LOG.error('send_sms validation error %s' % exception)
        return 
    sms.save()
    LOG.debug('send_sms saved new smsid %s' % sms.smsid)
    return sms.smsid
    
def send_carrier_lookup(mobile_phone_number):
    """ 
    Lookup a carrier for a phone number by EzTexting API. If test mode is 
    configured, it does not contact EzTexting and returns carrier AT&T.
    """
    if config.TEST_MODE:
        LOG.warning('In TEST_MODE! carrier not really looked up!!')
        carrier = Carrier.objects.get(id=2)
        return carrier
    # Note url can't be Unicode.
    url = '%s?user=%s&pass=%s&phonenumber=%s' % (config.SMS_LOOKUP_URL,
            config.SMS_LOOKUP_USER, config.SMS_LOOKUP_PASSWORD,
            mobile_phone_number)
    url = str(url)
    LOG.debug('send_carrier_lookup url: %s' % url)
    curl_buffer = CurlBuffer()
    curl = pycurl.Curl()
    curl.setopt(curl.VERBOSE, config.SMS_CURL_VERBOSITY)
    curl.setopt(curl.WRITEFUNCTION, curl_buffer.body_callback)
    curl.setopt(curl.URL, url)
    # Send the message.
    curl.perform()
    if curl.getinfo(curl.HTTP_CODE) != 200:
        LOG.error('send_carrier_lookup bad status code returned %s' 
            % curl.getinfo(curl.HTTP_CODE))
        return False
    LOG.debug('send_carrier_lookup response: %s' % curl_buffer.content)
    error_message = False
    if curl_buffer.content == '-1':
        error_message = 'Invalid Username or Password'
    elif curl_buffer.content == '-2':
        error_message = 'Invalid Phone Number Format'
    elif curl_buffer.content == '-3':
        error_message = 'Insufficient Credits'
    elif curl_buffer.content == '-4':
        error_message = 'Lookup Error. Please Reattempt'
    elif len(curl_buffer.content) == 2:
        error_message = curl_buffer.content 
    elif curl_buffer.content == 'UNKNOWN':
        error_message = 'Unrecognized carrier. Contact us to extend coverage.'
    elif curl_buffer.content == 'FAILURE':
        error_message = 'Lookup Failed Due to Inaccurate Mobile Number'
    if error_message:
        # Don't log the entirety of private data, just last four chars:
        LOG.error("send_carrier_lookup returned %s for nnn-%s" % (error_message,
            mobile_phone_number[-4:]))
        raise ValidationError(error_message)
    # Cingular customers receive SMS at AT&T:
    if curl_buffer.content == 'CINGULARUS':
        curl_buffer.content = 'ATTUS'
        LOG.debug('send_carrier_lookup switched CINGULARUS to ATTUS')
    # Get Carrier
    try:
        carrier = Carrier.objects.get(carrier=curl_buffer.content)
    except Carrier.DoesNotExist:
        error_message = "send_carrier_lookup unknown carrier received %s" % (
                curl_buffer.content
            )
        LOG.error(error_message)
        raise ValidationError(error_message)
    return carrier
    
def save_phone_by_carrier_lookup(mobile_phone_number):
    """ Given a phone number, derive carrier. Create or update MobilePhone. """
    # If the phone number is longer than 10 digits, strip the first numbers.
    # Ex: 18455551234 --> 8455551234
    scrubbed_mobile_phone_number = mobile_phone_number[-10:]
    try:
        carrier = send_carrier_lookup(scrubbed_mobile_phone_number)
    except ValidationError as exception:
        raise ValidationError(exception.messages)
    if carrier:    
        # Now we have a known good carrier for this phone. Save it.
        try:
            mobile_phone = MobilePhone.objects.get(
                mobile_phone_number=mobile_phone_number)
            LOG.debug('send_carrier_lookup existing mobile phone %s' 
                % mobile_phone_number)
        except MobilePhone.DoesNotExist:
            mobile_phone = MobilePhone()
            # Cannot have a mobile_phone without a subscriber.
            subscriber = Subscriber()
            subscriber.save()
            mobile_phone.subscriber = subscriber
        mobile_phone.mobile_phone_number = scrubbed_mobile_phone_number
        mobile_phone.carrier = carrier
        mobile_phone.save()
        LOG.debug('send_carrier_lookup saved new mobile phone: %s' 
            % mobile_phone.__dict__)
        return mobile_phone
    else:
        return False

def create_response_relationship(received_smsid, sent_smsid, is_opt_out=False):
    """
    When we have responded, create a response relationship between message 
    we received and the message we sent.
    """
    sms_response = SMSResponse()
    try:
        sms_response.sent = SMSMessageSent.objects.get(smsid=sent_smsid)
    except SMSMessageSent.MultipleObjectsReturned:
        # We sent this smsid multiple times.
        LOG.error("""create_response_relationship failed. Multiple
            sent messages with smsid %s""" % sent_smsid)
        return False
    except SMSMessageSent.DoesNotExist:
        # Not a real sent message. Is this a test?
        LOG.error("""create_response_relationship failed on new 
            sms_response sent %s""" % sent_smsid)
        return False
    try:
        sms_response.received = SMSMessageReceived.objects.get(
            smsid=received_smsid)
    except SMSMessageReceived.MultipleObjectsReturned:
        # We recieved this smsid multiple times. Allowed behavior.
        LOG.error("""create_response_relationship bailed. Multiple
            received messages with smsid %s""" % received_smsid)
        return False
    except SMSMessageReceived.DoesNotExist:
        # Not a real sent message. Is this a test?
        LOG.error("""create_response_relationship failed on new 
            sms_response received %s""" % received_smsid)
        return False
    sms_response.response_direction = 'out'
    sms_response.is_opt_out = is_opt_out
    sms_response.save()
    LOG.debug('create_response_relationship saved new sms_response %s' % 
        sms_response.id)
    return sms_response
        
def subscribe_sender(sms_message_received, subscriber_zip_postal):
    """
    Create or update Subscriber from a SMSMessageReceived and a zip/postal.
    If the mobile_phone is not verified, set it to verified.
    (To send a text message from a mobile phone is to verify.)
    """
    sites = list(Site.objects.get_sites_this_zip(code=subscriber_zip_postal))
    if len(sites) > 0:
        site = sites[0]
    else:
        site = Site.objects.get(id=1)
    # Get Carrier.
    try:
        carrier_id = Carrier.objects.get(
                carrier=sms_message_received.network
            ).id
    except Carrier.DoesNotExist:
        LOG.error("""subscribe_sender unknown carrier received %s""" 
            % sms_message_received.network)
        carrier_id = 1
    LOG.debug('subscribe_sender add/update subscriber')
    LOG.debug('sms_message_received: %s' % sms_message_received)
    LOG.debug('carrier id %s' % carrier_id)
    LOG.debug('mobile_phone_number %s' % sms_message_received.smsfrom)
    LOG.debug('subscriber_zip_postal %s' % subscriber_zip_postal)
    subscriber = add_update_subscriber(carrier_id=carrier_id, 
        mobile_phone_number=sms_message_received.smsfrom, 
        subscriber_zip_postal=subscriber_zip_postal, site=site)
    # Now we have a mobile phone. Set it to verified.
    mobile_phone = MobilePhone.objects.get(
        mobile_phone_number=sms_message_received.smsfrom)
    if not mobile_phone.is_verified:
        mobile_phone.is_verified = True
        mobile_phone.save()
    LOG.debug('subscriber id %s' % subscriber.id)
    return subscriber
    
def send_consumer_welcome(consumer, smsto):
    """
    Send the consumer welcome email and text message.
    """
    contest_is_running = check_contest_is_running()
    email_context = {
            'to_email': consumer.email,
            'subject': 'IMPORTANT - Get your Coupons',
            'from_address': 'Coupons',
            'contest_is_running': contest_is_running,
            'current_site': consumer.site, 
            'mobile_phone_number': format_phone(smsto),
            'ref_num': "%d SMS" % consumer.id,
        }
    send_email(template='consumer_welcome_sms', site=consumer.site,
        context=email_context)
    sms_context = {
            'contest_is_running': contest_is_running,
            'current_site': consumer.site, 
            'consumer': consumer,
        }
    sent = send_sms(template='sms/check_email_to_confirm.html', smsto=smsto, 
        context=sms_context)
    return sent

def cleanup_mobile_phone_no_carrier(purge=False):
    """
    For all mobile phones that have carrier = Other, do a carrier lookup.
    For matches, send double opt-in.
    For no matching Carrier, if purge, delete the record.
    """
    for mobile_phone in MobilePhone.objects.filter(carrier=1):
        try:
            save_phone_by_carrier_lookup(
                mobile_phone.mobile_phone_number)
        except ValidationError as exception:
            LOG.debug(exception.messages)
            LOG.debug('no good carrier for %s' % mobile_phone)
            if purge:
                try:
                    subscriber = mobile_phone.subscriber
                    try:
                        consumer = Consumer.objects.get(subscriber=subscriber)
                        consumer.subscriber = None
                        consumer.save()
                    except Consumer.DoesNotExist:
                        pass
                except Subscriber.DoesNotExist:
                    pass
                mobile_phone.delete()
                
def update_phones_carrier_other():
    """ Get good carriers for mobile phoneswith carrier 'Other'. """
    for mobile_phone in MobilePhone.objects.filter(carrier__name='Other'):
        send_carrier_lookup(mobile_phone.mobile_phone_number)
