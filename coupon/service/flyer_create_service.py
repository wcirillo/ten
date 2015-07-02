""" Service functions for creating flyers. """

import datetime
import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError
from django.db import IntegrityError, transaction
from django.db.models import Min

from coupon.models import (Coupon, CouponType, Flyer, FlyerCoupon,
    FlyerSubdivision)
from coupon.service.flyer_service import (get_flyer_placement_coupons,
    latest_flyer_datetime)
from geolocation.models import USCity, USZip

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

MAX_COUNT = 10

def min_days_away():
    """ For coupon expiration. """
    return datetime.datetime.today() + datetime.timedelta(days=4) 
    
def min_days_past():
    """ Allows wiggle room between iterations of create_flyers_this_week() """
    return datetime.datetime.today() - datetime.timedelta(days=5)

def append_coupon_to_flyer(flyer, coupon, max_count=MAX_COUNT):
    """ Attach a coupon to a flyer.
    Returns boolean: Does the flyer need more coupons?
    """
    @transaction.commit_on_success
    def do_append(flyer, coupon):
        """ Create a flyer_coupon. """
        try:
            FlyerCoupon.objects.create(
                flyer=flyer, coupon=coupon, rank=flyer.flyer_coupons.count() + 1
            )
            LOG.debug('appended %s to %s' % (coupon, flyer))
        except IntegrityError:
            transaction.rollback()
            LOG.debug('failed to append %s to %s' % (coupon, flyer))
            return
        return
    
    LOG.debug('appending %s to %s' % (coupon, flyer))
    if flyer.flyer_coupons.count() < max_count:
        do_append(flyer, coupon)
        # In fact, the flyer might be full now. Catch that on next iteration.
        return True
    return False

def conditionally_append_coupon(flyer, coupon, max_count=MAX_COUNT):
    """ Attach a coupon to a flyer if the business is not already in the flyer.

    Returns two boolean:
        1) Does the flyer need more coupons?
        2) Was this coupon skipped because the business is already in this
            flyer?
    """
    if coupon.offer.business.id in flyer.flyer_coupons.values_list(
            'coupon__offer__business__id', flat=True):
        LOG.debug('Skipping for biz already in flyer: %s' % coupon)
        return True, True
    else:
        return append_coupon_to_flyer(flyer, coupon, max_count), False

def conditionally_append_coupons(flyer, coupons, skipped_list,
        max_count=MAX_COUNT):
    """ Conditionally attach these coupons until no more are needed. """
    need_more = True
    while need_more:
        for coupon in coupons:
            need_more, skipped = conditionally_append_coupon(flyer, coupon,
                max_count)
            if skipped:
                skipped_list.append(coupon)
        break
    return need_more, skipped_list

def get_coupons_for_flyer(site):
    """ Select coupons that are eligible for the current flyer for this site.
    """
    zips = list(USZip.objects.get_zips_this_site(site))
    # Old phase 1 logic. Does not use FlyerPlacement model.
    if site.phase == 1:
        flyer_placement_coupons = list(
            Coupon.current_coupons.get_current_coupons_by_site(site).filter(
                coupon_type__coupon_type_name='Paid',
                is_approved=True,
                slot_time_frames__slot__in=site.order_items.filter(
                    product=1,
                    content_type=ContentType.objects.get(
                        app_label='coupon', model='slot')
                ).values('item_id')
            ).values_list('id', flat=True))
        LOG.debug('flyer_placement_coupons %s' % flyer_placement_coupons)
    else:
        # Here, flyer placements are those that are site wide.
        flyer_placements = site.flyer_placements.filter(
            flyer_placement_subdivisions=None)
        flyer_placement_coupons = list(get_flyer_placement_coupons(
            flyer_placements).values_list('id', flat=True))
    media_partner_coupons = list(Coupon.objects.distinct().filter(
        is_approved=True,
        start_date__gt=latest_flyer_datetime(site, only_sent_status=True),
        expiration_date__gt=min_days_away(),
        coupon_type__coupon_type_name='MediaPartner',
        location__location_zip_postal__in=zips
        ).values_list('id', flat=True))
    coupon_ids = (flyer_placement_coupons + media_partner_coupons)
    coupons = Coupon.objects.filter(id__in=coupon_ids) 
    # How many are paid, etc?
    coupons_by_type = {}
    for coupon_type in CouponType.objects.exclude(
        coupon_type_name__in=('Abandoned', 'In Progress')):
        coupons_by_type[coupon_type.coupon_type_name] = coupons.filter(
            coupon_type=coupon_type)
    # National ads here are aberrant; wtf is a local national ad?
    # But prefer it over national ads.
    LOG.debug('coupons_by_type: %s' % coupons_by_type)
    return coupons, coupons_by_type

