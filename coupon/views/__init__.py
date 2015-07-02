""" Init for views of coupon app. """

from coupon.views.coupon_views import redirect_view_single_coupon, \
    redirect_show_all_offers, show_single_coupon, \
    show_all_coupons_this_business, print_single_coupon, \
    show_send_sms_single_coupon, send_sms_single_coupon, \
    external_click_coupon, flyer_click_coupon, flyer_click_show_single_coupon, \
    scan_coupon_qr_code, tweet_coupon, facebook_coupon, window_display, \
    show_email_coupon, show_all_coupons
from coupon.views.preview_edit_views import PreviewCoupon, show_edit_coupon
from coupon.views.restrictions_views import show_create_restrictions
from coupon.views.widget_views import create_widget_from_web

