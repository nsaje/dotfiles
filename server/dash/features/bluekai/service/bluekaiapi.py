import base64
import collections
import copy
import hashlib
import hmac
import json
import urllib.request, urllib.parse, urllib.error
import urllib.parse

import requests
from django.conf import settings

from utils import dates_helper


TAXONOMY_URL = "https://taxonomy.bluekai.com/taxonomy/categories"
SEGMENT_INVENTORY_URL = "https://services.bluekai.com/" "Services/WS/SegmentInventory"
AUDIENCES_URL = "https://services.bluekai.com/Services/WS/audiences/"
CAMPAIGNS_REST_URL = "https://services.bluekai.com/rest/campaigns/"


PARENT_CATEGORY_ID = "671901"  # Oracle subtree, 344 can be used for root


HEADERS = {"Accept": "application/json", "Content-Type": "application/json"}


def get_taxonomy(parent_category_id=PARENT_CATEGORY_ID):
    params = collections.OrderedDict(
        [
            ("view", "BUYER"),
            ("partner.id", settings.BLUEKAI_API_PARTNER_ID),
            ("parentCategory.id", parent_category_id),
            ("showPriceAt", dates_helper.utc_now().replace(second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")),
            ("showReach", "true"),
        ]
    )

    response = _perform_request("GET", TAXONOMY_URL, params=params, data="")
    return json.loads(response.content)["items"]


def get_segment_reach(expression):
    params = collections.OrderedDict([("countries", "ALL")])
    response = _perform_request(
        "POST",
        SEGMENT_INVENTORY_URL,
        params=params,
        data=json.dumps(_transform_expression(expression)).replace(" ", ""),
    )
    query_result = json.loads(response.content)
    return query_result["reach"]


def get_audience(audience_id):
    url = AUDIENCES_URL + str(audience_id)
    response = _perform_request("GET", url, params={})
    return json.loads(response.content)


def get_campaign(campaign_id):
    url = CAMPAIGNS_REST_URL + str(campaign_id)
    response = _perform_request("GET", url, params={})
    return json.loads(response.content)


def update_audience(audience_id, data):
    url = AUDIENCES_URL + str(audience_id)
    response = _perform_request("PUT", url, params={}, data=json.dumps(data))
    return json.loads(response.content)


def _get_signed_params(method, url, params, data):
    path = urllib.parse.urlparse(url).path
    params_vals = "".join(urllib.parse.quote(val) for val in list(params.values()))
    payload = method + path + params_vals + data
    signature = base64.b64encode(
        hmac.new(
            settings.BLUEKAI_API_SECRET_KEY.encode("ascii", errors="ignore"),
            msg=payload.encode("ascii", errors="ignore"),
            digestmod=hashlib.sha256,
        ).digest()
    )
    params_signed = copy.copy(params)
    params_signed["bkuid"] = settings.BLUEKAI_API_USER_KEY
    params_signed["bksig"] = signature
    return params_signed


def _perform_request(method, url, params=None, data=""):
    if not params:
        params = {}
    params_signed = _get_signed_params(method, url, params, data)
    response = requests.request(method, url, params=params_signed, headers=HEADERS, data=data)
    response.raise_for_status()
    return response


def _transform_expression(expression):
    expression = _transform_expression_recur(expression)
    return _format_expression(expression)


def _format_expression(expression):
    if list(expression.keys()) == ["OR"]:
        expression = {"AND": [{"AND": [expression]}]}
    elif list(expression.keys()) == ["NOT"] or (
        list(expression.keys()) == ["AND"] and any(list(el.keys()) == ["OR"] for el in expression["AND"])
    ):
        expression = {"AND": [expression]}

    for subexp in expression["AND"]:
        if list(subexp.keys()) != ["AND"]:
            continue

        for i, subsubexp in enumerate(subexp["AND"]):
            if list(subsubexp.keys()) == ["NOT"]:
                # extract NOT into top level AND
                expression["AND"][0]["AND"].pop(i)
                expression["AND"].append(subsubexp)
                break

    return expression


def _transform_expression_recur(expression):
    if isinstance(expression, str) and expression.startswith("bluekai:"):
        return {"cat": int(expression.replace("bluekai:", ""))}
    operator = expression[0].upper()
    subexpression = [_transform_expression_recur(s) for s in expression[1:]]
    if operator == "NOT":
        # NOT must hold a dict instead of a list
        return {operator: {list(subexpression[0].keys())[0]: list(subexpression[0].values())[0]}}
    return {operator: subexpression}
