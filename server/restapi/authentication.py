from rest_framework.authentication import BaseAuthentication
from rest_framework.authentication import SessionAuthentication
from oauth2_provider.oauth2_backends import get_oauthlib_core


class OAuth2Authentication(BaseAuthentication):
    """
    OAuth 2 authentication backend using `django-oauth-toolkit`

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
    www_authenticate_realm = 'api'

    def authenticate(self, request):
        """
        Returns two-tuple of (user, token) if authentication succeeds,
        or None otherwise.
        """
        oauthlib_core = get_oauthlib_core()
        valid, r = oauthlib_core.verify_request(request, scopes=[])
        if valid:
            return r.user or r.client.user, r.access_token
        else:
            return None

    def authenticate_header(self, request):
        """
        Bearer is the only finalized type currently
        """
        return 'Bearer realm="%s"' % self.www_authenticate_realm
