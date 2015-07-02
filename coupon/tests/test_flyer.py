""" Flyer tests for the coupon app. """
#pylint: disable=C0103
import datetime
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.core import mail
from django.db import transaction
from django.db.models import Count
from django.test import TestCase, TransactionTestCase

from common.service.payload_signing import PAYLOAD_SIGNING
from common.test_utils import EnhancedTestCase
from consumer.factories.consumer_factory import CONSUMER_FACTORY
from consumer.models import Consumer
from coupon.factories.coupon_factory import COUPON_FACTORY
from coupon.factories.slot_factory import SLOT_FACTORY
from coupon.models import (Coupon, Flyer, FlyerCoupon, FlyerConsumer,
    FlyerSubdivision, FlyerPlacement, FlyerPlacementSubdivision)
from coupon.service.flyer_service import (add_flyer_subdivision,
    next_flyer_date, set_prior_weeks, get_available_flyer_dates,
    get_flyer_placements, get_national_text, send_flyers_this_week)
from coupon.service.flyer_create_service import (append_coupon_to_flyer,
    conditionally_append_coupon, process_city, process_county,
    split_subdivision, get_coupons_for_flyer, create_update_flyers_subs,
    create_flyers_this_site_phase2)
from geolocation.models import USCity
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class TestAppendCouponToFlyer(TransactionTestCase):
    """ Tests for append_coupon_to_flyer service function. """

    def test_coupon_flyer_unicity(self):
        """ Assert a coupon cannot be added to a flyer twice. """
        flyer = Flyer.objects.create(site_id=3)
        coupon = COUPON_FACTORY.create_coupon()
        # Adding works once.
        with transaction.commit_on_success():
            self.assertTrue(append_coupon_to_flyer(flyer, coupon))
        # This still returns True to say the flyer still needs more coupons.
        with transaction.commit_on_success():
            self.assertTrue(append_coupon_to_flyer(flyer, coupon))
        # The coupon is only relate to the flyer once, however.
        self.assertEqual(flyer.flyer_coupons.filter(coupon=coupon).count(), 1)


class TestConditionallyAppendCoupon(TestCase):
    """ Test case for conditionally_append_coupon service function. """

    def test_business_in_flyer(self):
        """ Assert a coupon is not appends to the flyer if its business already
        is in the flyer.
        """
        flyer = Flyer.objects.create(site_id=3)
        coupon = COUPON_FACTORY.create_coupon()
        coupon_2 = COUPON_FACTORY.create_coupon(offer=coupon.offer)
        FlyerCoupon.objects.create(flyer=flyer, coupon=coupon)
        need_more, skipped = conditionally_append_coupon(flyer, coupon_2)
        self.assertTrue(need_more)
        self.assertTrue(skipped)


class TestGetNationalText(TestCase):
    """ Test case for service function get_national_text. """

    def test_string_substitution(self):
        """ Assert string is dynamic; vars have been replaced.
        """
        flyer = Flyer.objects.create(site_id=2)
        for weeks in range(12):
            flyer.send_date += datetime.timedelta(weeks=1)
            flyer.save()
            context = get_national_text(flyer)
            LOG.debug('context for plus %s weeks: %s' % (weeks, context))
            self.assertTrue('%(' not in context['national_text'])
            self.assertTrue(flyer.site.domain in context['national_text']
                or flyer.site.name in context['national_text']
                or flyer.site.region in context['national_text'])


