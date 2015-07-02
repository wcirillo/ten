""" Views for the feed app """
#pylint: disable=W0613
import logging

from django.http import HttpResponse

from feed.tasks.coupon_feed_tasks import ShoogerCouponFeed, GenericCouponFeed

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def show_shooger_coupon_feed(request):
    """ Prepare current coupons feed for xml display for Shooger. """
    shooger_coupon_feed = ShoogerCouponFeed()
    # Retrieve cached data from disk
    feed_data = shooger_coupon_feed.run()
    if not feed_data:
        feed_data = shooger_coupon_feed.run(write=True)
    return HttpResponse(feed_data, mimetype='application/xml')

def show_generic_coupon_feed(request):
    """ Prepare current coupons feed for xml display. """
    generic_coupon_feed = GenericCouponFeed()
    # Retrieve cached data from disk
    feed_data = generic_coupon_feed.run()
    if not feed_data:
        feed_data = generic_coupon_feed.run(write=True)
    return HttpResponse(feed_data, mimetype='application/xml')
