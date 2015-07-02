""" Celery tasks for coupon app.
Includes routines for creating and updating the js files to make
"coupon widgets" work.
"""
import datetime
import logging
import os

from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import IntegrityError, connection, transaction
from django.db.models import Count, Sum
from django.utils import simplejson

from celery.decorators import task
from celery.task import Task

from advertiser.models import Advertiser, Business
from common.utils import open_url
from coupon.models import (Coupon, CouponAction, Action, RankDateTime,
    SlotTimeFrame)
from coupon.service.coupons_service import ALL_COUPONS, SORT_COUPONS
from coupon.service.flyer_service import latest_flyer_datetime
from coupon.service.flyer_create_service import (create_flyer_this_site_phase1,
    create_flyers_this_site_phase2, min_days_past)
from coupon.service.twitter_service import TWITTER_SERVICE
from coupon.service.widget_service import check_widget_dir
from email_gateway.send import send_admin_email, send_email
from market.models import Site

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

@task()
def update_fb_share_coupons_all(max_coupons=None):
    """ For each coupon, increment Facebook share action.
    max_coupons will limit number of coupons to check Facebook shares.  
    """ 
    LOG.debug("update_facebook_share_coupons_all started")
    coupons = Coupon.current_coupons.distinct().exclude(
        offer__business__advertiser__site=1).order_by('-start_date')
    for coupon in coupons[:max_coupons]:
        update_facebook_share_coupon(coupon=coupon) 
    return

@task()
def update_facebook_share_coupon(coupon, test_mode=False):
    """ For this coupon, update Facebook share or like action to match Facebook
    graph data.
    """ 
    LOG.debug("update_facebook_share_coupon started")
    LOG.debug(coupon)
    
    site = coupon.offer.business.advertiser.site
    # Set the resolver to use the correct urlconf. This is used by 'reverse' and
    # 'render'.
    urlconf = 'urls_local.urls_%s' % site.id
    initial_urlconf = urlresolvers.get_urlconf()
    urlresolvers.set_urlconf(urlconf)
    
    coupon_url = settings.HTTP_PROTOCOL_HOST + reverse('view-single-coupon', 
        kwargs={'slug' : coupon.slug(), 'coupon_id' : coupon.id})
    # puts back original urlconf
    urlresolvers.set_urlconf(initial_urlconf)

    LOG.debug(coupon_url)
    json = open_url('https://graph.facebook.com/%s' % coupon_url)
    if json:
        fb_graph_dict = simplejson.loads(json)
    else:
        fb_graph_dict = {}
    fb_count = None
    try:
        fb_count = fb_graph_dict['shares']
    except KeyError:
        pass
    try:
        fb_count = fb_graph_dict['likes']
    except KeyError:
        pass
    if test_mode and not fb_count:
        fb_count = 5
    LOG.debug('fb_count = %s' % fb_count)
    if fb_count:
        action = Action.objects.get(id=7)
        coupon_action, created = CouponAction.objects.get_or_create(
            coupon=coupon, action=action)
        if created:
            LOG.debug("CouponAction created %s" % coupon_action)
        coupon_action.count = fb_count
        coupon_action.save()
        LOG.debug("facebook coupon id: %s count: %s" % (coupon.id, fb_count))
    return

@task()
def tweet_approved_coupon(coupon):
    """ Tweet this approved coupon to the Twitter account for the local site as
    a status update.
    """
    message = TWITTER_SERVICE.build_tweet_message(coupon=coupon, add_url=True)
    TWITTER_SERVICE.twitter_connect(coupon, message)
    return


