""" Tests for admin views of project ten. """
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse, NoReverseMatch

from common.test_utils import EnhancedTestCase
from ecommerce.factories.order_factory import ORDER_FACTORY
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from subscriber.factories.subscriber_factory import SUBSCRIBER_FACTORY

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestAdminViews(EnhancedTestCase):
    """ Tests cases for admin views. """
    # Note the order of these is important:
    fixtures = ['admin-views-users.xml', 'test_promotion',
        'test_twitter_account', 'test_media_partner', 'test_sms_gateway',
        'test_sms_response']

    def setUp(self):
        super(TestAdminViews, self).setUp()
        self.client.login(username='super', password='secret')

    def test_installed_apps(self):
        """ 
        Asserts the admin login page renders. Asserts the model change list and
        change form render for each registered model of an installed app.

        All tests as one so we can load these fixtures exactly once.
        test_sms_response is particularly expensive.
        """
        response = self.client.get(reverse('admin:index'), follow=True)
        self.assertTemplateUsed(response, 'admin/index.html')

        ORDER_FACTORY.create_order()
        AD_REP_FACTORY.create_ad_rep()
        SUBSCRIBER_FACTORY.create_subscriber()

        for app_label in settings.TEN_COUPON_APPS:
            # Skip apps without models.
            if app_label in ('common', 'watchdog'):
                continue
            LOG.debug(app_label)
            try:
                response = self.client.get('/captain/%s/' % app_label)
                self.assertTemplateUsed(response, 'admin/app_index.html')
            except NoReverseMatch:
                continue
            for model in ContentType.objects.filter(app_label=app_label):
                LOG.debug(model)
                try:
                    response = self.client.get(
                        reverse('admin:%s_%s_changelist' %
                            (app_label, model.model)))
                    self.assertTemplateUsed(response, 'admin/change_list.html')
                except NoReverseMatch:
                    LOG.debug('No instances of %s' % model)
                    continue
                # Skip apps where add is disallowed.
                if app_label in ('firestorm',):
                    continue
                response = self.client.get(
                    reverse('admin:%s_%s_add' %  (app_label, model.model)))
                self.assertTemplateUsed(response, 'admin/change_form.html')
