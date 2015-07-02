""" Tasks for firestorm app of project ten. """
from firestorm.tasks.ad_rep_compensation import AD_REP_COMPENSATION_TASK
from firestorm.tasks.create_or_update_ad_rep import CREATE_OR_UPDATE_AD_REP
from firestorm.tasks.consumer_bonus_pool import (ALLOCATE_BONUS_POOL,
    SAVE_FIRESTORM_ORDER, UPDATE_CONSUMER_BONUS_POOL)
from firestorm.tasks.email_tasks import (NOTIFY_NEW_RECRUIT, 
    SEND_ENROLLMENT_EMAIL, SEND_ENROLLMENT_NOTIFICATION)
from firestorm.tasks.ad_rep_invite import AD_REP_INVITE_TASK
from firestorm.tasks.ad_rep_lead_promo import AD_REP_LEAD_PROMO_TASK