class TestFlyerPhase2(EnhancedTestCase):
    """ Test case for flyer logic for a site in phase 2. """

    fixtures = ['test_geolocation']
    urls = 'urls_local.urls_2'
    
    @classmethod
    def setUpClass(cls):
        super(TestFlyerPhase2, cls).setUpClass()
        cls.site = Site.objects.get(id=2)
        cls.county_type = ContentType.objects.get(model='uscounty')
        cls.city_type = ContentType.objects.get(model='uscity')
        cls.zip_type = ContentType.objects.get(model='uszip')
        cls.future_date = datetime.date.today() + datetime.timedelta(7)
        cls.send_date = datetime.date(2011, 5, 19)
        cls.next_flyer_date = next_flyer_date()

    def create_two_flyer_placements(self):
        """ Create two flyer placements. """
        slots = SLOT_FACTORY.create_slots(create_count=2)
        flyer_placements = []
        for slot in slots:
            flyer_placements.append(
                FlyerPlacement.objects.create(slot=slot, site=self.site,
                    send_date=self.send_date))
        return flyer_placements

    def test_get_flyer_placements(self):
        """ Assert flyer placements are selected for a site in phase 2. """
        self.create_two_flyer_placements()
        flyer_placements = get_flyer_placements(self.site,
            send_date=self.send_date)
        self.assertTrue(len(list(flyer_placements)), 2)

    def test_get_flyer_placements_subs(self):
        """ Assert flyer placements are selected for a site in phase 2 when
        subdivisions are specified.
        """
        flyer_placements = self.create_two_flyer_placements()
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placements[0],
            geolocation_type=self.zip_type,
            geolocation_id=16045)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placements[0],
            geolocation_type=self.zip_type,
            geolocation_id=23181)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placements[1],
            geolocation_type=self.county_type,
            geolocation_id=1844)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placements[1],
            geolocation_type=self.county_type,
            geolocation_id=1866)
        subdivision_dict = {
            'zip_array': (16045,23181),
            'county_array': (1844, 1866)
            }
        flyer_placements = get_flyer_placements(self.site,
            send_date=datetime.date(2011, 5, 19),
            subdivision_dict=subdivision_dict)
        self.assertTrue(len(list(flyer_placements)), 2)
        self.assertTrue(
            flyer_placements[0].flyer_placement_subdivisions.count(), 2)
    
    def test_create_flyers_phase2(self):
        """ Assert flyers are built for a site in phase 2. """
        # Use a unique date to avoid collision with other tests.
        send_date = datetime.date(2011, 11, 10)
        slots = SLOT_FACTORY.create_slots(create_count=15)
        coupons = SLOT_FACTORY.prepare_slot_coupons_for_flyer(slots, send_date)
        # 12550
        flyer_placement = FlyerPlacement.objects.create(slot=slots[0],
            site=self.site, send_date=send_date)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement,
            geolocation_type=self.zip_type,
            geolocation_id=23181)
        # Dutchess, Westchester
        flyer_placement = FlyerPlacement.objects.create(slot=slots[1],
            site=self.site, send_date=send_date)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement,
            geolocation_type=self.county_type,
            geolocation_id=1844)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement,
            geolocation_type=self.county_type,
            geolocation_id=1890)
        # 12601, 10570
        flyer_placement = FlyerPlacement.objects.create(slot=slots[2],
            site=self.site, send_date=send_date)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement,
            geolocation_type=self.zip_type,
            geolocation_id=16045)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement,
            geolocation_type=self.zip_type,
            geolocation_id=16142)
        # 12518
        flyer_placement = FlyerPlacement.objects.create(slot=slots[3],
            site=self.site, send_date=send_date)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement,
            geolocation_type=self.zip_type,
            geolocation_id=15145)
        # White Plains
        flyer_placement = FlyerPlacement.objects.create(slot=slots[4],
            site=self.site, send_date=send_date)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement,
            geolocation_type=self.city_type,
            geolocation_id=18258)
        pre_count = Flyer.objects.filter(send_date=send_date).count()
        admin_data = create_flyers_this_site_phase2(site=self.site,
            send_date=send_date, national_coupons=Coupon.objects.none())
        LOG.debug('admin_data: %s' % admin_data)
        self.assertEqual(admin_data[0], 
            'Hudson Valley, [<FlyerSubdivision: 12550>]')
        flyers = Flyer.objects.filter(send_date=send_date)
        LOG.debug([(
            flyer, flyer.flyer_coupons.all()) for flyer in flyers])
        # All of these flyers need at least one FlyerSubdivision.
        self.assertFalse(flyers.annotate(sub_count=Count(
            'flyer_subdivisions')).filter(sub_count=0).count())
        LOG.debug([(flyer, flyer.flyer_subdivisions.all()) for flyer in flyers])
        self.assertEqual(flyers.count(), pre_count + 6)
        # Assert this flyer has correct paid coupon, extra coupons, and goes to 
        # zip 12550.
        flyer = flyers.get(flyer_subdivisions__geolocation_id=23181)
        self.assertEqual(flyer.flyer_coupons.count(), 10)
        self.assertTrue(flyer.flyer_coupons.filter(coupon=coupons[0]).count())
        self.assertEqual(flyer.flyer_subdivisions.count(), 1)
        # Assert this flyer has another paid coupon too, and goes to zip 12601.
        # (10570 is a subset of Westchester and 12601 is a subset of Dutchess.)
        flyer = flyers.get(flyer_subdivisions__geolocation_id=16045)
        self.assertEqual(flyer.flyer_coupons.count(), 10)
        self.assertTrue(flyer.flyer_coupons.filter(coupon=coupons[1]).count())
        self.assertTrue(flyer.flyer_coupons.filter(coupon=coupons[2]).count())
        self.assertEqual(flyer.flyer_subdivisions.count(), 2)
        # Assert this flyer has the paid coupon and goes to 12518.
        flyer = flyers.get(flyer_subdivisions__geolocation_id=15145)
        self.assertEqual(flyer.flyer_subdivisions.count(), 1)
        self.assertEqual(flyer.flyer_coupons.count(), 10)
        self.assertTrue(flyer.flyer_coupons.filter(coupon=coupons[3]).count())
        # Assert this flyer for remaining zips of Dutchess.
        flyer = flyers.get(flyer_subdivisions__geolocation_id=30218)
        self.assertTrue(flyer.flyer_subdivisions.filter(
            geolocation_id=31367, geolocation_type__model='uszip').count())
        # Assert Westchester gets two flyers: one for 10570 and one without.
        # White Plains zip remains with the original Westchester flyer.
        flyer = flyers.get(flyer_subdivisions__geolocation_id=18258)
        self.assertTrue(flyer.flyer_coupons.filter(coupon=coupons[4]).count())
        # This Pleasantville zip, 10570, has a flyer with an extra coupon.
        flyer = flyers.get(flyer_subdivisions__geolocation_id=16142)
        self.assertTrue(flyer.flyer_coupons.filter(coupon=coupons[2]).count())
        self.assertTrue(flyer.flyer_coupons.filter(coupon=coupons[1]).count())

    def test_no_current_coupon(self):
        """ Assert a flyer placement is skipped when no current coupon. """
        slots = SLOT_FACTORY.create_slots(create_count=2)
        slots[0].slot_time_frames.all().delete()
        FlyerPlacement.objects.create(site=self.site,
            slot=slots[0], send_date=self.next_flyer_date)
        national_coupons = Coupon.objects.filter(
            id=slots[1].slot_time_frames.all()[0].coupon.id)
        create_flyers_this_site_phase2(self.site, self.next_flyer_date,
            national_coupons)
        try:
            flyer = self.site.flyers.get(send_date=self.next_flyer_date)
        except Flyer.DoesNotExist:
            self.fail('Flyer was not created.')
        self.assertEqual(flyer.flyer_subdivisions.count(), 0)

    def test_create_flyers_for_city(self):
        """ Assert flyers are created for Poughkeepsie placement. """
        slots = SLOT_FACTORY.create_slots(create_count=2)
        SLOT_FACTORY.prepare_slot_coupons_for_flyer(slots)
        flyer_placement = FlyerPlacement.objects.create(site=self.site,
            slot=slots[0], send_date=self.next_flyer_date)
        FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement, geolocation_id=17009,
            geolocation_type=self.city_type)
        create_flyers_this_site_phase2(self.site, self.next_flyer_date,
            Coupon.objects.none())
        flyers = self.site.flyers.filter(
            send_date=self.next_flyer_date).order_by('id')
        self.assertEqual(flyers.count(), 2)
        # This flyer has one subdivision, and it is Poughkeepsie.
        self.assertEqual(flyers[0].flyer_subdivisions.count(), 1)
        self.assertEqual(flyers[0].flyer_subdivisions.filter(
            geolocation_type=self.city_type,
            geolocation_id=17009).count(), 1)
        self.assertTrue(flyers[1].flyer_subdivisions.count() > 6)
        # This flyer has subdivisions for other counties except Dutchess, and
        # for Red Hook, a city in Dutchess.
        self.assertEqual(flyers[1].flyer_subdivisions.filter(
            geolocation_type=self.county_type,
            geolocation_id__in=[1866, 1890, 1886]).count(), 3)
        self.assertEqual(flyers[1].flyer_subdivisions.filter(
            geolocation_type=self.city_type,
            geolocation_id=17043).count(), 1)

    def test_create_update_flyer_subs(self):
        """ Assert minimal flyers created for placements in Dutchess county. """
        slot = SLOT_FACTORY.create_slot()
        coupon = SLOT_FACTORY.prepare_slot_coupons_for_flyer([slot])[0]
        flyer_placement = FlyerPlacement.objects.create(site=self.site,
            slot=slot, send_date=self.next_flyer_date)
        # 12601.
        flyer_placement_subdivision = FlyerPlacementSubdivision.objects.create(
            flyer_placement=flyer_placement, geolocation_type=self.zip_type,
            geolocation_id=16045)
        flyer = Flyer.objects.create(site=self.site, is_approved=True,
            send_date=self.next_flyer_date)
        # Poughkeepsie
        FlyerSubdivision.objects.create(flyer=flyer, geolocation_id=17009,
            geolocation_type=self.city_type)
        create_update_flyers_subs(FlyerPlacementSubdivision.objects.filter(
            id=flyer_placement_subdivision.id), 'uszip', flyer_placement,
            coupon, self.site)
        # The city flyer subdivision has been split into at least 3 zip
        # subdivisions.
        self.assertTrue(FlyerSubdivision.objects.filter(
            flyer__in=Flyer.objects.filter(
                site=self.site, send_date=self.next_flyer_date),
            geolocation_type=self.zip_type).count() > 2)

    def test_process_city(self):
        """ Assert all the zips of Poughkeepsie are covered when a flyer exists
        for the zip code 12601.
        """
        slots = SLOT_FACTORY.create_slots(create_count=2)
        coupons = SLOT_FACTORY.prepare_slot_coupons_for_flyer(slots)
        flyer_placement = FlyerPlacement.objects.create(site=self.site,
            slot=slots[0], send_date=self.next_flyer_date)
        catchall_flyer = Flyer.objects.create(site=self.site,
            send_date=self.next_flyer_date)
        flyer_12601 = Flyer.objects.create(site=self.site,
            send_date=self.next_flyer_date)
        FlyerSubdivision.objects.create(
            flyer=flyer_12601, geolocation_type=self.zip_type,
            geolocation_id=16045)
        process_city(catchall_flyer, 17009, coupons[1], flyer_placement, [])
        # Assert two other zip codes of Poughkeepsie were added to the catchall
        # flyer.
        self.assertEqual(catchall_flyer.flyer_subdivisions.filter(
            geolocation_type=self.zip_type,
            geolocation_id__in=[30218, 31367]).count(), 2)

    def test_process_county(self):
        """ Assert Orange County is fully covered for flyers. """
        slots = SLOT_FACTORY.create_slots(create_count=2)
        coupons = SLOT_FACTORY.prepare_slot_coupons_for_flyer(slots)
        flyer_placement = FlyerPlacement.objects.create(site=self.site,
            slot=slots[0], send_date=self.next_flyer_date)
        flyer_12550 = Flyer.objects.create(site=self.site,
            send_date=self.next_flyer_date)
        FlyerSubdivision.objects.create(flyer=flyer_12550,
            geolocation_type=self.zip_type, geolocation_id=23181)
        flyer_new_windsor = Flyer.objects.create(site=self.site,
            send_date=self.next_flyer_date)
        FlyerSubdivision.objects.create(flyer=flyer_new_windsor,
            geolocation_type=self.city_type, geolocation_id=17555)
        catchall_flyer = Flyer.objects.create(site=self.site)
        process_county(catchall_flyer, 1866, coupons[1], flyer_placement)
        # Assert it got the subdivision for city Cornwall.
        self.assertTrue(catchall_flyer.flyer_subdivisions.filter(
            geolocation_type=self.city_type, geolocation_id=17536).count(), 1)
        # Assert it got the subdivision for city Maybrook.
        self.assertTrue(catchall_flyer.flyer_subdivisions.filter(
            geolocation_type=self.city_type, geolocation_id=17549).count(), 1)

    def test_split_subdivision_city(self):
        """ Assert Poughkeepsie is divided into its component zip codes."""
        flyer = Flyer.objects.create(site=self.site, is_approved=True)
        FlyerSubdivision.objects.create(flyer=flyer, geolocation_id=17009,
            geolocation_type=self.city_type)
        split_subdivision(flyer, 'uscity', USCity.objects.filter(id=17009))
        try:
            flyer.flyer_subdivisions.get(geolocation_type=self.city_type,
                geolocation_id=17009)
            self.fail('City subdivision not removed while splitting.')
        except FlyerSubdivision.DoesNotExist:
            pass
        try:
            flyer.flyer_subdivisions.get(geolocation_type=self.zip_type,
                geolocation_id=16045)
            flyer.flyer_subdivisions.get(geolocation_type=self.zip_type,
                geolocation_id=31367)
            flyer.flyer_subdivisions.get(geolocation_type=self.zip_type,
                geolocation_id=30218)
        except FlyerSubdivision.DoesNotExist as error:
            self.fail(error)
    
    def test_send_flyers_12550(self):
        """ Assert a flyer is sent 3 consumers in the zip code 12550. """
        flyer = Flyer.objects.create(site=self.site, is_approved=True)
        FlyerSubdivision.objects.create(flyer=flyer, geolocation_id=23181,
            geolocation_type=ContentType.objects.get(model='uszip'))
        # These three get this flyer.
        for consumer_x in range(3):
            email = 'test_send_flyers_12550-%s@example.com' % consumer_x
            Consumer.objects.create_consumer(site=self.site, username=email,
                email=email, consumer_zip_postal='12550')
        # This one does not because it has a different zip code.
        bad_email = 'test_send_flyers_not_12550@example.com'
        Consumer.objects.create_consumer(site=self.site, username=bad_email,
                email=bad_email, consumer_zip_postal='12601')
        self.assertEqual(flyer.send_status, '0')
        send_flyers_this_week()
        flyer = Flyer.objects.get(id=flyer.id)
        self.assertEqual(flyer.send_status, '2')
        self.assertEqual(flyer.num_recipients, 3)
        # Three consumer recipients plus one admin email.
        self.assertEqual(len(mail.outbox), 4)
        recipients = [message.to[0] for message in mail.outbox]
        self.assertTrue(email in recipients)
        self.assertTrue(bad_email not in recipients)
    
    def test_send_flyers_newburgh(self):
        """ Assert a flyer is sent 3 consumers in the city Newburgh. """
        flyer = Flyer.objects.create(site=self.site, is_approved=True)
        FlyerSubdivision.objects.create(flyer=flyer, geolocation_id=17552,
            geolocation_type=ContentType.objects.get(model='uscity'))
        # These three get this flyer.
        for consumer_x in range(3):
            email = 'test_newburgh-%s@example.com' % consumer_x
            Consumer.objects.create_consumer(site=self.site, username=email,
                email=email, consumer_zip_postal='12550')
        # This one does not because it has a different zip code.
        bad_email = 'test_not_newburgh@example.com'
        Consumer.objects.create_consumer(site=self.site, username=bad_email,
                email=bad_email, consumer_zip_postal='12601')
        self.assertEqual(flyer.send_status, '0')
        send_flyers_this_week()
        flyer = Flyer.objects.get(id=flyer.id)
        self.assertEqual(flyer.send_status, '2')
        self.assertEqual(flyer.num_recipients, 3)
        # Three consumer recipients plus one admin email.
        self.assertEqual(len(mail.outbox), 4)
        recipients = [message.to[0] for message in mail.outbox]
        self.assertTrue(email in recipients)
        self.assertTrue(bad_email not in recipients)
        # Assert each email was sent to exactly one recipient.
        for email in range(0, 2):
            self.assertEqual(mail.outbox[email].extra_headers.get('To', False), 
                False)
            self.assertEqual(mail.outbox[email].extra_headers.get('Cc', False),
                False)

    def test_12550_and_dutchess(self):
        """  Assert a flyer for subdivisions 12550 and Dutchess county is sent
        to the correct group of recipients.
        """
        flyer = Flyer.objects.create(site=self.site, is_approved=True)
        FlyerSubdivision.objects.create(flyer=flyer, geolocation_id=23181,
            geolocation_type=ContentType.objects.get(model='uszip'))
        FlyerSubdivision.objects.create(flyer=flyer, geolocation_id=1844,
            geolocation_type=ContentType.objects.get(model='uscounty'))
        # First two consumers will receive this. Third will not.
        for zip_code in ['12550', '12601', '12518']:
            email = '12550_and_dutchess-%s@example.com' % zip_code
            Consumer.objects.create_consumer(site=self.site, username=email,
                email=email, consumer_zip_postal=zip_code)
        send_flyers_this_week()
        flyer = Flyer.objects.get(id=flyer.id)
        recipients = [message.to[0] for message in mail.outbox]
        self.assertTrue('12550_and_dutchess-12550@example.com' in recipients)
        self.assertTrue('12550_and_dutchess-12601@example.com' in recipients)
        self.assertTrue('12550_and_dutchess-12518@example.com' not in
            recipients)

    def test_flyers_phase2_no_sold(self):
        """ Assert a site in Phase 2 with no sold coupons does not generate a
        flyer with no coupons eligible.
        """
        site = Site.objects.get(id=3)
        send_date = datetime.date(2011, 5, 12)
        national_coupons = Coupon.objects.filter(id=None)
        pre_count = Flyer.objects.filter(send_date=send_date).count()
        admin_data = create_flyers_this_site_phase2(site, send_date, 
            national_coupons)
        LOG.debug('admin_data' % admin_data)
        post_count = Flyer.objects.filter(send_date=send_date).count()
        self.assertEqual(pre_count, post_count)


