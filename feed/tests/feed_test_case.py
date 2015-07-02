""" A TestCase for many unit tests of the Feed app. """

from common.test_utils import EnhancedTestCase
from feed import config


class FeedTestCase(EnhancedTestCase):
    """ Add setup and teardown methods to derived class. """
    
    def setUp(self):
        """ Set TEST_MODE from config. """
        self.original_mode = config.TEST_MODE
        config.TEST_MODE = True
    
    def tearDown(self):
        """ Reset TEST_MODE to original. """
        config.TEST_MODE = self.original_mode
