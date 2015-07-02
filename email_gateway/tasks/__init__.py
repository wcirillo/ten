""" Tasks for email_gateway app. """
# Things imported here are available for Celery scheduling.
from email_gateway.tasks.abandoned_coupon_follow_up import (
    AbandonedCouponEmailTask)
from email_gateway.tasks.ad_rep_mtg_reminder_email import (
    AdRepMtgReminderEmail)
from email_gateway.tasks.consumer_prospect_emails import (
    ConsumerProspectEmailTask)
from email_gateway.tasks.expiring_coupon import ExpiringCouponTask
from email_gateway.tasks.initial_inactive_emails import InitialInactiveEmail
from email_gateway.tasks.unqualified_consumer_emails import (
    UnqualifiedConsumerEmailTask)
from email_gateway.tasks.warm_lead_emails import WarmLeadEmailTask
