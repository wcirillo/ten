""" Tests for models of consumer app. """

from django.core.exceptions import ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.test import TestCase, TransactionTestCase

from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from geolocation.models import USZip
from market.models import Site
from subscriber.models import MobilePhone


class TestModels(TestCase):
    """ Tests for consumer model of consumer app. """
    fixtures = ['test_geolocation']
    
    def test_create_consumer_normal(self):
        """ Assert user with a typically sized email address is created. """
        site = Site.objects.get(id=1)
        try:
            consumer = Consumer.objects.create_consumer(
                username='normal@example.com', email='normal@example.com',
                consumer_zip_postal='00000', site=site)
        except IntegrityError:
            self.fail('Valid consumer not created.')
        # Username is email.
        self.assertTrue(consumer.username == 'normal@example.com')    
        # Try and create another consumer with same email.
        with self.assertRaises(ValidationError):
            Consumer.objects.create_consumer(
                username='abnormal@example.com', email='normal@example.com',
                consumer_zip_postal='00000', site=site)

    def test_create_consumer_local(self):
        """ Assert a consumer with zip 12601 is related to site 2. """
        email = 'create_consumer_local@example.com'
        # Pass in a local zip, and no site.
        code = '12550'
        us_zip = USZip.objects.get(code=code)
        try:
            consumer = Consumer.objects.create_consumer(username=email, 
                email=email, consumer_zip_postal=code, site=None)
        except IntegrityError as error:
            self.fail(error)
        # Username needed to become guid to fit.
        self.assertTrue(consumer.username != email)
        consumer = Consumer.objects.get(email=email)
        self.assertEquals(consumer.site.id, 2)
        self.assertEquals(consumer.geolocation_object, us_zip)
        # Change consumer_zip_postal and check for new GenericForeignKey.
        code = '12601'
        us_zip = USZip.objects.get(code=code)
        consumer.consumer_zip_postal = code
        consumer.save()
        consumer = Consumer.objects.get(email=email)
        self.assertEquals(consumer.geolocation_object, us_zip)
        
    def test_delete_subscriber(self):
        """ Delete a subscriber that has a consumer and assert the consumer is 
        not dropped.
        """
        consumer = CONSUMER_FACTORY.create_consumer()
        CONSUMER_FACTORY.qualify_consumer(consumer)
        mobile_phone = consumer.subscriber.mobile_phones.all()[0]
        consumer.subscriber.delete()
        with self.assertRaises(MobilePhone.DoesNotExist):
            MobilePhone.objects.get(id=mobile_phone.id)
        try:
            consumer = Consumer.objects.get(id=consumer.id)
        except Consumer.DoesNotExist:
            self.fail('Retain Consumer when subscriber is deleted!')
        self.assertEqual(consumer.subscriber, None)


class TestModelsTransaction(TransactionTestCase):
    """ Tests for consumer model requiring a transaction. """

    def test_create_consumer_very_long(self):
        """ Assert email address of 1000 characters is not allowed. """
        too_long_email = 'thisistool%sng@example.com' % ('o'*1000)
        consumer_zip_postal = '00000'
        site = Site.objects.get(id=1)
        with self.assertRaises(DatabaseError):
            Consumer.objects.create_consumer(username=too_long_email,
                email=too_long_email, consumer_zip_postal=consumer_zip_postal,
                site=site)
        transaction.rollback()

    def test_create_consumer_max(self):
        """ Assert email address longer that 30 chars is allowed. """
        max_email = 'thisismaxlenlimit%s@example.com' % ('x'*44)
        consumer_zip_postal = '00000'
        site = Site.objects.get(id=1)
        try:
            consumer = Consumer.objects.create_consumer(username=max_email,
                email=max_email, consumer_zip_postal=consumer_zip_postal,
                site=site)
        except DatabaseError:
            transaction.rollback()
            self.fail('Consumer not created.')
        # Username needed to become guid to fit.
        self.assertTrue(consumer.username != max_email)
        # Deleting turns a consumer inactive.
        self.assertTrue(consumer.is_active)
        consumer.delete()
        consumer = Consumer.objects.get(email=max_email)
        self.assertTrue(consumer.is_active == False)
