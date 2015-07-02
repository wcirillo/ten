""" Test for the coupon app. """

import datetime
import logging
import os
import time

from django.conf import settings 
from django.contrib.contenttypes.models import ContentType
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase

from advertiser.factories.location_factory import BUSINESS_LOCATION_FACTORY
from advertiser.models import BillingRecord
from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import (Coupon, CouponAction, CouponType, ConsumerAction,
    FlyerCoupon, Flyer, RankDateTime, SlotTimeFrame)
from coupon.service.flyer_service import send_flyer
from coupon.service.twitter_service import TWITTER_SERVICE
from coupon.tasks import (CreateWidget, ExtendCouponExpirationDateTask,
    RecordAction, create_flyers_this_week, expire_slot_time_frames,
    record_action_multiple_coupons, update_facebook_share_coupon,
    update_fb_share_coupons_all)
from ecommerce.models import Order, OrderItem
from feed.service import get_web_page, is_file_recent
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestCreateWidget(TestCase):
    """ Test case for CreateWidget task. """
    
    def test_business_preference(self):
        """ Assert distinct businesses are preferred. """
        slot_family = SLOT_FACTORY.create_slot_family()
        slots = SLOT_FACTORY.create_slots(create_count=3)
        site = Site.objects.get(id=2)
        content = CreateWidget().run(site, template='10CouponsWidget160x600.js')
        LOG.debug(content)
        LOG.debug('slot_family: %s' % str(slot_family))
        LOG.debug('slots: %s' % slots)
        # Parent slot, created first, in in content first.
        self.assertTrue(content.find(
            slot_family[0]['parent'].slot_time_frames.all(
                )[0].coupon.offer.headline) < content.find(
            slots[0].slot_time_frames.all()[0].coupon.offer.headline))
        # These unrelated slots are next.
        self.assertTrue(content.find(
                slots[0].slot_time_frames.all()[0].coupon.offer.headline) <
            content.find(
                slots[1].slot_time_frames.all()[0].coupon.offer.headline))
        self.assertTrue(content.find(
                slots[1].slot_time_frames.all()[0].coupon.offer.headline) <
            content.find(
                slots[2].slot_time_frames.all()[0].coupon.offer.headline))
        # The unrelated slots were preferred over the child slots
        self.assertTrue(content.find(
                slots[2].slot_time_frames.all()[0].coupon.offer.headline) <
            slot_family[0]['children'][0].slot_time_frames.all(
                )[0].coupon.offer.headline)


class TestRecordAction(TestCase):
    """ Tests for coupon app RecordAction that do not require transactions """

    def test_record_action(self):
        """ Assert an action is recorded. """
        coupons = COUPON_FACTORY.create_coupons(create_count=2)
        record_action = RecordAction()
        now = datetime.datetime.now()
        record_action.run(1, coupons[0].id)
        action_count = CouponAction.objects.get(
            action__id=1, coupon=coupons[0]).count
        LOG.debug('action_count = %s' % action_count)
        record_action.run(1, coupons[0].id)
        new_action_count = CouponAction.objects.get(
            action__id=1, coupon=coupons[0]).count
        LOG.debug('new_action_count = %s' % new_action_count)
        self.assertEqual(action_count + 1, new_action_count)
        coupon_ids = tuple([coupon.id for coupon in coupons])
        record_action_multiple_coupons(1, coupon_ids)
        newer_action_count = CouponAction.objects.get(
            action__id=1, coupon=coupons[0]).count
        LOG.debug('newer_action_count = %s' % newer_action_count)
        self.assertEqual(new_action_count + 1, newer_action_count)
        consumer = Consumer.objects.create(consumer_create_datetime=now)
        record_action_multiple_coupons(1, coupon_ids, consumer.id)
        newest_action_count = CouponAction.objects.get(
            action__id=1, coupon=coupons[0]).count
        LOG.debug('newest_action_count = %s' % newest_action_count)
        consumer_action = ConsumerAction.objects.get(
            action__id=1, coupon=coupons[0], consumer=consumer)
        self.assertTrue(consumer_action)
        LOG.debug('consumer_action = %s' % consumer_action)

    def test_rank_date(self):
        """ Assert rank date is updated when a coupon is 'printed'. """
        coupon = COUPON_FACTORY.create_coupon()
        RecordAction().run(3, coupon.id)
        try:
            rank_datetime = RankDateTime.objects.get(coupon=coupon)
        except RankDateTime.DoesNotExist:
            self.fail('RandDateTime not created.')
        LOG.debug('rank_datetime: %s' % rank_datetime.rank_datetime)
        self.assertTrue(rank_datetime.rank_datetime > datetime.datetime.now())


