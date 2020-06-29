import re
from typing import Dict
from typing import List
from typing import Tuple

from typing_extensions import TypedDict

import dash.models
from zemauth.models import User


class MarketerTypeDict(TypedDict):
    type: str
    content_classification: str
    importance: int


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


def calculate_marketer_parameters(account_id: int) -> Tuple[str, str]:
    try:
        entity_tag_names = list(
            dash.models.EntityTag.objects.get(name=MARKETER_TYPE_PREFIX)
            .get_descendants()
            .filter(account__id=account_id)
            .order_by("id")
            .values_list("name", flat=True)
        )
    except dash.models.EntityTag.DoesNotExist:
        return DEFAULT_OUTBRAIN_MARKETER_TYPE, DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION

    entity_tag_names = [name for name in entity_tag_names if name in MARKETER_TYPE_MAP]

    return determine_best_match(entity_tag_names)


def determine_best_match(entity_tag_names):
    if not entity_tag_names:
        return DEFAULT_OUTBRAIN_MARKETER_TYPE, DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION

    sorted_matches = sorted(
        [MARKETER_TYPE_MAP[name] for name in entity_tag_names if name in MARKETER_TYPE_MAP],
        key=lambda x: x["importance"],
    )
    if not sorted_matches:
        return DEFAULT_OUTBRAIN_MARKETER_TYPE, DEFAULT_OUTBRAIN_MARKETER_CONTENT_CLASSIFICATION

    return sorted_matches[0]["type"], sorted_matches[0]["content_classification"]


def get_marketer_user_emails(include_defaults=True) -> List[str]:
    emails = list(
        User.objects.get_users_with_perm("campaign_settings_cs_rep")
        .exclude(groups__name="ProdOps")
        .filter(is_active=True)
        .order_by("id")
        .values_list("email", flat=True)
    )

    if include_defaults:
        for email in DEFUALT_OUTBRAIN_USER_EMAILS:
            if email not in emails:
                emails.append(email)

    return emails
