import json

import httplib2
from django.conf import settings
from django.urls import reverse
from oauth2client.client import OAuth2WebServerFlow

from utils import zlogging

logger = zlogging.getLogger(__name__)

URL_APP_TOKEN = "https://accounts.google.com/o/oauth2/auth"
URL_USERINFO = "https://www.googleapis.com/oauth2/v2/userinfo"

REDIRECT_URI = ""
SCOPE = ""


def get_flow(request):
    url = request.build_absolute_uri(reverse("zemauth.views.google_callback"))
    url = url.replace("http://", "https://")

    next_url = request.GET.get("next")
    kwargs = {"state": next_url} if next_url is not None else {}

    flow = OAuth2WebServerFlow(
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
        scope="email",
        access_type="online",
        redirect_uri=url,
        **kwargs,
    )
    return flow


def get_uri(request, flow=None):
    if not flow:
        flow = get_flow(request)
    return flow.step1_get_authorize_url()


def authorize(request, flow=None):
    try:
        code = request.GET.get("code")
        if not code:
            return None
        if not flow:
            flow = get_flow(request)

        credentials = flow.step2_exchange(code)

        http = httplib2.Http()
        http = credentials.authorize(http)

        resp, content = http.request(URL_USERINFO, "GET")

        if resp and resp.status == 200:
            return json.loads(content)

    except Exception as e:
        logger.error("Google authentification failed")
        logger.exception(e)

    return None
