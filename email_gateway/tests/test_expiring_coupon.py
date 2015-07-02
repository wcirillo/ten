""" Unit tests for ExpiringCoupon task of email_gateway app of project ten. """
import datetime
import logging

from django.core import mail
from django.core.urlresolvers import reverse

from common.test_utils import EnhancedTestCase
from coupon.factories.slot_factory import SLOT_FACTORY
from email_gateway.tasks.expiring_coupon import ExpiringCouponTask
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY
from firestorm.models import AdRepAdvertiser

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestExpiringCouponTask(EnhancedTestCase):
    """ Test case for ExpiringCouponTask. """

    fixtures = ['test_sales_rep']

    @staticmethod
    def prep_coupon_in_slot(slot):
        """ Prepare the coupon in this slot by setting the expiration_date to
        ten days from today, and setting the advertiser to opted-in.
        """
        coupon = slot.slot_time_frames.all()[0].coupon
        coupon.expiration_date = (datetime.datetime.today() +
            datetime.timedelta(10))
        coupon.save()
        coupon.offer.business.advertiser.email_subscription.add(2)
        return coupon

    def test_email_sent(self):
        """ Assert an email is sent to an advertiser with a coupon expiring 10
        days from now.
        """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        coupon = self.prep_coupon_in_slot(slot)
        task = ExpiringCouponTask()
        task.run()
        LOG.debug(mail.outbox[0].body)
        LOG.debug(mail.outbox[0].alternatives[0][0])
        self.assertEqual(mail.outbox[0].to, [advertiser.email])
        self.assertTrue('This coupon expires soon' in mail.outbox[0].body)
        self.assertTrue(coupon.offer.headline in mail.outbox[0].body)
        self.assertTrue(reverse('advertiser-account') in mail.outbox[0].body)
        self.assertTrue('Your coupon' in mail.outbox[0].alternatives[0][0])
        self.assertTrue(coupon.offer.headline in
            mail.outbox[0].alternatives[0][0])
        self.assertTrue(reverse('advertiser-account') in
            mail.outbox[0].alternatives[0][0])
        self.assertEqual(mail.outbox[1].to, task.get_bcc_list())

    def test_multiple_expiring_coupons(self):
        """ Assert an advertiser with multiple expiring coupons receives email
        containing each.
        """
        slot_list = SLOT_FACTORY.create_slot_family(create_count=2)[1]
        for slot in slot_list:
            self.prep_coupon_in_slot(slot)
        task = ExpiringCouponTask()
        task.run()
        LOG.debug(mail.outbox[0].body)
        LOG.debug(mail.outbox[0].alternatives[0][0])
        self.assertTrue('These coupons expire soon' in mail.outbox[0].body)
        self.assertTrue('These coupons expire soon' in
            mail.outbox[0].alternatives[0][0])

    def test_ad_rep_version(self):
        """ Assert a referring ad_rep receives a copy of the email. """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        self.prep_coupon_in_slot(slot)
        AdRepAdvertiser.objects.create(ad_rep=ad_rep, advertiser=advertiser)
        mail_prior = len(mail.outbox)
        task = ExpiringCouponTask()
        task.run()
        LOG.debug(mail.outbox[mail_prior + 1].body)
        LOG.debug(mail.outbox[mail_prior + 1].alternatives[0][0])
        self.assertEqual(mail.outbox[mail_prior + 1].extra_headers['From'],
            'Reputable at 10HudsonValleyCoupons.com <Coupons@10Coupons.com>')
        self.assertTrue('Below is a message sent on your behalf.'
            in mail.outbox[mail_prior + 1].body)
        self.assertTrue('Below is an email sent on your behalf.'
            in mail.outbox[mail_prior + 1].alternatives[0][0])

    def test_ad_rep_no_location(self):
        """ Assert a referring ad_rep version for a coupon without a location.
        """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        coupon = self.prep_coupon_in_slot(slot)
        coupon.location.all().delete()
        AdRepAdvertiser.objects.create(ad_rep=ad_rep, advertiser=advertiser)
        mail_prior = len(mail.outbox)
        task = ExpiringCouponTask()
        task.run()
        LOG.debug(mail.outbox[mail_prior + 1].body)
        LOG.debug(mail.outbox[mail_prior + 1].alternatives[0][0])
        self.assertEqual(len(mail.outbox), mail_prior + 3)

    def test_opted_out(self):
        """ Assert an advertiser opted-out of list 2 does not get an email. """
        slot = SLOT_FACTORY.create_slot()
        advertiser = slot.business.advertiser
        self.prep_coupon_in_slot(slot)
        advertiser.email_subscription.clear()
        task = ExpiringCouponTask()
        task.run()
        self.assertEqual(len(mail.outbox), 0)
