""" Service methods for Media Partner App """
#pylint: disable=W0104

import calendar
import datetime
from decimal import Decimal

from django.db.models import Q
from django.template.defaultfilters import date as date_filter
from django.utils import simplejson

from common.custom_format_for_display import list_as_text
from ecommerce.models import Payment
from media_partner.models import MediaPartner, MediaPieShare

def filter_report_payments(site):
    """ Filter the payments for the transaction report. """
    return Payment.objects.filter(
            Q(status='A') | Q(status='J') | Q(status='R')
        ).filter(
            order__order_items__site=site
        ).exclude(is_void=True).distinct('id').order_by('-create_datetime')

def get_user_type(request):
    """ Return the user type for the user in session. This is for use after
    media_partner.decorators.media_partner_required, where the user is always
    either an affiliate_partner or a media_group_partner. """
    try:
        this_consumer = request.session['consumer']
        email = this_consumer['email']
        this_consumer['affiliate_partner']
        user_type = 'affiliate_partner'
    except KeyError:
        this_consumer['media_group_partner']
        user_type = 'media_group_partner'
    media_partner = MediaPartner.objects.get(email=email)
    return user_type, media_partner

def can_view_this_report(user_type, media_partner, site_id):
    """ Return boolean: Can this user_type view this report? """
    can_view_this_report_ = False
    affiliate = media_group = None
    if user_type in 'affiliate_partner':
        for this_affiliate in media_partner.affiliates.all():
            if site_id == this_affiliate.site.id:
                can_view_this_report_ = True
                media_group = None
                affiliate = this_affiliate
    else:
        for media_group in media_partner.media_groups.all():
            affiliates  = media_group.affiliates.all()
            for this_affiliate in affiliates:
                if site_id == this_affiliate.site.id:
                    can_view_this_report_ = True
                    affiliate = this_affiliate
    return can_view_this_report_, media_group, affiliate

def get_inception_string(site):
    """ Return a string labelling the revenue since inception report. """
    return 'From Launch Date (' + date_filter(site.launch_date, 'F') + ' ' + \
        date_filter(site.launch_date, 'Y') + ')'

def get_current_month_string():
    """ Return a string labelling this month. """
    today = datetime.date.today()
    return 'Current Month (' + date_filter(today, 'F') + ' ' + \
        date_filter(today, 'Y') + ')'

def get_drop_down_data(all_create_dates):
    """ Figure out what quarter this current payment belongs to and set the
    report string for the templates drop down.
    """
    first_quarter = [1, 2, 3]
    second_quarter = [4, 5, 6]
    third_quarter = [7, 8, 9]
    fourth_quarter = [10, 11, 12]
    payment_year = all_create_dates[0]['create_datetime'].year
    payment_month = all_create_dates[0]['create_datetime'].month
    if payment_month in first_quarter:
        report_name = 'Q1 ' + str(payment_year)
        first_month_of_quarter = first_quarter[0]
        last_month_of_quarter = first_quarter[2]
    if payment_month in second_quarter:
        report_name = 'Q2 ' + str(payment_year)
        first_month_of_quarter = second_quarter[0]
        last_month_of_quarter = second_quarter[2]
    if payment_month in third_quarter:
        report_name = 'Q3 ' + str(payment_year)
        first_month_of_quarter = third_quarter[0]
        last_month_of_quarter = third_quarter[2]
    if payment_month in fourth_quarter:
        report_name = 'Q4 ' + str(payment_year)
        first_month_of_quarter = fourth_quarter[0]
        last_month_of_quarter = fourth_quarter[2]
    first_date_of_the_quarter = datetime.date(payment_year,
        first_month_of_quarter, 1)
    return payment_year, report_name, last_month_of_quarter, \
        first_date_of_the_quarter

def filter_payments_by_dates(payments, report, all_create_dates):
    """ Filter payments for either the current_month or quarterly report.
    The only payments that will show are the ones for which a media_pie_share
    was active in a specific time period.
    """
    today = datetime.datetime.today()
    if report == get_current_month_string():
        first_date = datetime.date(today.year, today.month, 1)
        last_day = calendar.monthrange(today.year, today.month)[1]
        last_date = datetime.date(today.year, today.month, last_day)
    else:
        # Else we are running one of the dynamic Quarterly reports for
        # this specific market.
        while all_create_dates:
            payment_year, report_name, last_month_of_quarter, \
            first_date_of_the_quarter = get_drop_down_data(all_create_dates)
            if report == report_name:
                first_date = first_date_of_the_quarter
                last_day = calendar.monthrange(payment_year,
                    last_month_of_quarter)[1]
                last_date = datetime.date(payment_year, last_month_of_quarter,
                    last_day)
                break
            all_create_dates = all_create_dates.exclude(
                create_datetime__gte=first_date_of_the_quarter)
    last_date = last_date + datetime.timedelta(days=1)
    return payments.filter(
        create_datetime__range=(first_date, last_date)), first_date

