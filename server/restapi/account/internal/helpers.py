from django.db.models import Q

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
        "agencies": get_agencies(user, account),
    }

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

    if user.has_perm("zemauth.can_modify_allowed_sources"):
        extra["available_media_sources"] = restapi.common.helpers.get_available_sources(
            user, account.agency, account=account
        )

    return extra


def get_agencies(user, account):
    agencies = core.models.Agency.objects.filter(Q(users__in=[user]) | Q(id=account.agency_id)).distinct()
    if user.has_perm("zemauth.can_see_all_accounts"):
        agencies = core.models.Agency.objects.all()
    return list(
        agencies.values(
            "id",
            "name",
            "sales_representative",
            "cs_representative",
            "ob_sales_representative",
            "ob_account_manager",
            "default_account_type",
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


def get_allowed_sources(account):
    if account.id is None:
        if account.agency:
            if not account.agency.allowed_sources.exists():
                if not account.agency.available_sources.exists():
                    return list(core.models.Source.objects.filter(released=True, deprecated=False))
                return []
            return list(account.agency.allowed_sources.all())
        return list(core.models.Source.objects.filter(released=True, deprecated=False))
    return list(account.allowed_sources.all())


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
