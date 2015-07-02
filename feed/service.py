""" Service methods for the feed apps """

import datetime
import logging
import os
import re
import time

from django.conf import settings 
from django.db import DatabaseError
from django.template.defaultfilters import slugify
from BeautifulSoup import BeautifulSoup

from advertiser.models import Advertiser, Business, Location
from advertiser.business.tasks import take_web_snap
from common.utils import open_url
from coupon.models import Offer, Coupon, CouponType
from feed.models import FeedCoupon, FeedRelationship

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

def get_web_page(web_url, cache_file=None, request_pause=2.1, hours=5):
    """ This function gets web page for a given URL.
        A file is used to cache the html just like a web browser.
        Args:
            web_url = website name
            cache_file = filename to cache web pages to disk
            request_pause = amount of seconds to pause between web requests
            hours = amount of hours to cache web page data to disk
        Returns:
            web page source 
    """
    cache_path = '/tmp/'
    if not cache_file:
        cache_file = slugify(web_url.replace('http://', ''))[:100] + '.htm'
    cache_filename = cache_path + cache_file
    LOG.debug('cache_file = %s' % cache_filename) 
    LOG.debug('web_url = %s' % web_url)
    if os.path.exists(cache_filename) and is_file_recent(
        filename=cache_filename, hours=hours):
        LOG.debug('Get data from cache_file')
        myfile = open(cache_filename) # reading
        web_page = myfile.read()
    else:
        LOG.debug('Get data from web_url') 
        time.sleep(request_pause) 
        web_page = open_url(web_url)
        if web_page:
            myfile = open(cache_filename, 'w')
            myfile.write(web_page) 
            myfile.close()
            print 'Finished adding URL data to file: %s' % cache_filename
    return web_page

def is_file_recent(filename, hours): 
    """ Returns True if file modified (recently) under hours. """
    file_time = os.path.getmtime(filename) #Epoch seconds
    return (time.time() - file_time)/3600 < hours

def manage_feed_coupons(feed_provider):
    """ This will manage (create, expire, modify) feed coupons on the coupon 
    website for this feed provider.
    """
    try:
        advertiser = Advertiser.objects.get(id=feed_provider.advertiser.id)
    except Advertiser.DoesNotExist:
        LOG.error("Feed provider advertiser error")
        return
    if advertiser:
        create_coupons(feed_provider)
        expire_coupons(feed_provider) 
    return 

def create_coupons(feed_provider):
    """ If no feed relationship exists for this coupon, create a live coupon for 
    this feed coupon.
    """
    LOG.debug('create_coupons') 
    feed_coupons = FeedCoupon.objects.filter(
        feed_provider=feed_provider, 
        feed_relationship__coupon=None).select_related(
        'feed_relationship__coupon')
    LOG.debug(feed_coupons)
    for feed_coupon in feed_coupons:
        LOG.debug('About to create this coupon') 
        LOG.debug(feed_coupon)
        create_this_coupon(feed_coupon)
    return

def create_this_coupon(feed_coupon):
    """ Create live coupon from this feed coupon. Create relationship with external 
    coupon and live coupon. 
    """
    business_name, slogan = split_string(feed_coupon.business_name, 50, 50)
    short_business_name, created =  split_string(business_name, 25, 1)      
    business, created = Business.objects.get_or_create(
        advertiser=feed_coupon.feed_provider.advertiser,
        business_name=business_name)
    if created:
        business.slogan = slogan
        business.short_business_name = short_business_name
        business.web_url = feed_coupon.business_url
        business.save()
        if business.web_url and settings.CELERY_ALWAYS_EAGER is False:
            take_web_snap.delay(business)
    LOG.debug(business)
    headline, qualifier = split_string(feed_coupon.offer, 25, 40)
    offer, created = Offer.objects.get_or_create(business=business, 
        headline=headline, qualifier=qualifier) 
    LOG.debug(offer)
    location, created = Location.objects.get_or_create(business=business, 
        location_address1=feed_coupon.address1,
        location_address2=feed_coupon.address2,
        location_city=feed_coupon.city,
        location_state_province=feed_coupon.state_province,
        location_zip_postal=feed_coupon.zip_postal)
    LOG.debug(location)
    coupon_type = CouponType.objects.get(coupon_type_name='MediaPartner')
    coupon, created = Coupon.objects.get_or_create(offer=offer, 
        coupon_type=coupon_type, precise_url=feed_coupon.coupon_url)
    if created:
        coupon.is_valid_monday = False 
        coupon.is_valid_tuesday = False 
        coupon.is_valid_wednesday = False 
        coupon.is_valid_thursday = False  
        coupon.is_valid_friday = False
        coupon.is_valid_saturday = False 
        coupon.is_valid_sunday = False 
        coupon.is_redeemed_by_sms = False
        coupon.location = [location]
        coupon.save() 
    LOG.debug(coupon)
    feed_relationship, created = FeedRelationship.objects.get_or_create(
        feed_provider=feed_coupon.feed_provider, feed_coupon=feed_coupon, 
        coupon=coupon)
    LOG.debug(feed_relationship)
    if created:
        LOG.debug('created')
    return 

