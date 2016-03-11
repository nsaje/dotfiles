from django.conf import settings
from django.core.validators import validate_email
from django.contrib.auth import backends
from django.forms import ValidationError

import influx

from utils.statsd_helper import statsd_incr

from zemauth import models


class EmailOrUsernameModelBackend(backends.ModelBackend):
    def authenticate(self, username=None, password=None, oauth_data=None):
        statsd_incr('signin_try')
        influx.incr('signin_request', 1, stage='try')

        if oauth_data:
            kwargs = {'email__iexact': oauth_data['email']}
        else:
            try:
                validate_email(username)
                kwargs = {'email__iexact': username}
            except ValidationError:
                kwargs = {'username': username}

        try:
            user = models.User.objects.get(**kwargs)

            # maticz: Internal users in this context are users with @zemanta.com emails.
            # Checked and confirmed by product guys.
            if settings.GOOGLE_OAUTH_ENABLED and user.email.endswith('@zemanta.com'):
                if oauth_data and oauth_data['verified_email']:
                    statsd_incr('signin_success')
                    influx.incr('signin_request', 1, stage='success')
                    return user
                else:
                    return None
            elif user.check_password(password):
                statsd_incr('signin_success')
                influx.incr('signin_request', 1, stage='success')
                return user

            return None
        except models.User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            return None
