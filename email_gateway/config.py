"""
Settings specific to the emaiL_gateway app.
"""

HELP_EMAIL_ADDRESS = 'help@10coupons.com'

DEFAULT_SUBJECT = 'A message from 10Coupons.com'

DEFAULT_BOUNCE_USER = 'bounce'

DEFAULT_BOUNCE_DOMAIN = 'bounces.10coupons.com'

DEFAULT_FROM_USER = 'Coupons'

DEFAULT_FROM_DOMAIN = '10Coupons.com'

DEFAULT_FROM_ADDRESS = 'Coupons@10Coupons.com'

LIST_UNSUB_PREFIX = 'list_unsubscribe'

ABANDONED_COUPON_SCHED_DICT = {
        'May': {
            'week_1':['20110517', '20110518'], 
            'week_2':['20110524', '20110525']},
        'June': {
            'week_1':['20110607', '20110608'], 
            'week_2':['20110621', '20110622']},
        'July': {
            'week_1':['20110712', '20110713'], 
            'week_2':['20110719', '20110720']},
        'August': {
            'week_1':['20110809', '20110810'], 
            'week_2':['20110816', '20110817']},
        'September': {
            'week_1':['20110913', '20110914'], 
            'week_2':['20110920', '20110921']},  
        'October': {
            'week_1':['20111004', '20111005'], 
            'week_2':['20111018', '20111019']}, 
        'November': {
            'week_1':['20111101', '20111102'], 
            'week_2':['20111115', '20111116']},
        'December': {
            'week_1':['20111206', '20111207'], 
            'week_2':['20111213', '20111214']},
        'January': { # Future days to silence unscheduled errors til restored.
            'week_1':['29991206', '29991207'], 
            'week_2':['29991213', '29991214']},
        'February': {
            'week_1':['20111206', '20111207'], 
            'week_2':['20111213', '20111214']},
        'March': {
            'week_1':['20110306', '20110307'], 
            'week_2':['20110313', '20110314']},
        'April': { 
            'week_1':['20110406', '20110407'], 
            'week_2':['20110413', '20110414']}}

PERPETUAL_INACTIVE_SCHED_DICT = ABANDONED_COUPON_SCHED_DICT