def append_coupons_to_flyer(site, flyer, coupons, coupons_by_type, 
        national_coupons):
    """ Add these coupons to this flyer until it is full.
    
    coupons = A QuerySet of coupons for this flyer.
    coupons_by_type = a dictionary with coupon type names as keys and QuerySets
        as values, with each of these being a subset of coupons.
    
    "Current coupons" are coupons in a current time frame of a current slot.
    
    Business rules:
    - Maximum 10 coupons per flyer.
    
    Coupons are selected to be in the flyer in the following preference:

    All of these get in the flyer:
    - Coupons paid to be in this flyer.
    - Media partner coupons.

    For the following, prefer businesses that are not in this flyer yet:
    - Current coupons where slot ends this week.
    - Current coupons that have never been in a flyer.
    - Current coupons, ordered by most time since the last time it was in a 
        flyer to least.

    Then finally:
    - National coupons, newest first.
    """
    admin_data = []
    # In Phase 2, this flyer may already have coupons in it.
    excluding = list(flyer.flyer_coupons.values_list('coupon_id', flat=True))
    need_more = True
    # Coupons skipped because the business already exists in this flyer:
    skipped_list = []
    while need_more:
        for coupon in coupons_by_type['Paid']|coupons_by_type['MediaPartner']:
            need_more = append_coupon_to_flyer(flyer, coupon)
        # Slot ends this week:
        excluding += list(coupons.values_list('id', flat=True))
        LOG.debug('now excluding these ids: %s' % excluding)
        more_coupons = Coupon.current_coupons.get_current_coupons_by_site(
            site).filter(
                is_approved=True,
                slot_time_frames__slot__end_date__gte= \
                    datetime.datetime.today() - \
                    datetime.timedelta(days=7)).exclude(id__in=excluding)
        LOG.debug('coupons in slots ending this week: %s' % more_coupons)
        need_more, skipped_list = conditionally_append_coupons(flyer,
            more_coupons, skipped_list)
        excluding += list(more_coupons.values_list('id', flat=True))
        LOG.debug('now excluding these ids: %s' % excluding)
        # Has never been in a flyer:
        more_coupons = Coupon.current_coupons.get_current_coupons_by_site(
            site).filter(
                is_approved=True).exclude(id__in=excluding).exclude(id__in=
                    Coupon.objects.distinct().filter(flyers__site=site, 
                        flyers__send_status='2'))
        LOG.debug('coupons that have never been in a flyer: %s' % more_coupons)
        need_more, skipped_list = conditionally_append_coupons(flyer,
            more_coupons, skipped_list)
        excluding += list(more_coupons.values_list('id', flat=True))
        LOG.debug('now excluding these ids: %s' % excluding)
        # Since its been in a flyer latest, most time passed to least:
        try:
            more_coupons = Coupon.current_coupons.get_current_coupons_by_site(
                site).filter(
                    is_approved=True).exclude(id__in=excluding).annotate(
                    last_flyer=Min('flyer_coupons__flyer__create_datetime')
                    ).order_by('-last_flyer')
            excluding += list(more_coupons.values_list('id', flat=True))
            LOG.debug('now excluding these ids: %s' % excluding)
        except FieldError:
            # If there were no more coupons, the annotation is never done and
            # cause a FieldError on the ordering.
            more_coupons = []
        LOG.debug('Its been a while for these coupons: %s' % more_coupons)
        need_more, skipped_list = conditionally_append_coupons(flyer,
            more_coupons, skipped_list)
        # Coupons that have been skipped so far to avoid a business appearing
        # twice will now get in, before moving on to national coupons.
        for group in (skipped_list, coupons_by_type['National'],
            national_coupons.exclude(id__in=excluding)):
            for coupon in group:
                need_more = append_coupon_to_flyer(flyer, coupon)
        break
    if not flyer.flyer_coupons.count():
        flyer.delete()
        LOG.debug('%s will get no flyer... no coupons.' % site)
    else:
        # Building this dict for email report.
        admin_data.append('%s, %s' % 
            (flyer.site.name, flyer.flyer_subdivisions.all()))
        for key, value in coupons_by_type.iteritems():
            if len(value) > 0:
                admin_data.append(' ...%d %s coupon(s)' % (len(value), key))
    return admin_data

def create_flyer_this_site(site, send_date, coupons, coupons_by_type,
        national_coupons):
    """ Create a flyer for a given site. Relevant to Phase 1. """
    admin_data = []
    flyer = Flyer.objects.create(site=site, send_date=send_date)
    admin_data.extend(append_coupons_to_flyer(site, flyer, coupons, 
        coupons_by_type, national_coupons))
    return admin_data
    
