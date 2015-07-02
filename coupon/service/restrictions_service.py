""" Service functions for dealing with restriction changes. """

from copy import copy
import logging

from common.utils import change_unicode_list_to_int_list
from coupon.models import DefaultRestrictions

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class CouponRestrictions(object):
    """ Class that helps deal with single coupon instances and things related to
    a single coupon.
    """

    @staticmethod
    def check_redeemed_by_sms_changes(cleaned_data, coupon, this_coupon):
        """
        This method checks if a user backs up in the browser and changed the 
        is_redeemed_by_sms option in the create coupon process...  It compares 
        the session value with the value in the database.
        """
        is_redeemed_by_sms = cleaned_data['is_redeemed_by_sms']
        # Should this coupon only be redeemed by print and not sms?
        if not int(is_redeemed_by_sms):
            coupon.is_redeemed_by_sms = 0
            this_coupon['is_redeemed_by_sms'] = False
        else:
            coupon.is_redeemed_by_sms = 1
            this_coupon['is_redeemed_by_sms'] = True
   
    @staticmethod
    def check_for_restriction_changes(cleaned_data, coupon, this_coupon):
        """
        Check if we have a custom restriction.  If a custom restriction is checked 
        and no text is entered do not save custom restriction value. If text is
        entered and no check, do not save custom restriction text. 
        The value 1 for last_item_in_list is equal to 'Enter
        custom restriction' in the coupon_defaultrestrictions table.
        """
        default_restrictions = []
        for x in cleaned_data['default_restrictions']:
            default_restrictions.append(unicode(x.id))
        custom_restrictions = cleaned_data['custom_restrictions']
        default_restrictions_copy = copy(default_restrictions)
        last_item_in_list = 0
        if len(default_restrictions) > 0:
            last_item_in_list = int(
                default_restrictions_copy.pop(len(default_restrictions_copy)-1))
        if ((last_item_in_list == 1 and custom_restrictions == '') or
            (last_item_in_list != 1 and custom_restrictions != '') or
            (last_item_in_list != 1 and custom_restrictions == '')):
            if last_item_in_list == 1:
                coupon.default_restrictions = default_restrictions[:-1]
                this_coupon['default_restrictions'] = \
                    change_unicode_list_to_int_list(default_restrictions[:-1])
            else:
                coupon.default_restrictions = default_restrictions
                this_coupon['default_restrictions'] = \
                    change_unicode_list_to_int_list(default_restrictions)
            coupon.custom_restrictions = ''
        else: 
            if last_item_in_list == 1:
                coupon.default_restrictions = default_restrictions[:-1]
            else:
                # Text was entered in custom restrictions box and checkbox for 
                # custom restrictions was checked.
                coupon.default_restrictions = default_restrictions
            coupon.custom_restrictions = custom_restrictions
            this_coupon['default_restrictions'] = \
                change_unicode_list_to_int_list(default_restrictions)
        this_coupon['custom_restrictions'] = coupon.custom_restrictions
    
    @staticmethod
    def get_default_restrictions_list(coupon_id, custom_restrictions=''):
        """
        Build a list of id's to populate the custom restrictions form or the 
        preview edit form.
        """
        default_restrictions = DefaultRestrictions.objects.values(
            'id').filter(coupons=coupon_id)
        default_restrictions_list = []
        for restriction in default_restrictions:
            default_restrictions_list.append(restriction['id'])
        if custom_restrictions not in ('', None):
            default_restrictions_list.append(1)
        return default_restrictions_list
    
COUPON_RESTRICTIONS = CouponRestrictions()