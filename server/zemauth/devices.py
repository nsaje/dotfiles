import datetime
import string
import logging
from functools import partial

from ua_parser import user_agent_parser
import ipware.ip
import requests

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils.crypto import get_random_string

from zemauth import models
from utils import dates_helper, email_helper, threads

logger = logging.getLogger(__name__)

IP_INFO_TIMEOUT_SECONDS = 0.5
IP_INFO_URL = "https://ipinfo.io/{ip}/json"

DEVICE_COOKIE_NAME = "deviceid"
DEVICE_KEY_EXPIRY = datetime.timedelta(seconds=5 * 365 * 24 * 60 * 60)
VALID_KEY_CHARS = string.ascii_letters + string.digits

MAX_RETRIES = 20


def _get_ip_info(ip):
    # NOTE: this is internal to this module since calls to the service (1000 requests per day)
    # are throttled and it might not fit another use case
    url = IP_INFO_URL.format(ip=ip, timeout=IP_INFO_TIMEOUT_SECONDS)
    response = requests.get(url)
    return response.json()


def handle_user_device(request, response):
    try:
        _handle_user_device(request, response)
    except Exception:
        logger.exception("Exception occurred in handling user device")


@transaction.atomic
def _handle_user_device(request, response):
    if not request.user.is_authenticated or request.user.email.endswith("@zemanta-test.com"):
        return
    device_key = request.COOKIES.get(DEVICE_COOKIE_NAME)
    device = _get_or_create_device(device_key)
    if not models.UserDevice.objects.filter(user=request.user, device=device).exists():
        device.expire_date = _get_expire_date()
        device.save()

        models.UserDevice.objects.create(user=request.user, device_id=device.device_key)
        send_email_fn = partial(_send_email, request)
        send_email_thread = threads.AsyncFunction(send_email_fn)
        send_email_thread.start()

    response.set_cookie(
        DEVICE_COOKIE_NAME, device.device_key, expires=device.expire_date, secure=settings.SESSION_COOKIE_SECURE
    )


def _send_email(request):
    ip = ipware.ip.get_ip(request)
    try:
        ip_info = _get_ip_info(ip)
    except Exception:
        logger.exception("Exception occurred retrieving ip info")
        ip_info = {}
    user_agent = request.META["HTTP_USER_AGENT"]
    user_agent_parsed = user_agent_parser.Parse(user_agent)
    browser = user_agent_parsed.get("user_agent", {}).get("family") or "Unknown Browser"
    os = user_agent_parsed.get("os", {}).get("family") or "Unknown Operating System"
    city = ip_info.get("city") or "Unknown City"
    country = ip_info.get("country") or "Unknown Country"
    if any("Unknown" in prop for prop in [browser, os, city, country]):
        logger.warning(
            "Could't extract information for new device email. "
            "browser=%s, os=%s, city=%s, country=%s, ip=%s, user_agent=%s",
            browser,
            os,
            city,
            country,
            ip,
            user_agent,
        )
    email_helper.send_new_user_device_email(request, browser=browser, os=os, city=city, country=country)


def _get_new_device_key():
    for _ in range(MAX_RETRIES):
        device_key = get_random_string(32, VALID_KEY_CHARS)
        if not models.Device.objects.filter(device_key=device_key).exists():
            return device_key
    raise Exception("Reached retry limit for generating device key")


def _get_expire_date():
    return dates_helper.utc_now() + DEVICE_KEY_EXPIRY


def _get_or_create_device(device_key):
    if not device_key:
        return _create_device_entry()
    try:
        return models.Device.objects.get(device_key=device_key, expire_date__gte=dates_helper.utc_today())
    except models.Device.DoesNotExist:
        return _create_device_entry()


def _create_device_entry():
    for _ in range(MAX_RETRIES):
        device = models.Device(device_key=_get_new_device_key(), expire_date=_get_expire_date())
        try:
            device.save()
            return device
        except IntegrityError:
            pass
    raise Exception("Reached retry limit for inserting new device")
