import re
from collections import defaultdict
from decimal import Decimal
from functools import reduce
from typing import Callable
from typing import List
from typing import Type
from typing import Union

from django.conf import settings
from django.db import transaction
from django.db.models import BooleanField
from django.db.models import CharField
from django.db.models import Exists
from django.db.models import OuterRef
from django.db.models import QuerySet
from django.db.models import Value
from django.http import HttpRequest
from rest_framework.request import Request as DrfRequest
from typing_extensions import TypedDict

import utils.exc
import zemauth.access
import zemauth.features.entity_permission.helpers
from dash import constants
from dash import history_helpers
from dash import models
from dash.views import helpers
from utils import email_helper
from utils import k1_helper
from utils import zlogging
from zemauth.features.entity_permission import Permission
from zemauth.models import User

from . import connection_definitions
from . import exceptions

Request = Union[HttpRequest, DrfRequest]


class ConnectionDict(TypedDict):
    id: int
    name: str
    location: str
    user_access: bool


logger = zlogging.getLogger(__name__)

OUTBRAIN_MAX_BLACKLISTED_PUBLISHERS = 30
OUTBRAIN_CPC_CONSTRAINT_LIMIT = 30
OUTBRAIN_CPC_CONSTRAINT_MIN = Decimal("0.65")


def get_global_blacklist():
    # Publisher group with this id should always exist
    return models.PublisherGroup.objects.get(pk=settings.GLOBAL_BLACKLIST_ID)


def get_blacklist_publisher_group(obj, create_if_none=False, request=None):
    """
    Gets default blacklist publisher group or (optionally) creates a new one.
    """

    if obj is None:
        return get_global_blacklist(), False

    publisher_group = obj.default_blacklist
    if publisher_group is None and create_if_none:
        with transaction.atomic():
            publisher_group = models.PublisherGroup.objects.create(
                request,
                name=obj.get_default_blacklist_name(),
                account=obj.get_account(),
                default_include_subdomains=True,
                implicit=True,
            )
            obj.default_blacklist = publisher_group
            obj.save(request)
            return publisher_group, True

    return publisher_group, False


def get_whitelist_publisher_group(obj, create_if_none=False, request=None):
    """
    Gets default whitelist publisher group or (optionally) creates a new one.
    """

    if obj is None:
        raise exceptions.PublisherGroupTargetingException("Whitelisting not supported on global level")

    with transaction.atomic():
        publisher_group = obj.default_whitelist
        if publisher_group is None and create_if_none:
            publisher_group = models.PublisherGroup.objects.create(
                request,
                name=obj.get_default_whitelist_name(),
                account=obj.get_account(),
                default_include_subdomains=True,
                implicit=True,
            )
            obj.default_whitelist = publisher_group
            obj.save(request)
            return publisher_group, True

    return publisher_group, False


def can_user_handle_publisher_listing_level(user, obj):
    if (isinstance(obj, models.Account) or isinstance(obj, models.Campaign)) and not user.has_perm(
        "zemauth.can_access_campaign_account_publisher_blacklist_status"
    ):
        return False
    if obj is None and not user.has_perm("zemauth.can_access_global_publisher_blacklist_status"):
        return False
    return True


def concat_publisher_group_targeting(
    ad_group,
    ad_group_settings,
    campaign,
    campaign_settings,
    account,
    account_settings,
    agency=None,
    agency_settings=None,
    include_global=True,
):

    blacklist = set()
    whitelist = set()

    if ad_group:
        blacklist |= _get_blacklists(ad_group, ad_group_settings)
        whitelist |= _get_whitelists(ad_group, ad_group_settings)
    if campaign:
        blacklist |= _get_blacklists(campaign, campaign_settings)
        whitelist |= _get_whitelists(campaign, campaign_settings)
    if account:
        blacklist |= _get_blacklists(account, account_settings)
        whitelist |= _get_whitelists(account, account_settings)
    if agency:
        blacklist |= _get_blacklists(agency, agency_settings)
        whitelist |= _get_whitelists(agency, agency_settings)

    if include_global:
        blacklist |= set([get_global_blacklist().id])

    blacklist = sorted([x for x in blacklist if x])
    whitelist = sorted([x for x in whitelist if x])

    return blacklist, whitelist


