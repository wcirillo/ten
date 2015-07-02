""" Utility functions for the email_gateway app. """
from datetime import datetime, timedelta

from advertiser.models import Business
from logger.service import get_last_db_log


def qry_inactive_email(end_date, advertiser_id=None, mod_filter=None, 
    perpetual=0):
    """ 
    Return most recent business belonging to this advertiser who has an expired
    slot and has been inactive for a period of time indicated by the end_date
    passed in and whether or not perpetual param is true. Must respect excluded 
    auth_groups and email subscriptions. 
    """
    return Business.objects.raw("""
    SELECT advertiser_business.* 
    FROM advertiser_business 
    INNER JOIN advertiser_advertiser ad
        ON advertiser_business.advertiser_id = ad.consumer_ptr_id
    INNER JOIN consumer_consumer_email_subscription con_sub_xref
                ON ad.consumer_ptr_id = con_sub_xref.consumer_id
    INNER JOIN consumer_emailsubscription sub
            ON con_sub_xref.emailsubscription_id = sub.id
            AND sub.email_subscription_name in ('Advertiser_Marketing')
    INNER JOIN (
        Select MAX(b0.id) id
        From advertiser_business b0
            Inner Join coupon_slot slot0
                On b0.id = slot0.business_id
                And(
                        (1 = %(perpetual)s and slot0.end_date 
                            <= cast(COALESCE(%(end_date)s, slot0.end_date) 
                            as date) )
                    Or  (0 = %(perpetual)s and slot0.end_date 
                            = cast(COALESCE(%(end_date)s, slot0.end_date) 
                            as date) )
                    )
        GROUP BY b0.advertiser_id
        ) expired
        ON advertiser_business.id = expired.id
    LEFT JOIN 
        (Select b1.id as business_id, consumer_ptr_id
         From advertiser_advertiser ad1
            Inner Join advertiser_business b1
                On b1.advertiser_id = ad1.consumer_ptr_id
            Inner Join coupon_slot slot1
                On b1.id = slot1.business_id
                And slot1.end_date > cast(COALESCE(%(end_date)s, '2008-01-01')
                    as date)
        )
        active_advertisers
         ON ad.consumer_ptr_id = active_advertisers.consumer_ptr_id
    LEFT JOIN auth_user_groups groups
                ON ad.consumer_ptr_id = groups.user_id
    LEFT JOIN auth_group
        ON groups.group_id = auth_group.id
            AND name in ('advertisers__do_not_market') 
    WHERE ad.consumer_ptr_id = COALESCE(%(advertiser_id)s, ad.consumer_ptr_id)
        And MOD(advertiser_business.id, 2) = COALESCE(%(mod_filter)s, 
            MOD(advertiser_business.id, 2))
        AND  groups IS NULL
        AND active_advertisers.business_id IS NULL""", 
        {'advertiser_id': advertiser_id, 'end_date': end_date, 
        'mod_filter': mod_filter, 'perpetual': perpetual})
    
def check_email_schedule(task_name, schedule, status=None, 
         test_mode=False, default_days=5):
    """ Check if this task is scheduled to run today (determine by checking 
    db_log for last log having task_name and status in the date dictionary 
    passed in). Returns last_run_date and run_state. Override date-test if 
    test_mode = True. Used by perpetual_abandoned_coupon and perpetual_inactive
    email tasks. Filter_strategy dictates what half the email audience will 
    receive the email for this run (odds or evens based on month and week).
    """
    last_run = datetime.now() - timedelta(days=default_days+1)
    last_entry = get_last_db_log(task_name, status)
    if last_entry:
        last_run = last_entry.execution_date_time
    is_scheduled = False
    odd_only = None
    if schedule:
        current_month = datetime.now().strftime('%B')
        this_schedule = schedule.get(current_month, None)
        if this_schedule:
            for key in this_schedule:
                if datetime.now().strftime('%Y%m%d') in this_schedule[key]:
                    week = int(key[-1:])
                    if (week % 2 == 0 and datetime.now().month % 2 == 0) \
                    or (week % 2 != 0 and datetime.now().month % 2 != 0):
                        odd_only = 0
                    else:
                        odd_only = 1
                    is_scheduled = True
                    break
    else:
        is_scheduled = True
    process_state = 'EMAIL'
    if (not is_scheduled or last_run.date() >= datetime.now().date()
    - timedelta(days=default_days)) and not test_mode:
        process_state = 'ABORT'
    elif test_mode:
        process_state = 'TESTMODE'
    return last_run, process_state, odd_only