""" Utils for watchdog app. """

from advertiser.models import Advertiser
from consumer.models import Consumer, BadUserPattern

def cleanup_test_users(consumers=False, patterns=None):
    """
    Grabs Bad users (test users and anything we've identified as bad/abusive
      mail patterns... *.ru is an example)  and deactivates, unsibscribes and
      perm-opts them out
    """
    if patterns == None or len(patterns) == 0:
        patterns = list(BadUserPattern.objects.all())
    
    for pattern in patterns:
        if consumers:
            badusertype = "consumers"
            bad_users = Consumer.objects.filter(email__contains=pattern,
                is_active=True)
        else:
            badusertype = "advertisers"
            bad_users = Advertiser.objects.filter(email__contains=pattern,
                is_active=True)
        print "I found %d active %s that match pattern '%s'" % \
            (bad_users.count(),badusertype, pattern)
        for bad_user in bad_users:
            bad_user.is_active = False
            bad_user.is_emailable = False
            bad_user.nomail_reason.add(6)
            bad_user.email_subscription = []
            bad_user.save()
            print "  Cleaning for user: %s" % bad_user

