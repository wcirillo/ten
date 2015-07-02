""" Ad Rep Lead Factory used to help create quick AdRepLead instances for 
tests.
"""
from common.custom_format_for_display import list_as_text
from common.utils import random_string_generator
from firestorm.models import AdRepLead


class AdRepLeadFactory(object):
    """ AdRepLead Factory Class """
    
    @staticmethod
    def _create(**kwargs):
        """ Create a single ad_rep_lead instance. """
        add_subscriptions = kwargs.get('add_subscriptions', [1, 5, 6])
        email = '%s@example.com' % random_string_generator(
            lower_alpha_only=True)
        first_name = 'first_%s' % random_string_generator(string_length=5)
        last_name = 'last_%s' % random_string_generator(string_length=5)
        consumer_zip_postal = random_string_generator(
            string_length=5, numeric_only=True)
        primary_phone_number = random_string_generator(numeric_only=True)
        ad_rep_lead = AdRepLead.objects.create(
            username=email,
            email=email,
            consumer_zip_postal=consumer_zip_postal,
            primary_phone_number=primary_phone_number,
            first_name=first_name,
            last_name=last_name,
            is_emailable=True,
            site_id=2)
        ad_rep_lead.save()
        if add_subscriptions:
            eval('ad_rep_lead.email_subscription.add(%s)' 
                % list_as_text(add_subscriptions, last_=','))
        return ad_rep_lead
    
    def create_ad_rep_lead(self, **kwargs):
        """ Create ONE basic adreplead instance. """
        ad_rep_lead = self._create(**kwargs)
        return ad_rep_lead
       
    def create_ad_rep_leads(self, create_count=1, **kwargs):
        """ Create 1 or more ad_rep_lead and return them in a list. """
        ad_rep_lead_list = []
        while len(ad_rep_lead_list) < create_count:
            ad_rep_lead = self._create(**kwargs)
            ad_rep_lead_list.append(ad_rep_lead)
        return ad_rep_lead_list

AD_REP_LEAD_FACTORY = AdRepLeadFactory()
