""" Views for the firestorm app of project ten. """
#pylint: disable=W0613
import logging

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.http import (Http404, HttpResponse, HttpResponseRedirect,
    HttpResponsePermanentRedirect)
from django.shortcuts import render_to_response
from django.template import RequestContext

from gargoyle.decorators import switch_is_active
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, inch
from reportlab.pdfgen import canvas as canv
from reportlab.platypus import Image, Table, TableStyle, CellStyle

from common.context_processors import products
from common.custom_format_for_display import format_phone
from common.forms import (SetPasswordForm, SignInForm, TermsOfUseForm)
from common.views import show_home
from common.service.login_service import process_login_from_form, process_login
from common.service.payload_signing import PAYLOAD_SIGNING
from common.session import create_consumer_in_session
from consumer.models import Consumer
from consumer.service import get_consumer_instance_type
from ecommerce.service.calculate_current_price import get_product_price
from ecommerce.service.locking_service import get_unlocked_data
from geolocation.service import get_city_and_state
from firestorm.connector import FirestormConnector
from firestorm.forms import AdRepLeadForm, QuestionForm, AdRepUrlForm
from firestorm.models import AdRep, AdRepLead, AdRepConsumer
from firestorm.service import get_ad_rep_qr_image_path
from firestorm.soap import FirestormSoap
from firestorm.tasks import NOTIFY_NEW_RECRUIT, SEND_ENROLLMENT_EMAIL
from market.service import get_current_site, check_for_site_redirect

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.DEBUG)

ERROR_MSG_TERMS_ENROLLMENT = """An Advertising Representative must 
    agree to the three documents listed."""

ERROR_MSG_TERMS_REFERRER = """Please indicate that you agree with the Terms of 
    Use. """

@switch_is_active('replicated-website')
def ad_rep_home(request, ad_rep_url, connector=FirestormConnector()):
    """ The home page of the 'replicated website' for someone enrolled in the
    Firestorm product; either an "Advertising Representative" or a
    "Referring Consumer."

    This view takes a connector arg so that unit tests can pass in a mock
    connector.
    """
    connector.get_ad_rep_or_404(request, ad_rep_url)
    return show_home(request)

@switch_is_active('replicated-website')
def redirect_for_ad_rep(request, redirect_string,
        connector=FirestormConnector(), *args, **kwargs):
    """ Given a redirect_string, parse it such that the final 'directory' is the
    ad_rep_url and the remainder is a relative path to redirect to, put the
    referring ad rep in session then 302 redirect.
    """
    redirect_list = redirect_string.split('/')
    ad_rep_url = redirect_list.pop()
    connector.get_ad_rep_or_404(request, ad_rep_url)
    site = get_current_site(request)
    if site.id != 1:
        redirect_list = [site.directory_name] + redirect_list
    redirect_path = '/' + '/'.join(redirect_list) + '/'
    return HttpResponseRedirect(redirect_path, *args, **kwargs)

def redirect_benefits_for_business(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('benefits-for-business'))

def show_ad_rep_summary(request, ad_rep_id=None):
    """ Display ad rep details including image, name, phone number, email and
    web greeting (in modal window).
    """
    if not ad_rep_id:
        raise Http404
    ad_rep_recruit = AdRep.objects.get(id=ad_rep_id)
    context_dict = {'ad_rep': ad_rep_recruit}
    # Not setting context in RequestContext because we are overwriting the
    # context processor's ad rep (which is the ad rep in session, not 
    # THIS ad rep passed in.
    return render_to_response('include/dsp/dsp_ad_rep_data_detail.html',
        context_dict)
    
def show_benefits_for_business(request):
    """ Show the benefits for local business advertisers page. """
    return render_to_response(
        'marketing_resources/display_benefits_for_business.html',
        context_instance=RequestContext(request, {})
        )

def show_bulletin_board_print(request):
    """ Show the bulletin board tear-off page (print version). """
    site = get_current_site(request)
    context_instance_dict = {
            'site':site,
            'js_print': 1,
            'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
            'qr_image_path': get_ad_rep_qr_image_path(request)
            }
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'marketing_resources/display_bulletin_board_print.html',
        context_instance=context_instance)

