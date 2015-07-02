""" Service functions for dealing with twitter related coupon things. """

import twitter
import logging

from django.core.urlresolvers import reverse

from common.utils import shorten_url
from market.models import TwitterAccount

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class TwitterService(object):
    """ Class that helps deal with single coupon instances and things related to
    a single coupon.
    """

    @staticmethod
    def build_tweet_message(coupon, add_url=False):
        """ Create Tweet (Twitter Status) for this coupon. """
        site = coupon.get_site()
        try:
            twitter_account = TwitterAccount.objects.get(site=site)
            twitter_name = twitter_account.twitter_name
        except TwitterAccount.DoesNotExist:
            twitter_name = None
        qualifier = coupon.offer.qualifier
        # This change affects auto post status updates only:
        if add_url and len(qualifier) > 31: 
            qualifier = qualifier[:31] + '...'
        message = "%s %s - %s" % (coupon.offer.headline, qualifier, 
            coupon.offer.business.short_business_name)
        if twitter_name:
            message += " @%s." % twitter_name
        if add_url:
            message += " Go to: " 
            long_url = "http://%s%s" % (site.domain, reverse('view-single-coupon', 
                kwargs={'slug':coupon.slug(), 'coupon_id':coupon.id}))
            message += shorten_url(long_url)
        LOG.info('build tweet message = %s ' % message)
        return message
    
    @staticmethod
    def twitter_connect(coupon, message=None):
        """ Connect to Twitter then either update or return latest status. """
        site = coupon.get_site()
        LOG.info('twitter_connect')
        try:
            twitter_account = TwitterAccount.objects.get(site=site)
        except TwitterAccount.DoesNotExist:
            return 
        if twitter_account.consumer_key and \
            twitter_account.consumer_secret and \
            twitter_account.access_key and \
            twitter_account.access_secret and \
            twitter_account.consumer_key != '' and \
            twitter_account.consumer_secret != '' and \
            twitter_account.access_key != '' and \
            twitter_account.access_secret != '':
            try:
                api = twitter.Api(consumer_key = twitter_account.consumer_key,
                    consumer_secret = twitter_account.consumer_secret, 
                    access_token_key = twitter_account.access_key, 
                    access_token_secret = twitter_account.access_secret) 
                if message:
                    api.PostUpdate(message)
                    LOG.debug('Success: tweet coupon id: %s' % str(coupon.id))
                    return
                else:
                    LOG.debug('Returning status')
                    try:
                        statuses = api.GetUserTimeline(twitter_account.twitter_name)
                        status = str(statuses[0].text)
                    except ValueError:
                        status = None
                    return status
            except twitter.TwitterError:
                LOG.error('Twitter connect failed for this site: %s' % site)
        return
    
TWITTER_SERVICE = TwitterService()