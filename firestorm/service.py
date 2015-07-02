""" Service functions for the firestorm app of project ten. """

from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import connection

from common.service.qr_image_cache import QRImageCache
from firestorm.models import AdRep
from market.service import strip_market_from_url


class NotAuthenticatedError(Exception):
    """ Authenticated session is required. """
    pass

def build_adv_url_with_ad_rep(advertiser, url_path, ad_rep_url=None):
    """ Build a URL for an advertiser that is associated with a AdRepAdvertiser
    (and rank is not CUSTOMER). Particularly useful for building the QR Code 
    paths. This function uses join-me url to load the ad_rep before launching 
    the destination path.
    """
    if not ad_rep_url:
        try:
            if advertiser.ad_rep_advertiser.ad_rep.rank != 'CUSTOMER':
                ad_rep_url = advertiser.ad_rep_advertiser.ad_rep.url
        except ObjectDoesNotExist:
            pass
    if ad_rep_url:
        return reverse('redirect-for-ad-rep', 
            kwargs={'redirect_string': "%s%s" %
                (strip_market_from_url(url_path), ad_rep_url)})
    else:
        return url_path

def get_ad_rep_qr_image_path(request, site_directory=None):
    """ Return ad rep's qr code image path (either ad rep url's QR Code or 
    10coupons.com domain default. """
    try:
        url = AdRep.objects.get(id=request.session['ad_rep_id']).url
    except (AdRep.DoesNotExist, KeyError):
        url = None
    return QRImageCache().get_ad_rep_qr_code(url, site_directory)

def get_consumer_bonus_pool():
    """ Return the total consumer bonus pool points for ad_reps having at least 
    10 verified consumers.
    """
    cursor = connection.cursor()
    cursor.execute("""
    SELECT COALESCE(SUM(consumer_points), 0)
    FROM firestorm_adrep
    WHERE consumer_ptr_id IN (
        SELECT fc.ad_rep_id
        FROM firestorm_adrepconsumer fc
        JOIN consumer_consumer c
            ON fc.consumer_id = c.user_ptr_id
        JOIN consumer_consumer_email_subscription es
            ON c.user_ptr_id = es.consumer_id
        JOIN auth_user u
            ON c.user_ptr_id = u.id
        WHERE es.emailsubscription_id = 1
        AND c.is_email_verified = true
        AND c.consumer_zip_postal > '0'
        AND c.user_ptr_id NOT IN (
            SELECT consumer_ptr_id
            FROM media_partner_mediapartner
            )
        AND NOT u.is_staff = true
        GROUP BY fc.ad_rep_id
        HAVING COUNT(fc.id) > 9
        )""")
    query = cursor.fetchall()
    return int(query[0][0])

def get_ad_rep_from_request(request):
    """ Return ad rep request's session if logged in. This function may return a
    a NotAuthenticatedError, KeyError or DoesNotExist error.
    """
    if not request.user.is_authenticated():
        raise NotAuthenticatedError()
    email = request.session['consumer']['email']
    return AdRep.objects.get(email=email)