def show_business_print_benefits(request):
    """ Show the benefits for local business advertisers page (print version).
    """
    site = get_current_site(request)
    context_instance_dict = {
            'site':site,
            'js_print': 1,
            'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
            'qr_image_path': get_ad_rep_qr_image_path(request)
            }
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'marketing_resources/display_benefits_for_business_print.html',
        context_instance=context_instance)

def redirect_compensation_overview(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('compensation-overview'))

def show_compensation_overview(request, connector=FirestormConnector()):
    """ Show compensation overview faq. """
    site = get_current_site(request)
    context_instance = {'site':site, 'js_compensation_overview': 1,
        'firestorm_api_url': connector.repl_website_API, 
        'dealer_id': request.session.get('ad_rep_id',''),
        'collapsible': True
        }
    return render_to_response(
        'marketing_resources/display_compensation_overview.html',
        context_instance=RequestContext(request, context_instance))

def redirect_our_competition(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('our-competition'))

def show_our_competition(request):
    """ Show the our competition page. """
    site = get_current_site(request)
    slot_price = get_unlocked_data(site)[0]
    context_instance_dict = {
            'site':site,
            'annual_slot_price': get_product_price(3, site),
            'slot_price':slot_price,
            }
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'marketing_resources/display_our_competition.html',
        context_instance=context_instance)

def show_our_competition_print(request):
    """ Show the our competition page (print version). """
    site = get_current_site(request)
    slot_price = get_unlocked_data(site)[0]
    context_instance_dict = {
            'site':site,
            'annual_slot_price': get_product_price(3, site),
            'slot_price':slot_price,
            'js_print': 1,
            'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
            'qr_image_path': get_ad_rep_qr_image_path(request)
            }
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'marketing_resources/display_our_competition_print.html',
        context_instance=context_instance)

def show_simple_steps_print(request):
    """ Show the simple steps to increase profits page (print version). """
    site = get_current_site(request)
    context_instance_dict = {
            'site':site,
            'js_print': 1,
            'http_protocol_host': settings.HTTP_PROTOCOL_HOST,
            'qr_image_path': get_ad_rep_qr_image_path(request)
            }
    context_instance = RequestContext(request, context_instance_dict)
    return render_to_response(
        'marketing_resources/display_simple_steps_print.html',
        context_instance=context_instance)

def show_testimonial_ad_rep(request):
    """ Show the ad rep testimonials page. """
    return render_to_response(
        'marketing_resources/display_testimonial_ad_rep.html',
        context_instance=RequestContext(request, {})
        )

def redirect_10localcoupons_story(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('the-10localcoupons-story'))

def show_the_10localcoupons_story(request):
    """ Show the 10localcoupons story page. """
    connector = FirestormConnector()
    return render_to_response(
        'marketing_resources/display_the_10localcoupons_story.html',
        context_instance=RequestContext(request, {
            'firestorm_api_url': connector.repl_website_API
        }))

def redirect_your_opportunity(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('your-opportunity'))

def show_your_opportunity(request):
    """ Show the your opportunity page. """
    connector = FirestormConnector()
    return render_to_response(
        'marketing_resources/display_your_opportunity.html',
        context_instance=RequestContext(request, {
            'firestorm_api_url': connector.repl_website_API
        }))

def redirect_compensation_plan(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('compensation-plan'))

def show_compensation_plan(request):
    """ Show the compensation plan page. """
    return render_to_response(
        'marketing_resources/display_compensation_plan.html',
        {'nav_compensation_plan': "on"},
        context_instance=RequestContext(request, {}, [products])
        )

def redirect_terms_of_agreement(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('terms-of-agreement'))

def show_terms_of_agreement(request):
    """ Show the terms of agreement page. """
    return render_to_response(
        'marketing_resources/display_terms_of_agreement.html',
        {'nav_terms_of_agreement': "on"},
        context_instance=RequestContext(request, {})
        )

