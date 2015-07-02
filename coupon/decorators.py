""" Decordators for business in advertiser app. """

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from common.session import check_if_i_own_this_coupon
from coupon.models import Slot

def i_own_this_coupon():
    """ Require the coupon in session is owned by this user, or redir. """
    def _dec(view_func):
        """ Decorator inner function"""
        def _view(request, *args, **kwargs):
            """ 
            Decorator inner view function checking if advertiser owns this 
            coupon.
            """
            try:
                coupon_id = int(kwargs['coupon_id'].encode())
                if check_if_i_own_this_coupon(request, coupon_id):
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseRedirect(reverse('all-coupons'))        
            except KeyError:
                return HttpResponseRedirect(reverse('all-coupons'))        
        return _view
    return _dec

def i_own_this_active_coupon_slot():
    """ Require the slots coupon in session is owned by this user, or redir. 
    The coupon must be actively running in the slot with an active 
    SlotTimeFrame. """
    def _dec(view_func):
        """ Decorator inner function"""
        def _view(request, *args, **kwargs):
            """ 
            Decorator inner view function checking if advertiser owns this 
            slot coupon.
            """
            try:
                slot_id = int(kwargs['slot_id'].encode())
                coupon = Slot.objects.get(
                    id=slot_id).get_active_coupon()
                if check_if_i_own_this_coupon(request, coupon.id):
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseRedirect(reverse('all-coupons'))      
            except (KeyError, Slot.DoesNotExist, AttributeError):
                return HttpResponseRedirect(reverse('all-coupons'))        
        return _view
    return _dec
