"""  Functions for returning 'locked' and 'unlocked' pricing data. """

import datetime

from common.utils import format_date_for_dsp
from coupon.service.flyer_service import next_flyer_date
from ecommerce.service.calculate_current_price import (calculate_current_price,
    get_product_price)

def get_locked_data(request, site, lock_it_now=False):
    """ 
    Lock prices and consumer count so they can be passed around the create
    coupon path. lock_it_now flag will force a lock to occur.
    """
    if lock_it_now:
        # Lock these prices now!
        slot_price, locked_flyer_price, locked_consumer_count = \
            set_locked_data(request, site)
    else:
        try:
            # Prices and count should be set in session already, pull them out!
            locked_flyer_price = request.session['locked_flyer_price']
            locked_consumer_count = request.session['locked_consumer_count']
            slot_price = get_product_price(2, site)
        except KeyError:
            # If the price wasn't locked and it was supposed to be, lock it now!
            slot_price, locked_flyer_price, locked_consumer_count = \
                set_locked_data(request, site)
    return slot_price, locked_flyer_price, locked_consumer_count

def set_locked_data(request, site, subdivision_consumer_count=None):
    """ Get the data so we can lock it. """
    slot_price, flyer_price, consumer_count = get_unlocked_data(site, subdivision_consumer_count)
    request.session['locked_flyer_price'] = flyer_price
    request.session['locked_consumer_count'] = consumer_count
    return slot_price, flyer_price, consumer_count

def get_unlocked_data(site, subdivision_consumer_count=None):
    """ Return unlocked data. """
    if subdivision_consumer_count is not None:
        consumer_count = int(subdivision_consumer_count)
    else:
        consumer_count = site.get_or_set_consumer_count()
    slot_price = get_product_price(2, site)
    flyer_price = calculate_current_price(1, consumer_count=consumer_count)
    return slot_price, flyer_price, consumer_count

def get_incremented_pricing(consumer_count):
    """ 
    Take in locked or unlocked pricing and calculate the pricing if the 
    consumer count was +100, +500 and +1500 from what the current 
    consumer_count is. Return an incremented_pricing dictionary. 
    """
    consumer_count_100 = consumer_count + 100
    consumer_count_500 = consumer_count + 500
    consumer_count_1500 = consumer_count + 1500
    flyer_price_100 = calculate_current_price(1, consumer_count=consumer_count_100)
    flyer_price_500 = calculate_current_price(1, consumer_count=consumer_count_500)
    flyer_price_1500 = calculate_current_price(1, consumer_count=consumer_count_1500)
    incremented_pricing = {
        'flyer_price_100':flyer_price_100,
        'flyer_price_500':flyer_price_500,
        'flyer_price_1500':flyer_price_1500,
        'consumer_count_100':consumer_count_100,
        'consumer_count_500':consumer_count_500,
        'consumer_count_1500':consumer_count_1500}
    return incremented_pricing
    
def set_flyers_context(request, site):
    """
    Return a dict for displaying flyer selection form.
    """
    next_send_date = next_flyer_date()
    return {
        'first_flyer_date': (format_date_for_dsp(next_send_date)),
        'second_flyer_date': (format_date_for_dsp(
            next_send_date + datetime.timedelta(days=7))),
        'third_flyer_date': (format_date_for_dsp(
            next_send_date + datetime.timedelta(days=14))),
        'fourth_flyer_date': (format_date_for_dsp(
            next_send_date + datetime.timedelta(days=21))),
        'first_flyer_price': 
            '$%.2f' % (request.session['locked_flyer_price']),
        'second_flyer_price': 
            '$%.2f' % (request.session['locked_flyer_price'] * 2),
        'third_flyer_price': 
            '$%.2f' % (request.session['locked_flyer_price'] * 3),
        'fourth_flyer_price': 
            '$%.2f' % (request.session['locked_flyer_price'] * 4),
        'slot_price': get_product_price(2, site),
        'locked_flyer_price': request.session['locked_flyer_price'],
        'locked_consumer_count': request.session['locked_consumer_count']}