def redirect_policies_procedures(request):
    """ Permanent Redirect for old url path. """
    return HttpResponsePermanentRedirect(reverse('policies-procedures'))

def show_policies_procedures(request):
    """ Show the policies and procedures page. """
    return render_to_response(
        'marketing_resources/display_policies_procedures.html',
        {'nav_policies_procedures': "on"},
        context_instance=RequestContext(request, {})
        )

@switch_is_active('replicated-website')
def show_ad_rep_menu(request, connector=FirestormConnector()):
    """ Page to display options for ad rep coming from firestorm backlink to 
    begin doing their business.
    """
    # Redirect to correct site.
    try:
        site_id = request.session['consumer']['site_id']
    except KeyError:
        site_id = None
    if site_id and get_current_site(request).id != site_id:
        redirect_path = check_for_site_redirect(
            request, site_id=request.session['consumer']['site_id'],
            redirect_path=reverse('build-your-network'))[1]
        if redirect_path:
            return HttpResponseRedirect(redirect_path)
    try:
        user_type = get_consumer_instance_type(
            request.session['consumer']['email'])[0]
        connector.get_ad_rep_or_404(request, 
            request.session['referring_ad_rep_dict'].url)
    except (AttributeError, KeyError):
        user_type = "none"
    context_instance = RequestContext(request)
    context_instance.update({'user_type': user_type})
    return render_to_response("display_build_your_network.html",
        context_instance=context_instance)

@switch_is_active('replicated-website')
def show_ad_rep_sign_in(request):
    """ Display ad rep sign in page in an iframe, displayed in FireStorm when
    accessing an account-specific page and not authenticated.
    """
    context_dict = RequestContext(request)
    if request.POST:
        return process_ad_rep_sign_in(request, context_dict)
    context_dict.update({'form': SignInForm(), 'is_ad_rep': True})
    return render_to_response("login/display_ad_rep_sign_in.html", 
        context_instance=context_dict)

@switch_is_active('replicated-website')
def process_ad_rep_sign_in(request, context_dict):
    """ Process AdRep sign in. Bypass redirect to firestorm and log into their
    advertiser account.
    """
    form = SignInForm(request.POST, 
        test_mode=request.session.get('tlc_sandbox_testing', False))
    if form.is_valid():
        redirect_path = process_login_from_form(request, form)
        if redirect_path:
            _next = request.GET.get('next', None)
            if _next:
                redirect_path = '%s?id=%s' % (_next, request.GET.get('id', ''))
            return HttpResponseRedirect(redirect_path)
    context_dict.update({'form': form, 'is_ad_rep': True})
    return render_to_response("login/display_ad_rep_sign_in.html", 
        context_instance=context_dict)

def show_become_an_ad_rep(request):
    """ Sell lead on becoming an ad rep. """
    return render_to_response(
        'marketing_resources/display_sell_ad_rep.html',
        context_instance=RequestContext(request))

def show_ad_rep_form(request):
    """ Show the become an ad rep page with form to generate lead. """
    initial_data, is_ad_rep, is_lead = set_ad_rep_enroll_initial_data(request)
    if is_lead:
        return HttpResponseRedirect(reverse('show-apply-review'))
    if request.POST:
        return process_ad_rep_lead(request,
            redirect_path=reverse('show-apply-review'))
    context_dict = {'ad_rep_lead_form': AdRepLeadForm(initial=initial_data),
        'question_form': QuestionForm(), 'onload_ad_rep_lead_form': 1,
        'is_ad_rep': is_ad_rep}
    return render_to_response(
        'marketing_resources/display_become_an_ad_rep.html',
        context_instance=RequestContext(request, context_dict))

