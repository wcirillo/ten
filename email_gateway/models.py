""" Models of the email_gateway app for project ten. """
import datetime
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

SEND_STATUS_CHOICES = (
       (0, _('Draft')),
       (1, _('Send Now!')),
       (2, _('Sent Successfully')),
       (3, _('Sent with Errors')),
   )


class Email(models.Model):
    """ An email for sending to a group of users. """
    subject = models.CharField('subject',
        max_length=120)
    message = models.TextField(_('message'))
    email_subscription = models.ForeignKey('consumer.EmailSubscription',
        related_name='emails', default=6)
    user_type = models.ForeignKey(ContentType,
        limit_choices_to={"model__in": ("adrep",)},
        help_text=_("To which type of user will this be sent?"))
    draft_email = models.EmailField(blank=True,
        help_text=_('To which email address should a draft be sent?'))
    create_datetime = models.DateTimeField('Created',
        default=datetime.datetime.now)
    send_datetime = models.DateTimeField('Sent', blank=True, null=True)
    send_status = models.IntegerField(max_length=1, default=0,
        choices=SEND_STATUS_CHOICES,
        help_text=_('Choose "Send Now!" to send this message.'))
    num_recipients = models.IntegerField(default=-1,
        help_text=_('To how many addresses was this email sent?'))

    def __unicode__(self):
        return u'%s' % (self.subject)

    class Meta:
        ordering = ['-create_datetime']
        verbose_name = 'Email'
        verbose_name_plural = 'Email'

    def check_has_been_sent(self):
        """ Raise an error if this email has already been sent. """
        if self.id:
            original = Email.objects.get(id=self.id)
            if original.send_status > 1:
                raise ValidationError(
                    'Cannot modify an email that has already been sent.')

    def clean(self):
        self.check_has_been_sent()
        if self.user_type.model != 'adrep':
            raise ValidationError(
                'Currently only sending to ad reps is supported.')
        if self.email_subscription_id != 6:
            raise ValidationError(
                "Currently only sending to the list 'Meeting Reminders' is supported.")

    def save(self, *args, **kwargs):
        from email_gateway.send import send_email
        from firestorm.models import AdRep

        self.check_has_been_sent()
        context = {
            'to_email': [self.draft_email],
            'subject': self.subject,
            'message': self.message,
            'mailing_list': [self.email_subscription_id]}
        if self.send_status == 0 and self.draft_email:
            context['to_email'] = [self.draft_email]
            send_email('firestorm_base_from_admin', Site.objects.get(id=1),
                context)
        if self.send_status == 1:
            # Begin sending to ad reps.
            ad_rep_emails = list(AdRep.objects
                .exclude(rank='CUSTOMER')
                .filter(is_emailable=True,
                    email_subscription__id=self.email_subscription_id)
                .values_list('email', flat=True))
            context['to_email'] = ad_rep_emails
            LOG.debug('Now sending to %s' % ad_rep_emails)
            send_email('firestorm_base_from_admin', Site.objects.get(id=1),
                context)
            self.send_status = 2
            self.num_recipients = len(ad_rep_emails)
            self.send_datetime = datetime.datetime.now()
        super(Email, self).save(*args, **kwargs)
