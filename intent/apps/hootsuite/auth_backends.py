from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User

class AuthenticationBackend(ModelBackend):
    
    def authenticate(self, **credentials):
        user = None

        app_username = self._make_username(credentials['hootsuite_uid'] if 'hootsuite_uid' in credentials else credentials['username'])

        # Check if the user exists, if not, create it.
        user, created = User.objects.get_or_create(username=app_username)

        return user

    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def _make_username(self, uid):
        return 'hs_%s' % uid