def set_ad_rep_enroll_initial_data(request):
    """ For ad rep lead and ad rep enroll form, get user type then return 
    initial data to prepopulate the form. 
    """
    try:
        email = request.session['consumer']['email']
    except KeyError:
        email = None
    ad_rep = None
    ad_rep_lead = None
    if email:
        try:
            ad_rep = AdRep.objects.get(email=email)
        except AdRep.DoesNotExist:
            pass
        try:
            ad_rep_lead = AdRepLead.objects.get(email=email)
        except AdRepLead.DoesNotExist:
            pass
    initial_data = {}
    if not ad_rep:
        try:
            initial_data.update({'email': request.session['consumer']['email'],
                'first_name': request.session['consumer'].get('first_name', ''),
                'last_name': request.session['consumer'].get('last_name',
                        ''),
                'consumer_zip_postal': 
                    request.session['consumer'].get('consumer_zip_postal', '')
                })
            initial_data.update({'primary_phone_number': format_phone(
                request.session['consumer']['subscriber']
                    ['mobile_phone_number'])}) 
        except KeyError:
            pass
    if ad_rep_lead:
        initial_data.update({'primary_phone_number': 
            ad_rep_lead.primary_phone_number})
    return initial_data, bool(ad_rep), bool(ad_rep_lead)

def process_ad_rep_lead(request, redirect_path,
        connector=FirestormConnector()):
    """ Process lead form submission and show next step: apply review. """
    ad_rep_lead_form = AdRepLeadForm(request.POST)
    question_form = QuestionForm(request.POST)
    if ad_rep_lead_form.is_valid() and question_form.is_valid():
        try:
            ad_rep_lead = ad_rep_lead_form.save(request, redirect_path)
            ad_rep_lead = question_form.save(ad_rep_lead)
        except ValidationError:
            # ad rep lead is already ad rep
            email = ad_rep_lead_form.cleaned_data['email']
            consumer = Consumer.objects.get(email=email)
            create_consumer_in_session(request, consumer)
            return HttpResponseRedirect(reverse('show-ad-rep-form'))
        if ad_rep_lead:
            consumer = Consumer.objects.get(email=ad_rep_lead.email)
            create_consumer_in_session(request, consumer)
            AdRepConsumer.objects.create_update_rep(request, 
                    ad_rep_lead.consumer)
        return HttpResponseRedirect(ad_rep_lead_form.redirect_path)
    context_dict = {'ad_rep_lead_form': ad_rep_lead_form,
        'question_form': question_form}
    return render_to_response(
        'marketing_resources/display_become_an_ad_rep.html',
        context_instance=RequestContext(request, context_dict))

def show_apply_review(request):
    """ Check ad rep lead, if question is answered, display reviewing 
    application message.  
    """
    try: 
        email = request.session['consumer']['email']
        ad_rep_lead = AdRepLead.objects.get(email=email)
    except (KeyError, AdRepLead.DoesNotExist):
        return HttpResponseRedirect(reverse('show-ad-rep-form'))
    context_dict = {'ad_rep_lead': ad_rep_lead,
        'question_form': QuestionForm(initial={
            'right_person_text': ad_rep_lead.right_person_text}),
        'onload_ad_rep_lead_form': 1}    
    question_form = QuestionForm()
    if request.POST:
        question_form = QuestionForm(request.POST)
        if question_form.is_valid():
            ad_rep_lead = question_form.save(ad_rep_lead)
    context_dict = {'question_form': question_form, 'ad_rep_lead': ad_rep_lead}
    return render_to_response(
            'marketing_resources/display_apply_review.html',
            context_instance=RequestContext(request, context_dict))
  
@switch_is_active('replicated-website')
def show_offer_to_enroll(request, 
    firestorm_soap=FirestormSoap(sandbox_mode=settings.DEBUG), payload=None):
    """ Display final enrollment page with conditional password creation, chosen
    ad_rep_url and acceptance of our terms.
    """
    if payload:
        PAYLOAD_SIGNING.handle_payload(request, payload)
    try:
        consumer_values = Consumer.objects.filter(
            email=request.session['consumer']['email']).values_list(
            'adrep__id', 'adreplead__id', 'first_name')[0]
    except (Consumer.DoesNotExist, KeyError):
        consumer_values = None
    if not consumer_values or not(consumer_values[0] or consumer_values[1]):
        # If not an adrep and not an adrep lead, they do not belong here.
        return HttpResponseRedirect(reverse('become-an-ad-rep'))
    is_ad_rep = bool(consumer_values[0])
    context_dict = {'is_ad_rep': is_ad_rep, 'first_name': consumer_values[2]}
    if not is_ad_rep:
        if request.POST: # Don't show ad_reps forms, and don't post (back button).
            return process_offer_to_enroll(request)
        create_password_form = SetPasswordForm()
        terms_of_use_form = TermsOfUseForm()
        ad_rep_url_form = AdRepUrlForm()
        context_dict.update({'terms_of_use_form': terms_of_use_form,
            'create_password_form': create_password_form,
            'ad_rep_url_form': ad_rep_url_form})
    return render_to_response("firestorm/display_enrollment_offer.html",
        context_dict, context_instance=RequestContext(request))
    
