""" Celery task for recording ad rep compensation. """
from decimal import Decimal
import logging

from celery.task import Task

from firestorm.models import AdRepCompensation, AdRepOrder

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)


class AdRepCompensationTask(Task):
    """ Record ad rep compensation for an order.

    Compensation: The ad rep of an ad_rep_order receives a percent of the order:
        40% of the order -or- if the market of the order is in the 10k club,
        then 50%.
        If that amount is greater than $4 then the recruiter of the ad rep (if
        active) gets 25% of his recruit's compensation. If that amount is
        greater than $4 then the recruiter's recruiter (if active) gets 25% of
        that (and so on).
        We record compensations of less than $4, but when this happens we stop
        allocation further up the chain.
    """
    def recruiter_compensation(self, ad_rep_order_id, ad_rep, amount):
        """ Compute and record the compensation for the recruiter of this
        ad_rep.
        """
        if amount < 4:
            LOG.debug('Will not divide %s. Quitting' % amount)
            return
        recruiter = ad_rep.parent_ad_rep
        if not recruiter:
            LOG.debug('%s has no parent ad rep' % ad_rep)
            return
        if not recruiter.is_active or recruiter.rank == 'CUSTOMER':
            return
        amount *= .25
        rounded_amount = Decimal(str(round(amount, 2)))
        AdRepCompensation.objects.create(ad_rep_order_id=ad_rep_order_id,
            ad_rep=recruiter, child_ad_rep=ad_rep, amount=rounded_amount)
        LOG.debug('%s got %s thanks to %s' % (recruiter, rounded_amount,
            ad_rep))
        self.recruiter_compensation(ad_rep_order_id, recruiter, amount)

    def run(self, ad_rep_order_id):
        """ Compute and record ad_rep_compensation records for this
        ad_rep_order.
        """
        if AdRepCompensation.objects.filter(ad_rep_order__id=ad_rep_order_id):
            LOG.error('This order has already been allocated.')
            return
        ad_rep_order = AdRepOrder.objects.get(id=ad_rep_order_id)
        site = ad_rep_order.order.order_items.all()[0].site
        site_consumer_count = site.get_or_set_consumer_count()
        cut = .4
        if site_consumer_count > 10000:
            cut = .5
        amount = float(ad_rep_order.order.total) * cut
        rounded_amount = Decimal(str(round(amount, 2)))
        AdRepCompensation.objects.create(ad_rep_order=ad_rep_order,
            ad_rep=ad_rep_order.ad_rep, amount=rounded_amount)
        LOG.debug('%s got %s' % (ad_rep_order.ad_rep, rounded_amount))
        self.recruiter_compensation(ad_rep_order_id, ad_rep_order.ad_rep,
            amount)

AD_REP_COMPENSATION_TASK = AdRepCompensationTask()
