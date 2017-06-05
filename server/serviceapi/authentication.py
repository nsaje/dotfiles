from rest_framework import authentication

from utils import request_signer
from zemauth.models import User


def gen_service_authentication(service_name, keys):
    class RequestSignerAuthentication(authentication.BaseAuthentication):
        def authenticate(self, request):
            try:
                request_signer.verify_wsgi_request(request, keys)
                user = User.objects.get_or_create_service_user(service_name)
                return (user, None)
            except:
                return None
    return RequestSignerAuthentication