class CreateWidget(Task):
    """ Create a 'widget' for displaying coupons on remote web sites. This is
    called as a task by the Coupon save() method, and is also called by
    create_widget_from_web view for generation while-you-wait.
    """
    def __init__(self):
        self.widget = {}
        self.site = None

    def set_coupons_for_site(self, site):
        """ Set mode an ordered_coupons when type_instance is a Site. """
        self.site = site
        self.widget['mode'] = 'markets', site.directory_name
        ordered_coupons = Coupon.current_coupons. \
            get_current_coupons_by_site(site).annotate(
                action_sum=Sum('coupon_actions__count')).order_by(
                '-start_date')
        if len(ordered_coupons):
            # Prefer coupons from distinct businesses.
            # A little wonky until django gets "DISTINCT ON", but avoids raw sql.
            _distinct_business_ids = []
            _sorted_coupon_ids = []
            while len(_sorted_coupon_ids) < 10:
                for coupon in ordered_coupons:
                    if coupon.offer.business.id not in _distinct_business_ids:
                        _distinct_business_ids.append(coupon.offer.business.id)
                        _sorted_coupon_ids.append(coupon.id)
                break
            if len(_sorted_coupon_ids) < 10:
                _sorted_coupon_ids += list(
                    ordered_coupons.exclude(
                        id__in=_sorted_coupon_ids
                    ).values_list(
                        'id', flat=True)[:10 - len(_sorted_coupon_ids)])
            LOG.debug('_sorted_coupon_ids: %s' % _sorted_coupon_ids)
            self.widget['ordered_coupons'] = SORT_COUPONS.sorted_coupons(
                coupon_ids=_sorted_coupon_ids, presorted=True)[1]
        else:
            self.widget['ordered_coupons'] = Coupon.objects.none()

    def render_widget(self, template=None):
        """
        Input: return_content is None or the name of a valid widget template.

        Output:
        """
        content = None
        self.widget['templates'] = os.listdir(self.widget['template_dir'])
        for template_file in self.widget['templates']:
            if '.js' in template_file:
                file_name = os.path.join(self.widget['template_dir'],
                    template_file)
                template_instance = open (file_name, 'r')
                template_ = template_instance.read()
                nearly_rendered_widget = template_.replace('___JSON_DATA___',
                    self.widget['coupon_content'])
                rendered_widget = nearly_rendered_widget.replace(
                    '___HTTP_STRING___', settings.STATIC_URL)
                if self.widget['dir']:
                    # Write file to disk.
                    file_name = os.path.join(self.widget['dir'], template_file)
                    os.umask(2)
                    f = open(file_name, 'w')
                    f.write(rendered_widget)
                    f.close()
                if template and template.lower() == template_file.lower():
                    content = rendered_widget
        if template and content:
            return content
        return None

    def run(self, type_instance, template=None):
        """ For instance of type type_instance, determine to which site the
          instance applies, and select the relevant coupons.
        Then create a json object out of all that data and uses it to write out
          widget files for the instance, 1 file for each widget size -- 1 for
          each template in our widgets template directory.
        Return the requested widget based on return_content. return_content
          defaults to none to allow for running all widgets as a job
          (see create_all_market widgets). Expects None or the name of a valid
          widget template. Ex. '10CouponsWidget160x600.js'
        """
        if isinstance(type_instance, Site):
            self.set_coupons_for_site(type_instance)
        elif isinstance(type_instance, Advertiser):
            advertiser = type_instance
            self.site = advertiser.site
            self.widget['mode'] = 'advertisers', advertiser.id
            self.widget['ordered_coupons'] = Coupon.current_coupons.filter(
                offer__business__advertiser=advertiser
                ).order_by('coupon_create_datetime')[:10]
            LOG.debug('adv')
        elif isinstance(type_instance, Business):
            business = type_instance
            self.site = business.advertiser.site
            self.widget['mode'] = 'businesses', business.id
            self.widget['ordered_coupons'] = Coupon.current_coupons.filter(
                offer__business=business
                ).order_by('coupon_create_datetime')[:10]
            LOG.debug('bus')
        else:
            return None
        # Make sure the proper widget dir exists
        self.widget['dir'] = check_widget_dir(self.widget['mode'][0],
            self.widget['mode'][1])
        LOG.debug(self.widget['ordered_coupons'])
        self.widget['coupon_content'] = simplejson.dumps({
            'site_name': self.site.name,
            'site_name_no_spaces': self.site.get_name_no_spaces(),
            'site_url': '%s/%s/' % (settings.HTTP_PROTOCOL_HOST,
                self.site.directory_name),
            'coupons' : [{
                'coupon_url': '%s/%s%s' % (settings.HTTP_PROTOCOL_HOST,
                    self.site.directory_name, reverse('view-single-coupon',
                    kwargs={
                        'slug':coupon.slug(),
                        'coupon_id':coupon.id
                    }
                )),
                'business_name':coupon.offer.business.business_name,
                'headline':coupon.offer.headline,
                'qualifier':coupon.offer.qualifier,
            } for coupon in self.widget['ordered_coupons']
        ]})

        self.widget['template_dir'] = os.path.join(
            settings.PROJECT_PATH, "templates", "widgets")

        return self.render_widget(template)


@task()
def update_widget(coupon):
    """ Update relevant widget(s) for a given coupon. """
    # First, update widget for the coupon's market, always.
    CreateWidget().run(coupon.get_site())
    
    # Then check to see if the business or advertiser has a widget, if so,
    # then recreate it to reflect the change that called me
    widget_attr = {'businesses': coupon.offer.business}
    widget_attr['advertisers'] = widget_attr['businesses'].advertiser
    for widget_type in widget_attr.iterkeys():
        if check_widget_dir(widget_type, widget_attr[widget_type].id, 
                create=False):
            # widget dir exists, so we'll update this one
            LOG.debug('updating %s widget for %s' % (widget_type, 
                    widget_attr[widget_type].id))
            CreateWidget().run(widget_attr[widget_type])