class TestFlyer(EnhancedTestCase):
    """ Tests for flyer_create_service service functions. """
    
    fixtures = ['test_geolocation']
    urls = 'urls_local.urls_2'

    def test_max_ten_coupons_per_flyer(self):
        """ Assert a flyer may have at most 10 coupons. """
        flyer = Flyer.objects.create(site_id=3)
        coupons = COUPON_FACTORY.create_coupons(create_count=11)
        count = 0
        for coupon  in coupons:
            if append_coupon_to_flyer(flyer, coupon):
                count += 1
        self.assertEqual(count, 10)

    def test_send_flyers_this_week(self):
        """  Assert a flyer is sent. Assert the coupon links are correct. """
        flyer = Flyer.objects.create(site_id=2, is_approved=2)
        slots = SLOT_FACTORY.create_slots(create_count=2)
        coupons = SLOT_FACTORY.prepare_slot_coupons_for_flyer(slots)
        for coupon  in coupons:
            append_coupon_to_flyer(flyer, coupon)
        # It needs an eligible recipient.
        consumer = CONSUMER_FACTORY.create_consumer()
        CONSUMER_FACTORY.qualify_consumer(consumer)
        send_flyers_this_week()
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[0].subject, 'Recent Hudson Valley coupons')
        # Find the specific email to our test consumer.
        x = 0
        while x < len(mail.outbox):
            if mail.outbox[x].to[0] == consumer.email:
                break
            x += 1
        self.assertEqual(mail.outbox[0].extra_headers['From'], 
            '10HudsonValleyCoupons.com <Coupons@10Coupons.com>')
        target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST,
            reverse('opt_out', kwargs={'payload':
                PAYLOAD_SIGNING.create_payload(email=consumer.email)}))
        # We cannot predict the signed email payload, so trim that piece of the
        # url.
        payload = target_path.split('/')[-2]
        target_path = '/'.join(target_path.split('/')[:-2]) + '/'
        self.assertTrue(target_path in
            mail.outbox[x].extra_headers['List-Unsubscribe'])
        LOG.debug(mail.outbox[0].body)
        # Assert the opt out link is in the html version of the email.
        self.assertTrue(target_path in mail.outbox[0].alternatives[0][0])
        self.assertTrue('<mailto:list_unsubscribe-consumer_standard_flyer-' in 
            mail.outbox[0].extra_headers['List-Unsubscribe'])
        self.assertTrue('@bounces.10coupons.com>' in 
            mail.outbox[0].extra_headers['List-Unsubscribe'])
        for coupon in coupons:
            # We cannot predict the random obfuscation of the email hash.
            # So pass it as blank.
            target_path = '%s%s' % (settings.HTTP_PROTOCOL_HOST,
                reverse('flyer-click', args=[coupon.id, payload]))
            target_path = '/'.join(target_path.split('/')[:-2]) + '/'
            # Assert this url is in plain text version.
            self.assertTrue(target_path in mail.outbox[0].body)
            # Assert this url is in html version.
            self.assertTrue(target_path in mail.outbox[0].alternatives[0][0])
        # Assert a signed payload exists in each version.
        # The payload for the opt-out link does not need to be the same string
        # as the payload for the header, as long as they both load to the same.
        payload = mail.outbox[x].body[
            mail.outbox[x].body.index('opt-out-list/') + 13:].split('/')[0]
        self.assertEqual(PAYLOAD_SIGNING.parse_payload(payload)['email'],
            consumer.email)
        self.assertTrue(payload in mail.outbox[x].alternatives[0][0])
        flyer = Flyer.objects.get(id=flyer.id)
        # Assert the flyer is now marked as sent.
        self.assertTrue(flyer.send_status, '2')
        self.assertTrue(FlyerConsumer.objects.filter(flyer=flyer, 
            consumer__id=consumer.id).count(), 1)
        
    def test_no_flyers_this_week(self):
        """ Assert no flyers are sent. """
        flyers_before = Flyer.objects.filter(send_status='2').count()
        send_flyers_this_week()
        flyers_after = Flyer.objects.filter(send_status='2').count()
        self.assertEqual(flyers_before, flyers_after)


