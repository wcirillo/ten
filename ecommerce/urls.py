""" Urls for ecommerce app. """

from django.conf.urls.defaults import patterns, url

from ecommerce.views.add_flyers_views import (show_add_flyer_by_list,
    show_add_flyer_by_map, show_add_flyer_dates, show_buy_market_flyer)
from ecommerce.views.ecommerce_views import show_receipt
from ecommerce.views.add_slot_views import show_add_a_new_display

urlpatterns = patterns('',
    url(r'^receipt/(?P<order_id>\d+)/$', show_receipt, name="receipt"),
    url(r'^add-flyer-by-map/(?P<slot_id>\d+)/$', show_add_flyer_by_map,
        name='add-flyer-by-map'),
    url(r'^add-flyer-by-list/(?P<slot_id>\d+)/$', show_add_flyer_by_list,
        name='add-flyer-by-list'),
    url(r'^buy-market-flyer/(?P<slot_id>\d+)/$', show_buy_market_flyer,
        name='buy-market-flyer'),
    url(r'^add-flyer-dates/(?P<slot_id>\d+)/$', show_add_flyer_dates,
        name='add-flyer-dates'),
    url(r'^add-a-display/(?P<coupon_id>\d+)/$', show_add_a_new_display,
        name="add-a-new-display"),
)
