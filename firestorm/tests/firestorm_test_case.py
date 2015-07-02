""" A TestCase for many unit tests of the Firestorm app. """
#pylint: disable=C0103
from django.test import TestCase
from django.test import TransactionTestCase

from firestorm import soap


class FirestormTestCase(TestCase):
    """ Add setup and teardown methods to derived class. """

    ad_rep_repl_website_fields = ['status', 'first_name', 'last_name',
        'company', 'home_phone_number', 'primary_phone_number', 'web_greeting',
        'rank']

    @classmethod
    def setUpClass(cls):
        cls.original_mode = soap.TEST_MODE
        soap.TEST_MODE = True
        super(FirestormTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """ Revert TEST_MODE to original value. """
        soap.TEST_MODE = cls.original_mode
        super(FirestormTestCase, cls).tearDownClass()


class FirestormTransactionTestCase(TransactionTestCase):
    """ Add setup and teardown methods to derived class. """

    ad_rep_repl_website_fields = ['status', 'first_name', 'last_name',
        'company', 'home_phone_number', 'primary_phone_number', 'web_greeting',
        'rank']

    @classmethod
    def setUpClass(cls):
        cls.original_mode = soap.TEST_MODE
        soap.TEST_MODE = True
        super(FirestormTransactionTestCase, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        """ Revert TEST_MODE to original value. """
        soap.TEST_MODE = cls.original_mode
        super(FirestormTransactionTestCase, cls).tearDownClass()