def get_publisher_group_targeting_multiple_entities(accounts, campaigns, ad_groups, include_global=True):
    whitelist = set()
    blacklist = set()

    def gettargeting():
        return {"included": set(), "excluded": set()}

    targeting = {
        "ad_group": defaultdict(gettargeting),
        "campaign": defaultdict(gettargeting),
        "account": defaultdict(gettargeting),
        "global": {"excluded": set([get_global_blacklist().id]) if include_global else set()},
    }
    if include_global:
        blacklist = set([get_global_blacklist().id])

    def fill_up(any_settings, related_field):
        for x in any_settings:
            current = set(x.blacklist_publisher_groups) | set([getattr(x, related_field).default_blacklist_id])
            current = set(x for x in current if x)

            blacklist.update(current)
            targeting[related_field][getattr(x, related_field).id]["excluded"].update(current)

            current = set(x.whitelist_publisher_groups) | set([getattr(x, related_field).default_whitelist_id])
            current = set(x for x in current if x)

            whitelist.update(current)
            targeting[related_field][getattr(x, related_field).id]["included"].update(current)

    if accounts is not None:
        accounts_settings = (
            models.AccountSettings.objects.filter(account__in=accounts)
            .group_current_settings()
            .prefetch_related("account")
        )
        fill_up(accounts_settings, "account")

    if campaigns is not None:
        campaigns_settings = (
            models.CampaignSettings.objects.filter(campaign__in=campaigns)
            .group_current_settings()
            .prefetch_related("campaign")
        )
        fill_up(campaigns_settings, "campaign")

    if ad_groups is not None:
        ad_groups_settings = (
            models.AdGroupSettings.objects.filter(ad_group__in=ad_groups)
            .group_current_settings()
            .prefetch_related("ad_group")
        )
        fill_up(ad_groups_settings, "ad_group")

    return blacklist, whitelist, targeting


def get_default_publisher_group_targeting_dict(include_global=True):
    return {
        "ad_group": {"included": set(), "excluded": set()},
        "campaign": {"included": set(), "excluded": set()},
        "account": {"included": set(), "excluded": set()},
        "global": {"excluded": set([get_global_blacklist().id]) if include_global else set()},
    }


def get_publisher_group_targeting_dict(
    ad_group, ad_group_settings, campaign, campaign_settings, account, account_settings, include_global=True
):
    d = get_default_publisher_group_targeting_dict(include_global)
    if ad_group is not None:
        d.update(
            {
                "ad_group": {
                    "included": _get_whitelists(ad_group, ad_group_settings),
                    "excluded": _get_blacklists(ad_group, ad_group_settings),
                }
            }
        )
    if campaign is not None:
        d.update(
            {
                "campaign": {
                    "included": _get_whitelists(campaign, campaign_settings),
                    "excluded": _get_blacklists(campaign, campaign_settings),
                }
            }
        )
    if account is not None:
        d.update(
            {
                "account": {
                    "included": _get_whitelists(account, account_settings),
                    "excluded": _get_blacklists(account, account_settings),
                }
            }
        )
    return d


def get_publisher_entry_list_level(entry, targeting):
    if entry.publisher_group_id in targeting["ad_group"]["included"] | targeting["ad_group"]["excluded"]:
        return constants.PublisherBlacklistLevel.ADGROUP
    elif entry.publisher_group_id in targeting["campaign"]["included"] | targeting["campaign"]["excluded"]:
        return constants.PublisherBlacklistLevel.CAMPAIGN
    elif entry.publisher_group_id in targeting["account"]["included"] | targeting["account"]["excluded"]:
        return constants.PublisherBlacklistLevel.ACCOUNT
    elif entry.publisher_group_id in targeting["global"]["excluded"]:
        return constants.PublisherBlacklistLevel.GLOBAL
    raise exceptions.PublisherGroupTargetingException(
        "Publisher entry does not belong to specified targeting configuration"
    )


def _get_blacklists(obj, obj_settings):
    """
    Concats default blacklist and publisher group targeting
    """

    return set(x for x in [obj.default_blacklist_id] + obj_settings.blacklist_publisher_groups if x)


def _get_whitelists(obj, obj_settings):
    """
    Concats default whitelist and publisher group targeting
    """

    return set(x for x in [obj.default_whitelist_id] + obj_settings.whitelist_publisher_groups if x)


def handle_publishers(request, entry_dicts, obj, status):
    if status == constants.PublisherTargetingStatus.BLACKLISTED:
        blacklist_publishers(request, entry_dicts, obj)
    elif status == constants.PublisherTargetingStatus.WHITELISTED:
        whitelist_publishers(request, entry_dicts, obj)
    else:
        unlist_publishers(request, entry_dicts, obj)


