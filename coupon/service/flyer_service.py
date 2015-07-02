""" Service functions for flyers, including sending.

For functions specific to creating flyers, see flyer_create_service.py.
"""
import datetime
import logging

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import connection, transaction
from django.db.models import Q

from common.utils import format_date_for_dsp
from coupon.models import (Coupon, Flyer, FlyerCoupon, FlyerPlacement,
    FlyerSubject, FlyerPlacementSubdivision)
from ecommerce.models import OrderItem
from email_gateway.send import send_email
from firestorm.tasks import UPDATE_CONSUMER_BONUS_POOL
from geolocation.models import USZip, USCity
from market.models import Site
from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
# Please leave at "info" for normal usage, so we can see flyer send process.
LOG.setLevel(logging.INFO)

def get_subdivision_consumer_count(request):
    """ Get the consumer count for a specific subdivision. If one doesn't exist
    in session, grab the entire markets consumer_count.
    """
    site = get_current_site(request)
    try:
        subdivision_consumer_count = request.session['subdivision_dict']\
            ['subdivision_consumer_count']
    except KeyError:
        subdivision_consumer_count = site.get_or_set_consumer_count()
    return subdivision_consumer_count

def get_subdivision_dict(request, subdivision_consumer_count):
    """ Get the subdivision_dict out of session if it exist. If not, set it
    for the entire market. """
    try:
        return request.session['subdivision_dict']
    except KeyError:
        return set_subdivision_dict(request, subdivision_consumer_count)

def set_subdivision_dict(request, subdivision_consumer_count, county_array=None,
        city_array=None, zip_array=None):
    """ Set the subdivision_dict for county, city, zip and 
    subdivision_consumer_count appropriately for FlyerPlacementSubdivision
    orders to be processed. """
    if county_array is None:
        county_array = ()
    if city_array is None:
        city_array = ()
    if zip_array is None:
        zip_array = ()
    request.session['subdivision_dict'] = {
        'county_array':county_array,
        'city_array':city_array,
        'zip_array':zip_array,
        'subdivision_consumer_count':subdivision_consumer_count}
        
def add_flyer_subdivision(request, flyer_placement):
    """ When not buying the entire market, a flyer_placement gets associated
    with flyer placement subdivisions """
    subdivision_dict = request.session.get('subdivision_dict', None)
    if subdivision_dict is not None:
        for county in subdivision_dict['county_array']:
            FlyerPlacementSubdivision.objects.create(
                flyer_placement=flyer_placement, 
                geolocation_type=ContentType.objects.get(model='uscounty'),
                geolocation_id=int(county))
        for city in subdivision_dict['city_array']:
            FlyerPlacementSubdivision.objects.create(
                flyer_placement=flyer_placement, 
                geolocation_type=ContentType.objects.get(model='uscity'),
                geolocation_id=int(city))
        for _zip in subdivision_dict['zip_array']:
            FlyerPlacementSubdivision.objects.create(
                flyer_placement=flyer_placement, 
                geolocation_type=ContentType.objects.get(model='uszip'),
                geolocation_id=int(_zip))

def latest_flyer_datetime(site, only_sent_status=False):
    """ Return the create_datetime of latest flyer for this market, if any.
    If optional parameter only_sent_status is True, then get the latest flyer
    that has been sent.
    """
    try:
        flyers = Flyer.objects.filter(site=site)
        if only_sent_status:
            flyers = flyers.filter(send_status=2)
        latest_flyer = flyers.latest().create_datetime
    except Flyer.DoesNotExist:
        latest_flyer = datetime.datetime(1, 1, 1)
    return latest_flyer

def next_flyer_date(date=datetime.date.today()):
    """
    Get the closest future scheduled flyer date.
    
    Optionally pass in a date to find the next flyer date from then.
    """
    normal_send_isoweekday = 4
    days_from_now = normal_send_isoweekday - date.isoweekday()
    if days_from_now < 1:
        days_from_now += 7
    return date + datetime.timedelta(days=days_from_now)

