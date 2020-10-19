from .mv_adgroup_placement import MVAdGroupPlacement
from .mv_conversions import MVConversions
from .mv_derived_view import AdGroupPlacementDerivedView
from .mv_derived_view import ConversionsDerivedView
from .mv_derived_view import MasterDerivedView
from .mv_derived_view import TouchpointConversionsDerivedView
from .mv_helpers_ad_group_structure import MVHelpersAdGroupStructure
from .mv_helpers_campaign_factors import MVHelpersCampaignFactors
from .mv_helpers_currency_exchange_rates import MVHelpersCurrencyExchangeRates
from .mv_helpers_source import MVHelpersSource
from .mv_master import MasterView
from .mv_touchpoint_conversions import MVTouchpointConversions

AD_BREAKDOWN = ["date", "source_id", "account_id", "campaign_id", "ad_group_id", "content_ad_id"]
AD_GROUP_BREAKDOWN = ["date", "source_id", "account_id", "campaign_id", "ad_group_id"]
CAMPAIGN_BREAKDOWN = ["date", "source_id", "account_id", "campaign_id"]
ACCOUNT_BREAKDOWN = ["date", "source_id", "account_id"]

AD_BREAKDOWN_INDEX = AD_BREAKDOWN[1:] + ["date"]
AD_GROUP_BREAKDOWN_INDEX = AD_GROUP_BREAKDOWN[1:] + ["date"]
CAMPAIGN_BREAKDOWN_INDEX = CAMPAIGN_BREAKDOWN[1:] + ["date"]
ACCOUNT_BREAKDOWN_INDEX = ACCOUNT_BREAKDOWN[1:] + ["date"]