@transaction.atomic
def blacklist_publishers(request, entry_dicts, obj, should_write_history=True):
    publisher_group, created = get_blacklist_publisher_group(obj, create_if_none=True, request=request)

    # cpc constraints and history will be handled separately
    unlist_publishers(request, entry_dicts, obj, history=False)

    entries = _prepare_entries(entry_dicts, publisher_group)

    for entry in entries:
        validate_blacklist_entry(obj, entry)
    validate_outbrain_blacklist_count(obj, entries)

    models.PublisherGroupEntry.objects.bulk_create(entries)

    if created:
        _ping_k1(obj)

    if should_write_history:
        write_history(request, obj, entries, constants.PublisherTargetingStatus.BLACKLISTED)


@transaction.atomic
def whitelist_publishers(request, entry_dicts, obj, should_write_history=True):
    publisher_group, created = get_whitelist_publisher_group(obj, create_if_none=True, request=request)

    # cpc constraints and history will be handled separately
    unlist_publishers(request, entry_dicts, obj, history=False)

    entries = _prepare_entries(entry_dicts, publisher_group)
    models.PublisherGroupEntry.objects.bulk_create(entries)

    if created:
        _ping_k1(obj)

    if should_write_history:
        write_history(request, obj, entries, constants.PublisherTargetingStatus.WHITELISTED)


@transaction.atomic
def unlist_publishers(request, entry_dicts, obj, history=True):
    if not entry_dicts:
        return

    publisher_group, _ = get_blacklist_publisher_group(obj)
    selected_entries = models.PublisherGroupEntry.objects.filter(
        publisher_group=publisher_group
    ).filter_by_publisher_source(entry_dicts)
    if history and selected_entries.exists():
        write_history(
            request,
            obj,
            selected_entries,
            constants.PublisherTargetingStatus.UNLISTED,
            constants.PublisherTargetingStatus.BLACKLISTED,
        )

    selected_entries.delete()

    try:
        publisher_group, _ = get_whitelist_publisher_group(obj)
        selected_entries = models.PublisherGroupEntry.objects.filter(
            publisher_group=publisher_group
        ).filter_by_publisher_source(entry_dicts)
        if history and selected_entries.exists():
            write_history(
                request,
                obj,
                selected_entries,
                constants.PublisherTargetingStatus.UNLISTED,
                constants.PublisherTargetingStatus.WHITELISTED,
            )

        selected_entries.delete()
    except exceptions.PublisherGroupTargetingException:
        # pass if global level
        pass


@transaction.atomic
def upsert_publisher_group(request, publisher_group_dict, entry_dicts):
    changes = {}

    include_subdomains = bool(publisher_group_dict.get("include_subdomains"))
    agency_id = publisher_group_dict.get("agency_id")
    account_id = publisher_group_dict.get("account_id")

    # update or create publisher group
    if publisher_group_dict.get("id"):
        publisher_group = helpers.get_publisher_group(request.user, publisher_group_dict["id"])
        history_action_type = constants.HistoryActionType.PUBLISHER_GROUP_UPDATE
        changes_text = 'Publisher group "{} [{}]" updated'.format(publisher_group.name, publisher_group.id)

        if include_subdomains != publisher_group.default_include_subdomains:
            changes["include_subdomains"] = (publisher_group.default_include_subdomains, include_subdomains)
            publisher_group.default_include_subdomains = include_subdomains

        if publisher_group.name != publisher_group_dict["name"]:
            changes["name"] = (publisher_group.name, publisher_group_dict["name"])
            publisher_group.name = publisher_group_dict["name"]

        if publisher_group.agency_id != agency_id:
            agency = helpers.get_agency(request.user, agency_id) if agency_id is not None else None
            publisher_group.agency = agency

        if publisher_group.account_id != account_id:
            account = helpers.get_account(request.user, account_id) if account_id is not None else None
            publisher_group.account = account

        publisher_group.save(request)

    else:
        agency = helpers.get_agency(request.user, agency_id) if agency_id is not None else None
        account = helpers.get_account(request.user, account_id) if account_id is not None else None
        publisher_group = models.PublisherGroup.objects.create(
            request,
            name=publisher_group_dict["name"],
            agency=agency,
            account=account,
            default_include_subdomains=include_subdomains,
            implicit=False,
        )
        history_action_type = constants.HistoryActionType.PUBLISHER_GROUP_CREATE
        changes_text = 'Publisher group "{} [{}]" created'.format(publisher_group.name, publisher_group.id)

    # replace publishers
    if entry_dicts:
        changes["entries"] = [[], []]
        changes["entries"][0] = list(
            publisher_group.entries.all().values("id", "publisher", "source__name", "include_subdomains")
        )
        models.PublisherGroupEntry.objects.filter(publisher_group=publisher_group).delete()
        models.PublisherGroupEntry.objects.bulk_create(_prepare_entries(entry_dicts, publisher_group))
        changes["entries"][1] = list(
            publisher_group.entries.all().values("id", "publisher", "source__name", "include_subdomains")
        )

    if history_action_type == constants.HistoryActionType.PUBLISHER_GROUP_UPDATE and changes:
        changes_text += ", " + _get_changes_description(changes)

    # update entries
    for entry in publisher_group.entries.all():
        entry.include_subdomains = publisher_group.default_include_subdomains
        entry.save()

    # write history
    publisher_group.write_history(changes_text, changes, history_action_type, request.user)

    return publisher_group


