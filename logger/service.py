""" Service functions for the logger app. """
from ast import literal_eval
import logging

from django.db.models import Q

from logger.models import LogHistory

DB_LOG = logging.getLogger('db_logger.%s' % __name__)

def log_db_entry(name, status, details_dict, entry_date_time=None):
    """ Enter log message in database model LogHistory. """
    record = {}
    record['logger'] = name
    record['status'] = status
    record['detail_dict'] = details_dict
    record['execution_date_time'] = entry_date_time
    DB_LOG.info(record)
    
def get_last_db_log(logger, status=None):
    """ Retrieve the last log entry recorded for a given logger (name). """
    conditional_dict = {}
    if status:
        conditional_dict = {'status': status}
    try:
        record = LogHistory.objects.filter(
            Q(**conditional_dict), logger=logger).latest()
    except LogHistory.DoesNotExist:
        record = None
    else:
        try:
            record.detail_dict = literal_eval(record.detail_dict)
        except (SyntaxError, ValueError):
            record.detail_dict = {'err_msg':'Unexpected EOF while parsing.'}
    return record
