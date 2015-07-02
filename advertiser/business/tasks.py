""" Celery tasks for Business """
import logging
import os
from subprocess import call
from PIL import Image

from django.conf import settings
from django.utils.html import escape

from haystack.sites import site as haystack_site

from advertiser.business.config import BASE_SNAP_PATH
from celery.decorators import task
from common.utils import create_unique_datetime_str, parse_url_from_html
#from email_gateway.send import send_admin_email

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

@task(ignore_result=True)
def take_web_snap(business, base_snap_path=BASE_SNAP_PATH):
    """
    Grabs a snapshot of a businesses website via the 
    Business.web_url
    """
    LOG.debug('CELERY')
    old_snap_path = business.web_snap_path
    render_height = 665
    render_width = 1000
    file_format = 'png'  
    web_snap_path_name = '%s-%s-%s' % (str(business.slug()), str(business.id), 
        create_unique_datetime_str())
    web_snap_path = web_snap_path_name + '.' + file_format 
    web_snap_full_path = base_snap_path + web_snap_path
    business_web_url = parse_url_from_html(business.web_url)
    LOG.debug(business_web_url)
    try: # comment out enable-plugins if you get IOError on local  
        render_cmdline = "--load-error-handling ignore "
        if settings.ENVIRONMENT['environment'] != 'local':
            render_cmdline += "--enable-plugins " 
        render_cmdline += "--javascript-delay " + \
            "%d -f %s --crop-h %d --crop-w %d '%s' %s 2> /tmp/snapout.log" % (
            5000,
            'png',
            render_height,
            render_width,
            escape(business_web_url),
            web_snap_full_path,
            )
        LOG.debug(render_cmdline)
        x = call("/usr/local/bin/wkhtmltoimage %s" % render_cmdline, shell=True)
        LOG.debug("returned %s, trying to open %s" % (x, web_snap_full_path))
        try:
            image = Image.open(web_snap_full_path)
        except IOError:
            #context = {'to_email': ['vinny@10coupons.com', 'jeremy@10coupons.com'],
            #    'Subject': "Web_Snap Error for %s with url: %s" % (business.name, 
            #        business_web_url),
            #    'business': business,
            #    'admin_data': ['<a href="{% url admin:advertiser_business_change ' \
            #        'business.id %}">{{ business.business_name }}</a>']
            #    }
            #send_admin_email(context=context)
            raise
        size = (298, 198)
        image.thumbnail(size, Image.ANTIALIAS)
        image.save(web_snap_full_path, "png")
        if old_snap_path:
            try:
                # Delete the old file since the new one got saved.
                os.remove(base_snap_path + old_snap_path)
            except OSError:
                # File not Found.
                pass
        business.web_snap_path = web_snap_path
        business.save()
    except:
        raise

@task(ignore_result=True)
def index_all_business_coupons(business):
    """
    Index all of this businesses coupons.
    """
    index = None
    for offer in business.offers.all():
        if not index:
            index = haystack_site.get_index(offer.coupons.model)
        for coupon in offer.coupons.all():
            index.update_object(coupon)