def _get_changes_description(changes):
    texts = []
    if "name" in changes:
        texts.append('name changed from "{}" to "{}"'.format(*changes["name"]))
    if "include_subdomains" in changes:
        texts.append('subdomains included changed from "{}" to "{}"'.format(*changes["include_subdomains"]))
    if "entries" in changes:
        texts.append("{} publishers replaced".format(len(changes["entries"][1])))
    return ", ".join(texts)


def write_history(request, obj, entries, status, previous_status=None):
    if status == constants.PublisherTargetingStatus.UNLISTED and previous_status is None:
        raise Exception("Previous status required")

    action_map = {
        constants.PublisherTargetingStatus.WHITELISTED: "Whitelisted",
        constants.PublisherTargetingStatus.BLACKLISTED: "Blacklisted",
        constants.PublisherTargetingStatus.UNLISTED: (
            "Enabled" if previous_status == constants.PublisherTargetingStatus.BLACKLISTED else "Disabled"
        ),
    }
    if status is None:
        # adding entries to a publisher group where status is not known
        action_map.update({None: "Added"})

    action = action_map[status]

    if obj is None:
        level_description = "globally"
        history_actiontype = constants.HistoryActionType.GLOBAL_PUBLISHER_BLACKLIST_CHANGE
    else:
        level_description = "on {} level".format(
            constants.PublisherBlacklistLevel.get_text(obj.get_publisher_level()).lower()
        )
        history_actiontype = constants.HistoryActionType.PUBLISHER_BLACKLIST_CHANGE

    pubs_string = ", ".join(
        "{} on {}".format(x.publisher, x.source.name if x.source else "all sources") for x in entries
    )

    changes_text = "{action} the following publishers {level_description}: {pubs}.".format(
        action=action, level_description=level_description, pubs=pubs_string
    )

    if obj is None:
        history_helpers.write_global_history(changes_text, user=request.user, action_type=history_actiontype)
    else:
        obj.write_history(changes_text, user=request.user, action_type=history_actiontype)
        email_helper.send_obj_changes_notification_email(obj, request, changes_text)


def get_or_create_publisher_group(
    request,
    name,
    publisher_group_id=None,
    agency_id=None,
    account_id=None,
    default_include_subdomains=True,
    implicit=False,
):
    if publisher_group_id is not None:
        queryset_user_perm = (
            models.PublisherGroup.objects.filter_by_user(request.user)
            .filter(agency_id=agency_id)
            .filter(account_id=account_id)
            .filter(default_include_subdomains=default_include_subdomains)
        )
        queryset_entity_perm = (
            models.PublisherGroup.objects.filter_by_entity_permission(request.user, Permission.WRITE)
            .filter(agency_id=agency_id)
            .filter(account_id=account_id)
            .filter(default_include_subdomains=default_include_subdomains)
        )
        queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
            request.user, Permission.WRITE, queryset_user_perm, queryset_entity_perm, entity_id=publisher_group_id
        )
        return queryset.get(id=publisher_group_id), False

    try:
        agency = zemauth.access.get_agency(request.user, Permission.WRITE, agency_id) if agency_id is not None else None
    except utils.exc.MissingDataError as e:
        raise models.Agency.DoesNotExist(str(e))
    try:
        account = (
            zemauth.access.get_account(request.user, Permission.WRITE, account_id) if account_id is not None else None
        )
    except utils.exc.MissingDataError as e:
        raise models.Account.DoesNotExist(str(e))

    return (
        models.PublisherGroup.objects.create(
            request,
            name,
            agency=agency,
            account=account,
            default_include_subdomains=default_include_subdomains,
            implicit=implicit,
        ),
        True,
    )


