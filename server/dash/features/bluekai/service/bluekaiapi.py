import base64
import collections
import copy
import hashlib
import hmac
import json
import urllib.error
import urllib.parse
import urllib.request

import requests
import retrying
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


def _transform_expression(expression):
    expression = _transform_expression_recur(expression)
    return _format_expression(expression)


def _transform_expression_recur(expression):
    if _is_bluekai_category(expression):
        return _transform_to_leaf_node(expression)
    operator = expression[0].upper()
    subexpression = [_transform_expression_recur(s) for s in expression[1:]]
    if operator == "NOT":
        # NOTE: our NOT representation has direct OR children while bluekai expects a single AND level inbetween
        assert _is_simple_expression(
            subexpression, operator="OR"
        ), "expected NOT expression to have a single OR operator with a list of categories"
        return {operator: {"AND": subexpression}}
    return {operator: subexpression}


def _is_simple_expression(expression, *, operator):
    # is expression of form: {"OR": [{"cat": 1234}, {"cat": ...}]}
    only_has_operator = list(expression[0].keys()) == [operator]
    only_category_children = all(list(el.keys()) == ["cat"] for el in list(expression[0].values())[0])
    return only_has_operator and only_category_children


def _is_bluekai_category(expression):
    return isinstance(expression, str) and expression.startswith("bluekai:")


def _transform_to_leaf_node(expression):
    return {"cat": int(expression.replace("bluekai:", ""))}


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


def get_audience(audience_id):
    url = AUDIENCES_URL + str(audience_id)
    response = _perform_request_with_retry("GET", url, params={})
    return json.loads(response.content)


def get_campaign(campaign_id):
    url = CAMPAIGNS_REST_URL + str(campaign_id)
    response = _perform_request("GET", url, params={})
    return json.loads(response.content)


def update_audience(audience_id, data):
    url = AUDIENCES_URL + str(audience_id)
    response = _perform_request("PUT", url, params={}, data=json.dumps(data))
    return json.loads(response.content)


def get_expression_from_campaign(campaign_id):
    campaign = get_campaign(campaign_id)
    audience_id = campaign["audience"]["id"]
    audience = get_audience(audience_id)
    return _transform_object_to_expression(audience["segments"])


def _transform_object_to_expression(segments_object):
    if not segments_object:
        return []
    keys = segments_object.keys()
    if len(keys) == 1 and list(keys)[0] in {"AND", "OR", "NOT"}:
        operator = list(keys)[0]
        child = segments_object[operator]
        if isinstance(child, dict):  # NOT
            child_expression = [_transform_object_to_expression(segments_object[operator])]
        elif isinstance(child, list):  # AND, OR
            child_expression = _transform_list_to_expression(segments_object[operator])
        else:
            raise Exception("Bluekai audience format not recognized")
        if operator == "AND" and len(child) == 1:  # simplification only
            return child_expression
        return [operator.lower()] + child_expression
    else:
        return "bluekai:%s" % segments_object["cat"]


def _transform_list_to_expression(segments_list):
    expression = []
    for item in segments_list:
        expression.append(_transform_object_to_expression(item))
    if len(expression) == 1 and isinstance(expression[0], list):  # simplification only
        return expression[0]
    return expression


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


@retrying.retry(stop_max_attempt_number=10, wait_exponential_multiplier=4000, wait_exponential_max=120000)
def _perform_request_with_retry(method, url, params=None, data=""):
    return _perform_request(method, url, params=params, data=data)


def _perform_request(method, url, params=None, data=""):
    if not params:
        params = {}
    params_signed = _get_signed_params(method, url, params, data)
    response = requests.request(method, url, params=params_signed, headers=HEADERS, data=data)
    response.raise_for_status()
    return response
