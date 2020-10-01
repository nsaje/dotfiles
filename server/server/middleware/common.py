import re

import oauth2_provider.models

ID_RE = re.compile("/[0-9]+(/|$)")
UUID_RE = re.compile("/[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}(/|$)")
FILE_RE = re.compile(".*[.][a-zA-Z]{3}$")
TOKEN_RE = re.compile("/[0-9a-zA-Z]+(-[0-9a-zA-Z]+)+(/|$)")


def extract_request_params(request, high_cardinality=False):
    user = getattr(request, "user", None)
    user_email = getattr(user, "email", "unknown")
    is_oauth2 = isinstance(getattr(request, "auth", None), oauth2_provider.models.AccessToken)
    authenticator = "oauth2" if is_oauth2 else "session"
    return dict(
        endpoint=getattr(request, "handler_class_name", None),
        user=user_email,
        path=request.get_full_path() if high_cardinality else clean_path(request.path),
        method=request.method,
        authenticator=authenticator,
    )


def extract_response_params(response):
    return dict(status=str(getattr(response, "status_code", None)))


def clean_path(path):
    if FILE_RE.match(path):
        path = "_FILE_"
    path = ID_RE.sub("/_ID_\\1", path)
    path = UUID_RE.sub("/_UUID_\\1", path)
    path = TOKEN_RE.sub("/_TOKEN_\\2", path)
    return path
