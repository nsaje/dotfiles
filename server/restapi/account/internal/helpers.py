import core.models
import dash.features.custom_flags
import dash.models
import restapi.common.helpers
import zemauth.models

SUBAGENCY_MAP = {198: (196, 198)}


def get_extra_data(user, account):
    extra = {
        "archived": account.settings.archived,
        "can_archive": account.can_archive(),
        "can_restore": account.can_restore(),
        "is_externally_managed": account.is_externally_managed,
    }

    if user.has_perm("zemauth.can_set_agency_for_account"):
        extra["agencies"] = get_agencies(user)

    if user.has_perm("zemauth.can_modify_account_manager"):
        extra["account_managers"] = get_account_managers(user, account)

    if user.has_perm("zemauth.can_set_account_sales_representative"):
        extra["sales_representatives"] = get_sales_representatives(account)

    if user.has_perm("zemauth.can_set_account_cs_representative"):
        extra["cs_representatives"] = get_cs_representatives(account)

    if user.has_perm("zemauth.can_set_account_ob_representative"):
        extra["ob_representatives"] = get_ob_representatives()

    if user.has_perm("zemauth.can_see_backend_hacks"):
        extra["hacks"] = get_hacks(account)

    if user.has_perm("zemauth.can_see_deals_in_ui"):
        extra["deals"] = get_deals(account)

    return extra


def get_agencies(user):
    agencies = core.models.Agency.objects.filter(users__in=[user])
    if user.has_perm("zemauth.can_see_all_accounts"):
        agencies = core.models.Agency.objects.all()
    return list(
        agencies.values(
            "id", "name", "sales_representative", "cs_representative", "ob_representative", "default_account_type"
        )
    )


def get_account_managers(user, account):
    users = restapi.common.helpers.get_users_for_manager(user, account, account.settings.default_account_manager)
    return [{"id": user.id, "name": restapi.common.helpers.get_user_full_name_or_email(user)} for user in users]


def get_sales_representatives(account):
    users = zemauth.models.User.objects.get_users_with_perm("campaign_settings_sales_rep").filter(is_active=True)
    if account.agency_id in SUBAGENCY_MAP:
        subagencies = core.models.Agency.objects.filter(pk__in=SUBAGENCY_MAP[account.agency_id])
        users &= zemauth.models.User.objects.filter(agency__in=subagencies).distinct()
    return [{"id": user.id, "name": restapi.common.helpers.get_user_full_name_or_email(user)} for user in users]


def get_cs_representatives(account):
    users = zemauth.models.User.objects.get_users_with_perm("campaign_settings_cs_rep").filter(is_active=True)
    if account.agency_id in SUBAGENCY_MAP:
        subagencies = core.models.Agency.objects.filter(pk__in=SUBAGENCY_MAP[account.agency_id])
        users &= zemauth.models.User.objects.filter(agency__in=subagencies).distinct()
    return [{"id": user.id, "name": restapi.common.helpers.get_user_full_name_or_email(user)} for user in users]


def get_ob_representatives():
    users = zemauth.models.User.objects.get_users_with_perm("can_be_ob_representative").filter(is_active=True)
    return [{"id": user.id, "name": restapi.common.helpers.get_user_full_name_or_email(user)} for user in users]


def get_deals(account):
    if account.id is None:
        return []
    return restapi.common.helpers.get_applied_deals_dict(account.get_all_configured_deals())


def get_hacks(account):
    if account.id is None:
        return []
    return dash.models.CustomHack.objects.all().filter_applied(account=account).filter_active(
        True
    ).to_dict_list() + dash.features.custom_flags.helpers.get_all_custom_flags_on_account(account)


def get_media_sources_data(user, account):
    media_sources = []
    account_allowed_sources_ids_set = set(
        account.allowed_sources.values_list("id", flat=True) if account.id is not None else []
    )

    all_sources_queryset = _get_all_sources_queryset(user, account.agency)
    all_sources = list(all_sources_queryset.values("id", "name", "released", "deprecated"))
    for source in all_sources:
        if source["id"] not in account_allowed_sources_ids_set and source["deprecated"]:
            continue
        source["allowed"] = source["id"] in account_allowed_sources_ids_set
        media_sources.append(source)

    return media_sources


def get_all_sources(user, agency):
    all_sources_queryset = _get_all_sources_queryset(user, agency)
    return list(all_sources_queryset)


def get_allowed_sources(user, account):
    allowed_sources_queryset = account.allowed_sources.all()
    if not user.has_perm("zemauth.can_see_all_available_sources"):
        allowed_sources_queryset = allowed_sources_queryset.filter(released=True)
    return list(allowed_sources_queryset)


def get_new_allowed_sources(sources, media_sources_data):
    allowed_sources = []
    media_sources_data_dict = dict((x["id"], x) for x in media_sources_data)
    for source in sources:
        media_source = media_sources_data_dict.get(source.id)
        if media_source is not None and media_source.get("allowed", False):
            allowed_sources.append(source)
    return allowed_sources


def get_non_removable_sources_ids(account, sources_to_be_removed):
    return list(
        core.models.AdGroupSource.objects.all()
        .filter(settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        .filter(ad_group__settings__state=dash.constants.AdGroupSettingsState.ACTIVE)
        .filter(ad_group__campaign__account=account.id)
        .filter(source__in=sources_to_be_removed)
        .values_list("source_id", flat=True)
        .distinct()
    )


def get_changes_for_sources(added_sources, removed_sources):
    sources_text = []
    if added_sources:
        added_sources_names = [source.name for source in added_sources]
        added_sources_text = "Added allowed media sources ({})".format(", ".join(added_sources_names))
        sources_text.append(added_sources_text)

    if removed_sources:
        removed_sources_names = [source.name for source in removed_sources]
        removed_sources_text = "Removed allowed media sources ({})".format(", ".join(removed_sources_names))
        sources_text.append(removed_sources_text)

    return ", ".join(sources_text)


def _get_all_sources_queryset(user, agency):
    all_sources_queryset = core.models.Source.objects.all()
    if agency is not None and agency.allowed_sources.count() > 0:
        all_sources_queryset = agency.allowed_sources.all()
    if not user.has_perm("zemauth.can_see_all_available_sources"):
        all_sources_queryset = all_sources_queryset.filter(released=True)
    return all_sources_queryset
