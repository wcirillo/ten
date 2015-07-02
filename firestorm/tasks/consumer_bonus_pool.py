""" Classes of methods for managing the consumer bonus pool in firestorm app. """
from decimal import Decimal
import logging

from celery.task import Task
from django.db.models import Count, F

from firestorm.models import (AdRep, AdRepOrder, BonusPoolAllocation, 
    BonusPoolFlyer, BONUS_POOL_PERCENT, BONUS_POOL_MIN_SHARERS)
from firestorm.soap import FirestormSoap

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class AllocateBonusPool(Task):
    """ Create bonus pool allocations. """

    @staticmethod
    def get_qualified_ad_reps(ad_rep_order):
        """ Return the list of ad_reps who should receive an allocation. """
        qualified_ad_reps = []
        # If qualified, the ad_rep who made the sale should be the first member
        # of the list.
        if ad_rep_order.ad_rep.is_qualified():
            qualified_ad_reps.append(ad_rep_order.ad_rep)
        # Get other qualified ad_reps for this site.
        for ad_rep in (AdRep.objects
                .filter(site=ad_rep_order.ad_rep.site)
                .exclude(id=ad_rep_order.ad_rep.id)):
            if ad_rep.is_qualified():
                qualified_ad_reps.append(ad_rep)
        if len(qualified_ad_reps) < BONUS_POOL_MIN_SHARERS:
            # Assuming that if we get 50, at least 5 of them will be qualified.
            close_ad_reps = ad_rep_order.ad_rep.close_ad_reps(miles=2000,
                max_results=50)
            if not close_ad_reps:
                LOG.warning('No close ad reps.')
            LOG.debug('close_ad_reps: %s' % close_ad_reps)
            for ad_rep in close_ad_reps:
                if ad_rep not in qualified_ad_reps and ad_rep.is_qualified():
                    qualified_ad_reps.append(ad_rep)
                if len(qualified_ad_reps) == BONUS_POOL_MIN_SHARERS:
                    break
        LOG.debug('qualified_ad_reps: %s' % qualified_ad_reps)
        return qualified_ad_reps

    def run(self, ad_rep_order_id):
        """ Allocate a fixed percentage of the ad_rep_order.total toward the
        consumer bonus pool.

        Select the ad_rep_order.ad_rep and the four closest qualified ad_reps to
        him. Divvy up the allocation by their consumer bonus pool points.
        """
        if BonusPoolAllocation.objects.filter(ad_rep_order__id=ad_rep_order_id):
            LOG.error('This order has already been allocated.')
            return
        ad_rep_order = AdRepOrder.objects.get(id=ad_rep_order_id)
        total_allocation = round(
            ad_rep_order.order.total * BONUS_POOL_PERCENT / 100, 2)
        LOG.debug('total_allocation: %s' % total_allocation)
        if not total_allocation:
            LOG.debug('Nothing to allocate.')
            return
        qualified_ad_reps = self.get_qualified_ad_reps(ad_rep_order)
        total_consumer_points = 0
        consumer_points_list = []
        for ad_rep in qualified_ad_reps:
            this_ad_rep_points = ad_rep.qualified_consumer_points()
            total_consumer_points += this_ad_rep_points
            consumer_points_list.append(this_ad_rep_points)
        LOG.debug('total_consumer_points: %s' % total_consumer_points)
        if not total_consumer_points:
            LOG.warning('No consumer points for allocating %s.' % ad_rep_order)
            return
        allocation_per_point = total_allocation / total_consumer_points
        LOG.debug('allocation_per_point: %s' % allocation_per_point)
        # A running count of how much has been allocated so far.
        running_allocation = Decimal(0)
        # qualified_ad_rep[0] is treated differently: gets the remainder after
        # rounding.
        for counter, ad_rep in enumerate(qualified_ad_reps[1:]):
            allocation_this_ad_rep = Decimal(str(round(allocation_per_point *
                ad_rep.qualified_consumer_points(), 2)))
            LOG.debug('allocation_this_ad_rep: %s' % allocation_this_ad_rep)
            BonusPoolAllocation.objects.create(ad_rep=ad_rep,
                ad_rep_order=ad_rep_order, amount=allocation_this_ad_rep,
                consumer_points=consumer_points_list[counter + 1])
            running_allocation += allocation_this_ad_rep
        # Remainder after rounding goes to ad_rep_order.ad_rep.
        remainder = Decimal(str(total_allocation)) - running_allocation
        LOG.debug('remainder: %s' % remainder)
        BonusPoolAllocation.objects.create(ad_rep=qualified_ad_reps[0],
            ad_rep_order=ad_rep_order, amount=remainder,
            consumer_points=consumer_points_list[0])


class SaveFirestormOrder(Task):
    """ Pass ad rep orders to firestorm. """
    @staticmethod
    def run(ad_rep_order):
        """ For this ad rep order, save an external order to Firestorm and save 
        this firestorm order id to the ad_rep_order object.
        """
        firestorm_soap = FirestormSoap()
        firestorm_soap.save_order(ad_rep_order=ad_rep_order)


class UpdateConsumerBonusPool(Task):
    """ Task that updates the consumer bonus pool for each ad_rep with related 
    consumers.
    """
    @staticmethod
    def run(flyer_id, flyer_recipients):
        """ For this flyer to these recipients, update the consumer bonus pool
        for each ad_rep with related consumers.
        
        flyer_recipients = A list of consumer ids to whom this flyer was sent.
        """
        # Is this flyer already calculated?
        try:
            bonus_pool_flyer = BonusPoolFlyer.objects.get(flyer__id=flyer_id)
        except BonusPoolFlyer.DoesNotExist:
            bonus_pool_flyer = BonusPoolFlyer.objects.create(flyer_id=flyer_id)
        if bonus_pool_flyer.calculate_status == '2':
            LOG.error("Flyer %s already calculated for bonus pool." % flyer_id)
            return
        bonus_pool_flyer.calculate_status = '1'
        bonus_pool_flyer.save()
        for ad_rep in (AdRep.objects
                .filter(ad_rep_consumers__consumer__email__in=flyer_recipients)
                .annotate(consumer_count=Count('ad_rep_consumers'))):
            ad_rep.consumer_points = (
                F('consumer_points') + ad_rep.consumer_count)
            ad_rep.save()
        bonus_pool_flyer.calculate_status = '2'
        bonus_pool_flyer.save()

ALLOCATE_BONUS_POOL = AllocateBonusPool()
SAVE_FIRESTORM_ORDER = SaveFirestormOrder()
UPDATE_CONSUMER_BONUS_POOL = UpdateConsumerBonusPool()
