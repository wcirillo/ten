# -*- coding: utf-8 -*-
""" Common decorators for the project ten. """
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from advertiser.models import Advertiser

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

def password_required(view):
    """ Decorator for views that checks that the user has entered the password,
    redirecting to different pages if necessary.
    """
    def decorate(request, *args, **kwargs):
        """ The decorate wrapper. """
        if request.user.is_authenticated():
            try:
                advertiser = Advertiser.objects.only(
                        "is_email_verified", "is_active", "password"
                    ).get(id=request.user.id)
            except Advertiser.DoesNotExist:
                return HttpResponseRedirect(reverse('all-coupons'))
            if not advertiser.is_email_verified:
                return HttpResponseRedirect(reverse('contact-us'))
            if not advertiser.has_usable_password():
                return HttpResponseRedirect('%s?next=%s' % (
                        reverse('set-password'), 
                        request.META['PATH_INFO'])
                    )
            if not advertiser.is_active:
                return HttpResponseRedirect(reverse('contact-us'))
        return view(request, *args, **kwargs)
    return decorate

def superuser_required(view):
    """ Decorator for views that checks that the user has superuser status. """
    def decorate(request, *args, **kwargs):
        """ The decorate wrapper. """
        if not request.user.is_superuser:
            return HttpResponseRedirect('%s?next=%s' % (
                    reverse('sign-in'), 
                    request.META['PATH_INFO'])
                )
        return view(request, *args, **kwargs)
    return decorate