class TestGetCouponsForFlyer(TestCase):
    """ Test case for service function get_coupons_for_flyer. """

    def test_site_phase_1_no_coupons(self):
        """ Assert a Site in phase 1 with no current coupons returns None.
        """
        site = Site.objects.filter(phase=1).exclude(id=1).latest('id')
        coupons, coupons_by_type = get_coupons_for_flyer(site)
        self.assertEqual(len(coupons), 0)
        self.assertEqual(len(coupons_by_type['National']), 0)


class TestSetPriorWeeks(TestCase):
    """ Test case for flyer service function set_prior_weeks. """

    def test_early_date(self):
        """ Assert a flyer in the first week of the month skips no dates. """
        weeks_list = set_prior_weeks(datetime.date(2011, 8, 4))
        LOG.debug(weeks_list)
        self.assertEqual(len(weeks_list), 0)


class TestAddFlyerSubdivision(EnhancedTestCase):
    """ Test case for add_flyer_subdivision flyer service function. """

    def test_add_flyer_subdivision_good(self):
        """ Assert valid flyer placement subdivisions are created. """
        site = Site.objects.get(id=2)
        slot = SLOT_FACTORY.create_slot()
        flyer_placement = FlyerPlacement.objects.create(site=site, slot=slot,
            send_date=next_flyer_date())
        subdivision_dict = {
            'zip_array': (23181,),
            'city_array': (),
            'county_array': (1844,)
            }
        self.session['subdivision_dict'] = subdivision_dict
        add_flyer_subdivision(self, flyer_placement)
        self.assertTrue(flyer_placement.flyer_placement_subdivisions.count(), 2)


