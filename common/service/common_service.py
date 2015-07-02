""" The service.py for the common/views.py """
import datetime
import logging

from common.session import clear_session
from coupon.service.coupons_service import ALL_COUPONS
from coupon.service.flyer_service import next_flyer_date
from coupon.tasks import record_action_multiple_coupons
from ecommerce.service.locking_service import (get_unlocked_data,
    get_incremented_pricing)
from geolocation.models import USZip
from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def disjoin_sticky_session(request, response):
    """ 
    Method for internal users to be able to easily drop their site cookie and 
    clear their session.
    """
    # IE doesnt respect delete immediately, expire this cookie now.
    response.set_cookie(key='stamp',
        value=request.session.encode(1),
        expires=datetime.datetime.strftime(
        datetime.datetime.utcnow(),"%a, %d-%b-%Y %H:%M:%S GMT"))
    response.delete_cookie('stamp')
    clear_session(request)
    return

def get_home_data(request):
    """ Gets the data for the HOME Page on a GET, on a local site
    (not site.id=1). Converts complex ValuesListQuerySet to list.
    """
    site = get_current_site(request)
    all_coupons, coupon_ids = ALL_COUPONS.get_all_coupons(site)
    record_action_multiple_coupons.delay(action_id=1, 
        coupon_ids=tuple(coupon_ids))
    LOG.debug('all_coupons: %s' % all_coupons)
    slot_price, flyer_price, consumer_count = get_unlocked_data(site)
    context_instance_dict = {
        'nav_coupons':True,
        'all_coupons':all_coupons,
        'next_flyer_date': next_flyer_date(),
        'slot_price': slot_price,
        'flyer_price': flyer_price,
        'consumer_count': consumer_count}
    context_instance_dict.update(
        get_incremented_pricing(consumer_count))
    return context_instance_dict

def get_preferred_zip(request, site=None):
    """ 
    Retrieve a zip to use that is tied to this session or site. First grab
    from consumer, then try subscriber (in the session). If still not found, 
    check to see if site was passed in, if not then get site from request and 
    use the default zip of the site we are on. If site zip and consumer zip
    are different use the site zip.
    """
    user_zip, session_zip, site_zip = None, None, None
    try:
        session_zip = request.session['consumer']['consumer_zip_postal']
    except KeyError:
        try:
            session_zip = request.session['consumer']['subscriber']\
                ['subscriber_zip_postal']
        except KeyError:
            pass
    try:
        user_zip = USZip.objects.get(code=session_zip)
    except USZip.DoesNotExist:
        pass
    try:
        site_zip = USZip.objects.get(code=site.default_zip_postal)
    except (AttributeError, USZip.DoesNotExist):
        site = get_current_site(request)
        try:
            site_zip = USZip.objects.get(code=site.default_zip_postal)
        except USZip.DoesNotExist:
            # Local site does not have zip configured.
            pass
    if user_zip and (site.is_geom_in_market(user_zip.geom) or not site.geom):
        # Site.geom is not populated for local site 1.
        return user_zip.code
    elif site_zip:
        return site_zip.code
    else:
        return ''