def single_media_pie_share_handler(media_pie_share, payments, site):
    """ Return report data for a media_partner affiliate who has a single
    media_pie_share within this time period.
    """
    start_date = media_pie_share.start_date
    if media_pie_share.end_date:
        # Get the end_date for this affiliates share from this time
        # period.
        end_date = media_pie_share.end_date
    else:
        # This share is still active.
        end_date = datetime.datetime.today()
    # Get all payments for this shares time period and calculate
    # the rest.
    end_date = end_date + datetime.timedelta(1)
    payments_for_this_share = payments.filter(
        create_datetime__range=(start_date, end_date))
    payments = payments_for_this_share
    report_data = dict()
    report_data['gross_collected_revenue'] = get_gross_revenue(payments, site)
    report_data['variable_expenses'] = abs(
            (report_data['gross_collected_revenue'] * Decimal('.20')))
    report_data['net_collected_revenue'] = (
        report_data['gross_collected_revenue'] - 
        report_data['variable_expenses'])
    report_data['media_partner_revenue'] = (
        report_data['net_collected_revenue'] * Decimal('.70'))
    # media_pie_share changes from an instance to a share value!
    report_data['media_pie_share'] = Decimal(str(media_pie_share.share))
    report_data['total_earnings'] = (
        report_data['media_partner_revenue'] * report_data['media_pie_share'])
    return report_data, payments

def multiple_media_shares_handler(media_pie_shares, payments, site):
    """ Return report data for a media_partner affiliate who has multiple
    media_pie_shares within this time period.
    """
    hide_media_pie_share = False
    report_data = dict((var, 0) for var in ['gross_collected_revenue',
        'variable_expenses', 'net_collected_revenue', 'media_partner_revenue',
        'media_pie_share', 'total_earnings'])
    temp_payments = None
    if media_pie_shares:
        for media_pie_share in media_pie_shares:
            start_date = media_pie_share.start_date
            if media_pie_share.end_date:
                # Get the end_date for this affiliates share from
                # this time period.
                end_date = media_pie_share.end_date
            else:
                # This share is still active.
                end_date = datetime.datetime.today()
            end_date = end_date + datetime.timedelta(1)
            payments_for_this_share = payments.filter(
                create_datetime__range=(start_date, end_date))
            if temp_payments:
                temp_payments = payments_for_this_share | temp_payments
                hide_media_pie_share = True
            else:
                temp_payments = payments_for_this_share
            gross_for_this_share = get_gross_revenue(
                payments_for_this_share, site)
            variable_expenses_this_share = (
                gross_for_this_share * Decimal('.20'))
            net_collected_for_this_share = (
                gross_for_this_share - variable_expenses_this_share)
            media_revenue_for_this_share = (
                net_collected_for_this_share * Decimal('.70'))
            # media_pie_share changes from an instance to a share value!
            report_data['media_pie_share'] = Decimal(str(media_pie_share.share))
            total_earnings_for_this_share = (
                media_revenue_for_this_share * report_data['media_pie_share'])
            # Add all the for_this_share values to their totals
            report_data['gross_collected_revenue'] += gross_for_this_share
            report_data['variable_expenses'] += variable_expenses_this_share
            report_data['net_collected_revenue'] += net_collected_for_this_share
            report_data['media_partner_revenue'] += media_revenue_for_this_share
            report_data['total_earnings'] += total_earnings_for_this_share
    else:
        payments = []
    if temp_payments != None:
        # The temp_payments will be None if we are viewing the
        # current_month report and no payments have been processed
        # yet.
        payments = temp_payments
    return report_data, payments, hide_media_pie_share

