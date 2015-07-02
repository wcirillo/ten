""" Unit tests for Email model of email_gateway app of project ten. """

from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.exceptions import ValidationError

from common.test_utils import EnhancedTestCase
from email_gateway.models import Email
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY


class TestEmailModel(EnhancedTestCase):
    """ Test case for the Email model. """

    def test_draft_email_sent(self):
        """ Assert a draft multi-part email is sent. """
        email = Email.objects.create(
            subject='draft',
            message='<p>random message</p>',
            draft_email='test-draft@example.com',
            user_type=ContentType.objects.get(model='adrep')
            )
        self.assertEqual(len(mail.outbox), 1)
        self.assertTrue('<p>random message</p>' in
            mail.outbox[0].alternatives[0][0])
        self.assertFalse('<p>random message</p>' in mail.outbox[0].body)
        self.assertTrue('random message' in mail.outbox[0].body)
        self.assertEqual(email.send_status, 0)
        self.assertEqual(email.num_recipients, -1)

    def test_email_sent(self):
        """ Assert an email is delivered to two ad reps. """
        AD_REP_FACTORY.create_ad_reps(create_count=2)
        mail_prior = len(mail.outbox)
        Email.objects.create(
            subject='send now',
            message='this',
            send_status=1,
            user_type=ContentType.objects.get(model='adrep')
            )
        self.assertEqual(len(mail.outbox), mail_prior + 2)

    def test_resend_not_allowed(self):
        """ Assert an email that has already been sent cannot be resent. """
        email = Email.objects.create(
            subject='draft',
            message='<p>message</p>',
            draft_email='test-draft@example.com',
            send_status=1,
            user_type=ContentType.objects.get(model='adrep')
            )
        email = Email.objects.get(id=email.id)
        with self.assertRaises(ValidationError):
            email.save()