def get_flyer_placement_coupons(flyer_placements):
    """
    Select the coupons of these flyer_placements, for flyer inclusion.
    
    flyer_placements = an instance or QuerySet of FlyerPlacement.
    
    It is possible to have a sold flyer placement for a slot in which there is
    no coupon eligible to be in the flyer. Here, flyer placements is the set
    of "sold" flyer placement positions. coupons, returned is the set of valid 
    coupons within them.
    """
    if type(flyer_placements) == FlyerPlacement:
        compare_to = [flyer_placements.slot_id]
    else:
        compare_to = flyer_placements.values_list('slot_id', flat=True)
    flyer_placement_coupons = Coupon.current_coupons.filter(
        is_approved=True, slot_time_frames__slot__in=compare_to)
    return flyer_placement_coupons

def set_prior_weeks(date=None):
    """ Mark weeks of this month that are in the past as unavailable. """
    if not date:
        date = next_flyer_date()
    weeks_list = []
    previous_flyer_offset = -7
    first_flyer_numerical_day = int(date.strftime("%d"))
    if abs(previous_flyer_offset) > first_flyer_numerical_day:
        keep_priming_this_month = False
    else:
        keep_priming_this_month = True
    while keep_priming_this_month:
        previous_send_date = date + datetime.timedelta(previous_flyer_offset)
        week_dict = {'send_date':previous_send_date,
                    'date_is_available':False,
                    'checked':''}
        weeks_list.append(week_dict)
        previous_flyer_offset -= 7
        if abs(previous_flyer_offset) > first_flyer_numerical_day:
            keep_priming_this_month = False
    return weeks_list

def get_available_flyer_dates(site, subdivision_dict=None, slot_id=None):
    """ Get available flyer dates from the next flyer being sent out. Make sure
    at least 6 months of availability gets returned. Also, make sure that the
    flyers this advertiser has already purchased, for a specific subdivision, is
    not allowed to be purchased because of the flag
    this_flyer_purchased_already.
    """
    available_flyer_dates_list = []
    month_count = 0
    flyer_offset = 0
    month_is_available = True
    first_available_date = True
    this_flyer_purchased_already = False
    weeks_list = set_prior_weeks()
    next_flyer_date_ = next_flyer_date()
    while month_count < 6:
        send_date = next_flyer_date_ + datetime.timedelta(flyer_offset)
        month = send_date.strftime("%B")
        year = send_date.strftime("%Y")
        flyer_placements = get_flyer_placements(site, send_date=send_date,
            subdivision_dict=subdivision_dict)
        available_positions = get_flyer_positions_available(flyer_placements)
        if slot_id and flyer_placements.filter(slot__id=int(slot_id)).count():
            LOG.debug(send_date)
            this_flyer_purchased_already = True
        if send_date == next_flyer_date_:
            current_month = month
            current_year = year
            checked = 'checked'
        if available_positions == 0 or this_flyer_purchased_already:
            date_is_available = False
            this_flyer_purchased_already = False
        else:
            date_is_available = True
            month_is_available = True
            if first_available_date:
                first_available_date = False
                checked = 'checked'
                if current_month != month:
                    month_is_available = False
        if current_month != month:
            available_flyer_dates_list.append(
                {'month':current_month,
                'year':current_year,
                'month_is_available':month_is_available,
                'weeks':sorted(weeks_list, key=lambda date: date['send_date'])})
            current_month = month
            current_year = year
            weeks_list = []
            if month_is_available:
                month_count += 1
            month_is_available = False
            
        week_dict = {'send_date':send_date,
                     'date_is_available':date_is_available,
                     'checked':checked}
        weeks_list.append(week_dict)
        checked = ''
        flyer_offset += 7
    return available_flyer_dates_list