class TestGetAvailableFlyerDates(TestCase):
    """ Assert a flyer date already purchased is marked so in date_list.
    
    This test looks like it is more complex then it needs to be, but we
    can't know if next_flyer_date occurs within this month or next month.
    
    This test will fail if there is not at least one us_zip record, so load
    test_geolocation.json (geolocation initial data includes a county
    record and a city record).
    """
    def test_get_available_dates_good(self):
        """ Assert available dates are returned, in the expected format. """
        site = Site.objects.get(id=2)
        date_list = get_available_flyer_dates(site)
        LOG.debug('date_list: %s' % date_list)
        # Months are expected to be 6 or 7 for this test.
        self.assertTrue(5 < len(date_list) < 8)
        # Assert months are ordered chronologically.
        self.assertTrue(date_list[0]['weeks'][0]['send_date'] <
            date_list[1]['weeks'][0]['send_date'])

    def test_flyer_purchased(self):
        """ Assert a flyer date already purchased is marked so in date_list. """
        site = Site.objects.get(id=2)
        next_flyer_date_ = next_flyer_date()
        slot = SLOT_FACTORY.create_slot()
        FlyerPlacement.objects.create(site=site, slot=slot,
            send_date=next_flyer_date_)
        date_list = get_available_flyer_dates(site, None, slot_id=slot.id)
        LOG.debug('date_list: %s' % date_list)
        assertion_made = False
        for month in date_list:
            LOG.debug('month: %s' % month)
            for week in month['weeks']:
                LOG.debug('week: %s' % week)
                if week['send_date'] == next_flyer_date_:
                    self.assertFalse(week['date_is_available'])
                    assertion_made = True
                    break
            if assertion_made:
                break
        self.assertTrue(assertion_made)
