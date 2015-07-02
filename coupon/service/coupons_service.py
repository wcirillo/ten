""" This file should be associated with all actions that need to be taken in
order to display multiple coupons. 
Ex: (site_coupons, bulk_coupons, all_coupons_this_business...)
"""

import datetime
import logging

from advertiser.models import Location
from common.utils import uniquify_sequence
from coupon.models import Coupon, Slot

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class AllCoupons(object):
    """ Class that helps get different types of coupon results that are ready
    to get displayed back on a template.
    """

    def get_all_coupons(self, site):
        """ Return all_coupons for this site and coupon_ids. """
        coupon_ids = self.get_site_coupons(site, max_results=200)
        coupon_ids, all_coupons = SORT_COUPONS.sorted_coupons(coupon_ids,
            presorted=True)
        self.join_coupon_with_locations(coupon_ids, all_coupons)
        return all_coupons, coupon_ids
    
    def get_site_coupons(self, site, max_results=20):
        """ 
        Return a list of coupon ids that are eligible to be displayed on this
        site.
        """
        coupon_ids = list(Coupon.current_coupons.get_current_coupons_by_site(
            site).values_list('id', flat=True))
        coupon_ids = SORT_COUPONS.sort_coupon_ids(coupon_ids)
        media_partner_coupons = list(self.get_media_partner_coupons(site
            ).values_list('id', flat=True))
        coupon_ids += media_partner_coupons
        coupon_count = len(coupon_ids)
        if coupon_count < max_results:
            national_coupons = list(self.get_national_coupons().values_list(
                'id', flat=True)[:max_results - coupon_count])
            coupon_ids += national_coupons
        return coupon_ids

    @staticmethod
    def get_bulk_coupons(zip_postals=None, excluding=None):
        """
        Returns coupons that have are true for all the following criteria:
            - have a location in zip_postals
            - are not in exclude_ids
            - have a type of 'Bulk'
        
        These are relevant because they have a location in this market.
        """
        if excluding is None:
            excluding = []
        return Coupon.objects.distinct().filter(
                expiration_date__gt=datetime.date.today(),
                location__location_zip_postal__in=zip_postals,
                coupon_type__coupon_type_name='Bulk'
            ).exclude(
                id__in=excluding
            ).order_by('-start_date')
    
    @staticmethod
    def get_media_partner_coupons(site):
        """
        Return (unpaid) media partner coupons on this site.
        """
        return Coupon.objects.distinct().filter(
                expiration_date__gt=datetime.date.today(),
                coupon_type__coupon_type_name='MediaPartner',
                offer__business__advertiser__site=site).order_by('-start_date')
    
    @staticmethod
    def get_national_coupons():
        """ These are unpaid national filler coupons. """
        return Coupon.objects.distinct().filter(
                coupon_type__coupon_type_name='National',
                start_date__lte=datetime.date.today(),
                expiration_date__gt=datetime.date.today(),
                is_approved=True,
            ).order_by('-start_date')

    def get_business_coupons(self, business_id, site):
        """ Return all_coupons for this site and coupon_ids. """
        coupon_ids = self.get_coupons_this_business(business_id, site)
        coupon_ids, all_coupons = SORT_COUPONS.sorted_coupons(coupon_ids,
            presorted=True)
        self.join_coupon_with_locations(coupon_ids, all_coupons)
        return all_coupons, coupon_ids
            
    def get_coupons_this_business(self, business_id, site):
        """ Return all valid coupon_ids for a given business_id and site. """
        coupon_ids = list(
            Coupon.current_coupons.get_current_coupons_by_site(site).filter(
                offer__business__id=business_id).values_list('id', flat=True))
        coupon_ids += list(self.get_national_coupons().filter(
            offer__business__id=business_id).values_list('id', flat=True))
        coupon_ids += list(self.get_media_partner_coupons(site).filter(
            offer__business__id=business_id).values_list('id', flat=True))
        coupon_ids.sort()
        return coupon_ids
    
    @staticmethod
    def build_coupon_location_list(coupon_ids):
        """ Build location lists for coupons in list of coupon_ids for display.
        """
        all_locations = Location.objects.filter(
                coupons__id__in=coupon_ids
            ).exclude(location_city=''
            ).values('location_city', 'coupons__id')
        temp_loc_dict = {}
        for location in all_locations:
            try:
                if location['location_city'] \
                and location['location_city'].lower() \
                not in [x.lower() for x in temp_loc_dict[
                            location['coupons__id']]]:
                    temp_loc_dict[location['coupons__id']].append(
                    str(location['location_city']))
            except KeyError:
                # Add new dict entry.
                temp_loc_dict[location['coupons__id']] = [str(location[ 
                    'location_city'].title())]
        return temp_loc_dict

    def join_coupon_with_locations(self, coupon_ids, all_coupons):
        """ Associate all the locations for these coupons that we are about to
        display. """
        temp_loc_dict = self.build_coupon_location_list(coupon_ids)
        for coupon in all_coupons:
            if temp_loc_dict.get(coupon.id, None):
                coupon.location_list = ','.join(
                    temp_loc_dict[coupon.id]).replace(',', ', ')


