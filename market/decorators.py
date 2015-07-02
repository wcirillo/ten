""" Decorators for the market app. """
#pylint: disable=W0104

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from common.service.login_service import redirect_local_to_market_site

def market_required(destination_view):
    """ Require a market to draw this view. """

    def _dec(view_func, destination_view=destination_view, default_view='home'):
        """ The wrapper for decorating a view. Pass in default_url and url_path
        to control redirects when no market found.
        """
        
        def _view(request, destination_view=destination_view, 
            default_view=default_view, **kwargs):
            """ Require a market in session, url or cookie. """
            # If site 1, try to find market session to use, else redirect home.
            redirect_path, redirect_view = redirect_local_to_market_site(
                request, default_view = default_view, 
                destination_path=destination_view)
            if redirect_path:
                return HttpResponseRedirect(redirect_path)
            elif redirect_view:
                return HttpResponseRedirect(reverse(redirect_view))
            return view_func(request, **kwargs)
        return _view
    return _dec