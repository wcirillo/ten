""" Coupon service class for displaying coupon stats. """
from datetime import datetime, timedelta

from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

from coupon.models import Coupon
from coupon.service.expiration_date_service import (
    frmt_expiration_date_for_dsp)
from coupon.service.flyer_service import (get_coupons_scheduled_flyers)
from coupon.service.valid_days_service import VALID_DAYS


class CouponPerformance(object):
    """ Class methods to build list of coupon dicts for displaying coupon
    statistics and rendering preview (optionally).
    """
    def __init__(self, **kwargs):
        """ Init for CouponStatistics instance instantiation. """
        # Number of coupons to return
        self.size_limit = kwargs.get('size_limit')
        self.render_preview = kwargs.get('render_preview')
        if kwargs.get('exclude_unpublished'):
            self.omit_coupon_type_list = [1, 7]
        else:
            self.omit_coupon_type_list = []

    def _append_coupon_actions(self, coupons):
        """ Return coupons with appended coupon action data for the following:
        views, clicks, prints, facebook shares.
        """
        coupons = coupons.select_related('offer').extra(
            select={'views': """
                SELECT count
                FROM coupon_couponaction
                WHERE coupon_id = coupon_coupon.id
                AND action_id = 1
                """,
                'clicks': """
                SELECT count
                FROM coupon_couponaction
                WHERE coupon_id = coupon_coupon.id
                AND action_id = 2
                """,
                'prints': """
                SELECT count
                FROM coupon_couponaction
                WHERE coupon_id = coupon_coupon.id
                AND action_id = 3
                """,
                'shares': """
                SELECT count
                FROM coupon_couponaction
                WHERE coupon_id = coupon_coupon.id
                AND action_id = 7
                """,}
            )
        if self.size_limit:
            coupons = coupons[:self.size_limit]
        return coupons

    @staticmethod
    def _get_preview_detail(coupon):
        """ Return dict of coupon detail needed to display a preview. """
        coupon_dict = {
            'default_restrictions': ' '.join(
                coupon.default_restrictions.all().values_list(
                    'restriction', flat=True)),
            'custom_restrictions':
                getattr(coupon, 'custom_restrictions', '')}
        location_list = []
        for location in coupon.location.all():
            location_dict = {
                'location_address1':location.location_address1,
                'location_address2':location.location_address2,
                'location_city':location.location_city,
                'location_state_province':location.location_state_province,
                'location_zip_postal':location.location_zip_postal,
                'location_area_code':location.location_area_code,
                'location_exchange':location.location_exchange,
                'location_number':location.location_number,
                'location_description':location.location_description,
                'location_url':location.location_url}
            location_list.append(location_dict)
        coupon_dict['location'] = location_list
        return coupon_dict

    def _build_list_of_coupon_dicts(self, coupons):
        """ Build list of coupon dicts with only necessary keys for display.
        Optional parameter render_preview will throw in locations and custom
        restrictions to display a preview of each coupon when selected.
        """
        coupons = self._append_coupon_actions(coupons)
        coupon_list = []
        for coupon in coupons:
            expiring_soon = False
            if coupon.expiration_date - timedelta(5) <= datetime.now().date():
                expiring_soon = True
            coupon_dict = {
            'coupon_url':reverse('view-single-coupon', kwargs={
                'slug':coupon.slug(), 'coupon_id':coupon.id}),
            'edit_coupon_url':reverse('edit-coupon', kwargs={
                'coupon_id':coupon.id}),
            'business_name':coupon.offer.business.business_name,
            'coupon_id':coupon.id,
            'headline':coupon.offer.headline,
            'qualifier':coupon.offer.qualifier,
            'is_redeemed_by_sms':coupon.is_redeemed_by_sms,
            'valid_days':VALID_DAYS.create_valid_days_string(coupon),
            'expiration_date':frmt_expiration_date_for_dsp(
                coupon.expiration_date),
            'expiring_soon': expiring_soon,
            'flyers_scheduled': get_coupons_scheduled_flyers(coupon,
                ContentType.objects.get(app_label='coupon', model='slot'),
                pack=1),
            'views':[coupon.views],
            'clicks':[coupon.clicks],
            'prints':[coupon.prints],
            'shares':[coupon.shares],}
            if self.render_preview:
                coupon_dict.update(self._get_preview_detail(coupon))
            coupon_list.append(coupon_dict)
        return coupon_list

    def _qry_coupon(self, business_id, advertiser_ids):
        """ Retrieve all coupons for this business or these advertisers. """
        if int(business_id) != 0:
            coupons = Coupon.objects.filter(offer__business__id=business_id)
            if self.omit_coupon_type_list:
                coupons = coupons.exclude(
                    coupon_type__in=self.omit_coupon_type_list)
        else:
            coupons = Coupon.objects.filter(
                offer__business__advertiser__in=advertiser_ids).exclude(
                id__in=self.exclude_coupon_ids)
            if self.omit_coupon_type_list:
                coupons = coupons.exclude(
                    coupon_type__in=self.omit_coupon_type_list)
            coupons = coupons.order_by('-offer__business__id')
        return coupons

    def get_coupon_list(self, advertiser_ids=None, **kwargs):
        """ Return stats for coupons of this advertiser as json data. """
        try:
            business_id = kwargs.get('business_id', [0])[0]
        except TypeError:
            # Params coming different formats if coming from ajax.
            business_id = kwargs.get('business_id', 0)

        # Make coupon_list a python list and remove '' elements.
        try:
            self.exclude_coupon_ids = list(set(
                kwargs.get('coupon_list', [''])[0].split(',')) - set(['']))
        except (AttributeError, IndexError, KeyError):
            self.exclude_coupon_ids = kwargs.get('coupon_list', [])
        coupons = self._qry_coupon(business_id, advertiser_ids)
        coupon_count = coupons.count()
        if coupon_count <= self.size_limit:
            # This is the last delivery, must check before size limit applied.
            coupon_count = 0
        coupon_list = self._build_list_of_coupon_dicts(coupons)
        coupon_list.append(({'coupon_count': coupon_count}))
        return coupon_list