def process_offer_to_enroll(request):
    """ Process form POST of show_offer_to_enroll. Save password, and convert
    ad rep lead to ad rep, update session and reload page or display errors. """
    context_dict = {}
    ad_rep_lead = AdRepLead.objects.get(
        email=request.session['consumer']['email'])
    ad_rep_id = None
    terms_of_use_form = TermsOfUseForm(
        request.POST, err_msg=ERROR_MSG_TERMS_ENROLLMENT)
    create_password_form = SetPasswordForm(request.POST)
    ad_rep_url_form = AdRepUrlForm(request.POST)
    if (terms_of_use_form.is_valid() and create_password_form.is_valid() and
        ad_rep_url_form.is_valid()):
        ad_rep_url = ad_rep_url_form.cleaned_data['ad_rep_url']
        password = create_password_form.cleaned_data['password1']
        ad_rep_id = enroll_ad_rep(request, ad_rep_lead, ad_rep_url, password)
        if ad_rep_id:
            SEND_ENROLLMENT_EMAIL.run(ad_rep_id=ad_rep_id)
            NOTIFY_NEW_RECRUIT.run(ad_rep_id)
    else:
        # If ad rep offer enrollment form was invalid, we need to validate forms.
        create_password_form.is_valid()
        ad_rep_url_form.is_valid()
    context_dict.update({'create_password_form': create_password_form,
        'terms_of_use_form': terms_of_use_form, 
        'consumer': ad_rep_lead.consumer, 'is_ad_rep': bool(ad_rep_id), 
        'ad_rep_url_form': ad_rep_url_form})
    return render_to_response("firestorm/display_enrollment_offer.html",
        context_dict, context_instance=RequestContext(request))

def show_recommend_enroll(request):
    """ This recommend to enroll as as ad rep page will be only accessible
    when a referring ad rep is in session. The user type could be any. 
    """
    initial_data = set_ad_rep_enroll_initial_data(request)[0]
    if not request.session.get('ad_rep_id', None):
        return HttpResponseRedirect(reverse('become-an-ad-rep'))
    if request.POST:
        return process_recommend_enroll(request)
    ad_rep_lead_form = AdRepLeadForm(initial=initial_data)
    set_password_form = SetPasswordForm()
    terms_of_use_form = TermsOfUseForm()
    ad_rep_url_form = AdRepUrlForm()
    context_dict = {'terms_of_use_form': terms_of_use_form,
        'ad_rep_url_form': ad_rep_url_form, 
        'ad_rep_lead_form': ad_rep_lead_form,
        'set_password_form': set_password_form}
    return render_to_response("firestorm/display_recommend_enroll.html",
        context_dict, context_instance=RequestContext(request))

