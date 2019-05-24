import core.features.goals
import dash.campaign_goals
import dash.constants
import dash.features.custom_flags
import dash.models
import restapi.common.helpers


def get_extra_data(user, campaign):
    extra = {
        "archived": campaign.settings.archived,
        "language": campaign.settings.language,
        "can_archive": campaign.can_archive(),
        "can_restore": campaign.can_restore(),
    }

    if user.has_perm("zemauth.can_see_campaign_goals"):
        extra["goals_defaults"] = core.features.goals.get_campaign_goals_defaults(campaign.account)

    if user.has_perm("zemauth.can_modify_campaign_manager"):
        extra["campaign_managers"] = get_campaign_managers(user, campaign)

    if user.has_perm("zemauth.can_see_backend_hacks"):
        extra["hacks"] = get_hacks(campaign)

    if user.has_perm("zemauth.can_see_deals_in_ui"):
        extra["deals"] = restapi.common.helpers.get_applied_deals_dict(campaign.get_all_configured_deals())

    return extra


def get_campaign_managers(user, campaign):
    users = restapi.common.helpers.get_users_for_manager(user, campaign.account, campaign.settings.campaign_manager)
    return [{"id": user.id, "name": restapi.common.helpers.get_user_full_name_or_email(user)} for user in users]


def get_hacks(campaign):
    return dash.models.CustomHack.objects.all().filter_applied(campaign=campaign).filter_active(
        True
    ).to_dict_list() + dash.features.custom_flags.helpers.get_all_custom_flags_on_campaign(campaign)
