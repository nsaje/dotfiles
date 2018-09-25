from .mv_master import MasterView
from .mv_master_spark import MasterSpark
from .mv_master_publishers import MasterPublishersView
from .mv_conversions import MVConversions
from .mv_touchpoint_conversions import MVTouchpointConversions
from .mv_derived_view import (
    MasterDerivedView,
    MasterPublishersDerivedView,
    ConversionsDerivedView,
    TouchpointConversionsDerivedView,
)
from .mv_helpers_ad_group_structure import MVHelpersAdGroupStructure
from .mv_helpers_campaign_factors import MVHelpersCampaignFactors
from .mv_helpers_currency_exchange_rates import MVHelpersCurrencyExchangeRates
from .mv_helpers_normalized_stats import MVHelpersNormalizedStats
from .mv_helpers_source import MVHelpersSource


AD_BREAKDOWN = ["date", "source_id", "account_id", "campaign_id", "ad_group_id", "content_ad_id"]
AD_GROUP_BREAKDOWN = ["date", "source_id", "account_id", "campaign_id", "ad_group_id"]
CAMPAIGN_BREAKDOWN = ["date", "source_id", "account_id", "campaign_id"]
ACCOUNT_BREAKDOWN = ["date", "source_id", "account_id"]

MATERIALIZED_VIEWS = [
    # Views that help construct master view
    MVHelpersSource,
    MVHelpersAdGroupStructure,
    MVHelpersCampaignFactors,
    MVHelpersCurrencyExchangeRates,
    MVHelpersNormalizedStats,
    # Must be done before master, it is used there to generate empty rows for conversions
    MVTouchpointConversions,
    MasterSpark,
    MasterPublishersView,
    MasterView,
    MVConversions,
    # VIEW: Ad Group, TAB: Ads
    MasterDerivedView.create(
        table_name="mv_contentad", breakdown=AD_BREAKDOWN, sortkey=AD_BREAKDOWN, distkey="content_ad_id"
    ),
    MasterDerivedView.create(
        table_name="mv_contentad_device",
        breakdown=AD_BREAKDOWN + ["device_type", "device_os"],
        sortkey=AD_BREAKDOWN + ["device_type", "device_os"],
        distkey="content_ad_id",
    ),
    MasterDerivedView.create(
        table_name="mv_contentad_placement",
        breakdown=AD_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        sortkey=AD_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        distkey="content_ad_id",
    ),
    MasterDerivedView.create(
        table_name="mv_contentad_geo",
        breakdown=AD_BREAKDOWN + ["country", "state", "dma"],
        sortkey=AD_BREAKDOWN + ["country", "state", "dma"],
        distkey="content_ad_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_contentad_conv",
        breakdown=AD_BREAKDOWN + ["slug"],
        sortkey=AD_BREAKDOWN + ["slug"],
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch",
        breakdown=AD_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch_device",
        breakdown=AD_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch_placement",
        breakdown=AD_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch_geo",
        breakdown=AD_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        distkey="content_ad_id",
    ),
    # VIEW: Ad Group, TAB: Sources
    # VIEW: Campaign, TAB: Ad Groups
    MasterDerivedView.create(
        table_name="mv_adgroup", breakdown=AD_GROUP_BREAKDOWN, sortkey=AD_GROUP_BREAKDOWN, distkey="ad_group_id"
    ),
    MasterDerivedView.create(
        table_name="mv_adgroup_device",
        breakdown=AD_GROUP_BREAKDOWN + ["device_type", "device_os"],
        sortkey=AD_GROUP_BREAKDOWN + ["device_type", "device_os"],
        distkey="ad_group_id",
    ),
    MasterDerivedView.create(
        table_name="mv_adgroup_placement",
        breakdown=AD_GROUP_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        sortkey=AD_GROUP_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        distkey="ad_group_id",
    ),
    MasterDerivedView.create(
        table_name="mv_adgroup_geo",
        breakdown=AD_GROUP_BREAKDOWN + ["country", "state", "dma"],
        sortkey=AD_GROUP_BREAKDOWN + ["country", "state", "dma"],
        distkey="ad_group_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_adgroup_conv",
        breakdown=AD_GROUP_BREAKDOWN + ["slug"],
        sortkey=AD_GROUP_BREAKDOWN + ["slug"],
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch",
        breakdown=AD_GROUP_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_GROUP_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch_device",
        breakdown=AD_GROUP_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_GROUP_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch_placement",
        breakdown=AD_GROUP_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_GROUP_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch_geo",
        breakdown=AD_GROUP_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=AD_GROUP_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        distkey="ad_group_id",
    ),
    # VIEW: Campaign, TAB: Sources
    # VIEW: Account, TAB: Campaigns
    MasterDerivedView.create(
        table_name="mv_campaign", breakdown=CAMPAIGN_BREAKDOWN, sortkey=CAMPAIGN_BREAKDOWN, distkey="campaign_id"
    ),
    MasterDerivedView.create(
        table_name="mv_campaign_device",
        breakdown=CAMPAIGN_BREAKDOWN + ["device_type", "device_os"],
        sortkey=CAMPAIGN_BREAKDOWN + ["device_type", "device_os"],
        distkey="campaign_id",
    ),
    MasterDerivedView.create(
        table_name="mv_campaign_placement",
        breakdown=CAMPAIGN_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        sortkey=CAMPAIGN_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        distkey="campaign_id",
    ),
    MasterDerivedView.create(
        table_name="mv_campaign_geo",
        breakdown=CAMPAIGN_BREAKDOWN + ["country", "state", "dma"],
        sortkey=CAMPAIGN_BREAKDOWN + ["country", "state", "dma"],
        distkey="campaign_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_campaign_conv",
        breakdown=CAMPAIGN_BREAKDOWN + ["slug"],
        sortkey=CAMPAIGN_BREAKDOWN + ["slug"],
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch",
        breakdown=CAMPAIGN_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        sortkey=CAMPAIGN_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch_device",
        breakdown=CAMPAIGN_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=CAMPAIGN_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch_placement",
        breakdown=CAMPAIGN_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=CAMPAIGN_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch_geo",
        breakdown=CAMPAIGN_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=CAMPAIGN_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        distkey="campaign_id",
    ),
    # VIEW: Account, TAB: Sources
    # VIEW: All Accounts, TAB: Accounts
    # VIEW: All Accounts, TAB: Sources
    MasterDerivedView.create(
        table_name="mv_account", breakdown=ACCOUNT_BREAKDOWN, sortkey=ACCOUNT_BREAKDOWN, distkey="account_id"
    ),
    MasterDerivedView.create(
        table_name="mv_account_device",
        breakdown=ACCOUNT_BREAKDOWN + ["device_type", "device_os"],
        sortkey=ACCOUNT_BREAKDOWN + ["device_type", "device_os"],
        distkey="account_id",
    ),
    MasterDerivedView.create(
        table_name="mv_account_placement",
        breakdown=ACCOUNT_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        sortkey=ACCOUNT_BREAKDOWN + ["placement_medium", "placement_type", "video_playback_method"],
        distkey="account_id",
    ),
    MasterDerivedView.create(
        table_name="mv_account_geo",
        breakdown=ACCOUNT_BREAKDOWN + ["country", "state", "dma"],
        sortkey=ACCOUNT_BREAKDOWN + ["country", "state", "dma"],
        distkey="account_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_account_conv",
        breakdown=ACCOUNT_BREAKDOWN + ["slug"],
        sortkey=ACCOUNT_BREAKDOWN + ["slug"],
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch",
        breakdown=ACCOUNT_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        sortkey=ACCOUNT_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch_device",
        breakdown=ACCOUNT_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=ACCOUNT_BREAKDOWN + ["device_type", "device_os"] + ["slug", "conversion_window", "conversion_label"],
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch_placement",
        breakdown=ACCOUNT_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=ACCOUNT_BREAKDOWN + ["placement_medium"] + ["slug", "conversion_window", "conversion_label"],
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch_geo",
        breakdown=ACCOUNT_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        sortkey=ACCOUNT_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        distkey="account_id",
    ),
    # View: Ad Group, Tab: Publishers
    MasterPublishersDerivedView.create(
        table_name="mv_adgroup_pubs",
        breakdown=AD_GROUP_BREAKDOWN + ["publisher", "publisher_source_id", "external_id"],
        sortkey=AD_GROUP_BREAKDOWN + ["publisher_source_id"],
        distkey="ad_group_id",
    ),
    # View: Campaign, Tab: Publishers
    MasterPublishersDerivedView.create(
        table_name="mv_campaign_pubs",
        breakdown=CAMPAIGN_BREAKDOWN + ["publisher", "publisher_source_id", "external_id"],
        sortkey=CAMPAIGN_BREAKDOWN + ["publisher_source_id"],
        distkey="campaign_id",
    ),
    # View: Account: Tab: Publishers
    # View: All Accounts: Tab: Publishers
    MasterPublishersDerivedView.create(
        table_name="mv_account_pubs",
        breakdown=ACCOUNT_BREAKDOWN + ["publisher", "publisher_source_id", "external_id"],
        sortkey=ACCOUNT_BREAKDOWN + ["publisher_source_id"],
        distkey="account_id",
    ),
]
