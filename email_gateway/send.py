"""
Routines for sending individual and mass emails that conform to our specs.
"""
import logging
from smtplib import SMTPRecipientsRefused
import sys

from django.conf import settings
from django.core import mail, urlresolvers
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.template import loader, Context

from common.custom_format_for_display import list_as_text
from common.service.payload_signing import PAYLOAD_SIGNING
from common.utils import generate_email_hash
from consumer.models import Consumer
from email_gateway import config
from email_gateway.process import flag_bouncing_email
from email_gateway.service.email_service import process_message
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class CustomEmailMultiAlternative(EmailMultiAlternatives):
    """" Derived from django EmailMultiAlternatives (EmailMessage) to allow more 
    control over what displays in the TO and CC header values in each email. 
    """
    def message(self):
        """ Calls django's message method and then cleans up the header context.
        so that the CC'd addresses do not appear in the TO list (and the TO list
        remains unique.
        """
        msg = EmailMultiAlternatives.message(self)
        return process_message(msg)


def send_admin_email(context):
    """
    Send admin-type emails using a default template and site 1. Context is
    expected to have a key 'admin_data'.
    
    Old params: template='admin_generic', emails=None,
        subject='10coupons system email', from_address='sysadmin@10coupons.com', 
        friendly_from='10coupons Sysadmin', *args, **kwargs
    """
    site = Site.objects.get(id=1) 
    LOG.debug('admin - Sending "%s" to %s' % (context['subject'], 
        context['to_email']))
    send_email('admin_generic', site, context)

def clean_context(_context):
    """ Clean the key values in the context and set defaults to prepare for 
    email message creation.
    If context['to_email'] or context['internal_cc'] are strings, they will be
        converted to a 1 item list. 
    """
    _context['headers'] =  _context.get('headers', {})
    if type(_context['to_email']) in (unicode, str):
        _context['to_email'] = [_context['to_email']]
    _context['internal_cc'] = _context.get('internal_cc', [])
    if type(_context['internal_cc']) in (unicode, str):
        _context['internal_cc'] = [_context['internal_cc']]
    if _context.get('cc_signature_flag', False) and \
    _context.get('signature_email', False):
        if _context['signature_email'] \
        not in _context['internal_cc'] + _context['to_email']:
            _context['internal_cc'].append(_context['signature_email'])
        del _context['cc_signature_flag']
    return _context

def prepare_send_list(_context):
    """ Build actual send list, cc_list and to_list:
        actual_send_list: list of recipients to loop over for which email will
            be sent.
        internal_cc:     list of recipients to display in the CC in the header
        to_list:         list of recipients to send this email to
        dsp_to:         list of recipients to display in the TO in the header
    """
    _context = clean_context(_context)
    to_list = list(_context['to_email'])
    internal_cc = _context['internal_cc']
    actual_send_list = []
    
    # Header context keys are just for display.
    if _context.get('display_all_recipients', False):
        _context['headers'].update({'dsp_to': list_as_text(to_list, ', ')})
        if internal_cc:
            _context['headers'].update({'Cc': list_as_text(internal_cc, ', ')})
    for email in to_list + internal_cc:
        LOG.debug('Checking email %s' % email)
        if settings.LIVE_EMAIL_DOMAINS and email[email.index('@'):].lower() \
        not in [domain.lower() for domain in settings.LIVE_EMAIL_DOMAINS]:
            LOG.error("""Our settings.LIVE_EMAIL_DOMAINS prevented us from 
            sending to this email recipient: %s""" % email)
            continue
        actual_send_list.append(email)
        # Everyone gets the same email, so only update the real name if the
        # email has one recipient in the TO or real name will be wrong for
        # everyone else.
        if _context.get('real_name', False) and len(set(to_list)) == 1 \
        and to_list[0] == email:
            to_list[0] = '%s <%s>' % (_context['real_name'], to_list[0])
            _context.get('headers', {}).update({'dsp_to': to_list[0]})
    actual_send_list = set(actual_send_list)
    return _context, actual_send_list

