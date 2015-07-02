""" Decorators for the advertiser app. """
#pylint: disable=W0104
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def advertiser_required():
    """ Require an advertiser in session. """
    def _dec(view_func):
        """ The wrapper for decorating a view. """
        def _view(request, *args, **kwargs):
            """ Require an advertiser in session. """
            LOG.debug('Logging in.')
            try:
                request.session['consumer']['advertiser']
                LOG.debug('Advertiser is in session, %s.' % 
                   request.session['consumer']['advertiser'])
                return view_func(request, *args, **kwargs)
            except KeyError:
                LOG.debug('No valid advertiser in session.')
                return HttpResponseRedirect(reverse('sign-in'))
        return _view
    return _dec
