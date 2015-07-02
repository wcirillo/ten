""" Service functions for dealing with the valid days string associated with
a coupon. """

import logging

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

class ValidDays(object):
    """ Class that helps deal with single coupon instances and things related to
    a single coupon.
    """

    @staticmethod
    def check_for_valid_days_changes(cleaned_data, coupon, this_coupon):
        """
        Check if the any valid days have been modified when returning back to any
        of the forms that hold the valid days checkboxes.  This process will 
        automatically update all fields in session and the database.
        """
        coupon.is_valid_monday = cleaned_data['is_valid_monday']
        coupon.is_valid_tuesday = cleaned_data['is_valid_tuesday']
        coupon.is_valid_wednesday = cleaned_data['is_valid_wednesday']
        coupon.is_valid_thursday = cleaned_data['is_valid_thursday']
        coupon.is_valid_friday = cleaned_data['is_valid_friday']
        coupon.is_valid_saturday = cleaned_data['is_valid_saturday']
        coupon.is_valid_sunday = cleaned_data['is_valid_sunday']
        this_coupon['is_valid_monday'] = cleaned_data['is_valid_monday']
        this_coupon['is_valid_tuesday'] = cleaned_data['is_valid_tuesday']
        this_coupon['is_valid_wednesday'] = cleaned_data['is_valid_wednesday']
        this_coupon['is_valid_thursday'] = cleaned_data['is_valid_thursday']
        this_coupon['is_valid_friday'] = cleaned_data['is_valid_friday']
        this_coupon['is_valid_saturday'] = cleaned_data['is_valid_saturday']
        this_coupon['is_valid_sunday'] = cleaned_data['is_valid_sunday']

    def create_valid_days_string(self, coupon):
        """
        This method builds the appropriate valid days string to be displayed
        on a coupon.  
        """
        valid_days = ''
        valid_days_count = 0
        valid_days_list = [coupon.is_valid_monday, coupon.is_valid_tuesday, 
            coupon.is_valid_wednesday, coupon.is_valid_thursday, 
            coupon.is_valid_friday, coupon.is_valid_saturday, 
            coupon.is_valid_sunday]
        for valid_day in valid_days_list:
            if valid_day is True:
                valid_days_count += 1
        if valid_days_count > 0:
            valid_days = self._build_valid_days_string(coupon, valid_days_count)
        return valid_days

    def _build_valid_days_string(self, coupon, valid_days_count):
        """ 
        Iterated over by create_valid_days_string in building the string used 
        for the display. 
        """
        valid_days_temp_count = valid_days_count
        if valid_days_count == 7:
            valid_days_string = 'Offer good 7 days a week.'
        elif valid_days_count == 6:
            if not coupon.is_valid_sunday:
                valid_days_string = 'Offer good Monday - Saturday only.'
            else:
                valid_days_string = self._offer_valid_6_days(coupon)
        elif valid_days_count == 5 and coupon.is_valid_saturday == False \
        and coupon.is_valid_sunday == False:
            valid_days_string = 'Offer good Monday - Friday only.' 
        elif valid_days_count == 4 and coupon.is_valid_friday == False \
        and coupon.is_valid_saturday == False and coupon.is_valid_sunday == False:
            valid_days_string = 'Offer good Monday - Thursday only.' 
        elif valid_days_count == 3 and coupon.is_valid_friday == True \
        and coupon.is_valid_saturday == True and coupon.is_valid_sunday == True:
            valid_days_string = 'Offer good Friday, Saturday and Sunday only.'  
        elif valid_days_count == 2 and coupon.is_valid_friday == True \
        and coupon.is_valid_saturday == True:
            valid_days_string = 'Offer good Friday and Saturday only.'  
        elif valid_days_count == 2 and coupon.is_valid_saturday == True \
        and coupon.is_valid_sunday == True:
            valid_days_string = 'Offer good Saturday and Sunday only.'
        else:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._offer_valid_1_day_only(coupon, valid_days_count, 
                                       valid_days_temp_count)
        return valid_days_string

    def _check_valid_day(self, day, valid_days_string, valid_days_count, 
            valid_days_temp_count):
        """
        This method keeps track of the valid_days_string count,
        valid_days_temp_count, and modifies the valid_days_string if any extra
        text needs to be added to the string based on the counts.
        """
        valid_days_string = valid_days_string + day
        valid_days_temp_count -= 1
        valid_days_string = self._add_to_string_based_on_count(valid_days_string, 
            valid_days_count, valid_days_temp_count)
        return valid_days_string, valid_days_count, valid_days_temp_count
    
    @staticmethod
    def _add_to_string_based_on_count(valid_days_string, valid_days_count, 
            valid_days_temp_count):
        """
        This method adds the appropriate extra text to the valid days string
        based on different counts at different times in the 
        create_valid_days_string process.
        """
        if valid_days_count != valid_days_temp_count:
            if valid_days_temp_count > 1 and valid_days_count != 6:
                valid_days_string += ', '
            elif valid_days_temp_count == 1:
                valid_days_string += ' and '
            else:
                valid_days_string += ' only.'
        return valid_days_string
    
    @staticmethod
    def _offer_valid_6_days(coupon):
        """ This offer is valid for 6 days.  Figure out what day is left out. """
        valid_days_string = 'Offer not valid '
        if not coupon.is_valid_monday:
            valid_days_string += 'Mondays.'
        if not coupon.is_valid_tuesday:
            valid_days_string += 'Tuesdays.'
        if not coupon.is_valid_wednesday:
            valid_days_string += 'Wednesdays.'
        if not coupon.is_valid_thursday:
            valid_days_string += 'Thursdays.'
        if not coupon.is_valid_friday:
            valid_days_string += 'Fridays.'
        if not coupon.is_valid_saturday:
            valid_days_string += 'Saturdays.'
        return valid_days_string

    def _offer_valid_1_day_only(self, coupon, valid_days_count, 
            valid_days_temp_count):
        """ This offer is only valid for 1 day. Figure out what day it is. """
        valid_days_string = 'Offer valid '
        if coupon.is_valid_monday:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._check_valid_day('Monday', valid_days_string, valid_days_count, 
                    valid_days_temp_count)
        if coupon.is_valid_tuesday:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._check_valid_day('Tuesday', valid_days_string, valid_days_count,
                    valid_days_temp_count)
        if coupon.is_valid_wednesday:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._check_valid_day('Wednesday', valid_days_string,
                    valid_days_count, valid_days_temp_count)
        if coupon.is_valid_thursday:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._check_valid_day('Thursday', valid_days_string, valid_days_count,
                    valid_days_temp_count)
        if coupon.is_valid_friday:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._check_valid_day('Friday', valid_days_string, valid_days_count, 
                    valid_days_temp_count)
        if coupon.is_valid_saturday:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._check_valid_day('Saturday', valid_days_string, valid_days_count, 
                    valid_days_temp_count)
        if coupon.is_valid_sunday:
            valid_days_string, valid_days_count, valid_days_temp_count = \
                self._check_valid_day('Sunday', valid_days_string, valid_days_count,
                    valid_days_temp_count)
        return valid_days_string, valid_days_count, valid_days_temp_count
    
VALID_DAYS = ValidDays()