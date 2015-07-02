""" Tests for tasks for business of an advertiser. """
import logging
import os
import shutil
import time

from django.test import TestCase

from advertiser.business.config import BASE_SNAP_PATH
from advertiser.business.tasks import take_web_snap
from advertiser.models import Business

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestWebSnap(TestCase):
    """ Tests for web snap task. """

    fixtures = ['test_business_tasks']   

    def test_take_web_snap(self):
        """ Assert a web snap and rabbit task via .delay() ."""
        business = Business.objects.get(id=112)
        test_base_snap_path = '%stest' % BASE_SNAP_PATH
        # Cleanup old data before running tests.
        # Delete the test folder and all its contents in the 
        # media/images/web-snap/ directory.
        try:
            shutil.rmtree(test_base_snap_path)
            LOG.debug('Removed old test folder under %s' % BASE_SNAP_PATH)
            LOG.debug('Remove %s' % test_base_snap_path)
        except OSError:
            LOG.debug('Test folder did not exist in %s' % BASE_SNAP_PATH)
            # No test folder to delete atm.       
        try:
            # Create the 'test' folder in the media/images/web-snap/ directory.
            os.mkdir(test_base_snap_path)
            LOG.debug('Test folder created Path = %s' % test_base_snap_path)
        except OSError:
            # Test Directory folder already exists.
            LOG.debug('Test folder exists at Path = %s' % test_base_snap_path)
        base_snap_path = '%s/' % test_base_snap_path
        # Keep this test on a delay. This test should be testing that the
        # web snap is working and that rabbit mq is configured correctly.
        take_web_snap.delay(business, base_snap_path=base_snap_path)
        # Sleep 10 seconds because the snap should take at most 8 seconds before
        # a timeout.
        LOG.debug(
            'Sleeping for 10 seconds while rabbit task runs to snap web shot!')
        time.sleep(10) 
        # Check that a file has been saved to the directory
        self.assertTrue(os.listdir(base_snap_path))
        # Delete the test folder so it doesn't linger around on local machines.
        try:
            shutil.rmtree(test_base_snap_path)
            LOG.debug('Removed old test folder under %s' % BASE_SNAP_PATH)
            LOG.debug('Remove %s' % test_base_snap_path)
        except OSError:
            LOG.debug('Test folder did not exist in %s' % BASE_SNAP_PATH)
            # No test folder to delete atm.
