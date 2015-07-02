""" Models for firestorm app of project ten. """
#pylint: disable=E1120, W0404, W0611
import datetime
import logging

from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MinValueValidator
from django.db import connection, transaction
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

from advertiser.models import Advertiser
from common.contest import select_eligible_consumers
from consumer.models import Consumer
from consumer.service import qry_verified_consumers
from ecommerce.models import Promoter, PromotionCode, Order

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

CALCULATE_CHOICES = (
       ('0', _('Not calculated')),
       ('1', _('Calculating...')),
       ('2', _('Calculated Successfully')),
   )

AD_REP_RANK_CHOICES = (
        ('CUSTOMER', _('Referring Consumer')),
        ('JRADREP', _('Junior Advertising Rep')),
        ('ADREP', _('Advertising Representative')),
        ('SRADREP', _('Senior Advertising Rep')),
        ('ADDIR', _('Advertising Director')),
        ('SRADDIR', _('Senior Advertising Director')),
        ('EXECADDIR', _('Executive Advertising Director')),
        ('NATADDIR', _('National Advertising Director')),
    )

# The percent on an order ascribed to the Consumer Bonus Pool.
BONUS_POOL_PERCENT = 10
# How many ad_reps will share the Consumer Bonus Pool portion of an order.
BONUS_POOL_MIN_SHARERS = 5


class AdRepManager(models.GeoManager):
    """ Manager class of AdRep, """

    def create_ad_rep_from_consumer(self, consumer_id, ad_rep_dict):
        """ Create an ad_rep for an existing consumer. """
        cursor = connection.cursor()
        # Django doesn't inform database about defaults, so we specify them.
        parent_ad_rep_id = None
        if ad_rep_dict.get('parent_ad_rep_id'):
            try:
                parent_ad_rep_id = AdRep.objects.get(id=ad_rep_dict.get(
                    'parent_ad_rep_id')).id
            except AdRep.DoesNotExist:
                pass
        cursor.execute("""
            INSERT INTO firestorm_adrep(consumer_ptr_id, url, parent_ad_rep_id,
                consumer_points, ad_rep_create_datetime,
                ad_rep_modified_datetime, is_fulfilled)
            VALUES (%s, %s, %s, 0, NOW(), NOW(), FALSE);""", [consumer_id,
                ad_rep_dict['url'], parent_ad_rep_id])
        transaction.commit_unless_managed()
        return self.get(id=consumer_id)

    def create_ad_rep_from_ad_rep_lead(self, consumer_id, ad_rep_dict):
        """ Convert ad ad_rep_lead into an ad_rep. """
        ad_rep = self.create_ad_rep_from_consumer(consumer_id, ad_rep_dict)
        # Remove adreplead email subscription when they become an ad rep.
        ad_rep.email_subscription.remove(5)
        cursor = connection.cursor()
        cursor.execute("""
            DELETE FROM firestorm_adreplead
            WHERE consumer_ptr_id = %s;""", [consumer_id])
        transaction.commit_unless_managed()
        return ad_rep

    def get_ad_rep_for_lead(self, site):
        """ Given a site, return the appropriate ad_rep to receive leads for it.

        This is used, for example, for leads that are ad_rep_leads, or for
        advertisers who bail out of the coupon create process.
        """
        ad_rep = None
        try:
            # Get the ad_rep related to the site through AdRepSite.
            ad_rep = self.get(ad_rep_sites__site=site)
        except AdRep.DoesNotExist:
            if site.default_state_province:
                # Get the first ad_rep on the site, if any.
                try:
                    ad_rep = AdRep.objects.filter(site=site).exclude(
                        rank='CUSTOMER').order_by('ad_rep_create_datetime')[0]
                except IndexError:
                    # Get the ad_rep for the US state.
                    ad_rep = self.get(
                        ad_rep_states__us_state=site.default_state_province)
        if ad_rep is None:
            raise AdRep.DoesNotExist
        return ad_rep


