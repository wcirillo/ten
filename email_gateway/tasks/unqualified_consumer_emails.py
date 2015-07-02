""" Task to send unqualified consumer emails. """
from datetime import datetime, timedelta
import logging

from celery.task import Task
from django.conf import settings

from advertiser.models import Advertiser
from common.contest import check_contest_is_running
from common.utils import generate_email_hash
from consumer.models import Consumer
from consumer.service import qry_qualified_consumers
from email_gateway.context_processors import get_rep_context
from email_gateway.send import send_email
from logger.service import get_last_db_log, log_db_entry
from market.models import Site
from subscriber.models import MobilePhone

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class UnqualifiedConsumerEmailTask(Task):
    """ Class to define task that sends unqualified consumer an email trying to
    persuade them to fully qualify.
    """
    @classmethod
    def qry_unqualified_consumers(cls, from_date, to_date):
        """ Get all consumers that have registered after from_date and before or 
        on the to_date, but are not fully qualified (email not verified, no 
        subscriber, phone not verified, but are opted in to receive Email Flyer).
        """
        return Consumer.objects.exclude(id__in=qry_qualified_consumers()
                ).filter(consumer_create_datetime__range=(from_date, to_date),
                email_subscription__id=1, is_emailable=True).exclude(
                    groups__name__in=['advertisers__do_not_market'])

    @classmethod
    def run(cls, test_mode=False):
        """  Send "X + 3" emails to unqualified consumers (consumers that have 
        signed up but are not yet bonus-pool or content eligible) three days 
        after they have registered to complete their requirements.
    
        Cycle through each site, grab ineligible consumers signed up between the
        last run date and 3 days ago and send email with their IDs. Process will 
        run daily, so except for issues, this will only send to consumers that 
        registered 3 days earlier.
        """
        _task = {}
        _task.update({'name': 'email_gateway.tasks.send_unqualified_emails',
            'reg_date' : datetime.now().date()- timedelta(days=3)})
        last_log = get_last_db_log(_task['name'], 'EMAIL')
        if not last_log: # Default to 3 months.
            _task['last_run'] = datetime.now().date()- timedelta(days=87)
        else:
            _task['last_run'] = last_log.execution_date_time.date()
        if _task['last_run'] == datetime.today().date():
            LOG.info('%s already ran today, aborted.' % _task['name'])
            log_db_entry(_task['name'], 'ABORT', 
                {'last_run': _task['last_run']})
            return "Already ran today"
        elif not check_contest_is_running():
            LOG.info('%s Contest is no longer running, Aborted.' 
                % _task['name'])
            log_db_entry(_task['name'], 'ABORT',
                {'last_run': _task['last_run']})
            return "Contest is no longer running, Aborted"
        # Query consumers signed up between (last run - 4 days) 
        # and (today - 2 days).
        cut_off = _task['last_run'] - timedelta(days=3)
        _task['description'] = '%s %s %s and up to and including %s:' \
            % (_task['name'], 'start for consumers registered after', 
            cut_off, _task['reg_date'])
        LOG.info(_task['description'])
        summary_data = {}
        grand_total = 0
        consumers = cls.qry_unqualified_consumers(from_date=cut_off, 
                        to_date=_task['reg_date']+timedelta(days=1))
        subject = "Are you ready to win $10,000?"
        if test_mode: # Only process this consumer.
            consumers = consumers.filter(id=test_mode.id)
            _task['status'] = 'TESTMODE'
        else:
            _task['status'] = 'EMAIL'
        log_db_entry(_task['name'], _task['status'], 
               {'last_run': _task['last_run']})
        for consumer in consumers:
            context = {}
            summary_data[consumer.site] = summary_data.get(consumer.site, 0) + 1
            grand_total += 1
            instance_filter = None
            if Advertiser.objects.filter(id=consumer.id).exists():
                instance_filter = 'advertiser'
            try:
                phone = MobilePhone.objects.filter(
                    subscriber=consumer.subscriber, is_verified=True)[0]
            except IndexError:
                phone = MobilePhone()
            # Get sales rep info and add it into the context.
            context.update(get_rep_context(consumer.site, 
                consumer.email, instance_filter, cc_rep=True))
            context.update({
                'to_email': str(consumer.email),
                'display_all_recipients': True,
                'consumer': consumer,
                'subject': subject,
                'friendly_from': '%s at %s' %
                    (context['rep_first_name'], consumer.site.domain),
                'bouncing_checked': True,
                'show_unsubscribe': True,
                'mailing_list': [4],
                'ref_num': consumer.email,
                'phone': phone
                })
            context['headers'].update(
                    {'X-10LC-Hash': generate_email_hash(
                        consumer.email, 'email')})
            send_email(template='consumer_unqualified_follow_up',
                    site=consumer.site, context=context)
    
        subject = "%s Follow Up Email Results for %s, sent %s" \
        % ('Unqualified Consumers', _task['reg_date'], datetime.now().date())
        summary = ['X+3 Unqualified Consumer Follow Up Email']
        for key in summary_data:
            summary.append('%s unqualified %s consumers were sent an email.' % 
                (summary_data[key], key.name))
        summary.append('Total emails sent: %s.'
            % grand_total)
        context = {'to_email': settings.NOTIFY_CONSUMER_UNQUALIFIED_REPORT}
        context.update({'summary': summary, 'subject': subject})
        send_email(template='admin_unqualified_report',
            site=Site.objects.get(id=1), context=context)