class TestTransactionRecordAction(TransactionTestCase):
    """ Tests for record action tasks that require transactions """

    def test_record_action_bad_consumer(self):
        """ Assert action is not incremented when a bad consumer_id is passed.
        """
        coupon = COUPON_FACTORY.create_coupon()
        try:
            RecordAction().run(1, coupon.id, 999999)
        except IntegrityError:
            self.fail('IntegrityError thrown, not caught.')

    def test_record_act_mult_bad_con(self):
        """ Assert action for multiple coupons is not incremented when a bad
        consumer_id is passed.
        """
        coupons = COUPON_FACTORY.create_coupons(create_count=2)
        coupon_ids = tuple([coupon.id for coupon in coupons])
        try:
            record_action_multiple_coupons(1, coupon_ids, 999999)
        except IntegrityError as error:
            self.fail('IntegrityError thrown, not caught: %s' % error)


class TestCreateFlyers(EnhancedTestCase):
    """ Tests relating to the flyer creation process  """

    fixtures = ['test_advertiser', 'test_coupon', 'test_coupon_views',
        'test_slot', 'test_flyer']

    def test_create_flyers_this_week(self):
        """ Test the flyer creation process.
        This test sets up case where we have a new ordered coupon this week for
        site 2. Test is time sensitive, so we fix times during the test.
        
        Assert a new flyer is created, with a paid coupon.
        Assert that, when it is sent, its order_item is updated.
        """
        try:
            content_type = ContentType.objects.get(
                app_label='coupon', model='slot')
        except CouponType.DoesNotExist:
            content_type = ContentType.objects.create(
                app_label='coupon', model='slot')
        send_date = datetime.date(2011, 11, 3)
        slots = SLOT_FACTORY.create_slots(create_count=5)
        coupons = SLOT_FACTORY.prepare_slot_coupons_for_flyer(slots, send_date)
        # A slot ending this week:
        slots[0].end_date = datetime.date.today() + datetime.timedelta(days=1)
        slots[0].save()
        # A paid flyer placement.
        billing_record = BillingRecord.objects.create(
            business=slots[1].business)
        order = Order.objects.create(billing_record=billing_record)
        order_item = OrderItem.objects.create(
            site_id=2,
            business=slots[1].business,
            order=order,
            product_id=1,
            start_datetime=datetime.datetime.now() - datetime.timedelta(days=1),
            end_datetime=datetime.datetime.now() + datetime.timedelta(weeks=1),
            item_id=slots[1].id,
            content_type=content_type)
        # Media Partner
        # Media partner coupon will only be included if it was created after the
        # most current flyer for this site.
        coupons[2].coupon_type_id = 5
        coupons[2].save()
        # A Media partner coupon must have a zip in this market.
        location = BUSINESS_LOCATION_FACTORY.create_business_location(
            coupons[2].offer.business)
        location.location_zip_postal = '12550'
        location.save()
        coupons[2].location.add(location)
        # National
        coupons[3].coupon_type_id = 6
        coupons[3].save()
        flyers_count = Flyer.objects.count()
        LOG.debug('flyer count before: %s' % flyers_count)
        # Site needs consumers or no flyers are created.
        CONSUMER_FACTORY.create_consumer()
        create_flyers_this_week(send_date=send_date, test_mode=True)
        # The actual number here will depend on how many sites in initial_data:
        LOG.debug('flyer count after: %s' % Flyer.objects.count())
        self.assertTrue(Flyer.objects.count() > flyers_count)
        for coupon_id, flavor in (
            (coupons[0].id, 'slot ending'),
            (coupons[1].id, 'paid'),
            (coupons[2].id, 'media partner'),
            (coupons[3].id, 'national'),
            (coupons[4].id, 'never in a flyer before')):
            try:
                flyer = Flyer.objects.filter(site=2,
                    flyer_coupons__coupon__id=coupon_id).latest('id')
            except Flyer.DoesNotExist:
                self.fail('Failed to include this %s coupon.' % flavor)
        flyer.is_approved = True
        flyer.save()
        # Flyer needs eligible recipient.
        consumer = Consumer(email='test_create_flyers_this_week@example.com',
            site_id=2, is_emailable=True)
        consumer.save()
        consumer.email_subscription.add(1)
        send_flyer(flyer)
        order_item = OrderItem.objects.get(id=order_item.id)
        self.assertEqual(order_item.content_type,
            ContentType.objects.get(app_label='coupon', model='flyercoupon'))
        self.assertEqual(order_item.item_id,
            FlyerCoupon.objects.get(flyer=flyer, coupon=coupons[1]).id)

    def test_require_thursday(self):
        """ Assert cannot create flyers with a send_date not Thursday. """
        with self.assertRaises(ValidationError) as context_manager:
            create_flyers_this_week(send_date=datetime.date(2011, 1, 1))
        LOG.debug(context_manager.exception)

    def test_run_twice_safe(self):
        """ Assert if the process is called multiple times, no extra flyers are
        created in successive runs. """
        create_flyers_this_week(send_date=datetime.date(2011, 5, 19))
        create_flyers_this_week(send_date=datetime.date(2011, 5, 19))
        self.assertTrue(
            'No flyers created in this run' in mail.outbox[-1:][0].body)


