import urllib.request, urllib.error, urllib.parse
import json

from django.conf import settings

from utils import request_signer
from dash import models


AD_GROUP_IDS = []


def _update_redirect(redirect_id, url):
    data = json.dumps({"url": url})

    request_url = settings.R1_REDIRECTS_API_URL
    if not request_url.endswith("/"):
        request_url += "/"
    request_url += redirect_id + "/"

    request = urllib.request.Request(request_url, data.encode("utf-8"))
    request.get_method = lambda: "PUT"
    response = request_signer.urllib_secure_open(request, settings.R1_API_SIGN_KEY)

    status_code = response.getcode()
    if status_code != 200:
        raise Exception("Invalid response status code. status code: {}".format(status_code))

    ret = json.loads(response.read())
    if ret["status"] != "ok":
        raise Exception("Generate redirect request not successful. status: {}".format(ret["status"]))

    if not ret["data"]:
        raise Exception("Generate redirect request not successful. data: {}".format(ret["data"]))

    return ret["data"]


redirect_ids_before = {}
for ad_group_id in AD_GROUP_IDS:
    content_ads = models.ContentAd.objects.filter(ad_group_id=ad_group_id)
    for content_ad in content_ads:
        if not content_ad.redirect_id:
            continue

        redirect_ids_before[content_ad.id] = content_ad.redirect_id
        resp = _update_redirect(content_ad.redirect_id, content_ad.url)

        print(content_ad.redirect_id, resp)
