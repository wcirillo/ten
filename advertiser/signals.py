""" Signals for models of advertiser app """
#pylint: disable=W0613
import logging

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def business_categories_callback(sender, instance, **kwargs):
    """ Receive signal that the categories of a business have changed. """
    LOG.debug('business_categories_callback signal called')
    instance.index_coupons()