class TestCreateFlyersPhase2(EnhancedTestCase):
    """ Test case for flyer logic for a site in phase 2. """
    urls = 'urls_local.urls_2'
    
    def test_create_flyers_this_week(self):
        """ Assert a site in Phase 2 falls back to Phase 1 logic when no flyer
        placements are sold. Assert no flyer created for site 3 because no
        consumers. """
        # A slot on site 2 will be included in the flyer for free.
        slot = SLOT_FACTORY.create_slot()
        send_date = datetime.date(2011, 11, 17)
        coupon = SLOT_FACTORY.prepare_slot_coupons_for_flyer(
            [slot], send_date)[0]
        site = Site.objects.get(id=3)
        site.phase = 2
        site.save()
        create_flyers_this_week(send_date=send_date)
        flyer = Flyer.objects.filter(send_date=send_date).latest('id')
        self.assertEqual(flyer.site_id, 2) # Therefore no flyer site 3.
        self.assertFalse(flyer.is_approved)
        self.assertEqual(flyer.send_datetime, None)
        self.assertEqual(flyer.send_status, '0')
        self.assertEqual(flyer.flyer_coupons.count(), 1)
        self.assertEqual(
            flyer.flyer_coupons.filter(coupon__id=coupon.id).count(), 1)
        self.assertEqual(flyer.flyer_subdivisions.count(), 0)
        self.assertTrue('Hudson Valley, []' in mail.outbox[0].body)


class TestExtendCouponExpirationDate(TestCase):
    """ Test case for ExtendCouponExpirationDateTask. """

    def test_coupon_extended(self):
        """ Assert a current coupon expiring tomorrow is extended. """
        slot = SLOT_FACTORY.create_slot()
        coupon = slot.slot_time_frames.all()[0].coupon
        coupon.expiration_date = datetime.date.today() + datetime.timedelta(1)
        coupon.save()
        task = ExtendCouponExpirationDateTask()
        task.run()
        coupon = Coupon.objects.get(id=coupon.id)
        self.assertEqual(coupon.expiration_date, (datetime.date.today() +
            datetime.timedelta(90)))


class TestExpireSlotTimeFrames(TestCase):
    """ Test case for task expire_slot_time_frames. """
    
    def test_expire_slot_time_frames(self):
        """ Assert task expires time frames of expired coupons. """
        future_date = datetime.date.today() + datetime.timedelta(weeks=1)
        past_date = datetime.date.today() - datetime.timedelta(weeks=1)
        slot = SLOT_FACTORY.create_slot()
        slot_time_frame = slot.slot_time_frames.latest('id')
        coupon = slot_time_frame.coupon
        slot.end_date = future_date
        slot.save()
        coupon.expiration_date = past_date
        coupon.save()
        self.assertEqual(slot_time_frame.end_datetime, None)
        expire_slot_time_frames()
        slot_time_frame = SlotTimeFrame.objects.get(coupon=coupon)
        self.assertTrue(slot_time_frame.end_datetime) # Fail if still None.
        self.assertTrue(slot_time_frame.end_datetime < datetime.datetime.now())


class TestTweetApprovedCoupon(EnhancedTestCase):
    """ Test cases for task tweet_approved_coupon """
    
    def test_tweet_approved_coupon(self):
        """ Assert an approved coupon is tweeted.
        To verify Tweet is unique, a random string is added. 
        Revised test to run no more than once every 5 minutes.  """
        slot = SLOT_FACTORY.create_slot()
        coupon = SLOT_FACTORY.prepare_slot_coupons_for_flyer([slot])[0]
        hours = 0.08
        filename = settings.MEDIA_ROOT + 'feed/twittercom.htm'
        if os.path.exists(filename) and is_file_recent(filename=filename, 
            hours=hours):
            LOG.debug('skipping test_tweet_approved_coupon')
        else:
            get_web_page(web_url='http://twitter.com', hours=hours)
            time.sleep(10)
            # check latest twitter status
            tweet = TWITTER_SERVICE.twitter_connect(coupon)
            if tweet:
                LOG.debug('tweet = %s' % tweet)
                self.assertTrue(coupon.offer.headline in tweet)
                self.assertTrue(coupon.offer.qualifier in tweet)


class TestFBShareCouponAction(TestCase):
    """ Test cases for task update facebook share coupon action """
    
    def test_fb_share_coupon_action(self, test_mode=True):
        """  Assert task updates facebook share action. """
        coupon = COUPON_FACTORY.create_coupon()
        update_fb_share_coupons_all(max_coupons=10)
        with self.assertRaises(CouponAction.DoesNotExist) as context_manager:
            coupon_action_count = CouponAction.objects.get(coupon=coupon,
                action__id=7).count
            self.fail('CouponAction count: %s, should be zero.' % 
                coupon_action_count)
        LOG.debug(context_manager.exception)
        # Test mode will only cause count to exist.
        update_facebook_share_coupon(coupon, test_mode=test_mode)
        self.assertEqual(CouponAction.objects.get(coupon=coupon, 
            action__id=7).count, 5)
