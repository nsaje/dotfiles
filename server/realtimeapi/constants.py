from utils import constant_base


class ValidGroupByBreakdown(constant_base.ConstantBase):
    # ACCOUNT_ID = "account_id"
    CAMPAIGN_ID = "campaign_id"
    AD_GROUP_ID = "ad_group_id"
    CONTENT_AD_ID = "content_ad_id"

    _VALUES = {
        # ACCOUNT_ID: "Account Id",
        CAMPAIGN_ID: "Campaign Id",
        AD_GROUP_ID: "Ad Group Id",
        CONTENT_AD_ID: "Content Ad Id",
    }


class ValidTopNBreakdown(constant_base.ConstantBase):
    # ACCOUNT_ID = "account_id"
    CAMPAIGN_ID = "campaign_id"
    AD_GROUP_ID = "ad_group_id"
    CONTENT_AD_ID = "content_ad_id"
    MEDIA_SOURCE = "media_source"
    PUBLISHER = "publisher"

    _VALUES = {
        # ACCOUNT_ID: "Account Id",
        CAMPAIGN_ID: "Campaign Id",
        AD_GROUP_ID: "Ad Group Id",
        CONTENT_AD_ID: "Content Ad Id",
        MEDIA_SOURCE: "Media Source",
        PUBLISHER: "Publisher",
    }


class ValidOrder(constant_base.ConstantBase):
    SPEND = "spend"
    CLICKS = "clicks"
    IMPRESSIONS = "impressions"
    CTR = "ctr"
    CPC = "cpc"
    CPM = "cpm"

    _VALUES = {SPEND: "Spend", CLICKS: "Clicks", IMPRESSIONS: "Impressions", CTR: "CTR", CPC: "CPC", CPM: "CPM"}
