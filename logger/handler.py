""" Logger handlers to use for logging. """
import logging

class DatabaseHandler(logging.Handler):
    """ Handler for saving log entries to database table LogHistory. """
    def emit(self, record):
        try:
            from logger.models import LogHistory
            record_dict = {
            'logger' : record.msg['logger'],
            'status' : record.msg['status'],
            'detail_dict' : record.msg['detail_dict']}
            if record.msg['execution_date_time']:
                record_dict.update(
                    {'execution_date_time': record.msg['execution_date_time']})
            LogHistory.objects.create(**record_dict)
        except KeyError:
            # Invalid log call, abort.
            pass