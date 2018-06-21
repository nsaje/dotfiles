from rest_framework import authentication
import utils.rest_common.authentication

from utils import request_signer
from zemauth.models import User


def gen_service_authentication(service_name, keys):
    class RequestSignerAuthentication(authentication.BaseAuthentication):
        def authenticate(self, request):
            try:
                request_signer.verify_wsgi_request(request, keys)
                user = User.objects.get_or_create_service_user(service_name)
                return (user, None)
            except Exception:
                return None
    return RequestSignerAuthentication


def gen_oauth_authentication(service_name):
    class OAuth2Authentication(utils.rest_common.authentication.OAuth2Authentication):

        def authenticate(self, request):
            status = super(OAuth2Authentication, self).authenticate(request)
            if not status:
                return None
            user, token = status
            if user.email != '{}@service.zemanta.com'.format(service_name):
                return None
            return user, token
    return OAuth2Authentication