def clone_flyer(flyer, current_coupon, subdivision_model,
        diverging_geolocation_ids):
    """ In the flyer creation process, duplicate a given flyer. Coupons of the
    original are copied to the clone. Current coupon is added to the clone.
    Flyer subdivisions of subdivision_model are split, with
    diverging_geolocation_ids moving from the original to the clone.
    """
    clone = Flyer.objects.get(id=flyer.id)
    clone.id = None
    clone.save()
    LOG.debug('%s cloned from %s' % (clone, flyer))
    # Cloned flyer should include coupons of the original, plus this.
    for flyer_coupon in flyer.flyer_coupons.all():
        FlyerCoupon.objects.create(flyer=clone, 
            coupon=flyer_coupon.coupon)
        LOG.debug('%s copied to %s' % (flyer_coupon.coupon, clone))
    FlyerCoupon.objects.create(flyer=clone, coupon=current_coupon)
    LOG.debug('%s added to %s' % (current_coupon, clone))
    # These two flyers will go to two separate subdivision groups:
    # Clone will get the flyer_placement subdivisions, original
    # flyer will loose these and keep the remaining subdivisions.
    # Move the flyer_placement_subdivisions to the clone.
    for flyer_subdivision in flyer.flyer_subdivisions.filter(
            geolocation_type__model=subdivision_model,
            geolocation_id__in=diverging_geolocation_ids):
        flyer_subdivision.flyer = clone
        flyer_subdivision.save()
        LOG.debug('Subdivision %s moved from %s to %s.' % (
            flyer_subdivision, flyer, clone))

def add_subdivisions_to_catchall(catchall_flyer, subdivision_model,
        subdivision_ids):
    """ Add these subdivisions, of this ContentType model, which are not covered
    by any other flyer for the same site and send_date, to this catchall_flyer.
    """
    subdivision_type = ContentType.objects.get(model=subdivision_model)
    LOG.debug('Will add %s %s to %s' % (subdivision_type, subdivision_ids,
        catchall_flyer))
    for subdivision_id in subdivision_ids:
        FlyerSubdivision.objects.create(flyer=catchall_flyer,
            geolocation_id=subdivision_id,
            geolocation_type=subdivision_type)
        LOG.debug('%s %s added to %s' % (subdivision_type, subdivision_id,
            catchall_flyer))

def process_smaller_subdivision(current_coupon, flyer_placement,
        subdivision_dict):
    """ Process the subdivisions within a subdivision. Counties can have cities
    and zips. A city can have zips.

    subdivision_dict is required to have these keys: subdivision_model,
        subdivision_id, smaller_subdivision_model, smaller_subdivision_ids.

    For flyer placement having a subdivision_id of ContentType subdivision_type,
    whose smaller_subdivision_type in its entirety is considered to be the list
    smaller_subdivision_ids, add current_coupon to the minimal set of flyers.

    For smaller_subdivision_ids that are already know to be processed for this
    coupon, exclude them from smaller_subdivision_ids before passing it into
    here.
    """
    subdivision_type = ContentType.objects.get(
        model=subdivision_dict.pop('subdivision_model'))
    subdivision_id = subdivision_dict.pop('subdivision_id')
    smaller_subdivision_type = ContentType.objects.get(
        model=subdivision_dict.pop('smaller_subdivision_model'))
    smaller_subdivision_ids = subdivision_dict.pop('smaller_subdivision_ids')
    LOG.debug('Processing %s within %s %s' % (smaller_subdivision_type.model,
        subdivision_type.model, subdivision_id))
    LOG.debug('smaller_subdivision_ids: %s' % smaller_subdivision_ids)
    already_processed = []
    to_be_processed = []
    matches_flag = False # Did we find any smaller subdivision matches?
    for flyer in flyer_placement.site.flyers.distinct().filter(
            send_date=flyer_placement.send_date,
            flyer_subdivisions__geolocation_type= \
                smaller_subdivision_type,
            flyer_subdivisions__geolocation_id__in= \
                smaller_subdivision_ids):
        # This flyer contains at least one smaller subdivision within this
        # subdivision.
        matches_flag = True
        LOG.debug('%s needs to be looked at...' % flyer)
        diverging_geolocation_ids = flyer.flyer_subdivisions.filter(
                geolocation_type=smaller_subdivision_type,
                geolocation_id__in=smaller_subdivision_ids
            ).values_list('geolocation_id', flat=True)
        # Does it have any smaller subdivisions *not* in this subdivision?
        if len(flyer.flyer_subdivisions.filter(
                    geolocation_type=smaller_subdivision_type
                ).exclude(geolocation_id__in=smaller_subdivision_ids
                ).values_list('geolocation_id', flat=True)):
            # Clone this flyer.
            clone_flyer(flyer, current_coupon, subdivision_type,
                diverging_geolocation_ids)
        else:
            # This flyer is a subset of the subdivision. Add this coupon to
            # it.
            FlyerCoupon.objects.create(flyer=flyer, coupon=current_coupon)
            LOG.debug('%s added to %s' % (current_coupon, flyer))
        # These subdivisions are now processed, so do not need a flyer
        # created for them.
        to_be_processed += list(
            set(smaller_subdivision_ids).difference(
                set(diverging_geolocation_ids)))
        already_processed += diverging_geolocation_ids
    LOG.debug('Already processed: %s' % already_processed)
    LOG.debug('To be processed: %s' % to_be_processed)
    return already_processed, to_be_processed, matches_flag