class AdRep(Consumer):
    """ An Advertising Representative enrolled in the Firestorm product. """
    parent_ad_rep = models.ForeignKey('self', null=True, blank=True,
        help_text=_("Who is the immediate upline of this person?"))
    firestorm_id = models.PositiveIntegerField(null=True, blank=True)
    url = models.CharField(unique=True, max_length=25, editable=False,
        help_text=_("The custom part of the rep's replicated website"))
    company = models.CharField(max_length=50, null=True, blank=True,
        editable=False)
    home_phone_number = models.CharField(max_length=20, null=True, 
        blank=True, editable=False)
    primary_phone_number = models.CharField(max_length=20, null=True, 
        blank=True, editable=False)
    fax_phone_number = models.CharField(max_length=20, null=True, blank=True,
        editable=False)
    cell_phone_number = models.CharField(max_length=20, null=True, blank=True,
        editable=False)
    consumer_points = models.PositiveIntegerField(default=0, editable=False,
        help_text=_("The accumulated points for the consumer bonus pool"))
    rank = models.CharField(max_length=20, null=True, blank=True,
        choices=AD_REP_RANK_CHOICES, editable=False)
    web_photo_path = models.CharField(max_length=100, null=True, blank=True)
    mailing_address1 = models.CharField(max_length=50, null=True, blank=True,
        editable=False)
    mailing_address2 = models.CharField(max_length=50, null=True, blank=True,
        editable=False)
    mailing_city = models.CharField(max_length=50, null=True, blank=True,
        editable=False)
    mailing_state_province = models.CharField(max_length=2, null=True,
        blank=True, editable=False)
    mailing_zip_postal = models.CharField('Zip/Postal', max_length=9,
        null=True, blank=True, editable=False)
    is_fulfilled = models.BooleanField('Is Fulfilled?',
        default=False, help_text=_("""Indicates if ad rep details have been
        sent to the external vendor for printing personalized office forms.
        """))
    us_zip = models.ForeignKey('geolocation.USZip', null=True,
        blank=True, editable=False)
    ad_rep_photo = models.ImageField(upload_to='dynamic/images/ad-rep',
        null=True, blank=True)
    ad_rep_create_datetime = models.DateTimeField('Create Date',
        auto_now_add=True)
    ad_rep_modified_datetime = models.DateTimeField('Modified Date',
        auto_now=True)
    objects = AdRepManager()

    class Meta:
        verbose_name = 'Ad Rep / Referring Consumer'
        verbose_name_plural = \
            'Advertising Representatives & Referring Consumers'

    def __unicode__(self):
        if self.first_name or self.last_name:
            return u'%s %s' % (self.first_name, self.last_name)
        else:
            return u'%s' % self.email
            
    def save(self, *args, **kwargs):
        """ If this AdRep has a rank that is not 'CUSTOMER', the lowest rank,
        delete them from AdRepConsumer.

        Business rule: an AdRep does not accumulate consumer bonus pool points
        for an ad_rep who is not a Referring Consumer.

        Since a generic content type cannot be used as a filter, we need a fk
        to a geolocation model for proximity matching.
        """
        if self.rank and self.rank != 'CUSTOMER':
            try:
                ad_rep_consumer = AdRepConsumer.objects.get(
                    consumer__email=self.email)
                ad_rep_consumer.delete()
            except AdRepConsumer.DoesNotExist:
                pass
        if not self.us_zip and self.geolocation_object:
            if self.geolocation_type.model == 'uszip':
                self.us_zip = self.geolocation_object
        super(AdRep, self).save(*args, **kwargs)

    def child_ad_reps(self):
        """ The ad_reps who list this ad rep as the parent. """
        return AdRep.objects.filter(parent_ad_rep__id=self.id)

    def has_child_ad_reps(self):
        """ Does this ad_rep have any child ad_reps? """
        return bool(self.child_ad_reps().count())

    def advertisers(self):
        """ The advertisers of this advertising representative. """
        return Advertiser.objects.filter(id__in=AdRepAdvertiser.objects.filter(
            ad_rep__id=self.id).values_list('advertiser_id', flat=True))

    def orders(self):
        """ The orders of this advertising representative. """
        return Order.objects.filter(id__in=AdRepOrder.objects.filter(
            ad_rep__id=self.id).values_list('order_id', flat=True))

    def annual_orders(self):
        """ The orders of this ad_rep that are for the annual product. """
        return self.orders().filter(order_items__product__id=3)

    def consumers(self):
        """ The consumers of this advertising representative. """
        return Consumer.objects.filter(id__in=AdRepConsumer.objects.filter(
            ad_rep__id=self.id).values_list('consumer_id', flat=True))

    def verified_consumers(self):
        """ Consumers of this ad rep that are verified (and opted in). """
        return self.consumers().filter(
            id__in=qry_verified_consumers().values_list('id', flat=True))

    def qualified_consumers(self):
        """ Consumers of this ad rep that are fully contest qualified. """
        return self.consumers().filter(
            id__in=select_eligible_consumers().values_list('id', flat=True))

    def is_qualified(self):
        """ Does this ad_rep have ten or more consumers? """
        return bool(self.consumers().count() > 9)

    def qualified_consumer_points(self):
        """ The consumer_points of this ad_rep if the ad_rep has at least 10
        qualified consumers, else 0.
        """
        points = 0
        if self.is_qualified():
            points = self.consumer_points
        return points

    def close_ad_reps(self, miles=1000, max_results=4):
        """  Return the n closest ad reps within x miles of this zip, excluding
        this site, ie: "get sites close to me."
        """
        ad_reps = None
        try:
            _coordinate = self.us_zip.coordinate
            _point = Point(_coordinate.longitude, _coordinate.latitude)
            ad_reps = AdRep.objects.filter(
                    us_zip__geom__distance_lte=(_point, D(mi=miles))
                ).exclude(id=self.id).distance(
                    _point, field_name='us_zip__geom'
                ).order_by('distance')[:max_results]
        except (AttributeError, ObjectDoesNotExist) as error:
            LOG.error('Cannot compute close ad reps: %s' % error)
        return ad_reps

    def parent_generations(self, upline_ad_rep, max_generations=0):
        """ Return the number of generations the upline_ad_rep is above this
        ad rep, checking a maximum of n generations. If n is 0, check all
        generations. If the upline_ad_rep is not found, return 0.
        """
        generations = 1
        ad_rep = self
        while ad_rep.parent_ad_rep and (
                not max_generations or generations < max_generations):
            if ad_rep.parent_ad_rep == upline_ad_rep:
                return generations
            generations += 1
            ad_rep = ad_rep.parent_ad_rep
        return 0

    def is_ad_rep_in_upline(self, upline_ad_rep, max_generations=0):
        """ Return True if upline_ad_rep is the parent (or grandparent, etc) of
        this ad rep, checking n generations. If n is 0, check all generations.
        """
        return bool(self.parent_generations(upline_ad_rep, max_generations))


