""" Signals for firestorm app of project ten. """
#pylint: disable=W0404, W0613
import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from firestorm.models import AdRep, AdRepOrder

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

@receiver(post_save, sender=AdRep)
def send_enrollment_email_callback(sender, instance, created, **kwargs):
    """ Callback function for sending enrollment email after an ad_rep has been
    created on model save.
    """
    from firestorm.tasks import SEND_ENROLLMENT_EMAIL
    LOG.debug("Signal Send Enrollment Email")
    LOG.debug("RANK = %s" % instance.rank)
    if created and instance.id and instance.rank != 'CUSTOMER':
        SEND_ENROLLMENT_EMAIL(instance.id)

@receiver(post_save, sender=AdRepOrder)
def ad_rep_order_callback(sender, instance, created, **kwargs):
    """ Callback function for running tasks after an ad_rep_order has been
    saved.
    """
    from firestorm.tasks import SAVE_FIRESTORM_ORDER, AD_REP_COMPENSATION_TASK

    if created:
        AD_REP_COMPENSATION_TASK.delay(instance.id)
    SAVE_FIRESTORM_ORDER.delay(instance)