def process_city(catchall_flyer, city_id, current_coupon, flyer_placement,
        already_processed):
    """ Cover all the zip codes in this city to make sure they get a flyer with
    this coupon, excluding already_processed zips.

    args:
        catchall_flyer = A flyer that will get all the subdivisions of this
            flyer_placement not already covered by other flyers.
    """
    LOG.debug('Processing city %s, skipping %s' % (city_id, already_processed))
    # Process zips within this city.
    city_zip_ids = list(USZip.objects.filter(us_city__id=city_id
        ).exclude(id__in=already_processed).values_list('id', flat=True))
    LOG.debug('city_zip_ids: %s' % city_zip_ids)
    if len(city_zip_ids):
        subdivision_dict = {
            'subdivision_model': 'uscity',
            'subdivision_id': city_id,
            'smaller_subdivision_model': 'uszip',
            'smaller_subdivision_ids': city_zip_ids,
        }
        city_zips_to_be_processed, matches_flag = process_smaller_subdivision(
            current_coupon, flyer_placement, subdivision_dict)[1:3]
        if city_zips_to_be_processed:
            add_subdivisions_to_catchall(catchall_flyer, 'uszip',
                city_zips_to_be_processed)
        elif not matches_flag:
            # Add the city itself as a subdivision.
            add_subdivisions_to_catchall(catchall_flyer, 'uscity', [city_id])
    else:
        LOG.debug('All zips of city %s already processed.' % city_id)

def process_county(catchall_flyer, county_id, current_coupon, flyer_placement):
    """ Cover all cities and zip codes in this county to make sure they get a
    flyer with this coupon.
    
    args:
        catchall_flyer = A flyer that will get all the subdivisions of this 
            flyer_placement not already covered by other flyers.
     
    If zip codes in this county are already in a flyer that has zo zip codes
    outside the county, add this coupon to that flyer.
    If zip codes in this county are in a flyer that also has other zip codes,
    divide that flyer into two (external zips, internal zips) and add this 
    coupon to the flyer with external zips.
    For all zips in this county not already covered by a flyer, add them to the
    catchall_flyer.

    This must also be done for cities of a county, and zip codes of a city.
    """
    LOG.debug('Processing county %s' % county_id)
    # Process cities within this county.
    county_city_ids = list(USCity.objects.filter(
        us_county__id=county_id).values_list('id', flat=True))
    # Process zips within this county.
    county_zip_ids = list(USZip.objects.filter(
        us_county__id=county_id).values_list('id', flat=True))
    # Accumulate city ids we still need to handle.
    subdivision_dict = {
        'subdivision_model': 'uscounty',
        'subdivision_id': county_id,
        'smaller_subdivision_model': 'uscity',
        'smaller_subdivision_ids': county_city_ids,
    }
    county_cities_to_be_processed, matched_cities = \
        process_smaller_subdivision(current_coupon, flyer_placement,
            subdivision_dict)[1:3]
    LOG.debug('county_cities_to_be_processed: %s' %
        str(county_cities_to_be_processed))
    subdivision_dict = {
        'subdivision_model': 'uscounty',
        'subdivision_id': county_id,
        'smaller_subdivision_model': 'uszip',
        'smaller_subdivision_ids': county_zip_ids,
    }
    zips_already_processed, county_zips_to_be_processed, matched_zips = \
        process_smaller_subdivision(current_coupon, flyer_placement,
            subdivision_dict)
    LOG.debug('county_zips_to_be_processed: %s' %
        str(county_zips_to_be_processed))
    if county_city_ids == county_cities_to_be_processed:
        if county_zips_to_be_processed == county_zip_ids:
            add_subdivisions_to_catchall(catchall_flyer, 'uscounty',
                [county_id])
        else:
            leftover_zips = set(county_zips_to_be_processed).intersection(
                set(county_zip_ids))
            LOG.debug('Leftover zips: %s' % leftover_zips)
            add_subdivisions_to_catchall(catchall_flyer, 'uszip',
                leftover_zips)
    elif county_cities_to_be_processed:
        for city_id in county_cities_to_be_processed:
            process_city(catchall_flyer, city_id, current_coupon,
                flyer_placement, zips_already_processed)
    elif not matched_cities and not matched_zips:
        add_subdivisions_to_catchall(catchall_flyer, 'uscounty', [county_id])