class SortCoupons(object):
    """ Class that helps sort coupons. """
    
    def sorted_coupons(self, coupon_ids, presorted=False):
        """
        Convert a list of coupon ids to an ordered list of coupon instances.
        """
        # Make sure coupon_id list does not contain duplicate values.
        coupon_ids = uniquify_sequence(coupon_ids)
        if presorted:
            sorted_coupon_ids = coupon_ids
        else:
            sorted_coupon_ids = self.sort_coupon_ids(coupon_ids)
        coupons = Coupon.objects.filter(id__in=sorted_coupon_ids
            ).select_related('coupon_type', 'offer', 'offer__business')
        # Convert QuerySet to a sorted list of coupons.
        sorted_coupons_ = sorted_coupon_ids[:]
        for coupon in coupons:
            sorted_coupons_[sorted_coupon_ids.index(coupon.id)] = coupon
        return sorted_coupon_ids, sorted_coupons_
    
    @staticmethod
    def sort_coupon_ids(coupon_ids):
        """
        Return the given coupons_ids ranked using the following preference:
         1) Coupons created today, newest first.
         2) Coupons w/ flyer placement this week, newest first.
         3) Date created + 15 days/fb like, + 3 days/print, newest first.
            - This part of the formula is now precomputed and stored in
            coupon.rank_datetime.rank_datetime.
        """
        if not len(coupon_ids):
            return []
        coupons_placed_today = list(Coupon.objects.filter(id__in=coupon_ids,
            coupon_create_datetime__gt=datetime.date.today()).values_list(
            'id', flat=True).order_by('-coupon_create_datetime'))
        LOG.debug('coupons_placed_today: %s' % coupons_placed_today)
        coupons_in_flyer = list(Coupon.objects.filter(id__in=coupon_ids,
            slot_time_frames__slot__id__in=Slot.current_slots.filter(
                flyer_placements__send_date__gt=datetime.date.today(),
                flyer_placements__send_date__lte=datetime.date.today() +
                    datetime.timedelta(7))).values_list(
            'id', flat=True).order_by('-coupon_create_datetime'))
        LOG.debug('coupons_in_flyer: %s' % coupons_in_flyer)
        coupons_rank_dated = list(Coupon.objects.filter(
            id__in=coupon_ids).values_list(
            'id', flat=True).order_by('-rank_datetime__rank_datetime'))
        LOG.debug('coupons_rank_dated: %s' % coupons_rank_dated)
        sorted_coupon_ids = []
        for coupon_id in (coupons_placed_today + coupons_in_flyer +
                coupons_rank_dated):
            if coupon_id not in sorted_coupon_ids:
                sorted_coupon_ids.append(coupon_id)
        LOG.debug('sorted_coupon_ids: %s' % sorted_coupon_ids)
        return sorted_coupon_ids
    
ALL_COUPONS = AllCoupons()  
SORT_COUPONS = SortCoupons()