class AdRepWebGreeting(models.Model):
    """ The web greeting, a free form text blob, of an ad rep, for display on
    the replicated website.
    """
    web_greeting = models.TextField(max_length=2500, null=True, blank=True)
    ad_rep = models.OneToOneField(AdRep, related_name='ad_rep_web_greeting')

    def __unicode__(self):
        return u'%s' % self.ad_rep


class AdRepConsumerManager(models.Manager):
    """ Model manager for AdRepConsumer. """

    def create_update_rep(self, request, consumer, ad_rep=None):
        """ Create an association between an ad rep and consumer. """
        ad_rep_id = request.session.get('ad_rep_id', None)
        if ad_rep_id or ad_rep:
            try:
                if ad_rep_id:
                    # Use the rep in session
                    ad_rep = AdRep.objects.get(id=ad_rep_id)
                try:
                    self.get(consumer=consumer)
                except ObjectDoesNotExist:
                    self.create(ad_rep=ad_rep, consumer=consumer)
            except AdRep.DoesNotExist:
                pass


class AdRepConsumer(models.Model):
    """ The relation of an AdRep to a Consumer. """
    ad_rep = models.ForeignKey(AdRep, related_name='ad_rep_consumers')
    consumer = models.OneToOneField('consumer.Consumer',
        related_name='ad_rep_consumer')
    objects = AdRepConsumerManager()

    class Meta:
        verbose_name = 'Ad Rep Consumer'
        verbose_name_plural = 'Ad Rep Consumers'

    def __unicode__(self):
        return u'%s, %s' % (self.ad_rep, self.consumer)


class AdRepAdvertiserManager(models.Manager):
    """ Model manager for AdRepAdvertiser. """

    def create_update_rep(self, request, advertiser, ad_rep=None):
        """ Create an association between an ad rep and an advertiser. """
        ad_rep_id = request.session.get('ad_rep_id', None)
        if ad_rep_id or ad_rep:
            # Use the rep in session first
            try:
                if ad_rep_id:
                    ad_rep = AdRep.objects.get(id=ad_rep_id)
                try:
                    # Update advertiser rep with rep in session.
                    ad_rep_advertiser = self.get(advertiser=advertiser)
                    ad_rep_advertiser.ad_rep = ad_rep
                    ad_rep_advertiser.save()
                except ObjectDoesNotExist:
                    # Create this advertiser rep with the rep in session.
                    self.create(ad_rep=ad_rep, advertiser=advertiser)
            except AdRep.DoesNotExist:
                pass
        else:
            # check if ad rep advertiser exists
            try:
                self.get(advertiser=advertiser)
            except ObjectDoesNotExist:
                # Check if this user has a Consumer Rep already and use that.
                try:
                    ad_rep_consumer = AdRepConsumer.objects.get(
                        consumer=advertiser.consumer)
                    ad_rep_consumer_id = ad_rep_consumer.ad_rep_id
                    self.create(ad_rep_id=ad_rep_consumer_id,
                        advertiser=advertiser)
                except AdRepConsumer.DoesNotExist:
                    pass
        AdRepConsumer.objects.create_update_rep(request=request,
            consumer=advertiser.consumer, ad_rep=ad_rep)