def split_subdivision(flyer, subdivision_model, subdivisions):
    """ For this flyer, replace the subdivisions of ContentType subdivision_type
    with all of its component next smaller subdivisions; ie a county will be
    changed to all the cities within that county, and a city will be replaced
    with all the zip codes within that city.

    subdivision_model = 'uscounty' or 'uscity'.

    subdivisions = a QuerySet of distinct subdivisions of subdivision_type. For
        each of these that are related to flyer, split that subdivision into its
        component subdivisions of the next smaller type: a county is split into
        cities, a city is split into zips.
    """
    LOG.debug('Splitting %s %s of %s' % (
        subdivision_model, subdivisions, flyer))
    for flyer_subdivision in flyer.flyer_subdivisions.filter(
            geolocation_type__model=subdivision_model,
            geolocation_id__in=subdivisions):
        LOG.debug('Removing %s from %s' % (flyer_subdivision, flyer))
        flyer_subdivision.delete()
        if subdivision_model == 'uscounty':
            geolocation_type = ContentType.objects.get(model='uscity')
            for city_id in list(USCity.objects.filter(
                    us_county__id=flyer_subdivision.geolocation_id
                    ).values_list('id', flat=True)):
                LOG.debug('Adding city_id %s to %s' % (city_id, flyer))
                FlyerSubdivision.objects.create(flyer=flyer,
                    geolocation_id=city_id,
                    geolocation_type=geolocation_type)
        elif subdivision_model == 'uscity':
            geolocation_type = ContentType.objects.get(model='uszip')
            for zip_id in list(USZip.objects.filter(
                    us_city__id=flyer_subdivision.geolocation_id
                    ).values_list('id', flat=True)):
                LOG.debug('Adding zip_id %s to %s' % (zip_id, flyer))
                FlyerSubdivision.objects.create(flyer=flyer,
                    geolocation_id=zip_id,
                    geolocation_type=geolocation_type)

def process_flyer_sub(subdivision, subdivision_model, flyer_placement,
        current_coupon, site):
    """ Process this flyer placement subdivision. Creates a new flyer if there
    is no existing flyer for any subdivision of this flyer_placement. Updates a
    flyer if one exists for this subdivision. Returns a list of subdivisions it
    can process now, and returns the subdivision if it should be delayed to be
    processed by the caller.
    """
    # A list of other subdivision geolocation ids of this flyer placement that 
    # we are processing here, so we can ignore elsewhere.
    already_processed = []
    # A subdivision that we are skipping here, because no flyer exists yet for
    # it. The caller will collect these and build one flyer for them.
    to_be_processed = None
    # Do I already have a flyer for this sub? There should be at most one:
    # cannot send multiple flyers to any zip per week.
    try:
        flyer = site.flyers.get(send_date=flyer_placement.send_date,
            flyer_subdivisions__geolocation_type__model=subdivision_model,
            flyer_subdivisions__geolocation_id=subdivision.geolocation_id)
        flyer_placement_geolocation_ids = set(
            flyer_placement.flyer_placement_subdivisions.filter(
                geolocation_type__model=subdivision_model).values_list(
                'geolocation_id', flat=True))
        flyer_geolocation_ids = set(flyer.flyer_subdivisions.filter(
                geolocation_type__model=subdivision_model).values_list(
                'geolocation_id', flat=True))   
        LOG.debug('Found matching flyer %s' % flyer)
        LOG.debug('Flyer placement geolocations %s' % (
            flyer_placement_geolocation_ids))
        LOG.debug('Flyer geolocations %s' % flyer_geolocation_ids)
        if flyer_placement_geolocation_ids == flyer_geolocation_ids:
            # Best case: an existing flyer for the subdivisions I need.
            LOG.debug('Exact match of %s' % flyer)
            FlyerCoupon.objects.create(flyer=flyer, coupon=current_coupon)
            LOG.debug('%s added to %s' % (current_coupon, flyer))
            already_processed += list(flyer_placement_geolocation_ids)
            return already_processed, to_be_processed
        elif flyer_placement_geolocation_ids.issubset(flyer_geolocation_ids):
            # Here, flyer_placement subdivisions are a subset of flyer
            # subdivisions. Clone this flyer.
            LOG.debug('The subdivisions needed are a subset of %s.' % flyer)
            clone_flyer(flyer, current_coupon, subdivision_model,
                flyer_placement_geolocation_ids)
            # Pop this member from subdivisions since its now been processed 
            # ahead of its turn.
            already_processed += list(flyer_placement_geolocation_ids)
            return already_processed, to_be_processed
        elif flyer_geolocation_ids.issubset(flyer_placement_geolocation_ids):
            # Here, the flyer subdivisions are a subset of the divisions I need.
            # Add this coupon to this flyer.
            LOG.debug('%s is a subset of the subdivisions needed.' % flyer)
            FlyerCoupon.objects.create(flyer=flyer, coupon=current_coupon)
            LOG.debug('%s added to %s' % (current_coupon, flyer))
            already_processed += list(flyer_geolocation_ids)
            return already_processed, to_be_processed
        else:
            # Here the flyer intersects the zips I need.
            LOG.debug('%s intersects the subdivisions needed.' % flyer)
            matching_ids = flyer_geolocation_ids.intersection(
                flyer_placement_geolocation_ids)
            clone_flyer(flyer, current_coupon, subdivision_model, matching_ids)
            already_processed += list(matching_ids)
            return already_processed, to_be_processed
    except Flyer.DoesNotExist:
        LOG.debug('No flyers match %s yet.' % subdivision)
    to_be_processed = subdivision
    return already_processed, to_be_processed

