""" Context processors for the email_gateway app of project ten."""

from django.conf import settings

from common.custom_format_for_display import format_phone
from consumer.service import get_site_rep
from ecommerce.service.calculate_current_price import get_product_price
from firestorm import FIRESTORM_REPL_WEBSITE_API
from firestorm.models import AdRep

def set_header(sales_rep):
    """ Set the header from the sales rep. The reply-to should be to
    10coupons.com.
    """
    return { 'Reply-To': "%s@%s" % (sales_rep.consumer.first_name,
        sales_rep.email_domain)}

def get_ad_rep_context(ad_rep, instance_filter=None, cc_rep=False, site=None):
    """ Return the context for an ad_rep. """
    if ((instance_filter == 'advertiser' and ad_rep.rank == 'CUSTOMER')
    or instance_filter == 'ad_rep'):
        # Advertisers should not receive emails from a CUSTOMER ad rep.
        # Ad Reps should not receive emails from themselves.
        raise AdRep.DoesNotExist
    context = {
        'company': ad_rep.company,
        'firestorm_id': ad_rep.firestorm_id,
        'firestorm_repl_website_api': FIRESTORM_REPL_WEBSITE_API,
        'has_ad_rep': True,
        'rep_first_name': ad_rep.first_name,
        'rep_last_name': ad_rep.last_name,
        'signature_ad_rep_url': ad_rep.url,
        'signature_email': ad_rep.email,
        'signature_name': "%s %s" % (ad_rep.first_name, ad_rep.last_name),
        'signature_phone': format_phone(ad_rep.primary_phone_number),
        'signature_title': ad_rep.get_rank_display(),
        # This flag informs email_gateway.send.send_email that the
        # signature_email address should also be cc_rep:ed on this email.
        'cc_signature_flag': cc_rep,
        }
    if site:
        context['headers'] = set_header(get_site_rep(site))
    return context

def get_sales_rep_context(site, context):
    """ Return the context for a sales_rep. """
    sales_rep = get_site_rep(site)
    context = {
        'signature_name': "%s %s" % (sales_rep.consumer.first_name,
            sales_rep.consumer.last_name),
        'rep_first_name': sales_rep.consumer.first_name,
        'rep_last_name': sales_rep.consumer.last_name,
        'signature_title': sales_rep.title,
        'signature_email': "%s@%s" % (sales_rep.consumer.first_name,
            sales_rep.email_domain),
        'signature_phone': "%s ext %s" % (settings.MAIN_NUMBER,
            sales_rep.extension),
        'headers': set_header(sales_rep),
        'company': None,
        }
    return context

def get_rep_context(site, email, instance_filter=None, cc_rep=False,
        is_lead=False):
    """ Populate an email context with referring_ad_rep or sales_rep info.

    is_lead: If this is a lead email, use the get_ad_rep_for_lead logic to give
    this lead to the appropriate ad_rep.

    Note: This is not a standard context_processor in that it does not take a
    request object. As a result, you cannot pass it, with a template, to
    render_to_response, but have to call it directly.
    """
    consumer_count = site.get_or_set_consumer_count()
    slot_price = get_product_price(2, site=site)
    context = {
        'slot_price': slot_price,
        'consumer_count': consumer_count,
        }
    try:
        ad_rep = AdRep.objects.exclude(rank='CUSTOMER').get(
            ad_rep_advertisers__advertiser__email=email)
        context.update(get_ad_rep_context(ad_rep, instance_filter, cc_rep,
            site=site))
    except AdRep.DoesNotExist:
        try:
            ad_rep = AdRep.objects.exclude(rank='CUSTOMER').get(
                ad_rep_consumers__consumer__email=email)
            context.update(get_ad_rep_context(ad_rep, instance_filter, cc_rep,
                site=site))
        except AdRep.DoesNotExist:
            if is_lead:
                try:
                    ad_rep = AdRep.objects.get_ad_rep_for_lead(site)
                    context.update(get_ad_rep_context(ad_rep, instance_filter,
                        cc_rep, site=site))
                except AdRep.DoesNotExist:
                    context.update(get_sales_rep_context(site, context))
            else:
                context.update(get_sales_rep_context(site, context))
    return context
