""" The service.py for the common/views.py """

import logging

from django.contrib.auth import authenticate, login, logout
from django.core.urlresolvers import reverse

from advertiser.models import Advertiser
from common.custom_format_for_display import list_as_text
from common.forms import SignInForm, get_sign_in_form_initial_data
from common.session import (build_session_from_user,
    create_consumer_in_session)
from consumer.models import Consumer
from market.service import (get_current_site, check_for_site_redirect,
    check_for_cross_site_redirect)
from media_partner.models import MediaPartner, Affiliate

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class LocalSiteResolvedError(Exception):
    """ Site is local site 1 when looking for market site. """
    pass

class InvalidZipPostalError(Exception):
    """ Using session Consumer zip to obtain market site, None is invalid. """
    pass

def process_login_from_form(request, form):
    """ Identify user type and perform respective login/redirect functionality:
    Consumer: create consumer session and redirect to coupon view.
    Advertiser: authenticate session and load advertiser account.
    AdRep: authenticate session and redirect to ad_rep account page.
    MediaPartner: authenticate session and load media partner report.
    AffiliatePartner: authenticate session and load media partner report.
    """
    user_type = form.cleaned_data.get('user_type', None)
    is_ad_rep = form.cleaned_data.get('is_ad_rep', None)
    keep_me_signed_in = request.POST.get('keep_signed_in', None)
    email = form.cleaned_data.get('email', None)
    password = form.cleaned_data.get('password', None)
    redirect_path = reverse('all-coupons')
    if user_type == 'consumer' and not is_ad_rep:
        # Load consumer in session and redirect to coupon view.
        consumer = Consumer.objects.get(email=email)
        create_consumer_in_session(request, consumer)
    else: # Authenticate.
        user = authenticate(username=email, password=password)
        redirect_path =  process_login(
            request, user, keep_me_signed_in, is_ad_rep)
    return redirect_path

def process_login(request, user, keep_me_signed_in=None, is_ad_rep=False):
    """ Authenticate user login. """
    if user is not None:
        if not user.is_active:
            redirect_path = reverse('contact-us')
        # Correct password, and the user is marked "active"
        login(request, user)
        if request.session.test_cookie_worked():
            request.session.delete_test_cookie()
        redirect_path = process_redirect(request, user, is_ad_rep)
        if keep_me_signed_in is None:
            # Session expire on browser close.
            request.session.set_expiry(0)
        else:
            # Keep me logged in after the browser is closed.
            request.session.set_expiry(60*60*24*14)
    else:
        logout(request)
        redirect_path = None
    return redirect_path

def process_redirect(request, user, is_ad_rep):
    """ Get redirect based on user type """
    _next = request.GET.get('next', None)
    in_session = build_session_from_user(request, user)
    if in_session:
        
        if is_ad_rep:
            redirect_path = reverse('ad-rep-account')
            request.session['ad_rep_id'] = user.id
            site_id = request.session['consumer']['site_id']
        elif in_session in ('advertiser', 'consumer'):
            redirect_path = reverse('advertiser-account')
            site_id = request.session['consumer']['site_id']
        else:
            media_partner = MediaPartner.objects.get(
                email__iexact=user.email)
            redirect_path = reverse('media-partner-view-report')
            if in_session == 'media_group_partner':
                # Select the first affiliate for this media_group and 
                # use that site_id.
                media_groups = media_partner.media_groups.all()[0]
                affiliates = Affiliate.objects.filter(
                    media_group=media_groups)
                site_id = affiliates[0].site.id
            else:
                if in_session == 'affiliate_partner':
                    site_id = media_partner.affiliates.all()[0].site.id
                else:
                    redirect_path = reverse('contact-us')
        redirect_path = check_for_site_redirect(request, site_id=site_id, 
            redirect_path=redirect_path)[1]
    if _next:
        redirect_path = _next
    return redirect_path

def redirect_local_to_market_site(request, default_view, destination_path=None):
    """
    If this is local site 1, try to find site in session to use. If site 
    found in session, return a redirect_path to that market's home page,
    otherwise indicate view to execute to show local home page. If this is 
    not site 1 return the default view passed in. Caller will execute.
    """
    redirect_path = None
    redirect_view = None
    # Cannot perform reverse on None or empty string, perfrom reverse here.
    if destination_path:
        destination_path = reverse(destination_path)
    site = get_current_site(request)
    if site.id == 1: # Site not region.
        try: # Try to pull site from session.
            this_site_id = request.session['consumer']['site_id']
            if this_site_id == 1:
                raise LocalSiteResolvedError()
            redirect_path = check_for_site_redirect(request, this_site_id, 
                                destination_path)[1]
        except (KeyError, LocalSiteResolvedError):
            # No consumer in session, display site directory.
            try: # Try to pull zip from session.
                if not request.session['consumer']['consumer_zip_postal']:
                    raise InvalidZipPostalError()
                redirect_path = check_for_cross_site_redirect(request, 
                        request.session['consumer']['consumer_zip_postal'], 
                            destination_path)[1]
            except (InvalidZipPostalError, KeyError):
                try: # Try to pull market id from cookie storage.
                    redirect_path = check_for_site_redirect(request, 
                        request.session.decode(request.COOKIES["stamp"]), 
                            destination_path)[1] 
                except KeyError:
                    redirect_view = default_view
    return redirect_path, redirect_view

def build_sign_in_form_context(request, context_dict):
    """ 
    Advertiser sign in (header link) and Advertiser account sign in (footer
    link), currently share the same form and the same conditions to display
    text. White it makes sense, they can share this function to get that info.
    Returns context_dict and redirect_to vars.
    """
    initial_data = get_sign_in_form_initial_data(request)
    form = SignInForm(initial=initial_data,
        test_mode=request.session.get('tlc_sandbox_testing', False))
    context_dict.update({'form': form})
    # Display the sign in form
    try:
        advertiser_id = redirect_to = None
        advertiser_id = request.session['consumer']['advertiser']\
            ['advertiser_id']
        advertiser = Advertiser.objects.select_related().get(id=advertiser_id)
        if advertiser.businesses.count():
            context_dict['businesses'] = list_as_text(
                advertiser.businesses.all().order_by('id'
                ).values_list('business_name', flat=True))
        if advertiser.password == '!' and request.user.is_authenticated():
            # Send advertiser to set-password page.
            redirect_to = 'set-password'
    except KeyError:
        pass
    return context_dict, redirect_to