def create_flyer_uncovered_subs(site, send_date, subdivision_dict):
    """ Create a flyer and add subdivisions to it for these counties, cities,
    and zip codes, excluding known covered zips covered_zip_ids.

    subdivision_dict is required to have these keys: counties, cities, zips,
        covered_zip_ids
    """
    zip_type = ContentType.objects.get(model='uszip')
    city_type = ContentType.objects.get(model='uscity')
    county_type = ContentType.objects.get(model='uscounty')
    if subdivision_dict['counties'] or subdivision_dict['cities'] \
    or subdivision_dict['zips']:
        flyer = Flyer.objects.create(site=site, send_date=send_date)
        LOG.debug('%s created for the unsold parts of %s' % (flyer, site))
        for county_id in subdivision_dict['counties']:
            LOG.debug('Adding unsold county %s to %s' % (county_id, flyer))
            FlyerSubdivision.objects.create(flyer=flyer,
                geolocation_id=county_id, geolocation_type=county_type)
        for city_id in subdivision_dict['cities']:
            # A zip within this city might already have a flyer.
            # Squash this from a GeoValuesListQuerySet to list for comparison.
            city_zip_ids = list(USZip.objects.filter(us_city__id=city_id
                ).values_list('id', flat=True))
            uncovered_zip_ids = sorted(
                set(city_zip_ids) - set(subdivision_dict['covered_zip_ids']))
            if city_zip_ids == uncovered_zip_ids:
                LOG.debug('Adding unsold city %s to %s' % (city_id, flyer))
                FlyerSubdivision.objects.create(flyer=flyer,
                    geolocation_id=city_id, geolocation_type=city_type)
            else:
                subdivision_dict['zips'] += uncovered_zip_ids
        for zip_id in subdivision_dict['zips']:
            LOG.debug('Adding unsold zip %s to %s' % (zip_id, flyer))
            FlyerSubdivision.objects.create(flyer=flyer,
                geolocation_id=zip_id, geolocation_type=zip_type)

