""" Urls specific to the create a coupon page flow. """
#pylint: disable=E1120
from django.conf.urls.defaults import patterns, url

from advertiser import views as advertiser_views
from advertiser.business.location import views as location_views
from coupon import views as coupon_views
from coupon.offer import views as offer_views
from ecommerce.views.add_slot_views import show_add_slot
from ecommerce.views.ecommerce_views import (CouponPurchase,
    show_coupon_purchase_success)

urlpatterns = patterns('',
    url(r'^$', advertiser_views.show_advertiser_registration, 
        name="advertiser-registration"),
    url(r'^offer/$', offer_views.show_create_offer, name='add-offer'),
    url(r'^add-location/$', location_views.show_create_location, 
        name="add-location"),
    url(r'^restrictions/$', coupon_views.show_create_restrictions, 
        name="create-restrictions"),
    url(r'^preview/$', coupon_views.PreviewCoupon.as_view(),
        name="preview-coupon"),
    url(r'^checkout/$', CouponPurchase.as_view(),
        name="checkout-coupon-purchase"),
    url(r'^checkout-success/$', show_coupon_purchase_success,
        name="coupon-purchased"),
    url(r'^add-web-display/$', show_add_slot, name="add-slot"),
)