def get_flyer_placements(site, send_date=None, subdivision_dict=None):
    """
    Select the flyer_placements scheduled for the flyer that will be for this 
    date for this site for this set of market subdivisions (ie: counties, cities
    or zips).
    
    subdivision_dict supports the following keys:
        'zip_array' = a list of USZip pks.
        'city_array' = a lit of USCity pks.
        'county_array' = a list of USCounty pks.
    
    Answers this questions: how many spots are sold already for this site for
    this week, considering I want to buy this set of subdivisions.

    It answers through this: select the set of placements that are most
    restrictive to my intent of buying this set of subdivisions. If the count is
    less than 10 then I can buy.
    
    If no subdivisions are specified, use the entire market.
    """
    if not send_date:
        send_date = next_flyer_date()
    if site.phase == 1:
        # Get all the flyer placements for this site for this for this week.
        flyer_placements = site.flyer_placements.filter(send_date=send_date)
    elif site.phase == 2:
        county_array = site.us_county.values_list('id', flat=True)
        city_array = USCity.objects.filter(
            us_county__id__in=county_array).values_list('id', flat=True)
        zip_array = USZip.objects.filter(
            us_county__id__in=county_array).values_list('id', flat=True)
        if subdivision_dict:
            subdivision_dict_copy = subdivision_dict.copy()
            for key in ['zip_array', 'city_array', 'county_array']:
                try:
                    # If the key exists but has a len of 0, it is no good to us.
                    if not len(subdivision_dict_copy[key]):
                        subdivision_dict_copy.pop(key)
                except KeyError:
                    pass
            if 'county_array' in subdivision_dict_copy:
                county_array = subdivision_dict_copy['county_array']
            if 'city_array' in subdivision_dict_copy:
                city_array = subdivision_dict_copy['city_array']
        sub_dict = {
            'zip_array': tuple(zip_array),
            'city_array': tuple(city_array),
            'county_array': tuple(county_array)}
        if subdivision_dict:
            sub_dict.update(subdivision_dict_copy)
        # 1) Get all the flyer placements for the entire market. PLUS:
        # 2) Get all the flyer placements having a subdivision w/i the set
        # of the most popular county/city/zip combo.
        cursor = connection.cursor()
        cursor.execute("""
-- select the most popular county + city + zip combo,
-- and the count of placements in it.
SELECT cn.id AS "popular_county",
    popular_cities_per_county.us_city_id,
    popular_cities_per_county.us_zip_id,
    COUNT(s.id) +
    COALESCE(popular_cities_per_county.city_zip_count, 0) AS "aggregate_count"
FROM geolocation_uscounty cn
LEFT JOIN coupon_flyerplacementsubdivision s
    ON cn.id = s.geolocation_id
LEFT JOIN coupon_flyerplacement p
    ON s.flyer_placement_id = p.id
    AND p.site_id = %(site_id)s
    AND p.send_date = %(send_date)s
LEFT JOIN django_content_type ct
    ON geolocation_type_id = ct.id
    AND ct.model = 'uscounty'
LEFT JOIN (
    -- for each county, pick whichever is most popular:
    -- its most popular city and that cities most popular zip.
    -- or its popular zip and whatever city that zip lies is.

    SELECT DISTINCT ON (us_county_id) us_county_id, us_city_id, us_zip_id,
        MAX(city_zip_count) AS "city_zip_count"
    FROM (
        -- select the most popular city + zip combo,
        -- and the count of placements in it
        SELECT * FROM (
            SELECT us_county_id, us_city_id, us_zip_id,
                MAX(city_count + zip_count) AS "city_zip_count"
            FROM (
                --- select the count of placements for each of these cities
                SELECT us_c.us_county_id, s.geolocation_id AS "us_city_id",
                    COUNT(s.geolocation_id) AS "city_count",
                    us_z.id AS "us_zip_id",
                    COUNT(s2.geolocation_id) AS "zip_count"
                FROM coupon_flyerplacementsubdivision s
                JOIN coupon_flyerplacement p
                    ON s.flyer_placement_id = p.id
                    AND p.site_id = %(site_id)s
                    AND p.send_date = %(send_date)s
                JOIN django_content_type ct2
                    ON s.geolocation_type_id = ct2.id
                    AND ct2.model = 'uscity'
                JOIN geolocation_uscity us_c
                    ON s.geolocation_id = us_c.id
                    AND us_c.id IN %(city_array)s -- set of cities
                -- a zip within the city counts toward that city
                LEFT JOIN geolocation_uszip us_z
                    ON us_c.id = us_z.us_city_id
                LEFT JOIN coupon_flyerplacementsubdivision s2
                    ON us_z.id = s2.geolocation_id
                LEFT JOIN coupon_flyerplacement p2
                    ON s2.flyer_placement_id = p2.id
                    AND p2.site_id = %(site_id)s
                    AND p2.send_date = %(send_date)s
                LEFT JOIN django_content_type ct3
                    ON s2.geolocation_type_id = ct3.id
                    AND ct3.model = 'uszip'
                GROUP BY s.geolocation_id, us_c.us_county_id, us_z.id
            ) AS "max_city_zip"
            GROUP BY us_county_id, us_city_id, us_zip_id
        ) AS "popular_city_popular_zip"

        UNION

        -- select the most popular zip in each county
        -- and the count of placements in it
        SELECT us_county_id, us_city_id, geolocation_id,
            COUNT(s.geolocation_id) AS "zip_count"
        FROM coupon_flyerplacementsubdivision s
        JOIN coupon_flyerplacement p
            ON s.flyer_placement_id = p.id
            AND p.site_id = %(site_id)s
            AND p.send_date = %(send_date)s
        JOIN django_content_type ct2
            ON s.geolocation_type_id = ct2.id
            AND ct2.model = 'uszip'
        JOIN geolocation_uszip us_z
            ON s.geolocation_id = us_z.id
            AND us_z.id IN %(zip_array)s -- set of zips
        GROUP BY s.geolocation_id, us_county_id, us_city_id
    ) AS "count_by_max_zip_city_combo"
    GROUP BY us_county_id, us_city_id, us_zip_id
    ORDER BY us_county_id, city_zip_count DESC

) AS "popular_cities_per_county"
    ON cn.id = popular_cities_per_county.us_county_id

WHERE cn.id IN %(county_array)s
GROUP BY cn.id,
    popular_cities_per_county.us_city_id,
    popular_cities_per_county.us_zip_id,
    popular_cities_per_county.city_zip_count
ORDER BY aggregate_count DESC LIMIT 1
;
        """, {
            'site_id': site.id,
            'send_date': send_date,
            'zip_array': sub_dict['zip_array'],
            'city_array': sub_dict['city_array'],
            'county_array': sub_dict['county_array']
        })
        (county_id, city_id, zip_id, flyer_placement_count) = cursor.fetchone()
        subquery = Q(
            flyer_placement_subdivisions=None
            ) | Q(
                flyer_placement_subdivisions__in=
                    FlyerPlacementSubdivision.objects.filter(
                        geolocation_type__model='uscounty',
                        geolocation_id=county_id) |
                    FlyerPlacementSubdivision.objects.filter(
                        geolocation_type__model='uscity',
                        geolocation_id=city_id) |
                    FlyerPlacementSubdivision.objects.filter(
                        geolocation_type__model='uszip',
                        geolocation_id=zip_id))
        flyer_placements = FlyerPlacement.objects.filter(site=site,
            send_date=send_date).filter(subquery)
        LOG.debug('flyer_placements %s' % flyer_placements)
        if flyer_placements.count() != flyer_placement_count:
            LOG.error('Got %s flyer placements, expected %s' % (
                flyer_placements, flyer_placement_count))
    return flyer_placements