def create_flyer_unsold_subs(site, send_date):
    """ Once flyers have been created for site in phase 2 and this send_date
    according to sold flyer_placements, create a flyer to cover all the unsold
    subdivisions of this site.
    """
    zips_without_flyer = []
    cities_without_flyer = []
    counties_without_flyer = []
    covered_zip_ids = None
    covered_zip_ids_accumulator = []
    for county in site.us_county.all():
        city_matches_flag = False
        try:
            FlyerSubdivision.objects.get(flyer__site=site, 
                flyer__send_date=send_date,
                geolocation_type__model='uscounty',
                geolocation_id=county.id)
            # Flyer already exists for exactly this county.
            continue
        except FlyerSubdivision.DoesNotExist:
            county_city_ids = USCity.objects.filter(
                us_county__id=county.id).values_list('id', flat=True)
            county_zip_ids = USZip.objects.filter(
                us_county__id=county.id).values_list('id', flat=True)
            if county_city_ids:
                covered_city_ids = FlyerSubdivision.objects.filter(
                    flyer__site=site,
                    flyer__send_date=send_date,
                    geolocation_type__model='uscity',
                    geolocation_id__in=county_city_ids
                    ).values_list('geolocation_id', flat=True)
                if covered_city_ids:
                    city_matches_flag = True
                    cities_without_flyer += sorted(
                        set(county_city_ids) - set(covered_city_ids))
                    # Cities that are covered are also zips that are covered.
                    county_zip_ids = USZip.objects.filter(
                        us_county__id=county.id).exclude(
                        us_city__id__in=covered_city_ids).values_list(
                        'id', flat=True)
            if county_zip_ids:
                covered_zip_ids = FlyerSubdivision.objects.filter(
                    flyer__site=site,
                    flyer__send_date=send_date,
                    geolocation_type__model='uszip',
                    geolocation_id__in=county_zip_ids
                    ).values_list('geolocation_id', flat=True)
                if covered_zip_ids:
                    zips_without_flyer += sorted(
                        set(county_zip_ids) - set(covered_zip_ids))
                elif not city_matches_flag:
                    counties_without_flyer.append(county.id)
            elif not city_matches_flag:
                counties_without_flyer.append(county.id)
            if covered_zip_ids:
                covered_zip_ids_accumulator += covered_zip_ids
    subdivision_dict = {
        'counties': counties_without_flyer,
        'cities': cities_without_flyer,
        'zips': zips_without_flyer,
        # Ensure uniqueness:
        'covered_zip_ids': sorted(set(covered_zip_ids_accumulator))
    }
    create_flyer_uncovered_subs(site, send_date, subdivision_dict)

def split_flyer_subdivisions(flyer_placement, subdivision_model,
        subdivisions):
    """ For this flyer_placement, find all the flyers for the same site and
    send_date having a subdivision of subdivision_type matching subdivisions;
    for any matches, split those flyer subdivisions.
    """
    LOG.debug('Checking for flyers to split for %s.' % subdivision_model)
    done_flyers = []
    # This QuerySet might contain a flyer multiple times.
    for flyer in flyer_placement.site.flyers.filter(
            send_date=flyer_placement.send_date,
            flyer_subdivisions__geolocation_type__model=subdivision_model,
            flyer_subdivisions__geolocation_id__in=subdivisions):
        if flyer not in done_flyers:
            LOG.debug('Found flyer %s for splitting.' % flyer)
            split_subdivision(flyer, subdivision_model, subdivisions)
            done_flyers.append(flyer)

def create_update_flyers_subs(subdivisions, subdivision_model,
        flyer_placement, current_coupon, site):
    """ Create or update the minimal set of flyers to cover these subdivisions.
    
    Determine if a flyer already exists for each subdivision in the given 
    subdivisions. If so, add this subdivision to it. If not, create a flyer for 
    it.
    
    subdivision_model = the models of an allowed ContentType; ie 'uscounty',
    'uscity', 'uszip'.
    
    Any flyers created or updated will have the send_date of this 
    flyer_placement.
    """
    # Are there any flyers that match any of the subdivisions for this flyer 
    # placement?
    LOG.debug('Now working on %s for %s' % (subdivisions, flyer_placement))
    already_processed = [] # A list of subdivision geolocation ids.
    to_be_processed = [] # A list of subdivisions.
    #county_type = ContentType.objects.get(model='uscounty')
    #city_type = ContentType.objects.get(model='uscity')
    if subdivision_model == 'uszip':
        # Check for a flyer for a county or city any of these zips is in.
        # Group these zips by county or city they are in.
        distinct_counties, distinct_cities = zip(*USZip.objects.filter(
                id__in=subdivisions.values_list('geolocation_id', flat=True)
            ).values_list('us_county', 'us_city'))
        split_flyer_subdivisions(flyer_placement, 'uscounty',
            distinct_counties)
        # Check to see if there is a flyer for a city any of these zips is in.
        # This might have just been created, by splitting the county.
        split_flyer_subdivisions(flyer_placement, 'uscity', distinct_cities)
    elif subdivision_model == 'uscity':
        # Check for a flyer for a county any of these cities is in.
        distinct_counties = USCity.objects.filter(
                id__in=subdivisions.values_list('geolocation_id', flat=True)
            ).values_list('us_county')
        split_flyer_subdivisions(flyer_placement, 'uscounty',
            distinct_counties)
    for subdivision in subdivisions:
        if subdivision.geolocation_id not in already_processed:
            LOG.debug('Now processing %s' % subdivision)
            processed_id_list, delayed_process_id = process_flyer_sub(
                subdivision, subdivision_model, flyer_placement, current_coupon,
                site)
            if processed_id_list:
                already_processed.extend(processed_id_list)
            if delayed_process_id:
                to_be_processed.append(delayed_process_id)
            LOG.debug('already processed: %s' % already_processed)
            LOG.debug('to be processed: %s' % to_be_processed)
    if to_be_processed:
        # Create a flyer for these subdivisions.
        flyer = Flyer.objects.create(site=flyer_placement.site,
            send_date=flyer_placement.send_date)
        # If this subdivision is a county, check to see if any of its zip codes
        # are already attached to a flyer.
        if subdivision_model == 'uscounty':
            FlyerCoupon.objects.create(flyer=flyer, coupon=current_coupon)
            LOG.debug('%s added to %s' % (current_coupon, flyer))
            for subdivision in to_be_processed:
                process_county(flyer, subdivision.geolocation_id,
                    current_coupon, flyer_placement)
            # If every zip and county was already covered, delete flyer.
            if not flyer.flyer_subdivisions.count():
                flyer.delete()
        else:
            FlyerCoupon.objects.create(flyer=flyer, coupon=current_coupon)
            LOG.debug('subdivision_model: %s' % subdivision_model)
            geolocation_type = ContentType.objects.get(model=subdivision_model)
            for subdivision in to_be_processed:
                FlyerSubdivision.objects.create(flyer=flyer, 
                    geolocation_id=subdivision.geolocation_id, 
                    geolocation_type=geolocation_type)
            LOG.debug('%s created for %s' % (flyer, to_be_processed))

