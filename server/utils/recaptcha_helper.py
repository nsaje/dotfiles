import requests
from django.conf import settings

from utils import zlogging

logger = zlogging.getLogger(__name__)


def check_recaptcha(request):
    if request.method != "POST":
        return False

    recaptcha_response = request.POST.get("g-recaptcha-response")
    if not recaptcha_response:
        return False

    url = settings.RECAPTCHA_URL
    data = {"secret": settings.RECAPTCHA_SECRET_KEY, "response": recaptcha_response}

    try:
        response = requests.post(url=url, data=data)
    except requests.exceptions.RequestException as exception:
        logger.exception(exception)
        return False

    result = response.json()
    return result["success"]
