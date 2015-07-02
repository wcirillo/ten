"""
Processing functions related to email, be it incoming, outgoing or internal.
"""

import logging

from advertiser.models import Advertiser
from media_partner.models import MediaPartner
from firestorm.models import AdRep, AdRepLead
from email_gateway.send import send_admin_email



LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

def stupid_spam_complainers_check(consumer, email_type):
    """
    Checks a consumer object against important user types and sends up a flare
    if the user in question is someone who works for us or somesuch.
    """
    
    def send_alarm(user_type, to_email='eric@10coupons.com'):
        """ Sends an alert email about the stupid complainer """

        if user_type[0] in 'AEIOU':
            article = "an"
        else:
            article = 'a'
        context = { 'to_email': [to_email],
        'subject': 'ID 10 T email spam issue... %s ' % to_email, 
        'admin_data': ['%s ( %s %s ) marked a %s email as spam.' % 
            (consumer.email, article, user_type, email_type),
            'Please talk some sense into them'],
        }
        LOG.debug("sending admin email")
        send_admin_email(context=context)
        
    try:
        LOG.debug("checking if mediapartner")
        if consumer.mediapartner:
            send_alarm("MediaPartner", 'ckniffin@10coupons.com')
            return "MediaPartner"
    except MediaPartner.DoesNotExist:
        pass
    try:
        LOG.debug("checking if adrep")
        if consumer.adrep:
            send_alarm("AdRep")
            return "AdRep"
    except AdRep.DoesNotExist:
        pass
        
    try:
        LOG.debug("checking if advertiser")
        if consumer.advertiser:
            send_alarm("Advertiser")
            return "Advertiser"
    except Advertiser.DoesNotExist:
        pass
    try:
        LOG.debug("checking if adreplead")
        if consumer.adreplead:
            return "AdRepLead"
    except AdRepLead.DoesNotExist:
        pass

    return
