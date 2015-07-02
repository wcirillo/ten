""" Views for PreviewEdit for the coupon app. """
#pylint: disable=W0104,W0613

from datetime import timedelta
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template import RequestContext
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin

from advertiser.business.location.service import add_location_to_business
from advertiser.business.tasks import take_web_snap
from advertiser.models import Business, Location, BusinessProfileDescription
from common.session import (add_coupon_to_offer_in_session, 
    add_update_business_location, add_update_business_session, 
    add_update_business_offer, add_location_id_to_coupon, 
    check_business_has_this_offer, check_offer_has_in_progress, 
    check_business_has_in_progress,
    check_advertiser_owns_business, check_offer_has_been_published,
    parse_curr_session_keys, check_business_was_published,
    check_for_unpublished_business,
    move_coupon_to_offer, check_other_coupon_published, find_lonely_offer, 
    delete_key_from_session, delete_all_session_keys_in_list)
from coupon.decorators import i_own_this_coupon
from coupon.forms import EditCouponForm
from coupon.models import Coupon, Offer
from coupon.service.expiration_date_service import get_non_expired_exp_date_dsp
from coupon.service.flyer_service import next_flyer_date
from coupon.service.restrictions_service import COUPON_RESTRICTIONS
from coupon.service.single_coupon_service import SINGLE_COUPON
from coupon.service.slot_service import (check_available_family_slot,
    publish_business_coupon)
from coupon.tasks import send_coupon_published_email
from ecommerce.service.locking_service import (get_locked_data,
    get_incremented_pricing)
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.product_list import (get_selected_product, 
    set_selected_product)
from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

@i_own_this_coupon()
def show_edit_coupon(request, coupon_id):
    """ 
    Put this coupons session into EDIT mode so we can make the 
    appropriate changes to the coupon and offer in the database and the session
    when this preview coupon page gets POSTed. 
    """
    request.session['coupon_mode'] = 'EDIT'
    # We are losing the sanitizing from as_view here; we already have a request.
    return PreviewCoupon().dispatch(request)


