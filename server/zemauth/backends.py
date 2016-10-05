from django.conf import settings
from django.core.validators import validate_email
from django.contrib.auth import backends
from django.forms import ValidationError
from oauth2_provider.backends import OAuth2Backend
from oauth2_provider.oauth2_backends import get_oauthlib_core

import influx


from zemauth import models

OAuthLibCore = get_oauthlib_core()


class EmailOrUsernameModelBackend(backends.ModelBackend):
    def authenticate(self, username=None, password=None, oauth_data=None):
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
                    influx.incr('signin_request', 1, stage='success')
                    return user
                else:
                    return None
            elif user.check_password(password):
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


class OAuth2ZemauthBackend(OAuth2Backend):
    """
    Authenticate against an OAuth2 access token

    Zemauth addition: use the application's user if no user is associated directly with the token.

    Explanation: It's an Oauth2 thing, which is most commonly used in a 'three-legged' way,
    which means a 'provider' authorises an 'application' to perform some action on behalf of a 'user'.
    This is used in a case where one application performs actions on behalf of many different users,
    such as a mobile app posting tweets for any user that logs in through it.

    In our case, the 'application' represents only a single user, e.g. a set of application credentials
    give a certain Z1 user programmatic access to our API. Since the application belongs to that user,
    but the application itself is not technically a user, we need to modify L77 to authenticate as the application's user
    (added 'or r.client.user').
    """

    def authenticate(self, **credentials):
        request = credentials.get('request')
        if request is not None:
            oauthlib_core = get_oauthlib_core()
            valid, r = oauthlib_core.verify_request(request, scopes=[])
            if valid:
                return r.user or r.client.user
        return None

    def get_user(self, user_id):
        try:
            return models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            return None
