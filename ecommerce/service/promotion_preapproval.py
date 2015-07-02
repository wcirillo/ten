""" Promotion pre-approval service functions for ecommerce app """

import logging

from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from ecommerce.models import Promoter, Product
from ecommerce.service.compute_amount_discounted import (
    compute_amount_discounted)

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)
LOG.info('Logging Started')

def get_matching_promotion(promotion_code, product):
    """
    Determine if a promotion_code is valid for a product, prior to an order 
    being created.
    """
    promotion = promotion_code.promotion
    promotion.can_be_used()
    if product in promotion.product.filter(is_active=True):
        return promotion
    else:
        error_message = 'This promotion is not valid for this product.'
        LOG.debug('%s: %s, %s' % (error_message, promotion_code.code, product))
        raise ValidationError(_(error_message))

def check_one_use_advertiser_promo(promotion, advertiser):
    """
    Check to see if this is a once-per-advertiser promotion, and if so has it
    already been used.
    """
    if promotion.use_method == '2':
        LOG.debug('is use method 2')
        if advertiser.businesses.filter(
                order_items__order__promotion_code__promotion=promotion
            ):
            raise ValidationError(_(
                """This promo has already been used by this advertiser"""))
            
def check_promotion_preapproval(promotion_code, advertiser, product_list,
        request=None):
    """ 
    Checks that this promotion is valid for this advertiser for this list of
    products, and if so returns subtotal, discount amount and grand total. 
    
    There are many ways a promotion is invalid, one of which is that this
    promotion does not apply to this product. We are looping over a list of
    products, and only if every one returns this ValidationError does that
    error apply to the whole order. In this case, raise ValidationError.
    """
    qualifying_amount = 0
    amount = 0
    for this_product in product_list:
        product = Product.objects.get(id=this_product[0])
        amount += this_product[1]
        try:
            promotion = get_matching_promotion(promotion_code, product)
            qualifying_amount += this_product[1]
        except ValidationError as error:
            pass
    if not qualifying_amount:
        raise ValidationError(error.messages[0])
    try:
        check_one_use_advertiser_promo(promotion, advertiser)
    except ValidationError as error:
        raise error
    if request:
        if (request.session.get('ad_rep_id', None)
            and promotion.promoter != Promoter.objects.get_by_natural_key(
                'Firestorm Ad Reps')):
            raise ValidationError('Tracking Code not valid')
    amount_discounted = compute_amount_discounted(promotion, qualifying_amount)
    return amount, amount_discounted, amount - amount_discounted
