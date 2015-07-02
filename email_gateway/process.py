"""
Processing functions related to email, be it incoming, outgoing or internal.
"""

import logging

from consumer.models import Consumer

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)


def flag_bouncing_email(email, nomail_reason):
    """
    Set the consumer.is_bouncing_email flag to True for a given email address.
    
    Perform other logic (some still to come) about repeat bouncers.
    """
    try:
        consumer = Consumer.objects.get(email=email)
        if consumer.nomail_reason.filter(id__contains=nomail_reason):
            LOG.warning("Consumer %s is reporting problems repeatedly, pls "
                "find out why :: nomail reason %s" % (consumer, nomail_reason))
            consumer.is_emailable = False
            consumer.save()
            return 1
        else:
            consumer.is_emailable = False
            consumer.save()
            consumer.nomail_reason.add(nomail_reason)
            LOG.info("Consumer %s set to bouncing... is_emailable == %s" 
                % (consumer, consumer.is_emailable))
            return 0
    except Consumer.DoesNotExist:
        LOG.warning("'address' doesn't match any consumer! %s" % email)
        return False

def email_hash_decypher(email_hash):
    """
    Account for our standard (len 40) email hash and our newer, obfuscated,
    longer email_hash, where the hash is stored in the middle of a longer
    string, starting at the 6th character.
    """
    length = len(email_hash)
    if length > 40:
        if length < 55:
            email_hash = email_hash[5:45]
        return email_hash
    elif length == 40:
        return email_hash
    else:
        return email_hash
