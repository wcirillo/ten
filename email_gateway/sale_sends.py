""" 
Sale emailing procedures, giving the ability for 1-command sends in production 
instead of copy&pasting things.
"""
import logging

from email_gateway.context_processors import get_rep_context
from advertiser.models import Advertiser, Business
from coupon.models import Coupon, Offer

from email_gateway.send import send_email

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

def start_10(inactive_since, promo_code=None, test_mode=None, advertiser=None):
    """ Sale to advertisers who haven't purchased since inactive_since. """
    # If we passed in an advertiser, use that
    if advertiser:
        advertisers = [advertiser]
    else:
        # Grab advertisers who haven't purchased anything since inactive_date,
        # if ever.
        advertisers = Advertiser.objects.filter(
                is_emailable=True, is_active=True, email_subscription=2
            ).exclude(
                id__in=Advertiser.objects.filter(
                    businesses__order_items__order__create_datetime__gt=\
                        inactive_since
                    )).exclude(groups__name='advertisers__do_not_market')

    # Now cycle through the advertiser(s), grab their most recent business, and
    # then the most recent coupon or offer from that business, and send the 
    # sale email based on that info.
    skip_count = 0
    for advertiser in advertisers:
        try:
            if advertiser.site.id == 1:
                skip_count += 1
                continue
            coupon = None
            offer = None
            business = advertiser.businesses.latest('business_create_datetime')
            try:
                offer = business.offers.latest('create_datetime')
                try:
                    coupon = offer.coupons.latest('coupon_create_datetime')
                except Coupon.DoesNotExist:
                    pass
            except Offer.DoesNotExist:
                pass
            if test_mode:
                dest_address = test_mode
            else:
                dest_address = advertiser.email
            context = {
                'to_email': dest_address, 
                'subject': 'Display your coupon for just ten bucks on %s' % (
                    advertiser.site.domain),
                'bouncing_checked': True,
                'mailing_list': [2],
                'business': business,
                'offer': offer,
                'coupon': coupon,
                'promo_code': promo_code,
                }
            context.update(get_rep_context(advertiser.site, dest_address, 
                cc_rep=True))
            context.update({
                'friendly_from': '%s at %s' % (context['rep_first_name'], 
                        advertiser.site.domain)})
            LOG.debug("sending to %s with order date %s" % (advertiser.email, 
                offer))  
            send_email(template='advertiser_start_10', site=advertiser.site,
                context=context)
        except Business.DoesNotExist:
            pass
    print "Sale for promo code %s sent to %d advertisers" % (promo_code, 
        len(advertisers) - skip_count)
