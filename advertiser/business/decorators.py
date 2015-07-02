""" Decorators for business in advertiser app. """
#pylint: disable=W0104
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from common.session import check_if_i_own_this_business

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def i_own_this_business():
    """ Require the business in session is owned by this user, or redir. """
    def _dec(view_func):
        """ Decorator inner function"""
        def _view(request, *args, **kwargs):
            """ Decorator inner view function checking if advertiser owns this 
            business.
            """
            try:
                business_id = int(kwargs['business_id'].encode())
                if check_if_i_own_this_business(request, business_id):
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseRedirect(reverse('all-coupons'))
            except KeyError:
                return HttpResponseRedirect(reverse('all-coupons'))
        return _view
    return _dec

def business_required():
    """ Require an advertiser has a business. """
    def _dec(view_func):
        """ The wrapper for decorating a view. """
        def _view(request, *args, **kwargs):
            """  Require a business in session. """
            LOG.debug('Logging in.')
            try:
                request.session['consumer']['advertiser']['business']
                LOG.debug('Advertiser has a business in session, %s.'
                    % request.session['consumer']['advertiser']['business'])
                return view_func(request, *args, **kwargs)
            except KeyError:
                LOG.debug('This advertiser does not have a business yet.')
                return HttpResponseRedirect(reverse('advertiser-registration'))
        return _view
    return _dec
