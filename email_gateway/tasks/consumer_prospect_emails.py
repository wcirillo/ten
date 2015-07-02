""" Consumer Prospect Email task for email_gateway. """
from datetime import datetime, time, timedelta
import logging

from django.conf import settings
from celery.task import Task
from djcelery.models import TaskState

from common.utils import generate_email_hash
from email_gateway.send import send_email, send_admin_email
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

class ConsumerProspectEmailTask(Task):
    """ Task for sending emails to consumers signed up between a given date 
    and today.
    """
    @classmethod
    def run(cls, date_string=None, test_mode=False, rerun=False):
        """Send Eric's "X+1" or "Letter from the president" prospecting emails.
        Cycle through each site, grab eligible consumers signed up between a 
        given date and today, and send email with their IDs.
        """
        try:
            last_run = TaskState.objects.filter(name=
                'email_gateway.tasks.send_consumer_prospect_emails')[0].tstamp
            if last_run.date() == datetime.today().date() and not rerun:
                return "already ran today"
        except IndexError:
            last_run = datetime.today() - timedelta(days=1)
        # First moment of today.
        today = datetime.combine(datetime.today(), time())
        reg_date = last_run.date()
        if date_string == 'now':
            today = datetime.today()
            reg_date = datetime.combine(datetime.today(), time())
        elif date_string:
            LOG.info('X+1 - Submitted Date String - %s' % (date_string))
            reg_date = datetime.combine(datetime.date(date_string), 
                time())
            
        admin_data = []
        total = 0
        for site in Site.objects.all():
            LOG.debug('Doing %s' % site.name)
            recipients = site.consumers.filter(
                consumer_create_datetime__gt=reg_date,
                consumer_create_datetime__lt=today,
                is_active=True,
                email_subscription=1,
                is_emailable=True,
                adrep=None,
                advertiser=None,
                adreplead=None)
            emails_and_attrs = recipients.exclude(
                    email__contains="@yahoo.com").values_list(
                    'email', 'ad_rep_consumer__ad_rep__url')
            LOG.debug('to do %s consumers.' % len(emails_and_attrs))
            if emails_and_attrs:
                total = total + len(emails_and_attrs)
                if test_mode:
                    LOG.info('testing x+1 email to %d recipients on %s' %
                        (len(emails_and_attrs), site.domain))
                    admin_data.append('%s -- %d recipients -- TEST MODE\n' %
                        (site.domain, len(emails_and_attrs)))
                else:
                    LOG.info('sending x+1 email to %d recipients on %s' %
                        (len(emails_and_attrs), site.domain))
                    admin_data.append('%s -- Sending to %d recipients' %
                        (site.domain, len(emails_and_attrs)))
                for email, ad_rep_url in emails_and_attrs:
                    #admin_data.append('emailing to: %s' % (str(email)))
                    if not test_mode:
                        subject = "A message from the president of %s" \
                            % (site.domain)
                        if ad_rep_url:
                            subject = "Message from the president of %s" % (
                                site.domain)                          
                        
                        send_email(template='consumer_prospects',
                            site=site,
                            context={
                            'to_email': str(email),
                            'subject': subject,
                            'ad_rep_url': ad_rep_url,
                            'from_address': 'Eric@10Coupons.com',
                            'friendly_from': 'Eric Straus',
                            'bouncing_checked': True,
                            'show_unsubscribe': False,
                            'mailing_list': [4],
                            'ref_num': email,
                            'headers': {'X-10LC-Hash': 
                                generate_email_hash(email, 'email')
                                },
                            }
                            )
        admin_data.append('Total Recipients for %s :  %d' 
            % (reg_date, total))
        subject = "X+1 sent to %d consumers who registered on %s, sent %s" % (
            total, reg_date, datetime.now())
        send_admin_email(context={
            'to_email': settings.NOTIFY_CONSUMER_PROSPECTS_REPORT,
            'subject': subject,
            'admin_data': admin_data})