MATERIALIZED_VIEWS = [
    # NOTE: Run "create_derived_view" command manually after adding a new derived view to this list.
    # Views that help construct master view
    MVHelpersSource,
    MVHelpersAdGroupStructure,
    MVHelpersCampaignFactors,
    MVHelpersCurrencyExchangeRates,
    # Must be done before master, it is used there to generate empty rows for conversions
    MVTouchpointConversions,
    # VIEW: Ad Group, TAB: Placement
    MVAdGroupPlacement,
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch_placement",
        breakdown=AD_GROUP_BREAKDOWN
        + ["publisher", "publisher_source_id", "placement_type", "placement"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_GROUP_BREAKDOWN
        + ["publisher_source_id", "placement_type", "placement"]
        + ["slug", "conversion_window", "conversion_label"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    # VIEW: Campaign, TAB: Placement
    AdGroupPlacementDerivedView.create(
        table_name="mv_campaign_placement",
        breakdown=CAMPAIGN_BREAKDOWN + ["publisher", "publisher_source_id", "placement_type", "placement"],
        sortkey=CAMPAIGN_BREAKDOWN + ["publisher_source_id", "placement_type", "placement"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch_placement",
        breakdown=CAMPAIGN_BREAKDOWN
        + ["publisher", "publisher_source_id", "placement_type", "placement"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=CAMPAIGN_BREAKDOWN
        + ["publisher_source_id", "placement_type", "placement"]
        + ["slug", "conversion_window", "conversion_label"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    # VIEW: Account, TAB: Placement
    AdGroupPlacementDerivedView.create(
        table_name="mv_account_placement",
        breakdown=ACCOUNT_BREAKDOWN + ["publisher", "publisher_source_id", "placement_type", "placement"],
        sortkey=ACCOUNT_BREAKDOWN + ["publisher_source_id", "placement_type", "placement"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch_placement",
        breakdown=ACCOUNT_BREAKDOWN
        + ["publisher", "publisher_source_id", "placement_type", "placement"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=ACCOUNT_BREAKDOWN
        + ["publisher_source_id", "placement_type", "placement"]
        + ["slug", "conversion_window", "conversion_label"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    # Master view
    MasterView,
    MVConversions,
    # VIEW: Ad Group, TAB: Ads
    MasterDerivedView.create(
        table_name="mv_contentad",
        breakdown=AD_BREAKDOWN,
        sortkey=AD_BREAKDOWN,
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    MasterDerivedView.create(
        table_name="mv_contentad_device",
        breakdown=AD_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        sortkey=AD_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    MasterDerivedView.create(
        table_name="mv_contentad_environment",
        breakdown=AD_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        sortkey=AD_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    MasterDerivedView.create(
        table_name="mv_contentad_geo",
        breakdown=AD_BREAKDOWN + ["country", "state", "dma"],
        sortkey=AD_BREAKDOWN + ["country", "state", "dma"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_contentad_conv",
        breakdown=AD_BREAKDOWN + ["slug"],
        sortkey=AD_BREAKDOWN + ["slug"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch",
        breakdown=AD_BREAKDOWN + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch_device",
        breakdown=AD_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch_environment",
        breakdown=AD_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_contentad_touch_geo",
        breakdown=AD_BREAKDOWN
        + ["country", "state", "dma"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        index=AD_BREAKDOWN_INDEX,
        distkey="content_ad_id",
    ),
    # VIEW: Ad Group, TAB: Sources
    # VIEW: Campaign, TAB: Ad Groups
    MasterDerivedView.create(
        table_name="mv_adgroup",
        breakdown=AD_GROUP_BREAKDOWN,
        sortkey=AD_GROUP_BREAKDOWN,
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    MasterDerivedView.create(
        table_name="mv_adgroup_device",
        breakdown=AD_GROUP_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        sortkey=AD_GROUP_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    MasterDerivedView.create(
        table_name="mv_adgroup_environment",
        breakdown=AD_GROUP_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        sortkey=AD_GROUP_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    MasterDerivedView.create(
        table_name="mv_adgroup_geo",
        breakdown=AD_GROUP_BREAKDOWN + ["country", "state", "dma"],
        sortkey=AD_GROUP_BREAKDOWN + ["country", "state", "dma"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_adgroup_conv",
        breakdown=AD_GROUP_BREAKDOWN + ["slug"],
        sortkey=AD_GROUP_BREAKDOWN + ["slug"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch",
        breakdown=AD_GROUP_BREAKDOWN + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_GROUP_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch_device",
        breakdown=AD_GROUP_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_GROUP_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch_environment",
        breakdown=AD_GROUP_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_GROUP_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_adgroup_touch_geo",
        breakdown=AD_GROUP_BREAKDOWN
        + ["country", "state", "dma"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=AD_GROUP_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    # VIEW: Campaign, TAB: Sources
    # VIEW: Account, TAB: Campaigns
    MasterDerivedView.create(
        table_name="mv_campaign",
        breakdown=CAMPAIGN_BREAKDOWN,
        sortkey=CAMPAIGN_BREAKDOWN,
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    MasterDerivedView.create(
        table_name="mv_campaign_device",
        breakdown=CAMPAIGN_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        sortkey=CAMPAIGN_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    MasterDerivedView.create(
        table_name="mv_campaign_environment",
        breakdown=CAMPAIGN_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        sortkey=CAMPAIGN_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    MasterDerivedView.create(
        table_name="mv_campaign_geo",
        breakdown=CAMPAIGN_BREAKDOWN + ["country", "state", "dma"],
        sortkey=CAMPAIGN_BREAKDOWN + ["country", "state", "dma"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_campaign_conv",
        breakdown=CAMPAIGN_BREAKDOWN + ["slug"],
        sortkey=CAMPAIGN_BREAKDOWN + ["slug"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch",
        breakdown=CAMPAIGN_BREAKDOWN + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=CAMPAIGN_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch_device",
        breakdown=CAMPAIGN_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=CAMPAIGN_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch_environment",
        breakdown=CAMPAIGN_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=CAMPAIGN_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_campaign_touch_geo",
        breakdown=CAMPAIGN_BREAKDOWN
        + ["country", "state", "dma"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=CAMPAIGN_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    # VIEW: Account, TAB: Sources
    # VIEW: All Accounts, TAB: Accounts
    # VIEW: All Accounts, TAB: Sources
    MasterDerivedView.create(
        table_name="mv_account",
        breakdown=ACCOUNT_BREAKDOWN,
        sortkey=ACCOUNT_BREAKDOWN,
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    MasterDerivedView.create(
        table_name="mv_account_device",
        breakdown=ACCOUNT_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        sortkey=ACCOUNT_BREAKDOWN + ["device_type", "device_os", "browser", "connection_type"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    MasterDerivedView.create(
        table_name="mv_account_environment",
        breakdown=ACCOUNT_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        sortkey=ACCOUNT_BREAKDOWN + ["environment", "zem_placement_type", "video_playback_method"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    MasterDerivedView.create(
        table_name="mv_account_geo",
        breakdown=ACCOUNT_BREAKDOWN + ["country", "state", "dma"],
        sortkey=ACCOUNT_BREAKDOWN + ["country", "state", "dma"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    ConversionsDerivedView.create(
        table_name="mv_account_conv",
        breakdown=ACCOUNT_BREAKDOWN + ["slug"],
        sortkey=ACCOUNT_BREAKDOWN + ["slug"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch",
        breakdown=ACCOUNT_BREAKDOWN + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=ACCOUNT_BREAKDOWN + ["slug", "conversion_window", "conversion_label"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch_device",
        breakdown=ACCOUNT_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=ACCOUNT_BREAKDOWN
        + ["device_type", "device_os", "browser", "connection_type"]
        + ["slug", "conversion_window", "conversion_label"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch_environment",
        breakdown=ACCOUNT_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=ACCOUNT_BREAKDOWN + ["environment"] + ["slug", "conversion_window", "conversion_label"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    TouchpointConversionsDerivedView.create(
        table_name="mv_account_touch_geo",
        breakdown=ACCOUNT_BREAKDOWN
        + ["country", "state", "dma"]
        + ["slug", "conversion_window", "conversion_label", "type"],
        sortkey=ACCOUNT_BREAKDOWN + ["country", "state", "dma"] + ["slug", "conversion_window", "conversion_label"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
    # View: Ad Group, Tab: Publishers
    MasterDerivedView.create(
        table_name="mv_adgroup_pubs",
        breakdown=AD_GROUP_BREAKDOWN + ["publisher", "publisher_source_id"],
        sortkey=AD_GROUP_BREAKDOWN + ["publisher_source_id"],
        index=AD_GROUP_BREAKDOWN_INDEX,
        distkey="ad_group_id",
    ),
    # View: Campaign, Tab: Publishers
    MasterDerivedView.create(
        table_name="mv_campaign_pubs",
        breakdown=CAMPAIGN_BREAKDOWN + ["publisher", "publisher_source_id"],
        sortkey=CAMPAIGN_BREAKDOWN + ["publisher_source_id"],
        index=CAMPAIGN_BREAKDOWN_INDEX,
        distkey="campaign_id",
    ),
    # View: Account: Tab: Publishers
    # View: All Accounts: Tab: Publishers
    MasterDerivedView.create(
        table_name="mv_account_pubs",
        breakdown=ACCOUNT_BREAKDOWN + ["publisher", "publisher_source_id"],
        sortkey=ACCOUNT_BREAKDOWN + ["publisher_source_id"],
        index=ACCOUNT_BREAKDOWN_INDEX,
        distkey="account_id",
    ),
]
