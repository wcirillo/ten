""" Service functions for ecommerce app """

from decimal import Decimal
import datetime
import dateutil
import logging

from django.template.defaultfilters import date as date_filter

from common.session import delete_all_session_keys_in_list
from ecommerce.service.cache_service import get_product_from_cache
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.locking_service import get_locked_data
from market.service import get_current_site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)
LOG.info('Logging Started')

def create_products_list(request, site=None):
    """ Return a list of tuples of all products to be purchased """
    flyer_dates_list, add_slot_choice, add_annual_slot_choice = \
        get_selected_product(request)
    product_list = []
    if not site:
        site = get_current_site(request)
    if flyer_dates_list is not None:
        # Product for Flyers.
        pre_description = 'Email Flyer scheduled for '
        locked_flyer_price = request.session['locked_flyer_price']
        product_1_base_days = get_product_from_cache(1).base_days
        for flyer_date in flyer_dates_list:
            flyer_date = dateutil.parser.parse(flyer_date) 
            product_list.append((1, locked_flyer_price, 
                '%s%s.' % (pre_description, date_filter(flyer_date, "M j, Y")), 
                flyer_date, 
                flyer_date + datetime.timedelta(days=product_1_base_days)))
    elif add_slot_choice is not None:
        # Purchasing a Slot and Maybe a few Flyers
        try:
            slot_price = get_product_price(2, site)
        except KeyError:
            slot_price = get_locked_data(request, site)[0]
        slot_start_datetime = datetime.datetime.now()
        slot_start_date = date_filter(slot_start_datetime, "m/d/y")
        slot_end_date = datetime.date.today() + \
            dateutil.relativedelta.relativedelta(months=1)
        slot_end_datetime = datetime.datetime.combine(slot_end_date, 
            datetime.time())
        slot_description = \
            'Monthly 10Coupon Publishing Plan: %s - %s.' % (
                slot_start_date, date_filter(slot_end_date, "m/d/y"))
        product_list = [(2, slot_price, slot_description, slot_start_datetime, 
            slot_end_datetime)]
    elif add_annual_slot_choice is not None:
        slot_annual_start_datetime = datetime.datetime.now()
        slot_annual_start_date = date_filter(
            slot_annual_start_datetime, "m/d/y")
        slot_annual_end_date = datetime.date.today() + \
            dateutil.relativedelta.relativedelta(months=12)
        slot_annual_end_datetime = datetime.datetime.combine(
            slot_annual_end_date, datetime.time())
        slot_annual_description = \
            'Annual 10Coupon Publishing Plan: %s - %s.' % (
                slot_annual_start_date, date_filter(
                    slot_annual_end_date, "m/d/y"))
        product_list = [(3, get_product_price(3, site),
                         slot_annual_description, slot_annual_start_datetime, 
                         slot_annual_end_datetime)]
    return product_list
    
def calc_total_of_all_products(product_list):
    """ Add of the total amount for all products being purchased. """
    product_total = Decimal(str(0))
    for product in product_list:
        product_total += product[1]
    return product_total

def get_selected_product(request):
    """ Retrieve the selected product choice keys from the session.
        flyer_dates_list, add_slot_choice, add_annual_slot_choice
    """
    flyer_dates_list = request.session.get('flyer_dates_list', None)
    add_slot_choice = request.session.get('add_slot_choice', None)
    add_annual_slot_choice = request.session.get('add_annual_slot_choice', None)
    return flyer_dates_list, add_slot_choice, add_annual_slot_choice

def set_selected_product(request, product_id, quantity=None):
    """ Validate and set the production selection in the session. Maintain
    that only one add_[product]_choice key exists in the session at a time.
    """
    product_dict = {1:'add_flyer_choice', 2:'add_slot_choice', 
        3:'add_annual_slot_choice'}
    request.session[product_dict.pop(product_id)] = quantity or 0
    delete_all_session_keys_in_list(request, product_dict.values())
    request.session['product_list'] = create_products_list(request)
    return request.session['product_list']

def get_slot_renewal_rate(product_list):
    """ Get the renewal rate for a slot being saved.
    This renewal_rate is the rate the slot is being pitched at without any 
    promotion codes applied.
    """
    slot_renewal_rate = False
    product_id = False
    for product in product_list:
        if product[0] in [2, 3]:
            slot_renewal_rate = product[1]
            product_id = product[0]
            break
    return slot_renewal_rate, product_id

def get_product_quantity(product_list, product_id):
    """ Get the number of a product selected for purchase. Currently we only
    support multiple purchases of flyers per checkout. 
    """
    return sum(product.count(product_id) for product in product_list)