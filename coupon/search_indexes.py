""" Haystack search indexes for models of the coupon app. """

import datetime

from django.conf import settings
from django.db import IntegrityError, transaction

from haystack import indexes, site
from gargoyle import gargoyle

from coupon.models import Coupon, SlotTimeFrame

# Realtime search indexing thrashes for fixture resests during tests builds.
# Override it for *all* Jenkins builds, and (locally) any EnhancedTestCase).
INDEX_CLASS = indexes.RealTimeSearchIndex
if not settings.SEARCH_REALTIME:
    INDEX_CLASS = indexes.SearchIndex
try:
    # This will cause gargoyle to create the switch in an inactive state if it
    # does not already exist:
    if not gargoyle.is_active('real-time-search-index'):
        INDEX_CLASS = indexes.SearchIndex
except IntegrityError:
    # Gargoyle can fail to do an insert under test conditions, if the test loads
    # a fixture containing a switch. If that is the case; fall back to
    # SearchIndex.
    transaction.commit_unless_managed()
    INDEX_CLASS = indexes.SearchIndex


class CouponIndex(INDEX_CLASS):
    """ An index of coupons for solr searches, via haystack. """
    text = indexes.CharField(document=True, use_template=True)
    pub_date = indexes.DateTimeField(model_attr='start_date')
    site_id = indexes.IntegerField()
    categories = indexes.MultiValueField()
    suggestions = indexes.CharField()
    
    class Meta:
        app_label = 'coupon'

    def index_queryset(self):
        """ 
        Select QuerySet for use when the entire index for model is updated. 
        """
        return Coupon.objects.select_related('offer', 'offer__business', 
            'custom_restrictions', 'coupon_type').filter(
            expiration_date__gte=datetime.date.today()).exclude(
            coupon_type__coupon_type_name__in=('In Progress', 'Abandoned'))
            
    def prepare(self, obj):
        """ 
        Populate suggestions from text field.
        Suggestions will not be indexed, but used for spellcheck.
        """
        prepared_data = super(CouponIndex, self).prepare(obj)
        prepared_data['suggestions'] = prepared_data['text']
        return prepared_data
        
    @classmethod
    def prepare_categories(cls, obj): 
        """ Format categories m2m as MultiValueField. """
        return [category.id for category in obj.offer.business.categories.all()]

    @classmethod
    def prepare_site_id(cls, obj): 
        """ Format site_id to ensure this coupon has an active slot. """
        active_time_frame = \
            SlotTimeFrame.current_slot_time_frames.get_query_set().filter(
                coupon=obj)
        if active_time_frame:
            site_id = active_time_frame[0].slot.site.id
        else:
            site_id = None
        return site_id

site.register(Coupon, CouponIndex)