def process_recommend_enroll(request):
    """ Process the form fields on submit of the recommend enroll page. """
    context_dict = {}
    ad_rep_id = None
    terms_of_use_form = TermsOfUseForm(
        request.POST, err_msg=ERROR_MSG_TERMS_ENROLLMENT)
    set_password_form = SetPasswordForm(request.POST)
    ad_rep_url_form = AdRepUrlForm(request.POST)
    ad_rep_lead_form = AdRepLeadForm(request.POST)
    # be sure error messages get set for each form
    lead_form_is_valid = ad_rep_lead_form.is_valid()
    url_form_is_valid = ad_rep_url_form.is_valid()
    password_form_is_valid = set_password_form.is_valid()
    if (terms_of_use_form.is_valid() and lead_form_is_valid and
        url_form_is_valid and password_form_is_valid):
        try:
            ad_rep = AdRep.objects.get(
                email=ad_rep_lead_form.cleaned_data['email'])
            create_consumer_in_session(request, consumer=Consumer.objects.get(
                email=ad_rep.email))
            return HttpResponseRedirect(reverse('recommend-enroll-success'))
        except AdRep.DoesNotExist:
            pass
            # create consumer and ad rep lead
        ad_rep_lead = ad_rep_lead_form.save(request)
        ad_rep_url = ad_rep_url_form.cleaned_data['ad_rep_url']
        password = set_password_form.cleaned_data['password1']
        ad_rep_id = enroll_ad_rep(request, ad_rep_lead, ad_rep_url, password)
        if ad_rep_id:
            SEND_ENROLLMENT_EMAIL.run(ad_rep_id=ad_rep_id, referred=True)
            NOTIFY_NEW_RECRUIT.run(ad_rep_id)
        return HttpResponseRedirect(reverse('recommend-enroll-success'))
    else:
       # trigger on ad rep model save, when password changed from 
        context_dict.update({'terms_of_use_form': terms_of_use_form,
            'ad_rep_lead_form': ad_rep_lead_form, 
            'ad_rep_url_form': ad_rep_url_form,
            'set_password_form': set_password_form,
            'is_ad_rep': bool(ad_rep_id)})
        return render_to_response("firestorm/display_recommend_enroll.html",
            context_dict, context_instance=RequestContext(request))

def show_recommend_enroll_success(request):
    """ Success rendering for when a recommend form is filled 
    out appropriately.
    """
    return render_to_response("firestorm/display_recommend_enroll_success.html",
        context_instance=RequestContext(request))


def enroll_ad_rep(request, ad_rep_lead, ad_rep_url, password):
    """ For this ad rep lead, create ad rep. """
    ad_rep_id = None
    city, state_province = get_city_and_state(
        ad_rep_lead.consumer_zip_postal)
    parent_ad_rep_id = 101997
    if ad_rep_lead.ad_rep and ad_rep_lead.ad_rep.rank != 'CUSTOMER':        
        parent_ad_rep_id = ad_rep_lead.ad_rep.id
    else:
        try:
            ad_rep = AdRep.objects.get_ad_rep_for_lead(ad_rep_lead.site)
            parent_ad_rep_id = ad_rep.id 
        except AdRep.DoesNotExist:
            pass
    ad_rep_dict = {
        'email': ad_rep_lead.email, 
        'first_name': ad_rep_lead.first_name,
        'last_name': ad_rep_lead.last_name, 
        'site': ad_rep_lead.site,
        'primary_phone_number': ad_rep_lead.primary_phone_number, 
        'url': ad_rep_url,
        'parent_ad_rep_id': parent_ad_rep_id, 
        'password': password,
        'city': city, 
        'state_province': state_province,
        'zip_postal': ad_rep_lead.consumer_zip_postal}
    ad_rep_id = process_ad_rep_lead_to_ad_rep(request, ad_rep_dict)
    return ad_rep_id

def process_ad_rep_lead_to_ad_rep(request, ad_rep_dict):
    """ From ad rep enrollment form save (ad_rep_url), password and convert 
    this AdRepLead to an AdRep.
    """
    ad_rep_lead = AdRepLead.objects.get(email=ad_rep_dict['email'])
    ad_rep = AdRep.objects.create_ad_rep_from_ad_rep_lead(
        ad_rep_lead.consumer.id, ad_rep_dict)
    ad_rep.primary_phone_number = ad_rep_dict['primary_phone_number']
    ad_rep.rank = 'ADREP'
    ad_rep.save()
    consumer = ad_rep.consumer
    consumer.set_password(ad_rep_dict['password'])
    consumer.save()
    user = authenticate(username=consumer.email, 
        password=ad_rep_dict['password'])
    process_login(request, user)
    return ad_rep.id

