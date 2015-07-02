""" tasks for the feed app """

import calendar
import datetime
import dateutil.parser as dparser
import logging
import re
import xml.dom.minidom

from BeautifulSoup import BeautifulStoneSoup, BeautifulSoup, SoupStrainer
from celery.decorators import task

from django.core import validators
from django.core.exceptions import ValidationError

from advertiser.models import Business
from common.utils import parse_phone
from coupon.models import Coupon
from ecommerce.models import Order
from feed.models import FeedProvider, FeedCoupon
from feed.service import (get_web_page, manage_feed_coupons,
    scrape_incentrev_single_coupon)
from feed.sugar import Sugar 
from feed.sugar_in import (sync_sugar_account, sync_sugar_contact,
    set_sugar_relationship, create_sugar_reminder_task)
from feed.sugar_out import (get_recent_sugar_entry, prepare_sync_business,
    sync_advertiser, sync_business, sync_business_location)
from market.models import Site
from market.service import get_close_sites

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

@task()
def import_nashville_deals():
    """ Import Nashville half off daily deals and convert them to coupons """
    try:
        feed_provider = FeedProvider.objects.get(
            name="Nashville Half Off Deals")
    except FeedProvider.DoesNotExist:
        LOG.error('feed provider does not exist')
        return
    feed_xml = get_web_page(feed_provider.feed_url)
    if xml.dom.minidom.parseString(feed_xml):
        xml_soup = BeautifulStoneSoup(feed_xml)
        for promo in xml_soup.findAll(name="promo"):
            external_id = promo['id']
            business_name = promo.text.replace('&amp;', '&')[:100]
            LOG.debug('id: %s, business: %s' % (external_id, business_name))
            feed_coupon, created = FeedCoupon.objects.get_or_create(
                external_id=external_id, feed_provider=feed_provider)
            if created:
                LOG.debug(feed_coupon)
            price = promo['value']
            deal_type = promo['type']
            feed_coupon.offer = "50%% off $%s %s" % (price, deal_type)
            feed_coupon.business_name = business_name 
            feed_coupon.coupon_url = promo['url']
            try:
                feed_coupon.logo_url = promo['logoimage']
            except KeyError:
                pass
            feed_coupon.save()
        manage_feed_coupons(feed_provider)
    else:
        LOG.error('failed to get a valid xml file')
    return

@task() 
def scrape_incentrev_coupons():
    """ Screen scrape Incentrev main page using BeatifulSoup """
    try:
        feed_provider = FeedProvider.objects.get(
            name="IncentRev Coupon Scrape")
    except FeedProvider.DoesNotExist:
        LOG.error('feed provider does not exist')
        return
    LOG.debug('IncentRev scrape started')
    page = get_web_page(feed_provider.feed_url)
    all_soup = BeautifulSoup(page)
    for link in BeautifulSoup(page, parseOnlyThese=SoupStrainer('a')):
        if link.has_key('href') and link.text == 'Learn More & Buy Now':
            coupon_link = link['href']
            ext_coupon_id = coupon_link.replace('/detail/', '')
            LOG.debug('ext_coupon_id = %s' % ext_coupon_id)
            coupon_link = feed_provider.feed_url + coupon_link[1:]
            LOG.debug('coupon link = %s' % coupon_link)
            # Get business_logo.
            for div in all_soup.findAll('div', attrs={'class' : 'image'}): 
                if ext_coupon_id in div.a['href']:
                    image = div.find('img')['src']
                    LOG.debug('logo = %s' % image)
                    logo_url = feed_provider.feed_url + image[1:]
                    break
            scrape_incentrev_single_coupon(feed_provider, coupon_link, logo_url)
    manage_feed_coupons(feed_provider)
    return

@task()
def sync_business_to_sugar(coupon=None, offer=None, business=None, sugar=None): 
    """ Sync this coupon business to SugarCRM using web service """
    if sugar is None:
        sugar = Sugar()
    account_id = sync_sugar_account(sugar, coupon=coupon, offer=offer, 
        business=business)
    if account_id:
        contact_id = sync_sugar_contact(sugar, coupon=coupon, offer=offer, 
            business=business)
    else:
        contact_id = None
    if account_id and contact_id: 
        set_sugar_relationship(sugar, module1='Accounts', 
            module1_id=account_id, module2='Contacts', 
            module2_id=contact_id) 

@task()
def sync_all_to_sugar(sugar=Sugar(), business_id_start=1, business_id_end=1): 
    """ Sync a selection of coupon businesses to SugarCRM using web service. """
    LOG.debug(sugar.web_service_url)
    LOG.debug('syncing business id: %d to %d ' % (business_id_start, 
        business_id_end))
    businesses = Business.objects.filter(id__gte=business_id_start).filter(
        id__lte=business_id_end)
    for business in businesses:
        LOG.debug(business)
        sync_business_to_sugar(business=business, sugar=sugar)
    