@task()
def create_all_widgets():
    """ Cycle through all sites and update their widgets. """
    for site in Site.objects.all():
        CreateWidget().run(site)


class RecordAction(Task):
    """ Task class for recording an action for a coupon. """

    @staticmethod
    @transaction.commit_on_success
    def do_raw_sql(action_id, coupon_id, consumer_id, subscriber_id):
        """ Perform raw sql then commit or rollback. """
        # This would be the ORM way, which takes 4 queries...
        #coupon_action, created = CouponAction.objects.get_or_create(
        #   action=action, coupon=coupon)
        #coupon_action.increment_count()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO "coupon_couponaction" ("action_id", "coupon_id",
                "count")
            SELECT %(action_id)s, "id", 0
            FROM "coupon_coupon"
            WHERE "id" = %(coupon_id)s
            AND "id" NOT IN (
                SELECT "coupon_id"
                FROM "coupon_couponaction"
                WHERE "action_id" = %(action_id)s
                AND "coupon_id" = %(coupon_id)s
                );

            UPDATE "coupon_couponaction"
            SET "count" = "count" + 1
            WHERE "action_id" = %(action_id)s
            AND "coupon_id" = %(coupon_id)s;""",
            {
                'action_id': action_id,
                'coupon_id': coupon_id,
            }
            )
        if consumer_id:
            cursor.execute("""
            INSERT INTO "coupon_consumeraction" (
                "action_id", "coupon_id", "consumer_id", "create_datetime")
            SELECT %(action_id)s, "id", %(consumer_id)s, now()
            FROM "coupon_coupon"
            WHERE "id" = %(coupon_id)s
            AND "id" NOT IN (
                SELECT "coupon_id"
                FROM "coupon_consumeraction"
                WHERE "action_id" = %(action_id)s
                AND "consumer_id" = %(consumer_id)s
                AND "coupon_id" = %(coupon_id)s
                );""",
            {
                'action_id': action_id,
                'coupon_id': coupon_id,
                'consumer_id': consumer_id,
            }
            )
        if subscriber_id:
            cursor.execute("""
            INSERT INTO "coupon_subscriberaction" (
                "action_id", "coupon_id", "subscriber_id", "create_datetime")
            SELECT %(action_id)s, "id", %(subscriber_id)s, now()
            FROM "coupon_coupon"
            WHERE "id" = %(coupon_id)s
            AND "id" NOT IN (
                SELECT "coupon_id"
                FROM "coupon_subscriberaction"
                WHERE "action_id" = %(action_id)s
                AND "subscriber_id" = %(subscriber_id)s
                AND "coupon_id" = %(coupon_id)s
                );""",
            {
                'action_id': action_id,
                'coupon_id': coupon_id,
                'subscriber_id': subscriber_id,
            }
            )
        try:
            transaction.commit()
        except IntegrityError:
            transaction.rollback()

    def run(self, action_id, coupon_id, consumer_id=None, subscriber_id=None):
        """
        Creates or increments a coupon action.
        If consumer, creates or increments a consumer action.
        If subscriber, creates or increments a subscriber action.
        """
        self.do_raw_sql(action_id, coupon_id, consumer_id, subscriber_id)
        if action_id in [3, 7]:
            rank_date_time, created = RankDateTime.objects.get_or_create(
                coupon_id=coupon_id)
            if not created:
                rank_date_time.save()
        return

@task(ignore_result=True)
def record_action_multiple_coupons(action_id, coupon_ids, consumer_id=None):
    """
    Creates or increments a coupon action for multiple coupons.
    If consumer, creates or increments a consumer action for multiple coupons.
    """ 
    if not len(coupon_ids):
        return
    cursor = connection.cursor()
    cursor.execute("""
        INSERT INTO "coupon_couponaction" ("action_id", "coupon_id", "count")
        SELECT %s, "id", 0
        FROM "coupon_coupon"
        WHERE "id" IN %s
        AND "id" NOT IN (
            SELECT "coupon_id" 
            FROM "coupon_couponaction"
            WHERE "action_id" = %s
            AND "coupon_id" IN %s
            );
        UPDATE "coupon_couponaction"
        SET "count" = "count"+ 1
        WHERE "action_id" = %s 
        AND "coupon_id" IN %s;""", 
        [action_id, coupon_ids, action_id, coupon_ids, action_id, coupon_ids]
        )
    if consumer_id:
        cursor.execute("""
        INSERT INTO "coupon_consumeraction" (
            "action_id", "coupon_id", "consumer_id", "create_datetime")
        SELECT %s, "id", %s, now() 
        FROM "coupon_coupon"
        WHERE "id" IN %s
        AND "id" NOT IN (
            SELECT "coupon_id" 
            FROM "coupon_consumeraction"
            WHERE "action_id" = %s
            AND "consumer_id" = %s
            AND "coupon_id" IN %s
            );""", 
        [action_id, consumer_id, coupon_ids, 
         action_id, consumer_id, coupon_ids]
        )
    try:
        transaction.commit_unless_managed()
    except IntegrityError:
        transaction.rollback()
    return


class ExtendCouponExpirationDateTask(Task):
    """ Extend the expiration date of coupons that are expiring tomorrow. """

    @staticmethod
    def run(days=90):
        """ Update coupons with an expiration date of tomorrow, extending it by
        n days.
        """
        coupons = Coupon.current_coupons.filter(
            expiration_date=datetime.date.today() + datetime.timedelta(1))
        LOG.debug('Expiring coupons: %s' % coupons)
        coupons.update(expiration_date=datetime.date.today() +
            datetime.timedelta(days))
        LOG.debug('Updated %s coupons' % coupons.count())

@task()
def expire_slot_time_frames():
    """ End time frames that are current for coupons that are expired. """
    now = datetime.datetime.now()
    expiring_time_frames = SlotTimeFrame.objects.filter(
            start_datetime__lt=now,
            end_datetime__gt=now,
            coupon__expiration_date__lt=now
        ) | SlotTimeFrame.objects.filter(
            start_datetime__lt=now,
            end_datetime=None,
            coupon__expiration_date__lt=now
        )
    for time_frame in expiring_time_frames:
        time_frame.end_datetime = now
        time_frame.save()
        LOG.info('Expired time frame %s' % time_frame)
    LOG.info('Expired %s time frames.' % expiring_time_frames.count())

@task()
def create_flyers_this_week(send_date=None, test_mode=False):
    """
    For each site having at least 1 consumer, determine if it gets a flyer this 
    week and, if so, the coupons that go in it.
    
    It is expected that flyers are created on the day they will be sent. For
    testing purposes, this function takes send_date. If send_date != today some
    logic is short circuited.
    
    send_date must be a Thursday.
    """
    LOG.info('create_flyers_this_week started')
    if not send_date:
        send_date = datetime.date.today()
        LOG.info('send_date: %s' % send_date)
    # send_date must be a Thursday.
    if send_date.isocalendar()[2] != 4:
        LOG.error("Flyers not created. Bad send date: %s" % send_date)
        raise ValidationError("Send date must be a Thursday.")
    # How many are paid, etc?
    admin_data = []
    national_coupons = ALL_COUPONS.get_national_coupons()
    LOG.debug('national_coupons: %s' % national_coupons)
    for site in Site.objects.filter(
                inactive_flag=False, launch_date__lt=datetime.date.today()
            ).annotate(num_consumers=Count('consumers')
            ).filter(num_consumers__gt=0
            ).exclude(id=1):
        LOG.info('create_flyers_this_week starting %s' % site)
        if latest_flyer_datetime(site) > min_days_past():
            LOG.debug('latest_flyer_datetime(site): %s' % 
                latest_flyer_datetime(site))
            LOG.debug('min_days_past(): %s' % min_days_past())
            continue
        if site.phase == 1:
            admin_data.extend(create_flyer_this_site_phase1(site, 
                send_date, national_coupons))
        elif site.phase == 2:
            admin_data.extend(create_flyers_this_site_phase2(site, 
                send_date, national_coupons))
        else:
            LOG.error('Site %s phase %s not supported.' % (site, site.phase))
    if not admin_data:
        admin_data.append("No flyers created in this run")
    if settings.DEBUG or test_mode:
        LOG.debug(admin_data)
    else:
        send_admin_email(context={'to_email': ['jprice@strausdigital.com',
                    'danielle@10coupons.com', 'sbywater@10coupons.com'], 
            'subject': 'Create Flyers output', 
            'admin_data': admin_data})
        
@task()
def send_coupon_published_email(coupon, just_created=True, test_mode=False):
    """ Sends an email to all staff when a coupon gets published either from 
    the advertiser account or from preview edit.
    """
    site = coupon.offer.business.advertiser.site
    if test_mode:
        to_email = [test_mode]
    else:
        to_email = settings.NOTIFY_EVERYONE
    if just_created:
        publish_type = 'created'
    else:
        publish_type = 'published'
    subject = '%s just %s a coupon on %s' % (
        coupon.offer.business.business_name,
        publish_type, 
        site.domain)
    LOG.debug("Sending coupon just published email to everyone.")
    send_email(template='admin_coupon_just_published', 
                site=site,
                context={
                    'to_email': to_email,
                    'subject': subject,
                    'coupon':coupon,
                    'show_unsubscribe': False}) 