def send_email(template, site, context):
    """
    Render this template as a multipart email to one or more email recipients, 
    given as iterable context['to_email']. 
    
    For other expected keys of context, see build_email. build_email is iterated
    once per recipient because we *always* customize the email bounce header for
    tracking and deliverability.
    
    Takes advantage of connection pooling... instead of sending each message 
    individually, it builds a list of message objects (passed back from 
    build_email) and sends them all out in one connection.
    Header display options are based on the following keys in context:
        internal_cc : list of emails to cc AND display as CC's.
        display_all_recipients: defaults to False, indicates to display all To's 
            and CC's as specified, when false, it will only show a single To 
            email.
        cc_signature_flag: When true, in conjunction with signature_email, the
            signature_email will be CC'd.
    """
    # Ensure modified context is contained within.
    _context = context.copy()
    LOG.debug('context: %s' % _context)
    LOG.debug("Generating emails")
    messages = []
    _context, actual_send_list = prepare_send_list(_context)
    
    for recipient_email in actual_send_list:
        message = build_email(template, site, recipient_email, _context)
        if message:
            messages.append(message)
        else:
            LOG.error("Unknown Problem sending to email address: %s check " \
                "previous output errors from build_email" % recipient_email)      
    connection = mail.get_connection()
    connection.open()
    done = False
    while done is False:
        try:
            connection.send_messages(messages)
            done = True
        except SMTPRecipientsRefused:
            bad_email = sys.exc_info()[1][0].keys()[0]
            LOG.debug("Bad email address %s, setting to bounce and continuing" % 
                bad_email)
            flag_bouncing_email(bad_email, 1)
            bad_index = _context['to_email'].index(bad_email)
            if len(_context['to_email']) == bad_index + 1:
                # We're at the end of the list, don't bother to do try
                # and continue.
                done = True
            else:
                messages = messages[bad_index + 1:]
                LOG.info("Restarting send from the next address...")
    connection.close()
    LOG.debug("Finished email send")

def render_template(template, context):
    """
    Render this template path patterns as text and html.

    Email templates are organized by interpreting the first _ delimited
    stanza of "template" as the directory name; the remainder as the file
    name up to the ".".
    """
    text_part = loader.get_template('email_gateway/%s.txt' %
        (template.replace('_','/',1)))
    html_part = loader.get_template('email_gateway/%s.html' %
        (template.replace('_','/',1)))
    LOG.debug('textpart: %s' % text_part)
    LOG.debug('htmlpart: %s' % html_part)
    text_content = text_part.render(context)
    html_content = html_part.render(context)
    LOG.debug('headers: %s' % context['headers'])
    LOG.debug('text_content: %s' % text_content)
    LOG.debug('html_content: %s' % html_content)
    return text_content, html_content

def prepare_context(site, recipient_email, context):
    """ Does some preprocessing of the context for build_email. """
    # Set defaults.
    defaults = {
        'real_name': None,
        'friendly_from': site.domain,
        'from_address': config.DEFAULT_FROM_ADDRESS,
        'headers': {},
        'bouncing_checked': False,
        'mailing_list': [1],
        'show_unsubscribe': True,
        }
    defaults.update(context)
    context = defaults
    if not context['bouncing_checked']:
        LOG.debug("checking bounce status for %s" % recipient_email)
        try:
            consumer = Consumer.objects.get(email=recipient_email)
            if not consumer.is_emailable:
                reasons = str(consumer.nomail_reason.values_list('name',
                    flat=True))
                LOG.info("dropping email to address %s because %s" % (
                    recipient_email, reasons))
                return False
            if not consumer.is_active:
                LOG.info("dropping email to address %s because is_active"
                    "is False" % recipient_email)
                return False
        except Consumer.DoesNotExist:
            LOG.info("address %s not in address table, proceeding" 
                % recipient_email)
    LOG.debug("friendly_from: %s" % context['friendly_from'])
    # If from address was just a name w/o a domain, attach default domain.
    if not context['from_address'].partition('@')[2]:
        context['from_address'] = '%s@%s' % (context['from_address'],
            config.DEFAULT_FROM_DOMAIN)
    combined_from = "%s <%s>" % (context['friendly_from'],
        context['from_address'])
    context['headers'].update({'From': combined_from})
    return context

