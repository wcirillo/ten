"""
Common service class of project ten specific to django.core.signing.

signing is added to django.core in django 1.4 (alpha), Since our 3rd party apps
are not compliant with django 1.4, the module has been manually brought into
this project.
"""

import logging

#from django.core import signing
from common.from_django14 import signing

from consumer.models import Consumer
from common.session import build_session_from_user

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

# Hardcoded SALT value so it is constant through future structural changes.
SALT = 'common.service.payload_signing'


class PayloadSigning(object):
    """ Class containing methods to utilize payloads. """

    @staticmethod
    def create_payload(**kwargs):
        """ Build a cryptographically signed payload for inclusion in emails. 
        This is for use with @check_user.
        Kwargs can sign any number of key/value pairs into the payload. The 
        following are known to be used:
            email,
            subscription_list
        subscription_list is a list of email subscription ids to unsubscribe 
        the user from.
        """
        return signing.dumps(kwargs, salt=SALT, compress=True)

    @staticmethod
    def parse_payload(payload):
        """ Return value_dict as the signed contents of payload. """
        try:
            value_dict = signing.loads(payload, salt=SALT)
        except signing.BadSignature:
            # Try the deprecated SALT:
            DEPRECATED_SALT = 'common.signing_utils'
            try:
                value_dict = signing.loads(payload, salt=DEPRECATED_SALT)
            except signing.BadSignature:
                value_dict = {}
                LOG.error('Invalid payload detected.')
        return value_dict

    def handle_payload(self, request, payload, **kwargs):
        """ Check for a signed payload; if it exists, put the user in session 
        and check to see if the user is verified and if not update as verified.
        """ 
        value_dict = self.parse_payload(payload)
        try:
            consumer = Consumer.objects.get(email=value_dict['email'])
            if not consumer.is_email_verified:
                consumer.is_email_verified = True
                consumer.save()
            if kwargs.get('opting', False):
                consumer.email_subscription.add(1)
            build_session_from_user(request, consumer)
        except (Consumer.DoesNotExist, KeyError):
            pass
        return value_dict

PAYLOAD_SIGNING = PayloadSigning()
