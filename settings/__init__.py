""" Init for settings of project ten. """
import os
#pylint: disable=W0401,E0611,F0401
SERVER_EMAIL = 'django@%s.10coupons.com' % os.uname()[1]
try:
    if 'devweb' in os.uname()[1]:
        from settings.dev import *
    else:
        from settings.local import *
except ImportError:
    from settings.prod import *
    try:
        if 'hsdemo' in os.uname()[1]:
            from settings.hsdemo import *
    except ImportError:
        pass