class AdRepAdvertiser(models.Model):
    """ The relation of an AdRep to an Advertiser. """
    ad_rep = models.ForeignKey(AdRep, related_name='ad_rep_advertisers')
    advertiser = models.OneToOneField('advertiser.Advertiser',
        related_name='ad_rep_advertiser')
    objects = AdRepAdvertiserManager()

    class Meta:
        verbose_name = 'Ad Rep Advertiser'
        verbose_name_plural = 'Ad Rep Advertisers'

    def __unicode__(self):
        return u'%s, %s' % (self.ad_rep, self.advertiser)


class AdRepOrderManager(models.Manager):
    """ Model manager for AdRepOrder. """

    def create_update_rep(self, request, order):
        """ Create an association between an ad rep and an order. """
        ad_rep = None
        ad_rep_id = request.session.get('ad_rep_id', None)
        if ad_rep_id:
            # Use the rep in session first
            try:
                ad_rep = AdRep.objects.get(id=ad_rep_id)
                try:
                    # Update order rep with rep in session.
                    self.get(order=order)
                except ObjectDoesNotExist:
                    # Create this order rep with the rep in session.
                    self.create(ad_rep=ad_rep, order=order)
            except AdRep.DoesNotExist:
                pass
        else:
            # Check if this user has a Advertiser Rep already and use that.
            try:
                ad_rep_advertiser = AdRepAdvertiser.objects.get(
                    advertiser=order.order_items.all()[0].business.advertiser)
                ad_rep_advertiser_id = ad_rep_advertiser.ad_rep_id
                self.create(ad_rep_id=ad_rep_advertiser_id, order=order)
            except AdRepAdvertiser.DoesNotExist:
                # Check if this user has a consumer rep and use that rep.
                try:
                    ad_rep_consumer = AdRepConsumer.objects.get(
                        consumer=order.order_items.all(
                            )[0].business.advertiser.consumer)
                    ad_rep_consumer_id = ad_rep_consumer.ad_rep_id
                    self.create(ad_rep_id=ad_rep_consumer_id, order=order)
                except AdRepConsumer.DoesNotExist:
                    pass
        # Now make sure the AdRepAdvertiser get created or update.
        # AdRepAdvertiser create_update_rep will ensure AdRepConsumer Exists
        # as well.
        AdRepAdvertiser.objects.create_update_rep(request=request,
            advertiser=order.order_items.all()[0].business.advertiser,
            ad_rep=ad_rep)


class AdRepOrder(models.Model):
    """ The relation of an AdRep to an Order. """
    ad_rep = models.ForeignKey(AdRep, related_name='ad_rep_orders')
    order = models.OneToOneField('ecommerce.Order',
        related_name='ad_rep_order')
    firestorm_order_id = models.IntegerField(blank=True, null=True)
    objects = AdRepOrderManager()

    class Meta:
        verbose_name = 'Ad Rep Order'
        verbose_name_plural = 'Ad Rep Orders'
    
    def __unicode__(self):
        return u'%s, %s' % (self.order, self.firestorm_order_id)

    def save(self, *args, **kwargs):
        if self.id:
            original = AdRepOrder.objects.get(id=self.id)
            if not original.ad_rep == self.ad_rep:
                raise ValidationError(
                    'AdRep of an AdRepOrder cannot be changed.')
        self.check_order_promotion()
        super(AdRepOrder, self).save(*args, **kwargs)

    def set_default_promotion(self):
        """ Set the promotion_code of this order to the "default" promotion_code
        of the promoter 'Firestorm Ad Reps'.
        """
        self.order.promotion_code = \
            PromotionCode.objects.get_by_natural_key('zero')
        self.order.clean()
        self.order.save()

    def check_order_promotion(self):
        """ An order related to an ad_rep needs to also be related to a
        promotion of the promoter 'Firestorm Ad Reps', so that we can report
        transactions net of commissions.
        """
        try:
            promoter = self.order.promotion_code.promotion.promoter
            if promoter == Promoter.objects.get_by_natural_key(
                    'Firestorm Ad Reps'):
                pass
            else:
                self.set_default_promotion()
        except AttributeError:
            self.set_default_promotion()


