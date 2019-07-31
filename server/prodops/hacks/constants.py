import dash.constants

AGENCY_RCS_ID = 220
AGENCY_NEWSCORP_ID = 86
AGENCY_MEDIAMOND_ID = 196
CPC_GOAL_TO_BID_AGENCIES = (AGENCY_RCS_ID, AGENCY_NEWSCORP_ID)

# Non NAS AGENCY
AGENCY_AMMET_ID = 289
AGENCY_ROI_MARKETPLACE_ID = 208
AGENCY_KONTENT_ROOM = 109


AD_GROUP_SETTINGS_CREATE_HACKS_PER_AGENCY = {
    AGENCY_RCS_ID: {
        "target_regions": ["IT"],
        "exclusion_target_regions": [],
        "delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED,
    },
    AGENCY_AMMET_ID: {"target_regions": ["AU"], "exclusion_target_regions": []},
    AGENCY_MEDIAMOND_ID: {"tracking_code": "utm_source=Mediamond&utm_medium=referral"},
    AGENCY_NEWSCORP_ID: {
        "delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED,
        "target_regions": ["AU"],
        "exclusion_target_regions": [],
    },
    AGENCY_ROI_MARKETPLACE_ID: {"target_regions": ["US"]},
}
AD_GROUP_SETTINGS_HACKS_UPDATE_PER_AGENCY = {
    AGENCY_RCS_ID: {"delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED},
    AGENCY_NEWSCORP_ID: {"delivery_type": dash.constants.AdGroupDeliveryType.ACCELERATED},
}

CAMPAIGN_SETTINGS_CREATE_HACKS_PER_AGENCY = {
    AGENCY_RCS_ID: {"language": "it", "autopilot": True},
    AGENCY_NEWSCORP_ID: {"language": "en", "autopilot": True},
    AGENCY_ROI_MARKETPLACE_ID: {"iab_category": dash.constants.IABCategory.IAB3_11},
    AGENCY_KONTENT_ROOM: {"iab_category": dash.constants.IABCategory.IAB3_11},
}

CAMPAIGN_SETTINGS_UPDATE_HACKS_PER_AGENCY = {
    AGENCY_RCS_ID: {"language": "it", "autopilot": True},
    AGENCY_NEWSCORP_ID: {"language": "en", "autopilot": True},
}

FIXED_CAMPAIGN_TYPE_PER_AGENCY = {
    AGENCY_RCS_ID: dash.constants.CampaignType.CONTENT,
    AGENCY_NEWSCORP_ID: dash.constants.CampaignType.CONTENT,
}
