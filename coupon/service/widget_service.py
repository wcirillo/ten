""" Support functions for widgets of coupon app. """
import logging
import os
import sys

from django.conf import settings

from email_gateway.send import send_admin_email

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


def check_widget_dir(widget_type, widget_id, create=True):
    """
    Checks for the widget dir that corresponds to the given mode parameters and
    creates it if create is true.  Returns false if widget dir can't be created
    or if create = false and the dir doesn't exist.
    """
    path_name = os.path.join(
        settings.WIDGET_PATH,
        widget_type, 
        str(widget_id)
        )
    LOG.debug("path name = %s" % path_name)
    if os.path.lexists(path_name):
        LOG.debug("exists - returning previous path name")
        return path_name
    else:
        if create is True:
            try:
                os.umask(0)
                os.mkdir(path_name, 0775)
                return path_name
            except OSError:
                LOG.debug("OSERROR: %s " %  sys.exc_info()[1])
                send_admin_email(context={
                    'to_email': [admin[1] for admin in settings.ADMINS], 
                    'subject': 'Widget directory creation error', 
                    'admin_data': ['%s' %  sys.exc_info()[1]]})
                return False
        else:
            LOG.debug("path doesn't exist, and create is set to false")
            return False