def get_flyer_positions_available(flyer_placements):
    """ Return number of current spots available for this site. """
    return 10 - flyer_placements.count()

def record_flyer_consumers(flyer, consumer_ids):
    """
    Record that this flyer was sent to these consumers.
    """
    if type(consumer_ids) != tuple or len(consumer_ids) == 0:
        return
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO "coupon_flyerconsumer" ("flyer_id", "consumer_id")
        SELECT %(flyer_id)s, "user_ptr_id"
        FROM "consumer_consumer"
        WHERE "user_ptr_id" IN %(consumer_ids)s
        AND "user_ptr_id" NOT IN (
            SELECT "consumer_id"
            FROM "coupon_flyerconsumer"
            WHERE "flyer_id" = %(flyer_id)s
            AND "consumer_id" IN %(consumer_ids)s
            );""", {'flyer_id': flyer.id, 'consumer_ids': consumer_ids})
    transaction.commit_unless_managed()
    return

def update_order_item_sent_coupons(flyer):
    """
    When a coupon has been sent in a flyer, set its order item from 
    content_type slot to content_type flyercoupon.
    
    This coupon might belong to multiple slots.
    This slot might have several outstanding flyer placement purchases, choose 
    the first of them.
    """
    flyer_coupon_content_type = ContentType.objects.get(
        app_label='coupon', model='flyercoupon')
    for flyer_coupon in flyer.flyer_coupons.all():
        # What is the min flyer placement order id of the slot, if any?
        try:
            order_item = OrderItem.objects.filter(
                item_id__in=flyer_coupon.coupon.slot_time_frames.all(
                    ).values_list('id', flat=True),
                product=1,
                content_type=ContentType.objects.get(
                    app_label='coupon', model='slot')).order_by('id')[0]
            order_item.content_type = flyer_coupon_content_type
            order_item.item_id = flyer_coupon.id
            order_item.save()
            LOG.debug('updated order_item %s' % order_item)
        except IndexError:
            pass

def send_flyer(flyer, recipient=None, context=None):
    """
    For a flyer w/o subdivisions, grab a list of users from the site (opted-in, 
    non-bouncing, etc.). This could be a flyer for a site in phase 1, or a site
    in phase 2 that did not sell any subdivisions for this week.
    
    For a flyer with subdivisions, filter these consumers by those that have a
    zip code matching a flyer subdivision, or have a zip code that is in a
    county matching a flyer subdivision.
    
    Concatenate the coupons into a context dictionary. 
    Pass info into send.multi.
    """
    if not context:
        context = dict()
    num_flyer_recipients = 0
    if not recipient:
        consumers = flyer.site.get_flyer_recipients().filter(is_active=True)
        if flyer.flyer_subdivisions.all():
            flyer_sub_zips = USZip.objects.filter(
                id__in=flyer.flyer_subdivisions.filter(
                        geolocation_type=ContentType.objects.get(model='uszip')
                    ).values_list('geolocation_id', flat=True)
                ).values_list('code', flat=True)
            flyer_sub_city_zips = USZip.objects.filter(
                us_city__id__in=flyer.flyer_subdivisions.filter(
                        geolocation_type=ContentType.objects.get(
                            model='uscity')
                    ).values_list('geolocation_id', flat=True)
                ).values_list('code', flat=True)
            flyer_sub_county_zips = USZip.objects.filter(
                us_county__id__in=flyer.flyer_subdivisions.filter(
                        geolocation_type=ContentType.objects.get(
                            model='uscounty')
                    ).values_list('geolocation_id', flat=True)
                ).values_list('code', flat=True)
            consumers = consumers.filter(
                consumer_zip_postal__in= flyer_sub_zips | flyer_sub_city_zips |
                    flyer_sub_county_zips )
        flyer_recipients = list(consumers.values_list('email', flat=True))
        LOG.debug('flyer_recipients: %s' % flyer_recipients)
        num_flyer_recipients = len(flyer_recipients)
    num_this_flyer_coupons = flyer.flyer_coupons.count() 
    template = 'consumer_standard_flyer'
    week = flyer.create_datetime.isocalendar()[1]
    try:
        subject = FlyerSubject.objects.get(week=week).title % flyer.site.name
        subject = subject.encode('ascii','ignore')
    except FlyerSubject.DoesNotExist:
        LOG.error("No flyer subject found for week %d" % week)
        subject = "Recent %s coupons" % flyer.site.name
    LOG.debug("subject: %s" % subject)
    flyer_coupons = flyer.flyer_coupons.select_related(
        'coupon__coupon_type').order_by('rank')
    first_national = False
    for flyer_coupon in flyer_coupons:
        if flyer_coupon.coupon.coupon_type.coupon_type_name == 'National':
            first_national = flyer_coupon
            break
    context.update({
        'subject': subject,
        'bouncing_checked': True,
        'flyer_coupons': flyer_coupons,
        'first_national': first_national,
    })
    if num_flyer_recipients > 0:
        LOG.info('sending flyer to %d consumers in site %s' % 
            (len(flyer_recipients), flyer.site))
        context.update({'to_email': flyer_recipients})
        send_email(template, flyer.site, context)
        flyer_sent(flyer=flyer, num_recipients=len(flyer_recipients))
        update_order_item_sent_coupons(flyer)
        record_flyer_consumers(flyer, 
            tuple(consumers.values_list('id', flat=True)))
        UPDATE_CONSUMER_BONUS_POOL.delay(flyer.id, flyer_recipients)
    elif recipient:
        LOG.info('Sending flyer %s for site %s to %s' %
            (flyer.id, flyer.site, recipient))
        context.update({'to_email': recipient})
        send_email(template, flyer.site, context)
    else:
        LOG.warning('Flyer for %s has no eligible recipients!!!' % 
            flyer.site.domain)
        flyer.send_status = '3'
        flyer.num_recipients = 0
        flyer.save()
    return num_this_flyer_coupons

def get_national_text(flyer):
    """ Return text that will rotate weekly, for introducing national coupons
    in the flyer.
    """
    week = flyer.send_date.isocalendar()[1]
    switch = {
        0: """Tell your favorite local business to try %(domain)s to increase
        traffic. The following offers are available to the %(region)s or
        anywhere in the world.""",
        1: """%(market)s business can attract new people and increase visits
        from existing customers with %(domain)s. The following are national or
        regional offers.""",
        2: """Any business in the %(region)s can benefit from online exposure
        and email distribution. Show the coupons you've printed from %(domain)s
        to the businesses you visit. The following offers can be redeemed online
        or at multiple locations.""",
        3: """10 %(market)s Coupons in every weekly Email Flyer! Make sure they
        include a local business you visit. Print this Flyer and show it to the
        business owner. The following are national or regional offers. """,
        4: """Get coupons from the best %(market)s businesses. Tell them to use
        %(domain)s to boost traffic. The following offers are available to the
        %(region)s or anywhere in the world.""",
        5: """Get offers from the %(market)s businesses you know. Look for them
        on %(domain)s The following offers are available everywhere.""",
        6: """Tell your favorite local business to try %(domain)s to increase
        traffic. The following offers can be redeemed online or at multiple
        locations.""",
        7: """%(market)s business can attract new people and increase visits
        from existing customers with %(domain)s. The following offers are
        available to the %(region)s or anywhere in the world.""",
        8: """Any business the %(region)s can benefit from online exposure and
        email distribution. Show the coupons you've printed from %(domain)s to
        the businesses you visit. The following are national or regional
        offers.""",
        9: """10 %(market)s Coupons in every weekly Email Flyer! Make sure they
        include a local business you visit. Print this Flyer and show it to the
        business owner. The following offers are available everywhere.""",
        10: """Get coupons from the best %(market)s businesses. Tell them to use
        %(domain)s to boost traffic. The following offers are available
        everywhere. """,
        11: """Get offers from the %(market)s businesses you know. Look for them
        on %(domain)s. The following offers are available to the %(region)s or
        anywhere in the world.""",
        }
    position = week % len(switch)
    return {'national_text': switch[position] % {
        'market': flyer.site.name,
        'domain': flyer.site.domain,
        'region': flyer.site.region
        }}

def send_flyers_this_week():
    """
    Check for approved flyers that have not been sent and are scheduled to be
    send today, and pass each to send_flyer.
    """
    LOG.debug('getting all valid flyers')
    send_date = datetime.date.today()
    flyers = Flyer.objects.filter(send_date=send_date, send_status='0',
        is_approved=True).order_by('site__id')
    flyer_log = []
    total_recipients = 0
    subject = "Flyer send results for %s" % datetime.date.today()
    LOG.debug('got flyers, gonna do something with them')
    if flyers:
        send_start_time = datetime.datetime.now()
        for flyer in flyers:
            # Make sure flyer is unsent and not currently sending
            send_check_flyer = Flyer.objects.get(id=flyer.id)
            if send_check_flyer.send_status == '0':
                # Set status to "sending" to prevent double-taps
                flyer.send_status = '1'
                flyer.save()
                flyer.start_time = datetime.datetime.now()
                LOG.info('Prepping flyer %s' % flyer.id)
                context = get_national_text(flyer)
                send_flyer(flyer=flyer, context=context)
                flyer.finish_time = datetime.datetime.now()
                flyer.duration = flyer.finish_time - flyer.start_time
                flyer_log.append([flyer.site.domain, flyer.num_recipients,
                    flyer.duration.seconds])
                total_recipients += flyer.num_recipients
            else:
                LOG.warning('Flyer %s seems to be sending/sent already!' % 
                    flyer.id)
        if total_recipients:
            total_duration = datetime.datetime.now() - send_start_time
            flyer_log.append(['Total', total_recipients, '%d (minutes) ' %
                (total_duration.seconds/60)])
            subject = " %s flyers sent to %d markets on %s" % (
                str(total_recipients), flyers.count(), datetime.date.today())
        message = ''
    else:
        message = "There are no unsent, approved flyers available to send."
        LOG.warning(message)
    if not settings.DEBUG:
        send_email(template='admin_flyer-results', 
            site=Site.objects.get(id=1),
            context={'to_email': settings.NOTIFY_FLYER_SEND_REPORT,
                'subject': subject, 'show_unsubscribe': False,
                'flyer_log': flyer_log, 'warning': message})

def flyer_sent(flyer, num_recipients):
    """
    Perform cleanup/maintenance operations after a successful flyer send.
    
    Set num_recipients on flyer.
    Set is_sent = True on flyer.
    Updates service date on newly sent, paid coupons.
    
    Note: "recipients" here is a count of users that we sent to, not how many
    emails were actually received. 
    """
    flyer.num_recipients = num_recipients
    flyer.send_status = '2'
    flyer.send_datetime = datetime.datetime.now()
    flyer.save()
    LOG.debug('Checking/adding service dates for coupons in flyer %d' %
        flyer.id)
    for flyer_coupon in flyer.flyer_coupons.all():
        coupon_id = flyer_coupon.coupon.id
        LOG.debug("checking on coupon %d" % coupon_id)
        # See if the coupon has an order_item associated with it.
        try:
            order_item = OrderItem.objects.filter(item_id=coupon_id)[0]
            # If so, see if the coupon has been sent before. If not, set the
            # service date to now.
            used_before = FlyerCoupon.objects.filter(coupon__id=coupon_id,
                    flyer__send_status__gt=1)
            if used_before:
                LOG.debug('Coupon %d sent before, keeping original'
                    ' service date: %s' % (coupon_id, order_item.end_datetime))
            else:
                LOG.debug("Adding current service date for item %d" % 
                    coupon_id)
                order_item.end_datetime = datetime.datetime.now()
                order_item.save()
        # If not, we don't worry about a service date.
        except IndexError:
            LOG.debug('Coupon %d has no order item associated, skipping' % 
                coupon_id)

def get_coupon_sent_dates(coupon_id):
    """
    Takes a coupon id and returns a list of dates on which the coupon was sent 
    out in a flyer.
    """
    return FlyerCoupon.objects.filter(coupon__id=coupon_id,
        flyer__send_status__gt=1).values_list('flyer__send_date')

def deliver_multi_flyers(email, *args):
    """
    Send a list of flyers to an email, since one email address can't (currently)
    be signed up for flyers in more than one market. 
    Use-case: Danielle requested a copy of ~10 flyers each week for sales/
    customer service purposes.
    
    Takes an email address as first argument and then up to 8 unique site name
    pieces as further arguments, ex:
    self('jerm@example.com','hudsonvalley','triangle','nashville')
    
    The args are matched against domainname.
    """
    if args:
        for domain in args:
            try:
                site = Site.objects.get(domain__icontains=domain)
                flyer = Flyer.objects.filter(site=site).latest()
                LOG.info("Sending flyer for %s to %s" % (domain, email))
                send_flyer(flyer, email)
            except Site.MultipleObjectsReturned:
                LOG.warning("""WARNING: multiple results returned for '%s', 
                    please provide a more unique key""" % domain)
            except Site.DoesNotExist:
                LOG.warning("%s doesn't seem to exist" % domain)
            except Flyer.DoesNotExist:
                LOG.info("%s doesn't seem to have any flyers (yet?)" % domain)

def get_coupons_scheduled_flyers(coupon, slot_content_type, **kwargs):
    """
    Predicts the flyer send dates based on what the current order items are. 
    Flyers are associated with slots. If an order_items content type is of type
    'slot' with product.id == 1 that means the flyer has not been sent yet for 
    this coupon that is currently associated with said slot. Thus telling us 
    that this coupon still has flyers pending to get sent out every 7 days.
    Paramater pack indicates how many of the future flyers to retrieve.
    """
    pack = kwargs.get('pack', False)
    site = coupon.offer.business.advertiser.site
    try:
        coupon = Coupon.current_coupons.get_current_coupons_by_site(
            site).get(id=coupon.id)
        now = datetime.datetime.now()
        slot_time_frames = coupon.slot_time_frames.all().filter(
                start_datetime__lt=now).filter(
                    Q(end_datetime__gt=now) | Q(end_datetime=None))
        slot_id = slot_time_frames[0].slot.id
        purchased_flyers_count = OrderItem.objects.filter(
            item_id=slot_id, product=1, content_type=slot_content_type).count()
        if not purchased_flyers_count:
            return ''
        next_send_date = next_flyer_date()
        flyers_scheduled = []
        counter = 0
        offset = 0
        while counter <= purchased_flyers_count:
            flyer_date = format_date_for_dsp(
                next_send_date + datetime.timedelta(days=offset))
            flyers_scheduled.append(flyer_date)
            if pack and (counter + 1) >= pack:
                # We have the max number of flyers our caller can handle.
                break
            counter += 1
            offset += 7
        return flyers_scheduled
    except Coupon.DoesNotExist:
        return ''

def resend_flyer_report(recipients=None):
    """ Resend flyer send report of today to [recipients] or
    settings.NOTIFY_FLYER_SEND_REPORT
    """
    flyer_log = []
    total_recipients = 0
    flyers = Flyer.objects.filter(send_date=datetime.datetime.today().date(), 
        send_status=2)
    for flyer in flyers:
        flyer.duration = 'NA'
        flyer_log.append([flyer.site.domain, flyer.num_recipients, 0])
        total_recipients += flyer.num_recipients
    flyer_log.append(['Total', total_recipients, 'NA'])
    subject = "UPDATED - %s flyers sent to %d markets on %s" % (
        str(total_recipients),
        flyers.count(), datetime.date.today())
    message = ''
    if recipients is None:
        recipients = settings.NOTIFY_FLYER_SEND_REPORT
    send_email(template='admin_flyer-results', 
        site=Site.objects.get(id=1),
        context={'to_email': recipients,
            'subject': subject, 'show_unsubscribe': False,
            'flyer_log': flyer_log, 'warning': message})

def get_recent_flyer(site):
    """ Get the most recent sent flyer from this site. """
    last_flyer_sent = latest_flyer_datetime(site, only_sent_status=True).date()
    try:
        latest_flyer = Flyer.objects.filter(
            site=site, send_date=last_flyer_sent, send_status=2)[0]
    except IndexError:
        latest_flyer = None
    return latest_flyer
