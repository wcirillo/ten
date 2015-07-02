""" Signals for consumer app """
#pylint: disable=W0613
def on_change_email_subscription(sender, instance, **kwargs):
    """
    Receives signal that a Consumer's email subscription was changed and clears
    cache.
    """
    if kwargs.get('action') in ['post_add', 'post_clear', 'post_remove']:
        try:
            consumer = instance
            consumer.clear_cache()      
        except (AttributeError, KeyError):
            pass