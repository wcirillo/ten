""" Celery tasks for coupon feeds of project ten. """
import logging
import os

from celery.task import Task

from django.conf import settings
from django.template import Context, Template
from django.utils.encoding import smart_str

from coupon.models import Coupon
from coupon.service.valid_days_service import VALID_DAYS

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class BaseCouponFeed(Task):
    """ Base class for coupon feeds. """
    template = None # Define this in subclass.
    file_name = None # Define this in subclass.
    ignore_result = True

    def generate_context(self):
        """ Define this in the subclass. """
        raise NotImplementedError

    def get_rendered_data(self):
        """ Return data as rendered template with given context. """
        f = open(self.template)
        template_contents = f.read()
        t = Template(template_contents)
        context = Context(self.generate_context())
        return smart_str(t.render(context))

    def write_file(self):
        """ Write xml data to disk for caching. """
        data = self.get_rendered_data()
        LOG.debug('Write: %s' % data)
        f = open(self.file_name, 'w')
        f.write(data)
        f.close()
        return data

    def read_file(self):
        """ Read cached feed xml data from disk. """
        if os.path.exists(self.file_name):
            f = open(self.file_name)
            data = f.read()
            LOG.debug('Read: %s' % data)
            f.close()
            return data

    def run(self, write=False):
        """ Run task to read/write coupon feed from/to disk. """
        LOG.debug('Running coupon feed')
        if write:
            return self.write_file()
        else:
            return self.read_file()


class ShoogerCouponFeed(BaseCouponFeed):
    """ Create coupon feed of all current coupons. Cache the data to disk. """
    template = (os.path.join(settings.PROJECT_PATH, 'templates') +
        '/xml/shooger.xml')
    file_name = os.path.join(settings.PROJECT_PATH,
        'media/dynamic/feed/shooger.xml')

    @staticmethod
    def shooger_category_dict():
        """ Map Shooger categories to 10coupons categories. """
        return {
            '1' : 'Office',
            '2' : 'Automotive',
            '3' : 'Restaurants & Bars',
            '4' : 'Health & Beauty',
            '5' : 'Shoes & Apparel',
            '6' : 'Food & Drink',
            '7' : 'Entertainment',
            '8' : 'Events',
            '15' : 'Home Improvement',
            '16' : 'Computers & Electronics',
            '17' : 'Legal',
            '18' : 'Flowers & Gifts',
            '19' : 'Services',
            '20' : 'Real Estate',
            '21' : 'Insurance & Banking',
            '22' : 'Dentists & Doctors',
            '23' : 'Pets',
            '24' : 'Babies & Kids',
            '25' : 'Furniture',
            '26' : 'Grocery',
            '27' : 'Home & Garden',
            '28' : 'Retail Goods & Stores',
            '29' : 'Sports & Recreation',
            '30' : 'Travel & Transportation',
            '32' : 'Eco-Friendly'
        }

    def generate_context(self):
        """ Create variables for template file. """
        coupons = Coupon.current_coupons.select_related(
                'offer', 'offer__business', 'offer__business__advertiser'
            ).filter(location__isnull=False).order_by('offer__business')
        valid_days_dict = {}
        for coupon in coupons:
            valid_days_dict[coupon.id] = VALID_DAYS.create_valid_days_string(
                coupon)
        return {'coupons': coupons,
            'shooger_category_dict': self.shooger_category_dict(),
            'valid_days_dict': valid_days_dict
            }


class GenericCouponFeed(BaseCouponFeed):
    """ Create a generic feed of current coupons with locations. """
    template = (os.path.join(settings.PROJECT_PATH, 'templates') +
        '/xml/generic_coupon_feed.xml')
    file_name = os.path.join(settings.PROJECT_PATH,
        'media/dynamic/feed/generic.xml')
    ignore_result = True

    def generate_context(self):
        """ Return a dictionary of data for the feed."""
        coupons = (Coupon.current_coupons
            .select_related('offer', 'offer__business',
                'offer__business__advertiser')
            .filter(location__isnull=False, is_redeemed_by_sms=True)
            .order_by('offer__business'))
        valid_days_dict = {}
        for coupon in coupons:
            valid_days_dict[coupon.id] = VALID_DAYS.create_valid_days_string(
                coupon)
        return {'coupons': coupons, 'valid_days_dict': valid_days_dict}
