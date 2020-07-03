import re
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from django.db.models import Q
from typing_extensions import TypedDict

import dash.models
from zemauth.models import User


class MarketerTypeDict(TypedDict):
    type: str
    content_classification: str
    importance: int


class EntityTagDict(TypedDict):
    name: str
    account__id: Union[None, int]
    agency__id: Union[None, int]


MARKETER_NAME_REGEX = r"^Zemanta_(?P<account_id>\d+)_(?P<marketer_version>\d+)$"
MARKETER_TYPE_PREFIX = "account_type"
MARKETER_TYPE_MAP: Dict[str, MarketerTypeDict] = {
    f"{MARKETER_TYPE_PREFIX}/audiencedev/socagg": {
        "type": "ELASTIC_PUBLISHER",
        "content_classification": "PremiumElasticPublishers",
        "importance": 1,
    },
    f"{MARKETER_TYPE_PREFIX}/performance/search": {"type": "SEARCH", "content_classification": "SERP", "importance": 2},
}
DEFAULT_OUTBRAIN_MARKETER_TYPE = "AFFILIATES_AND_SMB"
DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION = "AdvertorialOther"
DEFUALT_OUTBRAIN_USER_EMAILS = ["ziga.stopinsek@zemanta.com", "bres@outbrain.com", "partners-cred@outbrain.com"]


def parse_marketer_name(marketer_name: str) -> Tuple[int, int]:
    if marketer_name is None:
        raise ValueError("Marketer name can not be None")

    match = re.match(MARKETER_NAME_REGEX, marketer_name)
    if match is None:
        raise ValueError("Invalid Zemanta marketer name")

    values = match.groupdict()
    return int(values["account_id"]), int(values["marketer_version"])


def calculate_marketer_parameters(account: dash.models.Account) -> Tuple[str, str]:
    try:
        filter_qs = Q(account__id=account.id)
        if account.agency_id is not None:
            filter_qs |= Q(agency__id=account.agency_id)

        entity_tag_data = list(
            dash.models.EntityTag.objects.get(name=MARKETER_TYPE_PREFIX)
            .get_descendants()
            .filter(filter_qs)
            .distinct()
            .order_by("id")
            .values("name", "account__id", "agency__id")
        )
    except dash.models.EntityTag.DoesNotExist:
        return DEFAULT_OUTBRAIN_MARKETER_TYPE, DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION

    entity_tag_data = [e for e in entity_tag_data if e["name"] in MARKETER_TYPE_MAP]

    return determine_best_match(entity_tag_data)


def determine_best_match(entity_tag_data: List[EntityTagDict]) -> Tuple[str, str]:
    if not entity_tag_data:
        return DEFAULT_OUTBRAIN_MARKETER_TYPE, DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION

    entity_tag_data = [e for e in entity_tag_data if e["name"] in MARKETER_TYPE_MAP]
    selected_entity_tag_data = [e for e in entity_tag_data if e["account__id"] is not None]
    if not selected_entity_tag_data:
        # there are no account specific tags, take agency ones
        selected_entity_tag_data = entity_tag_data

    sorted_matches = sorted(
        [MARKETER_TYPE_MAP[e["name"]] for e in selected_entity_tag_data], key=lambda x: x["importance"]
    )
    if not sorted_matches:
        return DEFAULT_OUTBRAIN_MARKETER_TYPE, DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION

    return sorted_matches[0]["type"], sorted_matches[0]["content_classification"]


def get_marketer_user_emails(include_defaults: bool = True) -> List[str]:
    emails = list(
        User.objects.get_users_with_perm("campaign_settings_cs_rep")
        .exclude(groups__name="ProdOps")
        .filter(is_active=True)
        .order_by("id")
        .values_list("email", flat=True)
    )

    # remove the "CS user" that does not exist in Amplify
    emails = [email for email in emails if email != "help@zemanta.com"]

    if include_defaults:
        for email in DEFUALT_OUTBRAIN_USER_EMAILS:
            if email not in emails:
                emails.append(email)

    return emails