class BonusPoolAllocation(models.Model):
    """ Money ascribed to an ad_rep for a ad_rep_order through the consumer
    bonus pool program.

    Consumer bonus pool program: when a order that is an ad_rep_order has been
    paid, allocate 10% of the order.total to the 5 nearest ad_reps to the
    order.ad_rep_order.ad_rep.consumer_zip_postal.
    """
    ad_rep_order = models.ForeignKey(AdRepOrder,
        related_name='bonus_pool_allocations')
    ad_rep = models.ForeignKey(AdRep, related_name='bonus_pool_allocations')
    consumer_points = models.PositiveIntegerField(editable=False,
        validators=[MinValueValidator(1)],
        help_text=
            _("The consumer bonus pool point for this ad rep at the time of " +
            "this allocation."))
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], editable=False,
        help_text=
            _("The dollar amount allocated to this ad rep for this order"))
    create_datetime = models.DateTimeField('Create Date',
        default=datetime.datetime.now)

    class Meta:
        verbose_name = 'Bonus Pool Allocation'
        verbose_name_plural = 'Bonus Pool Allocations'

    def clean(self):
        other_allocations = self.ad_rep_order.bonus_pool_allocations
        if self.id:
            other_allocations.exclude(id=self.id)
        sum_others = other_allocations.aggregate(total=Sum('amount'))['total']
        if not sum_others:
            sum_others = 0
        LOG.debug('amount: %s' % self.amount)
        LOG.debug('sum others: %s' % sum_others)
        if (sum_others + self.amount >
                self.ad_rep_order.order.total * BONUS_POOL_PERCENT):
            raise ValidationError(
                "Allocations cannot exceed %s%% of the order total." %
                BONUS_POOL_PERCENT)

    def save(self, *args, **kwargs):
        self.clean()
        super(BonusPoolAllocation, self).save(*args, **kwargs)


def get_current_pay_period_dates():
    """ Return the start date and end date of the current pay period for ad
    reps.

    This is the most recent past Saturday until 1 week later.
    """
    normal_start_weekday = 5 # Saturday. (Monday = 0)
    today = datetime.datetime.today()
    days_ago = normal_start_weekday + today.weekday() - 3
    if days_ago > 6:
        days_ago -= 7
    past_saturday = today - datetime.timedelta(days=days_ago)
    next_friday = past_saturday + datetime.timedelta(6)
    return past_saturday, next_friday

def get_curr_pay_period_datetimes():
    """ Return current pay period as datetimes.
    """
    past_saturday, next_friday = get_current_pay_period_dates()
    last_second_of_friday = datetime.datetime.combine(next_friday,
        datetime.time(23, 59, 59))
    return (datetime.datetime.combine(past_saturday, datetime.time()),
        last_second_of_friday)


class CurrentPayPeriodManager(models.Manager):
    """ Filter AdRepCompensation queries to this pay period. """

    def get_query_set(self):
        """ Pay period is Saturday through Friday inclusive.
        """
        past_saturday, next_friday = get_current_pay_period_dates()
        return super(CurrentPayPeriodManager, self).get_query_set().filter(
                create_datetime__gt=past_saturday,
                create_datetime__lt=next_friday + datetime.timedelta(1)
            )


class AdRepCompensation(models.Model):
    """ Money ascribed to an ad_rep for an ad_rep_order through the
    compensation plan.
    """
    ad_rep_order = models.ForeignKey(AdRepOrder,
        related_name='ad_rep_compensations')
    ad_rep = models.ForeignKey(AdRep, related_name='ad_rep_compensations')
    child_ad_rep = models.ForeignKey(AdRep,
        related_name='parent_ad_rep_compensations', blank=True, null=True,
        help_text=
            _("The ad rep from whom this compensation flowed up."))
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0,
        validators=[MinValueValidator(0)], editable=False,
        help_text=
            _("The dollar amount allocated to this ad rep for this order"))
    create_datetime = models.DateTimeField('Create Date',
        default=datetime.datetime.now)
    objects = models.Manager()
    current_pay_period = CurrentPayPeriodManager()

    class Meta:
        verbose_name = 'Ad Rep Compensation'
        verbose_name_plural = 'Ad Rep Compensations'


