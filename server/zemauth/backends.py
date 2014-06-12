from django.conf import settings
from django.core.validators import validate_email
from django.contrib.auth import backends
from django.forms import ValidationError

from statsd.defaults.django import statsd

from zemauth import models


class EmailOrUsernameModelBackend(backends.ModelBackend):
    def authenticate(self, username=None, password=None, oauth_data=None):
        statsd.incr('one.login_try')

        if oauth_data:
            kwargs = {'email': oauth_data['email']}
        else:
            try:
                validate_email(username)
                kwargs = {'email': username}
            except ValidationError:
                kwargs = {'username': username}

        try:
            user = models.User.objects.get(**kwargs)

            if settings.GOOGLE_OAUTH_ENABLED:
                if oauth_data and oauth_data['verified_email']:
                    return user
                if user.is_staff:
                    return None

            if user.check_password(password):
                statsd.incr('one.login_success')
                return user

            return None
        except models.User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            return None
