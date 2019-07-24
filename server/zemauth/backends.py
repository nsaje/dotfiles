from django.conf import settings
from django.contrib.auth import backends
from django.core.validators import validate_email
from django.forms import ValidationError
from oauth2_provider.oauth2_backends import get_oauthlib_core

from utils import metrics_compat
from zemauth import models

OAuthLibCore = get_oauthlib_core()


class EmailOrUsernameModelBackend(backends.ModelBackend):
    def authenticate(self, request, username=None, password=None, oauth_data=None):
        metrics_compat.incr("signin_request", 1, stage="try")

        if oauth_data:
            kwargs = {"email__iexact": oauth_data["email"]}
        else:
            try:
                validate_email(username)
                kwargs = {"email__iexact": username}
            except ValidationError:
                kwargs = {"username": username}

        try:
            user = models.User.objects.get(**kwargs)

            # maticz: Internal users in this context are users with @zemanta.com emails.
            # Checked and confirmed by product guys.
            if settings.GOOGLE_OAUTH_ENABLED and (
                user.email.endswith("@zemanta.com") or user.email.endswith("@outbrain.com")
            ):
                if oauth_data and oauth_data["verified_email"]:
                    metrics_compat.incr("signin_request", 1, stage="success")
                    return user
                else:
                    return None
            elif user.check_password(password):
                metrics_compat.incr("signin_request", 1, stage="success")
                return user

            return None
        except models.User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            return None
