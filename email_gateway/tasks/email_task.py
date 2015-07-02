""" Class for sending email tasks for project ten. """
#pylint: disable=R0921
from datetime import datetime, timedelta
import logging

from django.conf import settings

from celery.task import Task

from consumer.service import get_site_rep
from email_gateway.context_processors import get_rep_context
from logger.service import get_last_db_log, log_db_entry

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)


class EmailTask(Task):
    """ A class for housing common methods for email tasks for project ten. """

    test_mode = False
    start_datetime = None
    end_datetime = None

    @classmethod
    def get_task_name(cls):
        """ Subclasses must override this method and return a custom name;
        used by get_task_date_range.

        Example:
        return cls.__name__
        """
        raise NotImplementedError

    def get_to_email(self, business):
        """ Return to_email based on test mode. """
        if self.test_mode:
            to_email = [self.test_mode]
        else:
            to_email = [business.advertiser.email]
        return to_email

    @staticmethod
    def update_context_for_ad_rep(context, site, to_email, cc_rep=False):
        """ Get ad_rep or sales rep info for context. """
        context.update(get_rep_context(site, to_email[0], cc_rep=cc_rep))
        context.update({'friendly_from': '%s at %s' %
            (context['rep_first_name'], site.domain)})
        return

    @staticmethod
    def update_context_for_sales_rep(context, site):
        """ Add additional sales_rep context. This is used when an email is
        going to an ad_rep, to sign that email.
        """
        sales_rep = get_site_rep(site)
        context.update({
            'sales_rep_first_name': sales_rep.consumer.first_name,
            'sales_rep_signature_name': "%s %s" % (
                sales_rep.consumer.first_name,
                sales_rep.consumer.last_name),
            'sales_rep_signature_title': sales_rep.title,
            'sales_rep_signature_email': "%s@%s" % (
                sales_rep.consumer.first_name,
                sales_rep.email_domain),
            'sales_rep_signature_phone': "%s ext %s" % (
                settings.MAIN_NUMBER,
                sales_rep.extension),
            'is_to_ad_rep': True})
        return

    def get_task_date_range(self, days_past, **kwargs):
        """ For the email task, get the query date range. Typically, if a task 
        is run daily, this will return today and tomorrow dates. If a task
        doesn't run, then the missed days are accounted for in the from_date.
        """
        task_status = kwargs.get('task_status', 'EMAIL')
        get_missed_days = kwargs.get('get_missed_days', True)
        max_days = kwargs.get('max_days', 5)
        run_date = datetime.now().date() - timedelta(days=days_past)
        LOG.debug('run_date: %s' % run_date)
        LOG.debug('task: %s' % self.get_task_name())
        last_log = get_last_db_log(self.get_task_name(), task_status)
        now = datetime.now()
        missed_days = 0
        if get_missed_days and last_log:
            missed_days = (now - last_log.execution_date_time).days
            if missed_days > max_days:
                missed_days = max_days
        LOG.debug('missed_days: %s' % missed_days)
        to_date = run_date + timedelta(days=1)
        from_date = run_date - timedelta(days=missed_days)
        LOG.debug('return from_date: %s, to_date: %s' % (from_date, to_date))
        return from_date, to_date

    def has_task_run_today(self, status='EMAIL', rerun=False):
        """ Return True if this task ran today. """
        today = datetime.today().date()
        last_log = get_last_db_log(self.get_task_name(), status)
        if (last_log and last_log.execution_date_time.date() == today
            and rerun is False):
            LOG.info('%s already ran today, aborted.' % self.get_task_name())
            log_db_entry(self.get_task_name(), 'ABORT', {'last_run': today})
            return True
        return False