def create_flyer_this_site_phase1(site, send_date, national_coupons):
    """ Use Phase 1 logic to create a flyer for this site for this week.
    
    In phase 1, the same email flyer is distributed to the entire market.
    """
    LOG.debug('creating flyers for %s using Phase 1 logic.' % site)
    coupons, coupons_by_type = get_coupons_for_flyer(site) 
    admin_data = create_flyer_this_site(site, send_date, coupons,
        coupons_by_type, national_coupons)
    LOG.debug(admin_data)
    return admin_data

def create_flyers_this_site_phase2(site, send_date, national_coupons):
    """ For this site, create minimum set of flyers to contain flyer_placements
    using Phase 2 logic.
    
    Distinct sets of zips will need a flyer:
    Ex: placement A is for zips 1 and 2, 
     pB is for z2 and z3,
     pC is for z4 and z5, 
     pD is for z4 and z5.
     pE is for z6 and z7.
     pF is for z6 and z7.
     pG is for z6.
     
    This will derive this set of flyers:
     flyer 1 to zip 1 includes placement A.
     f2 to z2 includes pA, pB
     f3 to z3 includes pB
     f4 to z4 and z5 includes pC, pD
     f5 to z6 includes pE, pF, and pG
     f7 to z7 includes pE and pF.
    """
    admin_data = []
    flyer_placements = site.flyer_placements.filter(send_date=send_date)
    for flyer_placement in flyer_placements:
        try:
            current_coupon = get_flyer_placement_coupons(flyer_placement)[0]
        except IndexError:
            LOG.warning('flyer_placement %s has no current coupon!' % 
                flyer_placement)
            continue
        # Is it subdivided by zip?
        zip_subs = flyer_placement.flyer_placement_subdivisions.filter(
            geolocation_type__model='uszip')
        # Is it subdivided by city?
        city_subs = flyer_placement.flyer_placement_subdivisions.filter(
            geolocation_type__model='uscity')
        # Is it subdivided by county?
        county_subs = flyer_placement.flyer_placement_subdivisions.filter(
            geolocation_type__model='uscounty')
        if zip_subs:
            create_update_flyers_subs(zip_subs, 'uszip', flyer_placement,
                current_coupon, site)
        if city_subs:
            create_update_flyers_subs(city_subs, 'uscity', flyer_placement,
                current_coupon, site)
        if county_subs:
            create_update_flyers_subs(county_subs, 'uscounty', flyer_placement,
                current_coupon, site)
    # Select the resulting flyers.
    flyers = site.flyers.filter(send_status=0, send_date=send_date)
    if len(flyers) == 0:
        # Site is in Phase 2 but no purchased flyers this week.
        admin_data.extend(create_flyer_this_site_phase1(site, send_date,
            national_coupons))
    else:
        create_flyer_unsold_subs(site, send_date)
        # Now that I have flyers for the site for this week, with correct 
        # flyer_placement subdivisions and coupons related to them, fill unsold 
        # spots in those flyers with logic similar to phase 1.
        coupons, coupons_by_type = get_coupons_for_flyer(site) 
        for flyer in site.flyers.filter(send_date=send_date).order_by('id'):
            admin_data.extend(append_coupons_to_flyer(site, flyer, coupons, 
                coupons_by_type, national_coupons))
    return admin_data