def build_email(template, site, recipient_email, context):
    """ Build a multipart email to be sent. 
    old params: email, subject=config.DEFAULT_SUBJECT, 
        from_address=config.DEFAULT_FROM_ADDRESS, friendly_from=None, 
        real_name=None, show_unsubscribe=True, bouncing_checked=False, 
        mailinglist='1', context=None
    
    'template' (required) - the name part of a template located in 
      email_gateway/templates. This string is also used as an identifier in the
      bounce address and opt out link.
    'site' (required) - The site this email is from, which may or may not be 
      the current site in the case of a cross-site redirect, eg. registered on 
      site 3 with a zip code for site 2.
    'recipient_email' - (required) email address to receive this email.
    'context' - (required):

        'subject' defaults to "A message from site.domain"
        'from_address' - default = Coupons@10coupons.com. This also be passed-in
          as just the name part to the left of the @, in which case
          config.DEFAULT_FROM_DOMAIN will be substituted
        'friendly_from' - default = site.domain
        'show_unsubscribe' - default = True. Set to False to exclude the
            "unsubscribe" footer from an email -- for account-related emails
            only!
        'bouncing_checked' - default = False. Set this flag if this email is to
            an email address that has already been checked for bouncing, or
            if this email should go to email addresses that are bouncing.
            Ex: the "forgot password" email goes to email addresses that bounce.
        'mailing_list' - default = [1]. If the unsubscribe link is shown, this
            is the str(id) of the email_subscription the opt-out is for.

        'headers' - optional dictionary with header names as keys.
        'real_name' - optional friendly name of 'to' address.

    """
    context = prepare_context(site, recipient_email, context)
    if not context:
        return False
    # Set the resolver to use the correct urlconf. This is used by 'reverse', in
    # further preparation of the context, and by 'render'.
    urlconf = 'urls_local.urls_%s' % site.id
    initial_urlconf = urlresolvers.get_urlconf()
    urlresolvers.set_urlconf(urlconf)
    email_hash = generate_email_hash(recipient_email, 'email')
    payload = PAYLOAD_SIGNING.create_payload(
        email=recipient_email, subscription_list=context['mailing_list'])
    bounce_address = '%s-%s-%s@%s' % (config.DEFAULT_BOUNCE_USER, template,
        email_hash, config.DEFAULT_BOUNCE_DOMAIN)
    LOG.debug("bounce_address: %s" % bounce_address)
    # Can't use current_site context processor w/o a request, so recreate
    # the name_no_spaces variable for our templates.
    site.name_no_spaces = site.get_name_no_spaces()
    if context['show_unsubscribe']:
        opt_out_link = '<%s%s>, <mailto:%s-%s-%s@%s>' % (
            settings.HTTP_PROTOCOL_HOST,
            reverse('opt_out', kwargs={'payload': payload}),
            config.LIST_UNSUB_PREFIX, template, email_hash,
            config.DEFAULT_BOUNCE_DOMAIN)
        LOG.debug("opt_out_link: %s" % opt_out_link)
        context['headers'].update({'List-Unsubscribe': opt_out_link})
    context.update({'media_url': settings.MEDIA_URL,
        'recipient_email': recipient_email,
        'directory_name': site.directory_name, 'payload': payload,
        'base_url': settings.HTTP_PROTOCOL_HOST,
        'from_email': context['from_address'],
        'help_email_address': config.HELP_EMAIL_ADDRESS,
        'site': site,
        'current_site': site})
    context = Context(context)
    LOG.debug('sending to %s' % recipient_email)
    text_content, html_content = render_template(template, context)
    # Now that we have rendered templates, reset the urlconf.
    urlresolvers.set_urlconf(initial_urlconf)
    message = CustomEmailMultiAlternative(subject=context['subject'], 
        body=text_content, from_email=bounce_address, to=[recipient_email],
        headers=context['headers'])
    message.attach_alternative(html_content, "text/html")
    return message
