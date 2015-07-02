"""
Settings specific to the sms_gateway app.
"""

TEST_MODE = False

# This determines how much logging pycurl will do.
# It is passed into pycurl so must mimic pycurl VERBOSE allowed values.
SMS_CURL_VERBOSITY = 0

# What type of reports do we want back from EzTexting?
SMS_REPORT_TYPE = 7

SMS_SHORT_CODE = '71010'

SMS_SEND_URL = 'https://sms.mxtelecom.com/SMSSend' 
               #'https://api.eztexting.com/SMSSend'

# These are all for carrier lookup API:
SMS_LOOKUP_URL =  'https://app.eztexting.com/api/lookup'
SMS_LOOKUP_USER = '10CouponsLU'
SMS_LOOKUP_PASSWORD = '2Ogl4rqhmGmma1j9VT3f'

# These IPs are allowed to send SMS receive reports:
SMS_ALLOWED_IPS = [
    '209.160.22.126',
    '83.166.68.83',
    '74.84.136.104', 
    '74.84.136.101',
    # Internal IPs that happen during testing:
    '127.0.0.1',
    '192.168.88.61', 
    '192.168.88.105',
    '192.168.88.106',
    '192.168.88.107',
    # External IPs of office:
    '173.220.217.194',
    '173.220.217.195',
    '173.220.217.196',
    '173.220.217.197',
    '173.220.217.198'
    ]

# EXTexting also has a block:
for n in range(1, 24):
    SMS_ALLOWED_IPS.append('83.166.68.%s' % n)