@task()
def sync_business_from_sugar(test_mode=False, get_modified=False, 
    offset_minutes=10, sugar=None): 
    """ 
    Sync recently created or modified businesses from SugarCRM accounts and 
    contacts modules using web service. If get_modified is False, then only 
    create of new sugar businesses will sync else create/modified businesses
    will sync.
    """
    LOG.info('sync_business_from_sugar')
    if sugar is None:
        sugar = Sugar()
    account_module = 'Accounts'
    contact_module = 'Contacts'
    # Get recent sugar changes.
    account_list = get_recent_sugar_entry(sugar, module=account_module,
        test_mode=test_mode, get_modified=get_modified, 
        offset_minutes=offset_minutes) 
    contact_list = get_recent_sugar_entry(sugar, module=contact_module,
        test_mode=test_mode, get_modified=get_modified, 
        offset_minutes=offset_minutes)
    if account_list is None and contact_list is None:
        LOG.info("no recent entries")
        return
    # Sync sugar account changes.
    for account_dict in account_list:
        contact_dict = prepare_sync_business(sugar, module1=account_module, 
            module2=contact_module, module1_dict=account_dict)
        if contact_dict:
            sync_coupon_business(sugar, account_dict=account_dict, 
                contact_dict=contact_dict, modify_mode=get_modified)
    # Sync sugar contact changes
    for contact_dict in contact_list:
        account_dict = prepare_sync_business(sugar, module1=contact_module, 
            module2=account_module, module1_dict=contact_dict)
        if account_dict:
            sync_coupon_business(sugar, account_dict=account_dict, 
                contact_dict=contact_dict, modify_mode=get_modified)

@task()
def sync_coupon_business(sugar, account_dict, contact_dict, modify_mode=False):
    """
    Get most recently modified entry in this Sugar module. Make sure to only get
    records that are created and don't have a business_id value yet. 
    Make sure the Sugar Contact (advertiser) and Sugar Account (business) exists 
    for this business.(i.e. aren't synced yet).
    """
    # Why not combine account_dict and contact_dict here
    LOG.debug('sync_coupon_business')
    if account_dict['business_id_c'] and modify_mode is False:
        LOG.error('Business already exists')
        return 
    if contact_dict['primary_address_postalcode']:
        postal_code = re.findall(re.compile('\d{5}'), 
            contact_dict['primary_address_postalcode'])[0]
        if postal_code:
            site_list = get_close_sites(postal_code)
            if not site_list:
                LOG.error('No close site to this zip: %s' % postal_code) 
                return 
            site = Site.objects.get(id=site_list[0]['id'])
            LOG.debug('closet site id: %s' % str(site.id))    
        # Sync: Advertiser, Business, and Location.
        advertiser_name = (contact_dict['first_name'].strip() + ' ' +
            contact_dict['last_name'].strip())[:50]
        if account_dict['email1']:
            try:
                validators.validate_email(account_dict['email1'].strip())
            except ValidationError:
                return  
            advertiser = sync_advertiser(sugar=sugar, 
                email=account_dict['email1'].strip(), 
                advertiser_name=advertiser_name, site=site, 
                    contact_dict=contact_dict)
            if advertiser:
                business = sync_business(sugar, advertiser, account_dict)
                if business:
                    phone_dict = parse_phone(
                        phone_number=account_dict['phone_office'])
                    sync_business_location(business, postal_code, contact_dict, 
                        account_dict, phone_dict)
    return 

@task()
def create_sugar_coupon_expire_task(sugar=Sugar(), offset_days=2): 
    """ 
    Create a sugar activity task related to contact and account when a current 
    coupon is about to expire. 
    """
    future_date = datetime.datetime.today() + \
        datetime.timedelta(days=offset_days)
    business_list = []
    for coupon in Coupon.current_coupons.all():
        if coupon.expiration_date == future_date.date():
            business_list.append(coupon.offer.business)
    LOG.debug('business_list = %s' % business_list) 
    if not business_list:
        return 
    subject = 'Reminder to update offer.'
    for business in business_list:
        create_sugar_reminder_task(sugar, business, subject, offset_days)

@task()
def create_sugar_cc_expire_task(sugar=Sugar(), test_mode=False):
    """
    Create a sugar activity task related to contact and account when an order's
    credit card is about to expire in this month.
    """
    today = datetime.datetime.today()
    # Get number of days in this month.
    offset_days = calendar.mdays[datetime.date.today().month]
    subject = 'Reminder to update credit card.'
    orders = Order.objects.filter(create_datetime__gt=(
        today + datetime.timedelta(days=-offset_days))).order_by('-id')
    LOG.debug(orders)
    for order in orders:
        LOG.debug(order)
        credit_card = order.payments.all()[0].credit_card
        cc_exp_month = credit_card.exp_month
        cc_exp_year = credit_card.exp_year
        cc_exp_date = str(cc_exp_month) + '/1/' + str(cc_exp_year)
        LOG.debug(cc_exp_date)
        exp_datetime =  dparser.parse(cc_exp_date)
        if exp_datetime.date() == today.date() or (
            test_mode and exp_datetime < today):
            business = order.billing_record.business 
            create_sugar_reminder_task(sugar, business, subject, offset_days)