def split_string(string1, string1_max_length, string2_max_length):
    """ Split this long string into 2 smaller strings. Here are the rules:
    1. string1 has complete words and is under string1_max_length characters
    2. string2 is truncated to string2_max_length characters
    """
    string2 = ""
    string1_under_limit = True
    if len(string1) > string1_max_length:
        text = string1
        string1 = ""
        for word in text.split():
            temp = word + " "
            if len(string1 + temp) > string1_max_length:
                string1_under_limit = False
                string2 += temp
            else:
                if string1_under_limit:
                    string1 += temp
    return string1.strip(), string2.strip()[:string2_max_length]

def expire_coupons(feed_provider): 
    """ Get most recent coupon_modified_date and compare to rest of coupons.
    Expire live coupons from website when:
    FeedRelationship exists and feed_coupon_modified_date < latest coupon 
    modified date.
    """
    LOG.debug('expire_coupons')
    today = datetime.date.today()
    try:
        feed_coupons = FeedCoupon.objects.filter(
            feed_provider=feed_provider,  
            expiration_date__gt=today).order_by('-modified_datetime')
    except FeedCoupon.DoesNotExist:
        return
    LOG.debug('feed_coupons')
    if feed_coupons:
        latest_feed_date = feed_coupons[0].modified_datetime.date()
        LOG.debug(latest_feed_date)
    else:
        return   
    try:
        feed_relationships = FeedRelationship.objects.filter(
            feed_coupon__feed_provider=feed_provider, 
            coupon__expiration_date__gt=today,
            feed_coupon__modified_datetime__lt=latest_feed_date).select_related(
            'coupon')
    except FeedRelationship.DoesNotExist:
        return 
    LOG.debug(feed_relationships)      
    for feed_relationship in feed_relationships:
        coupon = feed_relationship.coupon
        LOG.debug(coupon)
        coupon.expiration_date = datetime.date.today() + datetime.timedelta(
            days=-1)
        coupon.save()
    return

def scrape_incentrev_single_coupon(feed_provider, coupon_url, logo_url):
    """ Scrape incentrev single coupon details page. """
    page = get_web_page(coupon_url)
    soup = BeautifulSoup(page)
    title = soup.find('h2').text
    title_div = soup.find('h2').find('div').text
    if title_div:
        title = title.replace(title_div, '')
    LOG.debug('title = %s' % title)
    start_date = re.findall(re.compile('[0-9]{2}/[0-9]{2}/[0-9]{4}'), page)[0]
    external_id = (slugify(title) + start_date.replace('/', ''))[:50]
    LOG.debug('external_id = %s' % external_id)
    feed_coupon, created = FeedCoupon.objects.get_or_create(
        external_id=external_id, feed_provider=feed_provider)
    if created:
        LOG.debug('feed_coupon = %s' % feed_coupon)
    feed_coupon.coupon_url = coupon_url
    feed_coupon.logo_url = logo_url
    business_name = title.split('-')[0]
    offer = title.split('$')[1].replace('Value', '')
    #offer = re.findall(re.compile('^\$\d{1,3}(\.\d{2})?'), title)[0]
    feed_coupon.offer = '50% off $' + offer.strip()
    LOG.debug('offer = %s' % feed_coupon.offer)
    feed_coupon.business_name = business_name.split('-')[0].strip()
    LOG.debug('business_name = %s' % feed_coupon.business_name)
    # get business address
    feed_coupon.address1 = soup.find('div', 
        attrs={'class' : 'location_address'}).text
    city_state_zip_country = soup.find('div', 
        attrs={'class' : 'location_city_state_zip_country'}).text
    feed_coupon.city = city_state_zip_country.split(',')[0].strip()
    feed_coupon.state_province = re.findall(re.compile('[A-Z]{2}'), 
        city_state_zip_country)[0]
    try:
        feed_coupon.zip_postal = re.findall(re.compile('\d{5}'), 
            city_state_zip_country)[0]
    except IndexError:
        pass 
    # get business website
    for div in soup.findAll('div', attrs={'class' : 'location_url'}):
        if div.text == 'Click for Website':
            feed_coupon.business_url = div.a['href']
            break
    try:
        feed_coupon.save()
    except DatabaseError:
        LOG.error('Error with this coupon: %s' % coupon_url)
    return
