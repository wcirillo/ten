""" Service functions for a single coupon. """

import datetime
import logging

from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect

from common.session import get_coupon_id
from coupon.config import TEN_COUPON_RESTRICTIONS
from coupon.models import Coupon, DefaultRestrictions, SlotTimeFrame
from coupon.service.coupons_service import ALL_COUPONS
from coupon.service.expiration_date_service import frmt_expiration_date_for_dsp
from coupon.service.valid_days_service import VALID_DAYS
from geolocation.models import USZip
from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class SingleCoupon(object):
    """ Class that helps deal with single coupon instances and things related to
    a single coupon.
    """
    
    @staticmethod
    def set_single_coupon_dict(request, coupon):
        """ Set this coupon into the dict for display. """
        if not coupon:
            return {}
        current_business = request.session['current_business']
        current_offer = request.session['current_offer']
        current_coupon = request.session['current_coupon']
        this_business = request.session['consumer']['advertiser']['business']\
            [current_business]
        this_offer = this_business['offer'][current_offer]
        this_coupon = this_offer['coupon'][current_coupon]
        this_coupon['slug'] = coupon.slug()
        try:
            location_count = len(this_coupon['location'])
            l_index = 0
            while l_index < location_count:
                for b_position in range(len(this_business['location'])):
                    try:
                        # Check if the location is a list of id's or a list of 
                        # addresses.... A TypeError will exist if 
                        # this_coupon['location'][l_index]['location_id'].
                        if this_coupon['location'][l_index]['location_id'] == \
                        this_business['location'][b_position]['location_id']:
                            this_coupon['location'][l_index] = this_business\
                                ['location'][b_position]
                    except TypeError:
                        if this_coupon['location'][l_index] == \
                        this_business['location'][b_position]['location_id']:
                            this_coupon['location'][l_index] = this_business\
                                ['location'][b_position]
                l_index += 1
        except KeyError:
            # This business has no physical locations or phone number. May just
            # have a Business.web_url.
            pass
        coupon_selected_restrictions = DefaultRestrictions.objects.filter(
            coupons=this_coupon['coupon_id']).exclude(id=1)
        valid_days = VALID_DAYS.create_valid_days_string(coupon)
        single_coupon_dict = {
            'business_name': this_business['business_name'],
            'slogan': this_business['slogan'],
            'web_url': this_business['web_url'], 
            'headline': this_offer['headline'],
            'qualifier': this_offer['qualifier'],
            'expiration_date': frmt_expiration_date_for_dsp(
                coupon.expiration_date),
            'coupon': this_coupon, 
            'default_restrictions': coupon_selected_restrictions, 
            'custom_restrictions': this_coupon['custom_restrictions'], 
            'valid_days': valid_days, 
            'ten_coupon_restrictions': TEN_COUPON_RESTRICTIONS}
        return single_coupon_dict
    
    @staticmethod
    def get_coupon(request):
        """
        Return a coupon instance, from the current coupon in session.
        """
        coupon_id = get_coupon_id(request)
        coupon = Coupon.objects.get(id=coupon_id)
        return coupon
    
    @staticmethod
    def check_single_coupon_redirect(coupon_id, site, slug):
        """ Redirect the request if this coupon is not valid. """
        try:
            coupon = Coupon.objects.select_related(
                'coupon_type', 'offer', 'offer__business', 
                'offer__business__business_profile_description').get(
                    id=coupon_id)
            # A coupon must be in a current slot, or Bulk, or National, but
            # go ahead and get other coupons of this biz now too:
            coupon_ids = list(
                Coupon.current_coupons.get_current_coupons_by_site(site)
                    .filter(offer__business__id=coupon.offer.business.id)
                    .values_list('id', flat=True))
            if not coupon.id in coupon_ids:
                coupon_ids += list(ALL_COUPONS.get_national_coupons()
                    .filter(offer__business__id=coupon.offer.business.id)
                    .values_list('id', flat=True))
            if not coupon.id in coupon_ids:
                coupon_ids += list(ALL_COUPONS.get_media_partner_coupons(site)
                    .filter(offer__business__id=coupon.offer.business.id)
                    .values_list('id', flat=True))
            if not coupon.id in coupon_ids:
                zip_postals = list(USZip.objects.get_zips_this_site(site))
                if zip_postals:
                    coupon_ids += list(ALL_COUPONS.get_bulk_coupons(zip_postals)
                        .filter(offer__business__id=coupon.offer.business.id)
                        .values_list('id', flat=True))
            if not coupon.id in coupon_ids:
                if coupon_ids:
                    return HttpResponseRedirect(
                        reverse('view-all-businesses-coupons', 
                        kwargs={'slug':coupon.offer.business.slug, 
                            'business_id':coupon.offer.business.id}))
                return HttpResponseRedirect(reverse('all-coupons-msg',
                    kwargs={'msg': 1}))
        except Coupon.DoesNotExist:
            return HttpResponseRedirect(reverse('all-coupons-msg',
                kwargs={'msg': 1}))
        if slug != coupon.slug():
            return HttpResponsePermanentRedirect(reverse('view-single-coupon', 
                kwargs={'slug': coupon.slug(), 'coupon_id': coupon_id}))
        return coupon
    
    @staticmethod
    def get_coupon_canonical(site, coupon, view_name, view_kwargs):
        """
        Return the canonical url for this coupon for this view.
        """
        canonical = ''
        if coupon.coupon_type.coupon_type_name == "National":
            canonical = "%s%s" % (settings.HTTP_PROTOCOL_HOST, reverse(
                view_name, kwargs=view_kwargs, urlconf='urls_local.urls_2'))
        if coupon.coupon_type.coupon_type_name == "Paid":
            coupon_site = coupon.get_site()
            if site != coupon_site:
                canonical = "%s%s" % (settings.HTTP_PROTOCOL_HOST, reverse(
                    view_name, kwargs=view_kwargs, 
                    urlconf='urls_local.urls_%s' % coupon_site.id))
        return canonical
    
    @staticmethod
    def get_coupon_title_meta_desc(site, coupon, display_city,
            display_location):
        """
        Return the title and meta description for show_single_coupon.
        """
        if not display_city:
            display_location = site.region
        title = '%s Coupon - %s in %s' % (coupon.offer.headline.title(),
            coupon.offer.business.business_name, display_location)
        if len(title) > 66 and display_city:
            title = '%s - %s in %s' % (coupon.offer.headline, 
                coupon.offer.business.business_name, display_city)
        if len(title) > 66:
            title = '%s - %s' % (coupon.offer.headline, 
                coupon.offer.business.business_name)
        # A Twitter button bug crashes with % in title.
        title = title.replace('%', ' Percent ')
        meta_description = 'Get %s %s at %s in %s - Valid through %s.' % (
            coupon.offer.headline.title(), coupon.offer.qualifier.title(),
            coupon.offer.business.business_name, display_location,
            coupon.expiration_date)
        # Max ideal len = 160.
        if len(meta_description) < 130:
            meta_description = '%s %s' % (meta_description,
                "Click here to get this coupon!")
        elif len(meta_description) < 133:
            meta_description = '%s %s' % (meta_description,
                "Get your coupon & save now!")
        elif len(meta_description) < 135:
            meta_description = '%s %s' % (meta_description,
                "Click to get this coupon!")
        elif len(meta_description) < 138:
            meta_description = '%s %s' % (meta_description, 
                "Get this coupon today!")
        return title, meta_description
    
    @staticmethod
    def get_coupon_site(coupon):
        """ Return site if slot exists else return advertiser site """
        try:
            site = coupon.slot_time_frames.latest('id').slot.site
            LOG.info('coupon slot site = %s' % site.id)
        except SlotTimeFrame.DoesNotExist:
            site = coupon.offer.business.advertiser.site
            LOG.info('coupon advertiser site = %s' % site.id)
        return site
    
    @staticmethod
    def set_sample_phone_display_text(request):
        """ Builds the text for the sample phone display. """
        site = get_current_site(request)
        current_coupons = Coupon.current_coupons.get_current_coupons_by_site(
            site)
        offer = 'Planet Fashion $5 Off purchase of $25 or more Code: SAVE5'
        expiration_date = datetime.date.today() + datetime.timedelta(days=23)
        try:
            # Passing in a "select_related" to override that from 
            # ordered coupons. Selecting only fields needed.
            recent_coupon = current_coupons.select_related('coupon').filter(
                    is_approved=True, is_redeemed_by_sms=True
                ).only('sms', 'expiration_date')[0]
            offer = recent_coupon.sms
            expiration_date = recent_coupon.expiration_date
        except IndexError:
            pass
        sample_phone_text = '%s %s  Exp: %s %s' % (
            '<p><strong>71010:</strong><br/>10Coupons Alrts: ',
            offer,
            expiration_date.strftime("%m/%d/%y"),
            'See details online. Message &amp; Data Rates May Apply</p>')
        return sample_phone_text

SINGLE_COUPON = SingleCoupon()
