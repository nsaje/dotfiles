import dash.constants
import dash.models


def write_ad_group_history(ad_group,
                           changes_text,
                           user=None,
                           system_user=None,
                           history_type=dash.constants.HistoryType.AD_GROUP
                           ):
    if not changes_text:
        return  # nothing to write
    dash.models.create_ad_group_history(
        ad_group,
        history_type,
        None,
        changes_text,
        user=user,
        system_user=system_user
    )


def write_campaign_history(campaign,
                           changes_text,
                           user=None,
                           system_user=None,
                           history_type=dash.constants.HistoryType.CAMPAIGN
                           ):
    if not changes_text:
        return   # nothing to write
    dash.models.create_campaign_history(
        campaign,
        history_type,
        None,
        changes_text,
        user=user,
        system_user=system_user
    )


def write_account_history(account,
                          changes_text,
                          user=None,
                          system_user=None,
                          history_type=dash.constants.HistoryType.ACCOUNT
                          ):
    if not changes_text:
        return   # nothing to write
    dash.models.create_account_history(
        account,
        history_type,
        None,
        changes_text,
        user=user,
        system_user=system_user
    )
