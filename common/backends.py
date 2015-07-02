""" Custom backends for ten project. """

from django.contrib.auth.models import User
 
class EmailOrUsernameModelBackend(object):
    """ Allows user to authenticate with username or email address. """
    supports_anonymous_user = True # Django assumes True when not set.
    supports_object_permissions = False # Default django assumes when not set.
    @classmethod
    def authenticate(cls, username=None, password=None):
        """ Checks email or username. """
        if '@' in username:
            kwargs = {'email': username}
        else:
            kwargs = {'username': username}
        try:
            user = User.objects.get(**kwargs)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None
    
    @classmethod
    def get_user(cls, user_id):
        """ Get user object by id. """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None