class PreviewCoupon(FormMixin, TemplateResponseMixin, View):
    """  Edit coupon all in one page. """
    template_name = 'coupon/display_preview_coupon.html'
    context = {}

    def __init__(self, **kwargs):
        """ PreviewCoupon initialization method. """
        super(PreviewCoupon, self).__init__(**kwargs)
        self.this = None
        self.form = None
        self.request = None
        self.create_new_slot = True
        self.coupon = None

    def get_coupon_mode(self):
        """ Return coupon_mode from session. """
        return self.request.session.get('coupon_mode', None)

    def get_business_name(self):
        """ Return business_name from the form. """
        return self.form.cleaned_data.get('business_name', None)

    def get_success_url(self):
        """ Return the success confirmation page for this coupon_mode. """
        created_redirect = 'checkout-coupon-purchase'
        if self.get_coupon_mode() in ('EDIT', 'PUBLISH'):
            # 'Edit' mode on success will bring us back to this advertisers
            # account page.
            created_redirect = 'advertiser-account'
        return reverse(created_redirect)

    def get_location_count(self):
        """ Return the location count. """
        try:
            self.session_dict['this_business']['location'][0]
            location_count = len(
                self.session_dict['this_business']['location'])
        except KeyError:
            location_count = None
        return location_count

    def prepare(self):
        """ Prepare to handle either a GET or a POST. """
        site = get_current_site(self.request)
        try:
            self.session_dict = parse_curr_session_keys(
                self.request.session, ['this_business'])
            if not self.get_coupon_mode():
                family_availability_dict = check_available_family_slot(
                    business_id=
                        self.session_dict['this_business']['business_id'])
                if family_availability_dict['available_parent_slot']:
                    self.request.session['coupon_mode'] = 'PUBLISH'
                    self.request.session['family_availability_dict'] = \
                        family_availability_dict
            delete_key_from_session(self.request, 'add_flyer_choice')
            annual_slot_price = get_product_price(3, site)
            self.context.update({
                'js_edit_coupon': 1,
                'coupon_mode': self.get_coupon_mode(),
                'css_date_picker': 1,
                'location_count':  self.get_location_count(),
                'next_flyer_date': next_flyer_date(),
                'minimum_expiration_date':
                    next_flyer_date() + timedelta(days=1),
                'annual_slot_price': annual_slot_price})
            if self.get_coupon_mode() not in ('EDIT', 'PUBLISH'):
                slot_price, locked_flyer_price, locked_consumer_count = \
                    get_locked_data(self.request, site)
                self.context.update(
                    get_incremented_pricing(locked_consumer_count))
                self.context.update({
                    'slot_price': slot_price,
                    'locked_flyer_price': locked_flyer_price,
                    'locked_consumer_count': locked_consumer_count})
        except KeyError:
            return HttpResponseRedirect(reverse('all-coupons'))
        return False

    def get(self, request):
        """ Process a GET request. """
        self.request = request
        response = self.prepare()
        if response:
            return response
        try:
            business_name = self.session_dict['this_business']['business_name']
            slogan = self.session_dict['this_business']['slogan']
            web_url = self.session_dict['this_business']['web_url']
            self.session_dict.update(parse_curr_session_keys(self.request.session,
                ['this_coupon', 'this_offer']))
            # If coupon_type is 1 this is an "In Progress" coupon which means 
            # this is not a new coupon OR coupon_mode == 'EDIT' which means,
            # we are editing this coupon
            headline = None
            qualifier = None
            if self.session_dict['this_coupon']['coupon_type_id'] == 1 \
            or self.get_coupon_mode() in ('EDIT', 'RENEWAL'):
                headline = self.session_dict['this_offer']['headline']
                qualifier = self.session_dict['this_offer']['qualifier']
            self.coupon = Coupon.objects.select_related(
                'offer', 'offer__business').get(
                id=self.session_dict['this_coupon']['coupon_id'])
            if self.get_coupon_mode() != 'EDIT':
                try:
                    business_description = self.coupon.offer.business.\
                        business_profile_description.business_description
                    self.context['business_description'] = business_description
                except BusinessProfileDescription.DoesNotExist:
                    pass
            default_restrictions_list = \
                COUPON_RESTRICTIONS.get_default_restrictions_list(
                    self.session_dict['this_coupon']['coupon_id'],
                    self.session_dict['this_coupon']['custom_restrictions'])
            # If the expiration_date in session is expired, bump it up to the
            # default expiration_date. The expiration_date in session could
            # either be in type(unicode()) or type(date()).
            expiration_date = get_non_expired_exp_date_dsp(
                self.session_dict['this_coupon']['expiration_date'])
            initial_dict = {
                'business_name': business_name,
                'slogan': slogan,
                'web_url': web_url,
                'headline': headline,
                'qualifier': qualifier,
                'default_restrictions':default_restrictions_list,
                'custom_restrictions':
                    self.session_dict['this_coupon']['custom_restrictions'],
                'is_valid_monday': 
                    self.session_dict['this_coupon']['is_valid_monday'],
                'is_valid_tuesday': 
                    self.session_dict['this_coupon']['is_valid_tuesday'],
                'is_valid_wednesday': 
                    self.session_dict['this_coupon']['is_valid_wednesday'],
                'is_valid_thursday': 
                    self.session_dict['this_coupon']['is_valid_thursday'],
                'is_valid_friday': 
                    self.session_dict['this_coupon']['is_valid_friday'],
                'is_valid_saturday': 
                    self.session_dict['this_coupon']['is_valid_saturday'],
                'is_valid_sunday': 
                    self.session_dict['this_coupon']['is_valid_sunday'],
                'is_redeemed_by_sms': 
                    int(self.session_dict['this_coupon']['is_redeemed_by_sms']),
                'expiration_date': expiration_date}
            count = 0
            while count < self.get_location_count():
                location = self.session_dict['this_business']['location'][count]
                initial_dict.update({'location_address1_%s' % str(count+1): 
                        location['location_address1'],
                    'location_address2_%s' % str(count+1): 
                        location['location_address2'],
                    'location_city_%s' % str(count+1): 
                        location['location_city'],
                    'location_state_province_%s' % str(count+1):
                        location['location_state_province'],
                    'location_zip_postal_%s' % str(count+1): 
                        location['location_zip_postal'],
                    'location_description_%s' % str(count+1): 
                        location['location_description'],
                    'location_area_code_%s' % str(count+1):
                        location['location_area_code'],
                    'location_exchange_%s' % str(count+1):
                        location['location_exchange'],
                    'location_number_%s' % str(count+1):
                        location['location_number']})
                count += 1
            self.context['form'] = EditCouponForm(initial=initial_dict)
            self.context.update(SINGLE_COUPON.set_single_coupon_dict(
                self.request, self.coupon))
            return self.render_to_response(
                RequestContext(self.request, self.context))
        except KeyError:
            return HttpResponseRedirect(reverse('all-coupons'))

    def get_this(self):
        """ Return many local vars as attributes of "this" or redirect on
        KeyError.
        """
        class This(object):
            """ A primitive class on which to pass vars as attributes. """
            pass
        
        self.this = This()
        try:
            self.this.advertiser = self.request.session['consumer']['advertiser']
            # Just ensuring the key exists.
            self.this.advertiser['advertiser_id']
            self.this.current_business = self.request.session['current_business']
            self.this.current_offer = self.request.session['current_offer']
            self.this.current_coupon = self.request.session['current_coupon']
            self.this.business = self.this.advertiser['business'][
                self.this.current_business]
            self.this.offer = self.this.business['offer'][self.this.current_offer]
            self.this.coupon = self.this.offer['coupon'][self.this.current_coupon]
            # Check if this_coupon['coupon_type_id'] is 'Free' or 'Paid'
            # if this_coupon['coupon_type_id'] in (2, 3):
            self.this.coupon_id = self.this.coupon['coupon_id']
            return
        except KeyError:
            return HttpResponseRedirect(reverse('all-coupons'))

    def get_sms(self, headline):
        """ Return the sms value. """
        try:
            short_business_name = self.this.business['short_business_name']
        except KeyError:
            short_business_name = self.this.business['business_name'][:25]
        return '%s %s' % (headline, short_business_name)

    def move_coupon_to_offer(self, old_current_offer):
        """ Move the coupon to an existing offer. """
        self.this.current_offer = self.request.session['current_offer']
        self.this.offer = self.this.business['offer'][self.this.current_offer]
        # Associate this current_coupon with this existing
        # offer. Move this coupon away from the prior offer
        # to this matching offer.
        move_coupon_to_offer(self.request, old_current_offer,
            self.coupon)
        self.this.current_coupon = self.request.session['current_coupon']
        self.coupon.offer_id = self.this.offer['offer_id']
        self.coupon.save()

    def check_for_lonely_offer(self):
        """ Check for a lonely offer and reposition the current keys. """
        has_lonely_offer = find_lonely_offer(self.request)
        if has_lonely_offer:
            self.this.current_offer = self.request.session['current_offer']
            self.this.offer = self.this.business['offer'][self.this.current_offer]
        else:
            self.this.current_offer = None
            self.this.offer = None
        return has_lonely_offer

    def update_coupon_other_published(self, old_current_offer):
        """ Update this coupon, which is for an offer that has another coupon
        published.
        """
        headline = self.form.cleaned_data.get('headline', None)
        qualifier  = self.form.cleaned_data.get('qualifier', None)
        has_lonely_offer = self.check_for_lonely_offer()
        if has_lonely_offer:
            # Use existing offer that has no coupon
            # associated with it.
            # Update this offer since no other Paid
            # coupons are associated with this offer.
            self.update_this_offer(headline, qualifier)
            self.move_coupon_to_offer(old_current_offer)
        else:
            # Create a new offer for this business.
            business_id = self.this.business['business_id']
            offer = Offer.objects.create(
                business_id=business_id,
                headline=headline,
                qualifier=qualifier)
            add_update_business_offer(self.request, offer)
            self.move_coupon_to_offer(old_current_offer)

    def update_this_offer(self, headline, qualifier):
        """ This offer has no coupons associated with it.  Utilize this offer.  """
        offer_id = self.this.offer['offer_id']
        offer = Offer.objects.get(id=offer_id)
        offer.headline = headline
        offer.qualifier = qualifier
        offer.save()
        add_update_business_offer(self.request, offer)
        self.this.current_offer = self.request.session['current_offer']
        self.this.offer =  self.this.business['offer'][self.this.current_offer]
        return offer

    def get_location_kwargs(self):
        """ Return kwargs needed for adding a location. """
        kwargs = {}
        add_location_flag = False
        for field in ['location_address1_1', 'location_address2_1',
            'location_city_1', 'location_description_1',
            'location_state_province_1', 'location_zip_postal_1',
            'location_area_code_1', 'location_exchange_1',
            'location_number_1']:
            value = self.form.cleaned_data.get(field, None)
            if value:
                add_location_flag = True
            kwargs.update({field[:-2]: value})
        return kwargs, add_location_flag

    def get_new_coupon_offer(self):
        """ Create a new offer and a new coupon. """
        headline = self.form.cleaned_data.get('headline', None)
        qualifier  = self.form.cleaned_data.get('qualifier', None)
        self.this.current_business = self.request.session['current_business']
        self.this.business = self.request.session['consumer']\
            ['advertiser']['business'][self.this.current_business]
        try:
            self.this.current_offer = len(self.this.business['offer'])
        except KeyError:
            # This business has no offers associated with it
            self.this.current_offer = 0
        self.request.session['current_offer'] = self.this.current_offer
        self.this.current_coupon = 0
        self.request.session['current_coupon'] = self.this.current_coupon
        self.request.session.modified = True
        business_id = self.this.business['business_id']
        offer = Offer.objects.create(
            business_id=business_id,
            headline=headline,
            qualifier=qualifier)
        add_update_business_offer(self.request, offer)
        self.this.offer = self.this.business['offer'][self.this.current_offer]
        self.create_coupon(offer)
        #self.add_locations_to_coupon()

    def create_coupon(self, offer):
        """ Create a new coupon for this offer and add it to the session.
        Coupon_type_id == 1 is 'In Progress'.
        """
        self.coupon = Coupon.objects.create(offer_id=offer.id, coupon_type_id=1,
            sms=self.get_sms(offer.headline))
        add_coupon_to_offer_in_session(self.request, self.coupon)
        self.this.current_coupon = self.request.session['current_coupon']
        self.this.coupon = self.this.offer['coupon'][self.this.current_coupon]

    def add_locations_to_coupon(self):
        """ Add all locations for that this business has to this coupon being
        posted right now. """
        try:
            # Get all of this businesses locations.
            locations = self.this.business['location']
            # Loop through all the location for this
            # business and add them to the coupon.
            for location in locations:
                location_id = location['location_id']
                self.coupon.location.add(location_id)
                add_location_id_to_coupon(self.request, location_id)
        except KeyError:
            kwargs, add_location_flag = self.get_location_kwargs()
            if add_location_flag:
                # Add this first location to the business.
                location_id = add_location_to_business(self.request,
                    business_id=self.coupon.offer.business.id, **kwargs)
                self.coupon.location = [location_id]
                add_location_id_to_coupon(self.request, location_id)

    def assign_coupon_to_this_offer(self):
        """ Check if the current_offer we are on has an In Progress coupon.
        If In Progress coupon exists for this offer, assign that coupon to the 
        current_coupon we need to get Published.  If no In Progress coupon
        exists for this offer, check if we have a PAID a.k.a. Published coupon 
        for this offer already.  If we have a PAID coupon already, we do not 
        want to create a duplicate running offer for this advertiser.  If no 
        In Progress or Paid coupon found, create one for this offer. """
        in_progress_coupon_exists = check_offer_has_in_progress(self.request)
        if in_progress_coupon_exists:
            self.this.current_coupon = self.request.session['current_coupon']
            self.this.coupon = self.this.offer['coupon'][self.this.current_coupon]
            self.this.coupon_id = self.this.coupon['coupon_id']
            # Utilize in progress coupon
            self.coupon = Coupon.objects.get(id=self.this.coupon_id)
        else:
            # Create new coupon for this offer
            offer = Offer.objects.get(id=self.this.offer['offer_id'])
            try:
                self.coupon = Coupon.current_coupons.get_current_coupons_by_site(
                    get_current_site(self.request)).filter(
                        offer=offer)[0]                
                # If identical coupon is already running, don't create a duplicate.
                self.create_new_slot = False
            except IndexError:
                # No coupon is actively running with this offer 
                self.create_coupon(offer)

    def update_business(self):
        """ Get the business and the offer. """
        business_name = self.get_business_name()
        slogan = self.form.cleaned_data.get('slogan', None)
        web_url = self.form.cleaned_data.get('web_url', None)
        business_exists_for_advertiser = check_advertiser_owns_business(
            self.request, business_name)
        if business_exists_for_advertiser:
            self.this.current_business = self.request.session['current_business']
            self.this.business = self.this.advertiser['business'][
                self.this.current_business]
        business_id = self.this.business['business_id']
        business = Business.objects.get(id=business_id)
        business_has_been_published = check_business_was_published(self.request)
        if business_has_been_published:
            if business_name != business.business_name:
                has_unpublished_business = check_for_unpublished_business(
                    self.request)
                if has_unpublished_business:
                    self.this.current_business = self.request.session[
                        'current_business']
                    self.this.business = self.this.advertiser['business'][
                        self.this.current_business]
                    business_id = self.this.business['business_id']
                    business = Business.objects.get(id=business_id)
                    # Update this unpublished business
                    business.business_name = business_name
                    business.slogan = slogan
                    business.web_url = web_url
                    business.short_business_name = business_name[:25]
                    business.save()                    
                    add_update_business_session(self.request, business)
                else:
                    # Create New Business
                    business = Business.objects.create(
                        advertiser_id=self.this.advertiser['advertiser_id'],
                        business_name=business_name,
                        short_business_name=business_name[:25],
                        slogan=slogan,
                        web_url = web_url)
                    add_update_business_session(self.request, business)
                    self.this.current_business = self.request.session[
                        'current_business']
                    self.this.business = self.this.advertiser['business'][
                        self.this.current_business]
                self.this.current_offer = 0
                self.this.offer = None
                self.this.current_coupon = 0
                self.this.coupon = None
                self.request.session['current_offer'] = 0
                self.request.session['current_coupon'] = 0
            else:
                # Update other business items
                if (slogan != business.slogan or web_url != business.web_url):
                    business.slogan = slogan
                    business.web_url = web_url
                    business.save()
                    add_update_business_session(self.request, business)
                    self.this.business = self.this.advertiser['business'][
                        self.this.current_business]
            # Update this business which has never been published
        else:
            if (business_name != business.business_name
                or slogan != business.slogan
                or web_url != business.web_url):
                business.business_name = business_name
                business.slogan = slogan
                business.web_url = web_url
                business.short_business_name = business_name[:25]
                business.save()
                add_update_business_session(self.request, business)
        self.update_web_snap(business)
        return business

    def update_offer(self):
        """ Process the request; this offer doesn't match current offer in
        session.
        """
        headline = self.form.cleaned_data.get('headline', None)
        qualifier  = self.form.cleaned_data.get('qualifier', None)
        old_current_offer = self.this.current_offer
        # Check if this business already has this exact offer.
        # If so, reposition the current_offer position.
        if check_business_has_this_offer(self.request, headline, qualifier):
            # Use existing offer
            self.this.current_offer = self.request.session['current_offer']
            self.this.offer = self.this.business['offer'][self.this.current_offer]
            self.assign_coupon_to_this_offer()
        else:
            # New Offer
            if self.get_coupon_mode() == 'EDIT':
                # Check if this offer has a different coupon that
                # has been published besides the current coupon.
                if check_other_coupon_published(self.request,
                        coupon_id=self.this.coupon_id):
                    self.update_coupon_other_published(old_current_offer)
                else:
                    # Update this offer since no other Paid Coupons
                    # are associated with this offer.
                    self.update_this_offer(headline, qualifier)
            else:
                in_progress_coupon_exists = \
                    check_business_has_in_progress(self.request)
                self.this.current_offer = self.request.session['current_offer']
                self.this.current_coupon = self.request.session['current_coupon']
                try:
                    self.this.offer = self.this.business['offer'][self.this.current_offer]
                    try:
                        self.this.coupon = self.this.offer['coupon'][self.this.current_coupon]
                        self.this.coupon_id = self.this.coupon['coupon_id']
                        self.coupon = Coupon.objects.get(id=self.this.coupon_id)
                    except KeyError:
                        self.this.coupon = None
                        self.this.coupon_id = None
                        self.coupon = None
                except KeyError:
                    self.this.offer = None
                    self.this.coupon = None
                    self.this.coupon_id = None
                    self.coupon = None                    
                if in_progress_coupon_exists:
                    #Check if this in progress coupon has at least one
                    # coupon published with this offer already.
                    offer_has_been_published = check_offer_has_been_published(
                        self.request)
                    if offer_has_been_published:
                        self.update_coupon_other_published(old_current_offer)
                    else:
                        # Update this offer and this coupon.
                        self.update_this_offer(headline, qualifier)
                else:
                    has_lonely_offer = self.check_for_lonely_offer()
                    if has_lonely_offer:
                        # Utilize Lonely offer and overwrite it with current
                        # posted information.
                        offer = self.update_this_offer(headline, qualifier)
                        #Create coupon for this updated offer.
                        self.create_coupon(offer)
                    else:
                        self.get_new_coupon_offer()
                    self.add_locations_to_coupon()

    def update_coupon(self):
        """ Update the coupon. """
        # Use cleaned_data of Restrictions Default & Custom.
        cleaned_request_post = self.form.cleaned_data
        COUPON_RESTRICTIONS.check_for_restriction_changes(
            cleaned_request_post, self.coupon, self.this.coupon)
        # SMS Redeemed
        COUPON_RESTRICTIONS.check_redeemed_by_sms_changes(
            cleaned_request_post, self.coupon, self.this.coupon)
        # Valid Days
        self.coupon.is_valid_monday = self.form.cleaned_data.get('is_valid_monday',
            False)
        self.coupon.is_valid_tuesday = self.form.cleaned_data.get('is_valid_tuesday',
            False)
        self.coupon.is_valid_wednesday = self.form.cleaned_data.get('is_valid_wednesday',
            False)
        self.coupon.is_valid_thursday = self.form.cleaned_data.get('is_valid_thursday',
            False)
        self.coupon.is_valid_friday = self.form.cleaned_data.get('is_valid_friday',
            False)
        self.coupon.is_valid_saturday = self.form.cleaned_data.get(
            'is_valid_saturday', False)
        self.coupon.is_valid_sunday = self.form.cleaned_data.get('is_valid_sunday',
            False)
        # Make sure update_businessthe sms gets updated. Headline or business name may
        # have changed.
        business_name = self.get_business_name()
        headline = self.form.cleaned_data.get('headline', None)
        self.coupon.sms = '%s %s' % (headline, business_name[:25])
        # Expiration Date
        expiration_date = self.form.cleaned_data.get('expiration_date')
        self.coupon.expiration_date = expiration_date
        self.coupon.save()
        add_coupon_to_offer_in_session(self.request, self.coupon)

    def update_locations(self):
        """ Update every location from the preview/edit form for this coupon.
        """
        try:
            location_count = len(self.request.session['consumer']['advertiser']\
                ['business'][self.this.current_business]['location'])
            count = 0
            while count < location_count:
                self.request.session['current_location'] = count
                location_id = self.this.business['location'][count]['location_id']
                location = Location.objects.get(id=location_id)
                setattr(location, 'location_address1',
                    self.form.cleaned_data.get('location_address1_%s' %
                        str(count+1)))
                setattr(location, 'location_address2',
                    self.form.cleaned_data.get('location_address2_%s' %
                        str(count+1)))
                setattr(location, 'location_city',
                    self.form.cleaned_data.get('location_city_%s' %
                        str(count+1)))
                setattr(location, 'location_state_province',
                    self.form.cleaned_data.get('location_state_province_%s' %
                        str(count+1)))
                setattr(location, 'location_zip_postal',
                    self.form.cleaned_data.get('location_zip_postal_%s' %
                        str(count+1)))
                setattr(location, 'location_description',
                    self.form.cleaned_data.get('location_description_%s' %
                        str(count+1)))
                setattr(location, 'location_area_code',
                    self.form.cleaned_data.get('location_area_code_%s' %
                        str(count+1)))
                setattr(location, 'location_exchange',
                    self.form.cleaned_data.get('location_exchange_%s' %
                        str(count+1)))
                setattr(location, 'location_number',
                    self.form.cleaned_data.get('location_number_%s' %
                        str(count+1)))
                location.save()
                add_update_business_location(self.request, location)
                count += 1
        except KeyError:
            # This coupon has no locations associated with it.
            # Check if a location was entered on the form.
            kwargs, add_location_flag = self.get_location_kwargs()
            if add_location_flag:
                # Add this first location to the business.
                location_id = add_location_to_business(self.request,
                    business_id=self.this.business['business_id'], **kwargs)
                self.coupon.location = [location_id]
                add_location_id_to_coupon(self.request, location_id)

    @staticmethod
    def update_web_snap(business):
        """ Snap/Re-snap this business web_url. Resnapping will help keep
        the image up to date. 
        """
        if business.web_url:
            if not settings.CELERY_ALWAYS_EAGER:
                take_web_snap.delay(business)


    def finish_process_for_mode(self):
        """ Finish processing the request for this coupon, depending on
        what coupon_mode we are currently in.
        """
        coupon_mode = self.get_coupon_mode()
        if coupon_mode not in ('EDIT', 'PUBLISH'):
            # If we are not in EDIT or PUBLISH mode we need to elect a
            # product to purchase. Flyer must be removed if it exists, and
            # we need to respect previous selections (if they came back).
            add_annual_slot_choice = get_selected_product(self.request)[2]
            # Create/Recreate the product_list with the associated prices.
            # If Ad rep in session, default to monthly price unless
            # populated.
            if not self.request.session.get('product_list', False):
                if add_annual_slot_choice is not None or \
                self.request.session.get('ad_rep_id', False):
                    set_selected_product(self.request, 2)
                else:
                    set_selected_product(self.request, 2)
        elif coupon_mode == 'PUBLISH' and self.create_new_slot:
            self.this.coupon = self.this.offer['coupon'][self.this.current_coupon]
            self.this.coupon['coupon_type_id'] = 3
            self.coupon.coupon_type_id = 3
            self.coupon.save()
            family_availability_dict = \
                self.request.session['family_availability_dict']
            publish_business_coupon(family_availability_dict, self.coupon)
            send_coupon_published_email.delay(coupon=self.coupon)

    def process_preview_coupon(self):
        """ The process method of show_preview_coupon. """
        response = self.get_this()
        if response:
            return response
        self.coupon = Coupon.objects.get(id=self.this.coupon_id)
        self.form = EditCouponForm(self.request.POST)
        # Check all required fields are filled out
        if not self.form.is_valid():
            # All required fields not filled out. Return page with form data.
            context = {'form': self.form}
            context.update(SINGLE_COUPON.set_single_coupon_dict(
                self.request, self.coupon))
            return self.render_to_response(
                RequestContext(self.request, self.context))
        self.update_business()
        self.update_offer()
        self.update_coupon()
        self.update_locations()
        self.finish_process_for_mode()
        # Session has been modified, save the session.
        self.request.session.modified = True
        success_url = self.get_success_url()
        delete_all_session_keys_in_list(self.request, ['coupon_mode',
                    'family_availability_dict'])
        return HttpResponseRedirect(success_url)

    def post(self, request):
        """ Process a POST request. """
        self.request = request
        response = self.prepare()
        if response:
            return response
        return self.process_preview_coupon()
