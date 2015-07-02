""" Decorators for the media_project app. """
#pylint: disable=W0104
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def media_partner_required():
    """ Require a media partner in session. """
    def _dec(view_func):
        """ The wrapper for decorating a view. """
        def _view(request, *args, **kwargs):
            """ 
            Requires a media group partner of affiliate partner in session.
            """
            LOG.debug('Logging in.')
            try:
                request.session['consumer']['media_group_partner']
                LOG.debug('Media group partner is in session.')
                return view_func(request, *args, **kwargs)
            except KeyError:
                try:
                    request.session['consumer']['affiliate_partner']
                    LOG.debug('Affiliate partner is in session.')
                    return view_func(request, *args, **kwargs)
                except KeyError:
                    LOG.debug('No valid user is in session.')
                    return HttpResponseRedirect(reverse('all-coupons'))        
        return _view
    return _dec