def redirect_virtual_office(request, connector=FirestormConnector()):
    """ Virtual office link in header menu to take them to firestorm url and
    with credentials to be automatically logged in.
    """
    ad_rep = None     
    try:
        if not request.user.is_authenticated():
            raise(KeyError)
        ad_rep = AdRep.objects.get(email=request.session['consumer']['email'])
    except (AdRep.DoesNotExist, KeyError):
        LOG.debug('Ad_rep not in session: %s' % ad_rep)
        return HttpResponseRedirect(reverse('sign-out'))
    return HttpResponseRedirect(connector.load_virtual_office_home(request))

def show_firestorm_password_help(request):
    """ Show page with iframe of Firestorm password help. """
    context = {'firestorm_pwd_reset_url': 
        FirestormConnector().reset_password_URL}
    return render_to_response("firestorm/display_password_reset.html",
        RequestContext(request, context))

def show_quick_start_assistance(request, payload=None):
    """ Provide links to comp plan power points, business cards to ad reps. """
    if payload:
        PAYLOAD_SIGNING.handle_payload(request, payload)
    return render_to_response("firestorm/display_quick_start.html",
        RequestContext(request))

def show_pdf_business_cards(request):
    """ Display pdf version of this adreps business cards. """
    try:
        email = request.session['consumer']['email']
    except KeyError:
        email = None
    if email:
        try:
            ad_rep = AdRep.objects.get(email=email)
        except AdRep.DoesNotExist:
            ad_rep = None
    ad_rep_name = '%s %s' % (ad_rep.first_name, ad_rep.last_name)
    ad_rep_url = 'www.10coupons.com/%s/' % ad_rep.url
    if ad_rep.primary_phone_number:
        ad_rep_phone_number = format_phone(ad_rep.primary_phone_number)
    else:
        ad_rep_phone_number = ''
    card_width = 3.5
    card_height = 2
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'filename=BusinessCards.pdf'
    site_logo = Image("%s/media/images/print/Ad_Rep_BizCard.png" % 
        settings.PROJECT_PATH, width=card_width*inch, height=card_height*inch)
    canvas = canv.Canvas(response, pagesize=letter)
    CellStyle.leftPadding = 0
    CellStyle.rightPadding = 0
    CellStyle.topPadding = 0
    CellStyle.bottomPadding = 0
    table = Table([[site_logo]], colWidths=card_width*inch, rowHeights=card_height*inch)
    table.setStyle(TableStyle([
                           ('VALIGN', (0,0), (-1,-1), 'TOP'),
                           ('BOX', (0,0), (-1,-1), 0.25, colors.lightgrey),
                           ])) 
    table.wrapOn(canvas, 0, 0)
    y_draw = .5
    x_txt_point = .9
    y_txt_point = 1.15
    while y_draw <= 8.5:      
        table.drawOn(canvas, .75*inch, y_draw*inch)
        table.drawOn(canvas, 4.25*inch, y_draw*inch)
        canvas.setFont('Helvetica', 10)
        canvas.drawString(x_txt_point*inch,
                          y_txt_point*inch,ad_rep_name)
        canvas.drawString((x_txt_point+.38)*inch,
                          (y_txt_point-.405)*inch, ad_rep_url)
        canvas.drawString((x_txt_point+3.51)*inch,
                          y_txt_point*inch,ad_rep_name)
        canvas.drawString((x_txt_point+3.88)*inch,
                          (y_txt_point-.405)*inch, ad_rep_url)
        canvas.setFont('Helvetica', 6)
        canvas.drawRightString((x_txt_point+3.3)*inch,
                               y_txt_point*inch, ad_rep.email)
        canvas.drawRightString((x_txt_point+3.3)*inch,
                               (y_txt_point-.13)*inch, ad_rep_phone_number)
        canvas.drawRightString((x_txt_point+6.8)*inch,
                               y_txt_point*inch, ad_rep.email)
        canvas.drawRightString((x_txt_point+6.8)*inch,
                               (y_txt_point-.13)*inch, ad_rep_phone_number)
        y_draw += 2
        y_txt_point += 2
    canvas.showPage()
    canvas.save()
    return response
