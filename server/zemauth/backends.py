from django.forms import ValidationError
from django.contrib.auth import backends
from django.core.validators import validate_email

from utils.statsd_helper import statsd_incr

from zemauth import models


class EmailOrUsernameModelBackend(backends.ModelBackend):
    def authenticate(self, username=None, password=None):
        statsd_incr('signin_try')
        try:
            validate_email(username)
            kwargs = {'email': username}
        except ValidationError:
            kwargs = {'username': username}

        try:
            user = models.User.objects.get(**kwargs)
            if user.check_password(password):
                statsd_incr('signin_success')
                return user

            return None
        except models.User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            return None
