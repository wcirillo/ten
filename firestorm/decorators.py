""" Decorators for firestorm app. """
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from common.session import process_sign_out
from firestorm.models import AdRep
from firestorm.service import get_ad_rep_from_request, NotAuthenticatedError

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def ad_rep_required_md():
    """ Require an ad rep in session as a method decorator for class views. """
    def _dec(view_func):
        """ The wrapper for decorating a view. """
        def _view(request, *args, **kwargs):
            """ Require an ad rep in session. """
            try:
                ad_rep = get_ad_rep_from_request(request)
                LOG.debug('AdRep is in session, %s.' % ad_rep.email)
                return view_func(request, *args, **kwargs)
            except (AdRep.DoesNotExist, NotAuthenticatedError):
                LOG.debug('No valid ad rep in session.')
            return HttpResponseRedirect('%s?next=%s&%s' % (
                reverse('sign-in'),
                request.META['PATH_INFO'],
                request.META['QUERY_STRING']))
        return _view
    return _dec

def ad_rep_required(view):
    """ Decorator for views that checks the request for a valid current ad rep
    in session matches firestorm_id passed in.
    """
    def decorate(request, *args, **kwargs):
        """ Decorate wrapper to perform session verification. """
        try:
            ad_rep = get_ad_rep_from_request(request)
            kwargs['ad_rep'] = ad_rep
            LOG.debug('AdRep is in session, %s.' % ad_rep.email)
        except (AdRep.DoesNotExist, KeyError, NotAuthenticatedError):
            # Clear session and display sign in form.
            LOG.debug('Ad Rep not found in session.')
            process_sign_out(request)
            return HttpResponseRedirect('%s?next=%s&%s' % (
                    reverse('sign-in'),
                    request.META['PATH_INFO'],
                    request.META['QUERY_STRING'])
                )
        return view(request, *args, **kwargs)
    return decorate