def get_json_data(request, site, all_create_dates, media_pie_shares):
    """ Return json formatted data for rendering the transaction report. """
    payments = filter_report_payments(site).select_related(
            'order__billing_record__business'
        )
    # Select the payments so we can calculate the Starting Quarter and the
    # final quarter to report on.
    # The media_pie_share will be hidden if there is more than 1 share
    # spanning a report that is being viewed.
    hide_media_pie_share = False
    report = request.POST['report']
    if report == get_inception_string(site):
        report_data = dict()
        payments_count = payments.count()
        if payments_count > 0:
            # Inception aka From Launch report only displays the
            # gross_collected_revenue.
            report_data['gross_collected_revenue'] = \
                get_gross_revenue(payments, site)
        else:
            report_data['gross_collected_revenue'] = 0
        report_data['variable_expenses'] = 0
        report_data['net_collected_revenue'] = 0
        report_data['media_partner_revenue'] = 0
        report_data['media_pie_share'] = 0
        report_data['total_earnings'] = 0
    else:
        payments, first_date = filter_payments_by_dates(
            payments, report, all_create_dates)
        # Get the pie shares that have an end_date that is >= first_date the
        # report is for, or the end_date is null meaning it is a current
        # active share.
        old_media_pie_shares = media_pie_shares.filter(
            end_date__gte=first_date)
        active_media_pie_shares = media_pie_shares.filter(
            end_date__isnull=True)
        media_pie_shares = old_media_pie_shares | active_media_pie_shares
        if media_pie_shares.count() == 1:
            report_data, payments = single_media_pie_share_handler(
                media_pie_shares[0], payments, site)
        else:
            report_data, payments, hide_media_pie_share = \
                multiple_media_shares_handler(media_pie_shares, payments, site)
    if hide_media_pie_share is True:
        report_data['media_pie_share'] = ''
    else:
        report_data['media_pie_share'] = 'x  ' '%d%%' % (
            report_data['media_pie_share'] * 100)
    # Create the Json.
    json = simplejson.dumps({'items':[
        {
            'subtotal':get_subtotal(payment, site),
            'business':get_business_str_with_refund(payment),
            'date':date_filter(payment.create_datetime, 'n/j/y'),
            'invoice':payment.order.invoice,
        }
        for payment in payments],
        'gross_collected_revenue':
            '$' '%.2f' % report_data['gross_collected_revenue'],
        'variable_expenses':
            '-$' '%.2f' % abs(report_data['variable_expenses']),
        'net_collected_revenue':
            '$' '%.2f' % report_data['net_collected_revenue'],
        'media_partner_revenue':
            '$' '%.2f' % report_data['media_partner_revenue'],
        'media_pie_share':
            report_data['media_pie_share'],
        'total_earnings':
            '$' '%.2f' % report_data['total_earnings']})
    return json

def get_report_list(site, all_create_dates, media_pie_shares):
    """ Return a list of reports. """
    report_list = [get_inception_string(site), get_current_month_string()]
    for media_pie_share in media_pie_shares:
        start_date = media_pie_share.start_date
        if media_pie_share.end_date:
            # Get the end_date for this affiliates share from this time
            # period.
            end_date = media_pie_share.end_date
        else:
            # This share is still active.
            end_date = datetime.date.today()
        # Add a day to the end_date so we select all records for the current
        # date.
        end_date = end_date + datetime.timedelta(days=1)
        all_create_dates_this_share = all_create_dates.filter(
            create_datetime__range=(start_date, end_date))
        while all_create_dates_this_share:
            # Only need the 2nd and 4th items return by this:
            report_name, first_date_of_the_quarter = \
                get_drop_down_data(all_create_dates_this_share)[1::2]
            all_create_dates_this_share = all_create_dates_this_share.exclude(
                create_datetime__gte=first_date_of_the_quarter)
            if report_name not in report_list:
                report_list.append(report_name)
    return report_list

def get_business_str_with_refund(payment):
    """ Append the string (Refund) to a business_name if a payment is 
    a Refund in the Transaction Report. 
    """
    business_name = payment.order.billing_record.business.business_name
    if payment.status == 'R':
        business_name = '%s (Refund)' % business_name
    return business_name

def get_gross_revenue(payments, site):
    """ Add up the gross collected revenue for the monthly and the current month
    Transaction Report.
    """
    gross_collected_revenue = 0
    for payment in payments:
        gross_collected_revenue = gross_collected_revenue + \
            Decimal(get_subtotal(payment, site))
    return gross_collected_revenue

def get_site_active_media_mediums(site_id):
    """ Return a distinct list of media mediums currently advertised
    by media affiliates on a given site (as per MediaPieShare).
    """
    today = datetime.date.today()
    medium_list = MediaPieShare.objects.filter(site=site_id
        ).exclude(Q(start_date__gt=today
        ) | Q(end_date__isnull=False,end_date__lt=today)
        ).values_list('affiliate__medium__name',flat=True).distinct()
    return list_as_text(medium_list).lower()

def has_medium_partnered(medium_list, site_id):
    """ Return True if any medium in the list matches a media partner's medium
    for this site. 
    """
    site_media = set(get_site_active_media_mediums(site_id).split(' '))
    medium_set = set(medium_list)
    if medium_set.intersection(site_media):
        return True
    else:
        return False
    
def get_subtotal(payment, site):
    """ Return the collected revenue (or refund) for this payment net of any
    promoter cut. This method is called for each payment when building the json
    for the Transaction Report.  We are either returning a refunded payment
    amount, or the sum of all order_items for a specific payment related to
    this site.
    """
    order_items_subtotal = 0
    percent_total = payment.order.total / payment.order.subtotal
    percent_paid = payment.amount / payment.order.total
    for order_item in payment.order.order_items.filter(site=site):
        order_item_total = order_item.amount * percent_total
        order_item_paid_amount = percent_paid * order_item_total
        order_items_subtotal = order_items_subtotal + order_item_paid_amount
    # Promoter cut, if any, reduces order_items_subtotal.
    order_items_subtotal -= payment.order.promoter_cut_amount
    return '%.2f' % order_items_subtotal