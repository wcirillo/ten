""" Slot models of the coupon app """

import datetime
from dateutil import relativedelta
import logging

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from coupon.models.coupon_models import Coupon

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class SlotManager(models.Manager):
    """ A manager for slots. Doesn't have to be current slots. """
    def get_all_business_slots(self, business_id):
        """ Get all slots old and new for this business_id  """
        return self.filter(business__id=business_id)


class CurrentSlotManager(SlotManager):
    """ A manager that filters current slots. """
    def get_query_set(self):
        today = datetime.date.today()
        return super(CurrentSlotManager, self).get_query_set().filter(
            end_date__gte=today, start_date__lte=today)

    def get_current_business_slots(self, business_id):
        """ Get all currently running slots for this business_id  """
        return self.get_all_business_slots(business_id
            ).order_by('parent_slot', 'id')

    def get_current_family_slots(self, business_id):
        """ For this business, return a list of current parent slots and a list
        of current children slots. """
        current_parent_slots = []
        current_children_slots = []
        for slot in self.get_current_business_slots(business_id):
            if slot == slot.parent_slot:
                current_parent_slots.append(slot)
            else:
                current_children_slots.append(slot)
        return current_parent_slots, current_children_slots


class Slot(models.Model):
    """ The website placement container for the business of an advertiser. """
    site = models.ForeignKey('market.Site', related_name='slots')
    business = models.ForeignKey('advertiser.Business', related_name='slots')
    renewal_rate = models.DecimalField(max_digits=8, decimal_places=2, 
        null=True, blank=True, default=10)
    is_autorenew = models.BooleanField('Is Autorenewing?', default=False)
    start_date = models.DateField('Start Date', default=datetime.date.today,
        db_index=True)
    end_date = models.DateField('End Date', db_index=True, 
        help_text=_("Date this slot is paid until."))
    parent_slot = models.ForeignKey('self', related_name='child_slots',
        null=True, blank=True, default=None)
    objects = SlotManager()
    current_slots = CurrentSlotManager()
    
    class Meta:
        app_label = 'coupon'

    def __unicode__(self):
        cache_key = "site-%s" % self.site_id
        # This will work for browsing admin, but not for shell.
        site = cache.get(cache_key)
        if not site:
            site = self.site
        return u'Slot %s on %s' % (self.id, site.name)
    
    def clean(self):
        if self.id and bool(self.flyer_placements.count()) \
        and self.site_id != Slot.objects.get(id=self.id).site_id:
            raise ValidationError(
                _("Cannot change the site of a slot with flyer placements."))
        if self.site_id == 1:
            raise ValidationError(_("No slots for site 1."))
        if not self.end_date:
            raise ValidationError(_("End date is required."))
        if self.start_date > self.end_date:
            raise ValidationError(
                _("You can't end a slot before it starts."))
        if self.start_date == self.end_date:
            raise ValidationError(_("Start and end dates can't be equal."))
        start_datetime = datetime.datetime.combine(self.start_date, 
            datetime.time())
        end_datetime = datetime.datetime.combine(self.end_date, 
            datetime.time())
        for slot_time_frame in self.slot_time_frames.all():
            if slot_time_frame.start_datetime < start_datetime:
                raise ValidationError(
                    _("A slot cannot begin after a related slot time frame."))
            if slot_time_frame.end_datetime \
            and slot_time_frame.end_datetime > end_datetime:
                raise ValidationError(
                    _("A slot cannot end after the slot time frame ends."))
    
    def save(self, no_recurse=False, *args, **kwargs):
        """ Save the slot.
        If the end_date is changing and this is a parent, also update the
        end_date of the child slots.
        If this slot does not have a parent, make it a parent.
        """
        LOG.debug('In save of slot %s' % self)
        LOG.debug(self.__dict__)
        self.clean()
        if self.id and self.parent_slot and self.id == self.parent_slot.id:
            original = Slot.objects.get(id=self.id)
            if original.end_date != self.end_date:
                for child_slot in self.child_slots.exclude(id=self.id):
                    child_slot.end_date = self.end_date
                    child_slot.save()
        super(Slot, self).save(*args, **kwargs)
        if not self.parent_slot and not no_recurse:
            # Now that we have an id, we can be a parent.
            self.parent_slot_id = self.id
            self.save(no_recurse=True)
        return self

    def calculate_next_end_date(self):
        """ Given a slot, calculate the next end date. 
        
        Slots that begin on the 31st of a month should renew on the 31st of 
        months that have one, or the 30th of months that have one, or the 29th, 
        or the 
        38th.
        
        If a slot begins 2000-01-31, it will renew on:
            2000-02-28
            2000-03-31
            2000-04-30.
        """
        # relativedelta() produces a datetime. Can't compare a datetime to date.
        start_date = datetime.datetime.combine(self.start_date, datetime.time())
        end_date = datetime.datetime.combine(self.end_date, datetime.time())
        current_end_date = end_date
        months = 1
        while current_end_date >= end_date:
            LOG.debug('end date so far... %s' % end_date)
            end_date =  start_date + relativedelta.relativedelta(months=months)
            months += 1
        return datetime.date(end_date.year, end_date.month, end_date.day)
    
    def has_active_time_frame(self):
        """ Check if this Slot has an active slot_time_frame. """
        return bool(
            SlotTimeFrame.current_slot_time_frames.filter(slot=self).count())

    def get_active_coupon(self):
        """ Return the current coupon for this slot, or None. """
        try:
            coupon = Coupon.current_coupons.get(
                slot_time_frames__in=
                    SlotTimeFrame.current_slot_time_frames.filter(
                        slot__id=self.id))
        except Coupon.DoesNotExist:
            coupon = None
        return coupon


