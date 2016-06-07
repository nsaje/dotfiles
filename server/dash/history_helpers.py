import dash.constants
import dash.models


def write_ad_group_history(ad_group,
                           changes_text,
                           user=None,
                           system_user=None,
                           history_type=dash.constants.AdGroupHistoryType.AD_GROUP
                           ):
    if not changes_text:
        return  # nothing to write

    history = dash.models.AdGroupHistory(
        ad_group=ad_group,
        system_user=system_user,
        created_by=user,
        changes_text=changes_text,
    )
    history.type = history_type
    history.save()


def write_campaign_history(campaign,
                           changes_text,
                           user=None,
                           system_user=None,
                           history_type=dash.constants.CampaignHistoryType.CAMPAIGN
                           ):
    if not changes_text:
        return   # nothing to write

    history = dash.models.CampaignHistory(
        campaign=campaign,
        created_by=user,
        system_user=system_user,
        changes_text=changes_text,
    )
    history.type = history_type
    history.save()


def write_account_history(account,
                          changes_text,
                          user=None,
                          system_user=None,
                          history_type=dash.constants.AccountHistoryType.ACCOUNT
                          ):
    if not changes_text:
        return   # nothing to write

    history = dash.models.AccountHistory(
        account=account,
        created_by=user,
        system_user=system_user,
        changes_text=changes_text,
    )
    history.type = history_type
    history.save()