class BonusPoolFlyer(models.Model):
    """ Has the consumer bonus pool already been incremented for ad reps having
    consumers who received this flyer?
    """
    flyer = models.OneToOneField('coupon.Flyer')
    calculate_status = models.CharField(max_length=1, default='0',
        choices=CALCULATE_CHOICES)


class AdRepLeadManager(models.Manager):
    """ Manager class of AdRepLead. """

    def create_ad_rep_lead_from_con(self, consumer_id, ad_rep_lead_dict):
        """ Create an ad_rep for an existing consumer. """
        ad_rep_lead = AdRepLead()
        ad_rep_lead.email = ad_rep_lead_dict['email']
        ad_rep_lead.clean()
        cursor = connection.cursor()
        # Django doesn't inform database about defaults, so we specify them.
        cursor.execute("""
            INSERT INTO firestorm_adreplead(consumer_ptr_id, 
            primary_phone_number, create_datetime, ad_rep_id, right_person_text, 
            is_commission_ok, sales_ability_rating)
            VALUES (%s, %s, %s, %s, %s, FALSE, 1);""", [consumer_id,
                ad_rep_lead_dict['primary_phone_number'], 
                datetime.datetime.now(),
                ad_rep_lead_dict.get('ad_rep_id', None), 
                ad_rep_lead_dict.get('right_person_text', '')]
            )
        transaction.commit_unless_managed()
        ad_rep_lead = self.get(id=consumer_id)
        if ad_rep_lead_dict.get('first_name', None) \
        or ad_rep_lead_dict.get('last_name', None):
            consumer = Consumer.objects.get(id=consumer_id)
            consumer.first_name = ad_rep_lead_dict.get('first_name', None)
            consumer.last_name = ad_rep_lead_dict.get('last_name', None)
            consumer.save()
        ad_rep_lead = self.get(id=consumer_id)
        # Make sure you now use model save.
        ad_rep_lead.save()
        return ad_rep_lead


class AdRepLead(Consumer):
    """ A person who has identified themselves as being interested in becoming
    an AdRep, but is not yet an AdRep.
    """
    ad_rep = models.ForeignKey(AdRep, related_name='ad_rep_leads', null=True,
        blank=True, help_text=_("The ad rep, if any, who referred this lead."))
    primary_phone_number = models.CharField(max_length=20, null=True,
        blank=True, editable=False)
    is_commission_ok = models.BooleanField(_("Is earning commission ok?"),
        default=False)
    sales_ability_rating = models.PositiveSmallIntegerField(default=1,
        help_text=_("""Poor 1-10 Excellent"""))
    right_person_text = models.TextField(
        max_length=2500, null=True, blank=True, help_text=_("""The user's
        explanation as to why they are the right person for this opportunity.
        """))
    create_datetime = models.DateTimeField('Create Date', auto_now_add=True)

    objects = AdRepLeadManager()

    class Meta:
        verbose_name = 'Ad Rep Lead'
        verbose_name_plural = 'Ad Rep Leads'

    def email_clean(self):
        """ An ad rep lead may not be an ad_rep. """
        try:
            AdRep.objects.get(email=self.email)
            raise ValidationError('AdRepLead may not be an AdRep.')
        except AdRep.DoesNotExist:
            pass

    def clean(self):
        self.email_clean()


class AdRepSite(models.Model):
    """ This ad_rep receives leads for this site. """
    ad_rep = models.ForeignKey(AdRep, related_name='ad_rep_sites',
        help_text=_("The ad rep who covers this site, for leads."))
    site = models.ForeignKey('market.Site',
        related_name='ad_rep_sites', unique=True)

    class Meta:
        verbose_name = 'Ad Rep Site'
        verbose_name_plural = 'Ad Rep Sites'

    def __unicode__(self):
        return u'%s, %s' % (self.ad_rep, self.site)


class AdRepUSState(models.Model):
    """ This ad_rep receives leads for this US State. """
    ad_rep = models.ForeignKey(AdRep, related_name='ad_rep_states',
        help_text=_("The ad rep who covers this state, for leads."))
    us_state = models.ForeignKey('geolocation.USState',
        related_name='ad_rep_states', unique=True)

    class Meta:
        verbose_name = 'Ad Rep US State'
        verbose_name_plural = 'Ad Rep US States'

    def __unicode__(self):
        return u'%s, %s' % (self.ad_rep, self.us_state)

# Signals for firestorm models:
from firestorm.signals import (send_enrollment_email_callback,
    ad_rep_order_callback)
