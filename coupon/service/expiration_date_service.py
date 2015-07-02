"""  Service functions for changing the expiration date into different formats.
Also, this file holds the default expiration date function.
"""

import datetime

from common.utils import format_date_for_dsp

def default_expiration_date():
    """ Return the default expiration date. """
    return datetime.date.today() + datetime.timedelta(days=90)

def get_default_expiration_date():
    """ Return default_expiration_date in its most commonly used form: unicode,
    with the proper formatting. Note: *all* dates for display should do same.
    """
    return format_date_for_dsp(default_expiration_date())

def frmt_expiration_date_for_dsp(expiration_date):
    """ Return a given date formatted for display. """
    return format_date_for_dsp(expiration_date)

def frmt_expiration_date_for_db(expiration_date):
    """  Given a date that has been formatted for display by
    format_date_for_dsp, return it as a date type.
    """
    if type(expiration_date).__name__ == 'unicode':
        expiration_date = datetime.datetime.strptime(
                                str(expiration_date), "%m/%d/%y").date()
    return expiration_date

def get_non_expired_exp_date(expiration_date):
    """ Given an expiration_date of either type(unicode()) or type(date()),
    check if the expiration_date coming in is expired. If it is, bump the
    expiration_date to the default.
    
    This always will return in type(date()) format.
    """
    if type(expiration_date) == type(unicode()):
        #expiration_date passed in is as unicode format.
        #Check if the unicode expiration_date is less than the 
        #unicode format of todays date.
        if frmt_expiration_date_for_db(expiration_date) < datetime.date.today():
            # This coupon is expired... Bump the expiration_date up 
            # 90 days from today as a type(date()).
            expiration_date = default_expiration_date()
        else:
            #Change the unicode formated version of this expiration_date
            #to a type(date()) for the return.
            expiration_date = frmt_expiration_date_for_db(expiration_date)
    elif expiration_date < datetime.date.today():
        # This coupon is expired... Bump the expiration_date up 
        # 90 days from today.
        expiration_date = default_expiration_date()
    return expiration_date

def get_non_expired_exp_date_dsp(expiration_date):
    """ Given an expiration_date of either type(unicode()) or type(date()),
    check if it is expired. If it is, bump the expiration_date to the default.
    
    This always will return in type(unicode()) format.
    """
    return frmt_expiration_date_for_dsp(
        get_non_expired_exp_date(expiration_date))