@transaction.atomic
def add_publisher_group_entries(request, publisher_group, entry_dicts, should_write_history=True):
    if not entry_dicts:
        return models.PublisherGroupEntry.objects.none()

    entries = _prepare_entries(entry_dicts, publisher_group)
    models.PublisherGroupEntry.objects.filter(publisher_group=publisher_group).filter_by_publisher_source(
        entry_dicts
    ).delete()
    if should_write_history:
        write_history(request, None, entries, None)
    return models.PublisherGroupEntry.objects.bulk_create(entries)


def get_publisher_group_connections(
    user: User, publisher_group_id: int, show_unauthorized: bool = False
) -> List[ConnectionDict]:
    reducing_func: Callable[[QuerySet, QuerySet], QuerySet] = lambda x, y: x.union(y)

    query_sets: List[QuerySet]

    if show_unauthorized:

        def get_model_access_qs(
            user: User,
            model: Union[Type[models.Agency], Type[models.Account], Type[models.Campaign], Type[models.AdGroup]],
        ) -> QuerySet:
            if user.has_perm("zemauth.fea_use_entity_permission"):
                return model.objects.filter_by_entity_permission(user, Permission.READ).filter(id=OuterRef("id"))
            return model.objects.filter_by_user(user).filter(id=OuterRef("id"))

        query_sets = [
            (
                models.Agency.objects.all()
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AGENCY_BLACKLIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.Agency)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
            (
                models.Agency.objects.all()
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AGENCY_WHITELIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.Agency)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
            (
                models.Account.objects.all()
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_ACCOUNT_BLACKLIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.Account)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
            (
                models.Account.objects.all()
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_ACCOUNT_WHITELIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.Account)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
            (
                models.Campaign.objects.all()
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_CAMPAIGN_BLACKLIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.Campaign)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
            (
                models.Campaign.objects.all()
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_CAMPAIGN_WHITELIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.Campaign)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
            (
                models.AdGroup.objects.all()
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AD_GROUP_BLACKLIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.AdGroup)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
            (
                models.AdGroup.objects.all()
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AD_GROUP_WHITELIST, output_field=CharField()),
                    user_access=Exists(get_model_access_qs(user, models.AdGroup)),
                )
                .order_by("id")
                .values("id", "name", "location", "user_access")
            ),
        ]
    else:

        def get_model_access_qs(
            user: User,
            model: Union[Type[models.Agency], Type[models.Account], Type[models.Campaign], Type[models.AdGroup]],
        ) -> QuerySet:
            if user.has_perm("zemauth.fea_use_entity_permission"):
                return model.objects.filter_by_entity_permission(user, Permission.READ)
            return model.objects.filter_by_user(user)

        query_sets = [
            (
                get_model_access_qs(user, models.Agency)
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AGENCY_BLACKLIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
            (
                get_model_access_qs(user, models.Agency)
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AGENCY_WHITELIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
            (
                get_model_access_qs(user, models.Account)
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_ACCOUNT_BLACKLIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
            (
                get_model_access_qs(user, models.Account)
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_ACCOUNT_WHITELIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
            (
                get_model_access_qs(user, models.Campaign)
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_CAMPAIGN_BLACKLIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
            (
                get_model_access_qs(user, models.Campaign)
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_CAMPAIGN_WHITELIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
            (
                get_model_access_qs(user, models.AdGroup)
                .filter(settings__blacklist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AD_GROUP_BLACKLIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
            (
                get_model_access_qs(user, models.AdGroup)
                .filter(settings__whitelist_publisher_groups__contains=[publisher_group_id])
                .annotate(
                    location=Value(connection_definitions.CONNECTION_TYPE_AD_GROUP_WHITELIST, output_field=CharField()),
                    user_access=Value(True, BooleanField()),
                )
                .order_by("created_dt")
                .values("id", "name", "location", "user_access")
            ),
        ]

    return list(reduce(reducing_func, query_sets))


def remove_publisher_group_connection(request: Request, publisher_group_id: int, location: str, entity_id: int) -> None:
    connection_type = connection_definitions.CONNECTION_TYPE_MAP.get(location)
    if connection_type is None:
        raise connection_definitions.InvalidConnectionType("Invalid location")

    queryset_user_perm = connection_type["model"].objects.filter_by_user(request.user)
    queryset_entity_perm = connection_type["model"].objects.filter_by_entity_permission(request.user, Permission.WRITE)
    queryset = zemauth.features.entity_permission.helpers.log_differences_and_get_queryset(
        request.user, Permission.WRITE, queryset_user_perm, queryset_entity_perm, entity_id=entity_id
    )

    entity = queryset.get(id=entity_id)
    publisher_group_ids = getattr(entity.settings, connection_type["attribute"]).copy()
    publisher_group_ids.remove(publisher_group_id)

    entity.settings.update(request, **{connection_type["attribute"]: publisher_group_ids})


def _ping_k1(obj):
    message = "publisher_group.create"
    level = obj.get_publisher_level()

    if level == constants.PublisherBlacklistLevel.ADGROUP:
        k1_helper.update_ad_group(obj, message)

    elif level == constants.PublisherBlacklistLevel.CAMPAIGN:
        k1_helper.update_ad_groups(obj.adgroup_set.filter_active().exclude_archived(), message)

    elif level == constants.PublisherBlacklistLevel.ACCOUNT:
        k1_helper.update_ad_groups(
            models.AdGroup.objects.filter(campaign__account=obj).filter_active().exclude_archived(), message
        )


def _prepare_entries(entry_dicts, publisher_group):
    """
    Creates publisher group entries from entry dicts. Does __not__ save them to the database.
    """

    entries = []
    added = set()

    # remove duplicates
    for entry in entry_dicts:
        key = frozenset(list(entry.values()))
        if key in added:
            continue

        added.add(key)

        entries.append(
            models.PublisherGroupEntry(
                publisher=entry.get("publisher"),
                source=entry.get("source"),
                placement=entry.get("placement"),
                include_subdomains=entry["include_subdomains"],
                outbrain_publisher_id=entry.get("outbrain_publisher_id", ""),
                outbrain_section_id=entry.get("outbrain_section_id", ""),
                outbrain_amplify_publisher_id=entry.get("outbrain_amplify_publisher_id", ""),
                outbrain_engage_publisher_id=entry.get("outbrain_engage_publisher_id", ""),
                publisher_group=publisher_group,
            )
        )
    return entries


def validate_blacklist_entry(obj, entry):
    if (
        entry.source
        and entry.source.source_type.type == constants.SourceType.OUTBRAIN
        and ((obj and obj.get_publisher_level() != constants.PublisherBlacklistLevel.ACCOUNT) or not obj)
    ):
        raise exceptions.PublisherGroupTargetingException(
            "Outbrain specific blacklisting is only available on account level"
        )


def validate_outbrain_blacklist_count(obj, entries):
    if obj is None:
        # no need to handle when we do global blacklisting:
        return
    account = obj.get_account()
    ob_blacklist_count_existing = get_ob_blacklisted_publishers_count(account)
    ob_blacklist_count_added = len(
        [e for e in entries if e.source and e.source.source_type.type == constants.SourceType.OUTBRAIN]
    )

    if (
        ob_blacklist_count_added
        and ob_blacklist_count_existing + ob_blacklist_count_added > OUTBRAIN_MAX_BLACKLISTED_PUBLISHERS
    ):
        raise exceptions.PublisherGroupTargetingException("Outbrain blacklist limit exceeded")


def get_ob_blacklisted_publishers_count(account):
    blacklists = _get_blacklists(account, account.get_current_settings())
    return models.PublisherGroupEntry.objects.filter(
        publisher_group_id__in=blacklists, source__source_type__type=constants.SourceType.OUTBRAIN
    ).count()


def parse_default_publisher_group_origin(publisher_group):
    type_, level, obj, name = None, None, None, ""
    possible_ids = re.findall("([0-9]+)", publisher_group.name)

    if publisher_group.name.startswith("Default blacklist for account"):
        type_, level = "Blacklist", "Account"
        obj = models.Account.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default whitelist for account"):
        type_, level = "Whitelist", "Account"
        obj = models.Account.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default blacklist for campaign"):
        type_, level = "Blacklist", "Campaign"
        obj = models.Campaign.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default whitelist for campaign"):
        type_, level = "Whitelist", "Campaign"
        obj = models.Campaign.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default blacklist for ad group"):
        type_, level = "Blacklist", "Ad Group"
        obj = models.AdGroup.objects.filter(pk=possible_ids[-1])
    elif publisher_group.name.startswith("Default whitelist for ad group"):
        type_, level = "Whitelist", "Ad Group"
        obj = models.AdGroup.objects.filter(pk=possible_ids[-1])

    if obj is not None:
        obj = obj.first()
        if obj is not None:
            name = "{} [{}]".format(obj.name, obj.id)

    return type_, level, obj, name
