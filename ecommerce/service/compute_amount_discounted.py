""" check_one_use_advertiser_promo service function for ecommerce app """

from decimal import Decimal
import logging

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

def compute_amount_discounted(promotion, amount):
    """ Given a promotion and a dollar amount that qualifying products would
    cost, return the amount discounted.
    """
    if promotion.promo_type == '1': # % off
        amount_discounted = promotion.promo_amount * amount / Decimal(100)
        amount_discounted = Decimal(str(round(amount_discounted, 2)))
    elif promotion.promo_type == '2': # $ off
        if promotion.promo_amount < amount:
            amount_discounted = promotion.promo_amount
        else:
            amount_discounted = amount
    elif promotion.promo_type == '3': # fixed $ cost
        if promotion.promo_amount < amount:
            amount_discounted = amount - promotion.promo_amount
        else:
            # If you have a fixed cost promo of $20, but your items 
            # only cost $10, you don't save.
            amount_discounted = 0
    LOG.debug('compute discount: amount_discounted = %s' % amount_discounted)
    return amount_discounted
