from . import constants

######################
# AdGroup hacks
######################


def apply_ad_group_create_hacks(request, ad_group):
    if ad_group.campaign.account.agency_id in constants.AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY:
        data = constants.AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY[ad_group.campaign.account.agency_id]
        ad_group.settings.update(request, skip_validation=True, **data)


def override_ad_group_settings(ad_group, updates):
    if ad_group.campaign.account.agency_id in constants.AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY:
        updates.update(constants.AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY[ad_group.campaign.account.agency_id])
    return updates


######################
# Campaign hacks
######################


def apply_campaign_create_hacks(request, campaign):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY:
        campaign.settings.update(
            request, **constants.CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY[campaign.account.agency_id]
        )
    if campaign.account.agency_id in constants.FIXED_CAMPAIGN_TYPE_PER_AGENCY:
        campaign.update_type(type=constants.FIXED_CAMPAIGN_TYPE_PER_AGENCY[campaign.account.agency_id])


def override_campaign_settings_form_data(campaign, form_data):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY:
        form_data.update(constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY[campaign.account.agency_id])
    return form_data


def override_campaign_settings(campaign, updates):
    if campaign.account.agency_id in constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY:
        updates.update(constants.CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY[campaign.account.agency_id])
    return updates


######################
# Account hacks
######################
def apply_account_create_hack(request, account):
    if account.agency_id == constants.AGENCY_QOOL_MEDIA:
        account_cf = account.custom_flags or dict()
        account_cf.update({constants.MSN_BLOCK_CF_ID: True})
        account.update(request, custom_flags=account_cf)
