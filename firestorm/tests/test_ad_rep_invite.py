""" Unit tests for AdRepInviteTask. """
import datetime
import logging

from django.core import mail

from common.test_utils import EnhancedTestCase
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.factories.ad_rep_lead_factory import AD_REP_LEAD_FACTORY
from firestorm.tasks.ad_rep_invite import AD_REP_INVITE_TASK

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestAdRepInviteTask(EnhancedTestCase):
    """ Test case for AdRepInviteTask. """

    def test_email_good(self):
        """ Assert ad rep leads created yesterday receive an invite email.
        """
        ad_rep_leads = list(
            AD_REP_LEAD_FACTORY.create_ad_rep_leads(create_count=2))
        for ad_rep_lead in ad_rep_leads:
            ad_rep_lead.create_datetime -= datetime.timedelta(1)
            ad_rep_lead.save()
        AD_REP_INVITE_TASK.run()
        self.assertEqual(len(mail.outbox), 2)
        ad_rep_lead_1_found = False
        ad_rep_lead_2_found = False
        for email in mail.outbox:
            if ad_rep_leads[0].first_name in email.alternatives[0][0]:
                ad_rep_lead_1_found = True
                self.assertTrue(ad_rep_leads[0].first_name in email.body)
            elif ad_rep_leads[1].first_name in email.alternatives[0][0]:
                ad_rep_lead_2_found = True
                self.assertTrue(ad_rep_leads[1].first_name in email.body)
        self.assertTrue(ad_rep_lead_1_found and ad_rep_lead_2_found)

    def test_ad_rep_signature(self):
        """ Assert the referring ad rep of a lead is included in the signature.
        """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        ad_rep_lead.ad_rep = AD_REP_FACTORY.create_ad_rep()
        ad_rep_lead.save()
        mail_prior = len(mail.outbox)
        AD_REP_INVITE_TASK.run(test_mode=[ad_rep_lead])
        LOG.debug(mail.outbox[mail_prior].alternatives[0][0])
        LOG.debug(mail.outbox[mail_prior].body)
        self.assertEqual(len(mail.outbox), mail_prior + 1)
        self.assertTrue(ad_rep_lead.ad_rep.first_name in
            mail.outbox[mail_prior].alternatives[0][0])
        self.assertTrue(ad_rep_lead.ad_rep.last_name in
            mail.outbox[mail_prior].alternatives[0][0])
        self.assertTrue(ad_rep_lead.ad_rep.email in
            mail.outbox[mail_prior].alternatives[0][0])
        self.assertTrue(ad_rep_lead.ad_rep.url in
            mail.outbox[mail_prior].alternatives[0][0])
        self.assertTrue(ad_rep_lead.ad_rep.first_name in
            mail.outbox[mail_prior].body)
        self.assertTrue(ad_rep_lead.ad_rep.last_name in
            mail.outbox[mail_prior].body)
        self.assertTrue(ad_rep_lead.ad_rep.email in
            mail.outbox[mail_prior].body)
        self.assertTrue(ad_rep_lead.ad_rep.url in mail.outbox[mail_prior].body)
        
    def test_email_task_already_ran(self):
        """ Assert task will not run twice on the same day (without rerun flag)
        """
        ad_rep_lead = AD_REP_LEAD_FACTORY.create_ad_rep_lead()
        self.assertEqual(len(mail.outbox), 0)
        AD_REP_INVITE_TASK.run(test_mode=[ad_rep_lead])
        self.assertEqual(len(mail.outbox), 1)
        # Run again.
        result = AD_REP_INVITE_TASK.run(test_mode=[ad_rep_lead])
        self.assertEqual(result, 
            'Aborted:: AdRepInviteTask already ran today')
