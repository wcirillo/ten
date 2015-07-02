""" Class to run task to add or update existing ad rep."""
import logging

from celery.task import Task

from common.custom_cleaning import clean_phone_number
from consumer.models import Consumer
from firestorm.models import AdRep, AdRepWebGreeting, AdRepLead
from firestorm.soap import FirestormSoap
from firestorm.tasks.email_tasks import (NOTIFY_NEW_RECRUIT, 
    SEND_ENROLLMENT_EMAIL)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class CreateOrUpdateAdRep(Task):
    """ Task that creates or updates an AdRep from a dict of replicated website 
    details.
    """
    accept_magic_kwargs = False
    
    @staticmethod
    def run(ad_rep_dict):
        """ Create or update an AdRep from a dict of replicated website details.
        """
        if ad_rep_dict['email']:
            for field in ['home_phone_number', 'primary_phone_number']:
                ad_rep_dict[field] = clean_phone_number(ad_rep_dict[field])
            try:
                ad_rep = AdRep.objects.get(email=ad_rep_dict['email'])
                ad_rep.username = ad_rep_dict['email']
                for field in ['first_name', 'last_name', 'url', 'company',
                        'home_phone_number', 'primary_phone_number', 'rank']:
                    setattr(ad_rep, field, ad_rep_dict[field])
                ad_rep.parent_ad_rep = ad_rep_dict.get('parent_ad_rep')
                ad_rep.save()
            except AdRep.DoesNotExist:
                try:
                    # Already have a consumer with this email address.
                    consumer_id = Consumer.objects.values_list(
                        'id', flat=True).get(email__iexact=ad_rep_dict['email'])
                    try:
                        AdRepLead.objects.get(id=consumer_id)
                        ad_rep = AdRep.objects.create_ad_rep_from_ad_rep_lead(
                            consumer_id, ad_rep_dict)
                    except AdRepLead.DoesNotExist:
                        ad_rep = AdRep.objects.create_ad_rep_from_consumer(
                            consumer_id, ad_rep_dict)
                    # Need to send the enrollment email explicitly, since the
                    # ad_rep.save() method was not called.
                    ad_rep.rank = ad_rep_dict['rank']
                    ad_rep.save()
                    if ad_rep_dict['rank'] != 'CUSTOMER':
                        SEND_ENROLLMENT_EMAIL.run(ad_rep.id)
                        NOTIFY_NEW_RECRUIT.run(ad_rep.id)
                except Consumer.DoesNotExist:
                    # Need at minimum the fields that make this ad rep unique,
                    # for promotion creation in SEND_ENROLLMENT_EMAIL
                    ad_rep = AdRep.objects.create(username=ad_rep_dict['email'], 
                        email=ad_rep_dict['email'], 
                        first_name=ad_rep_dict['first_name'],
                        last_name=ad_rep_dict['last_name'],
                        url=ad_rep_dict['url'],
                        company=ad_rep_dict['company'],
                        home_phone_number=ad_rep_dict['home_phone_number'],
                        primary_phone_number=ad_rep_dict['primary_phone_number'],
                        rank=ad_rep_dict['rank'],
                        )
                    ad_rep.email_subscription.add(1)
            web_greeting_ = ad_rep_dict.get('web_greeting', '').strip()
            if web_greeting_:
                try:
                    web_greeting = AdRepWebGreeting.objects.get(ad_rep=ad_rep)
                    web_greeting.web_greeting = web_greeting_
                    web_greeting.save()
                except AdRepWebGreeting.DoesNotExist:
                    AdRepWebGreeting.objects.create(ad_rep=ad_rep,
                        web_greeting=web_greeting_)
        return
        
CREATE_OR_UPDATE_AD_REP = CreateOrUpdateAdRep()