class CurrentSlotTimeFrameManager(models.Manager):
    """ A manager that filters current time frames of current slots. """
    def get_query_set(self):
        now = datetime.datetime.now()
        today = datetime.date.today()
        return super(CurrentSlotTimeFrameManager, self).get_query_set().filter(
            Q(end_datetime__gt=now) | Q(end_datetime=None),
            start_datetime__lt=now, slot__start_date__lte=today,
            slot__end_date__gte=today).defer('slot__site__envelope')


class SlotTimeFrame(models.Model):
    """ The coupon related to a slot for a time frame. """
    slot = models.ForeignKey(Slot, related_name='slot_time_frames')
    coupon = models.ForeignKey(Coupon, related_name='slot_time_frames')
    start_datetime = models.DateTimeField('Start Date/Time', 
        default=datetime.datetime.now, db_index=True,
        help_text=_("The date/time the coupon will begin to occupy this slot."))
    end_datetime = models.DateTimeField('End Date/Time', blank=True, null=True, 
        db_index=True, 
        help_text=_("The date/time this coupon will end occupying this slot."))
    objects = models.Manager()
    current_slot_time_frames = CurrentSlotTimeFrameManager()
    
    class Meta:
        app_label = 'coupon'

    def __unicode__(self):
        return u'%s for %s' % (self.id, self.slot)
    
    def save(self, *args, **kwargs):
        """ If this time frame begins now, set end date of any previous time 
        frame having a null end date to now. By rule, there can only be one 
        open-ended time frame per slot.
        """
        LOG.debug('In save of slot time frame %s' % self)
        self.clean()
        LOG.debug('Passed cleaning.')
        try:
            other_time_frame = self.slot.slot_time_frames.filter(
                end_datetime=None).exclude(id=self.id)[0]
            LOG.debug('Found open ended time frame %s' % other_time_frame)
            self, other_time_frame = self.justify_time_frames(other_time_frame)
            if other_time_frame.end_datetime != None:
                other_time_frame.save()
        except IndexError:
            pass
        super(SlotTimeFrame, self).save(*args, **kwargs)
        LOG.debug('Saved slot time frame %s, %s to %s' % (self.id, 
            self.start_datetime, self.end_datetime))
        self.coupon.update_index()
        return self

    def clean(self):
        if self.start_datetime < datetime.datetime.combine(self.slot.start_date, 
                datetime.time()):
            raise ValidationError(
                _("A slot time frame cannot begin before the slot."))
        if self.end_datetime:
            if self.start_datetime > self.end_datetime:
                raise ValidationError(
                    _("You cannot end a time frame before it starts."))
            if self.start_datetime == self.end_datetime:
                raise ValidationError(_("Start and end dates can't be equal.")) 
        self.compare_time_frames()

    def compare_time_frames(self):
        """ Compare the time frames of a slot and check against business rules. 
        
        Rules:
        - Cannot have more than one time frame covering any period.
        - This time frame can be open-ended, if it closes the previous 
        open-ended time frame (in save method).
        - If there is a open-ended time frame that starts in the future, this 
        one cannot be open_ended, and will end when that one starts.
        """
        slot_time_frames = self.slot.slot_time_frames.exclude(
            id=self.id).order_by('id')
        for slot_time_frame in slot_time_frames:
            LOG.debug('slot_time_frame.id: %s' % (slot_time_frame.id)) 
            LOG.debug('started with %s to %s' % (slot_time_frame.start_datetime, 
                slot_time_frame.end_datetime)) 
            if not slot_time_frame.end_datetime:
                self, slot_time_frame = self.justify_time_frames(
                    slot_time_frame)
                LOG.debug('justified to %s to %s' % 
                    (slot_time_frame.start_datetime, 
                    slot_time_frame.end_datetime))
            start_datetime = slot_time_frame.start_datetime
            end_datetime = slot_time_frame.end_datetime
            if not end_datetime:
                # Pretend it's a far away date so date comparisons can work.
                now = datetime.datetime.now()
                end_datetime = now + datetime.timedelta(days=1000)
            if self.start_datetime == start_datetime:
                raise ValidationError(_(
                    "Time frames of a slot cannot begin at same time."))
            if self.end_datetime == end_datetime:
                LOG.debug('Problem end_datetime %s' % self.end_datetime)
                raise ValidationError(_(
                    "Time frames of a slot cannot end at same time."))
            if self.start_datetime > start_datetime \
            and self.start_datetime < end_datetime:
                raise ValidationError(_("""This time frame cannot be included in
                    another time frame."""))
            if self.end_datetime:
                if self.start_datetime < start_datetime \
                and self.end_datetime > end_datetime:
                    raise ValidationError(_(
                        "This time frame cannot include another time frame."))
                if self.start_datetime < start_datetime \
                and self.end_datetime > start_datetime:
                    raise ValidationError(_(
                        "This time frame cannot overlap another time frame."))
    
    def justify_time_frames(self, time_frame_y):
        """ Given two time frames, expecting at least one of them to be
        open-ended, adjust them so they do not break business rules.
        """
        now = datetime.datetime.now()
        if not (self.end_datetime \
                and self.end_datetime < time_frame_y.start_datetime):
            if not time_frame_y.end_datetime:
                if time_frame_y.start_datetime < now:
                    time_frame_y.end_datetime = now
                    if time_frame_y.end_datetime > self.start_datetime:
                        time_frame_y.end_datetime = self.start_datetime
                else:
                    if self.start_datetime > time_frame_y.start_datetime:
                        time_frame_y.end_datetime = self.start_datetime
                    else:
                        self.end_datetime = time_frame_y.start_datetime
        return self, time_frame_y
    
    def close_this_frame_now(self):
        """ Close this time frame, for example when a coupon is no longer
        associated with this slot.
        """
        self.end_datetime = datetime.datetime.now()
        self.save()
        return self
