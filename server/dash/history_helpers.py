import dash.constants
import dash.models


def write_ad_group_history(ad_group,
                           changes_text,
                           user=None,
                           system_user=None,
                           history_type=dash.constants.HistoryType.AD_GROUP,
                           action_type=None
                           ):
    if not changes_text:
        return  # nothing to write
    dash.models.create_ad_group_history(
        ad_group,
        history_type,
        None,
        changes_text,
        user=user,
        system_user=system_user,
        action_type=action_type
    )


def write_campaign_history(campaign,
                           changes_text,
                           user=None,
                           system_user=None,
                           history_type=dash.constants.HistoryType.CAMPAIGN,
                           action_type=None
                           ):
    if not changes_text:
        return   # nothing to write
    dash.models.create_campaign_history(
        campaign,
        history_type,
        None,
        changes_text,
        user=user,
        system_user=system_user,
        action_type=action_type
    )


def write_account_history(account,
                          changes_text,
                          user=None,
                          system_user=None,
                          history_type=dash.constants.HistoryType.ACCOUNT,
                          action_type=None
                          ):
    if not changes_text:
        return   # nothing to write
    dash.models.create_account_history(
        account,
        history_type,
        None,
        changes_text,
        user=user,
        system_user=system_user,
        action_type=action_type
    )
