import os.path
from collections import OrderedDict

from django.conf import settings
from django.db.models import Case
from django.db.models import CharField
from django.db.models import F
from django.db.models import Value
from django.db.models import When
from django.db.models.functions import Coalesce

import core.features.goals
import core.features.videoassets
import core.models
import dash.constants
import dash.features.custom_hacks
import dash.features.geolocation
import dash.features.publisher_classification
from etl import redshift
from etl import s3


class RDSModelization(object):
    MODEL = None
    FIELDS = dict()
    BUCKET_NAME = "z1-rds-materialization"
    FOLDER = ""
    PK = "id"

    def __init__(self):
        self.rds_data = None
        self.file_name = "{}.csv".format(self.MODEL.__name__.lower())
        self.s3_path = os.path.join(self.FOLDER, self.file_name)

    @staticmethod
    def _get_constant_value(field, constant, output_field=CharField):
        return Case(
            *[When(**{field: i, "then": Value(constant.get_text(i))}) for i in constant._VALUES],
            output_field=output_field()
        )

    def _get_rds_queryset(self):
        qs = self.MODEL.objects.values(self.PK).annotate(
            **{k: F(v) if isinstance(v, str) else v for k, v in self.FIELDS.items()}
        )
        if hasattr(self, "EXCLUDE"):
            qs = qs.exclude(**self.EXCLUDE)
        if hasattr(self, "ORDER_BY"):
            qs = qs.order_by(*self.ORDER_BY)
        if hasattr(self, "DISTINCT"):
            qs = qs.distinct(*self.DISTINCT)
        return qs

    def _put_csv_to_s3(self):
        return s3.upload_csv_without_job(self.TABLE, self._data_generator, self.s3_path, self.BUCKET_NAME)

    def _data_generator(self):
        if not self.rds_data:
            self.rds_data = self._get_rds_queryset()
        columns = [self.PK] + list(self.FIELDS.keys())
        for elm in self.rds_data.iterator():
            yield [elm.get(col) for col in columns]

    def _load_csv_from_s3(self):
        redshift.refresh_materialized_rds_table(self.s3_path, self.TABLE, bucket_name=self.BUCKET_NAME)

    def extract_load_data(self):
        self._put_csv_to_s3()
        self._load_csv_from_s3()


class RDSAgency(RDSModelization):
    MODEL = core.models.Agency
    TABLE = "mv_rds_agency"
    FIELDS = OrderedDict(
        name="name",
        whitelabel="white_label__theme",
        default_account_type=RDSModelization._get_constant_value("default_account_type", dash.constants.AccountType),
        sales_representative="sales_representative__email",
        cs_representative="cs_representative__email",
        ob_sales_representative="ob_sales_representative__email",
        ob_account_manager="ob_account_manager__email",
    )


class RDSSource(RDSModelization):
    MODEL = core.models.Source
    TABLE = "mv_rds_source"
    FIELDS = OrderedDict(
        tracking_slug="tracking_slug",
        bidder_slug="bidder_slug",
        name="name",
        maintenance="maintenance",
        deprecated="deprecated",
        released="released",
        supports_retargeting="supports_retargeting",
        impression_trackers_count="impression_trackers_count",
        content_ad_submission_policy=RDSModelization._get_constant_value(
            "content_ad_submission_policy", dash.constants.SourceSubmissionPolicy
        ),
        content_ad_submission_type=RDSModelization._get_constant_value(
            "content_ad_submission_type", dash.constants.SourceSubmissionType
        ),
        source_type="source_type__type",
    )


class RDSAccount(RDSModelization):
    MODEL = core.models.Account
    TABLE = "mv_rds_account"
    FIELDS = OrderedDict(
        name="name",
        auto_archiving_enabled="auto_archiving_enabled",
        currency="currency",
        agency_id="agency",
        account_sales_representative="settings__default_sales_representative__email",
        account_account_manager="settings__default_account_manager__email",
        account_cs_representative="settings__default_cs_representative__email",
        ob_sales_representative="settings__ob_sales_representative__email",
        account_ob_account_manager="settings__ob_account_manager__email",
        archived="settings__archived",
        account_type=RDSModelization._get_constant_value("settings__account_type", dash.constants.AccountType),
        whitelist_publisher_groups="settings__whitelist_publisher_groups",
        blacklist_publisher_groups="settings__blacklist_publisher_groups",
    )


class RDSCampaign(RDSModelization):
    MODEL = core.models.Campaign
    TABLE = "mv_rds_campaign"
    FIELDS = OrderedDict(
        name="name",
        type=RDSModelization._get_constant_value("type", dash.constants.CampaignType),
        account_id="account__id",
        real_time_campaign_stop="real_time_campaign_stop",
        campaign_manager="settings__campaign_manager__email",
        language=RDSModelization._get_constant_value("settings__language", dash.constants.Language),
        iab_category=RDSModelization._get_constant_value("settings__iab_category", dash.constants.IABCategory),
        campaign_promotion_goal=RDSModelization._get_constant_value(
            "settings__promotion_goal", dash.constants.PromotionGoal
        ),
        campaign_goal=RDSModelization._get_constant_value("settings__campaign_goal", dash.constants.CampaignGoal),
        goal_quantity="settings__goal_quantity",
        target_devices="settings__target_devices",
        target_environments="settings__target_environments",
        target_os="settings__target_os",
        target_regions="settings__target_regions",
        exclusion_target_regions="settings__exclusion_target_regions",
        whitelist_publisher_groups="settings__whitelist_publisher_groups",
        blacklist_publisher_groups="settings__blacklist_publisher_groups",
        automatic_campaign_stop="settings__automatic_campaign_stop",
        landing_mode="settings__landing_mode",
        autopilot="settings__autopilot",
        enable_ga_tracking="settings__enable_ga_tracking",
        ga_tracking_type=RDSModelization._get_constant_value(
            "settings__ga_tracking_type", dash.constants.GATrackingType
        ),
        enable_adobe_tracking="settings__enable_adobe_tracking",
        archived="settings__archived",
    )


class RDSCampaignGoal(RDSModelization):
    MODEL = core.features.goals.CampaignGoalValue
    TABLE = "mv_rds_campaign_goal"
    PK = "campaign_goal_id"
    FIELDS = OrderedDict(
        campaign_id="campaign_goal__campaign_id",
        campaign_goal_type=RDSModelization._get_constant_value("campaign_goal__type", dash.constants.CampaignGoalKPI),
        campaign_goal_primary="campaign_goal__primary",
        conversion_goal_id="campaign_goal__conversion_goal__id",
        conversion_goal_pixel_slug="campaign_goal__conversion_goal__pixel__slug",
        impressions="campaign_goal__conversion_goal__pixel__impressions",
        value="value",
    )
    ORDER_BY = ["campaign_goal", "created_dt"]
    DISTINCT = ["campaign_goal"]


class RDSContentAd(RDSModelization):
    MODEL = core.models.ContentAd
    TABLE = "mv_rds_content_ad"
    FIELDS = OrderedDict(
        ad_group_id="ad_group__id",
        archived="archived",
        amplify_review="amplify_review",
        label="label",
        url="url",
        title="title",
        display_url="display_url",
        brand_name="brand_name",
        description="description",
        call_to_action="call_to_action",
        image_id="image_id",
        image_width="image_width",
        image_height="image_height",
        image_hash="image_hash",
        crop_areas="crop_areas",
        image_crop="image_crop",
        state="state",
        tracker_urls="tracker_urls",
        additional_data="additional_data",
        video_asset_id="video_asset__id",
        video_status=RDSModelization._get_constant_value(
            "video_asset__status", core.features.videoassets.constants.VideoAssetStatus
        ),
        video_name="video_asset__name",
        video_duration="video_asset__duration",
        video_formats="video_asset__formats",
        video_type=RDSModelization._get_constant_value(
            "video_asset__type", core.features.videoassets.constants.VideoAssetType
        ),
        video_vast_url="video_asset__vast_url",
    )
    EXCLUDE = dict(ad_group__campaign__account_id=settings.HARDCODED_ACCOUNT_ID_OEN)


class RDSAdGroup(RDSModelization):
    MODEL = core.models.AdGroup
    TABLE = "mv_rds_ad_group"
    FIELDS = OrderedDict(
        name="name",
        campaign_id="campaign_id",
        amplify_review="amplify_review",
        state="settings__state",
        cpc="settings__cpc",
        local_cpc="settings__local_cpc",
        daily_budget_cc="settings__daily_budget_cc",
        target_devices="settings__target_devices",
        target_environments="settings__target_environments",
        target_os="settings__target_os",
        target_browsers="settings__target_browsers",
        target_regions="settings__target_regions",
        exclusion_target_regions="settings__exclusion_target_regions",
        retargeting_ad_groups="settings__retargeting_ad_groups",
        exclusion_retargeting_ad_groups="settings__exclusion_retargeting_ad_groups",
        bluekai_targeting="settings__bluekai_targeting",
        interest_targeting="settings__interest_targeting",
        exclusion_interest_targeting="settings__exclusion_interest_targeting",
        audience_targeting="settings__audience_targeting",
        exclusion_audience_targeting="settings__exclusion_audience_targeting",
        whitelist_publisher_groups="settings__whitelist_publisher_groups",
        blacklist_publisher_groups="settings__blacklist_publisher_groups",
        archived="settings__archived",
        autopilot_state="settings__autopilot_state",
        autopilot_daily_budget="settings__autopilot_daily_budget",
        local_autopilot_daily_budget="settings__local_autopilot_daily_budget",
        landing_mode="settings__landing_mode",
        b1_sources_group_enabled="settings__b1_sources_group_enabled",
        b1_sources_group_daily_budget="settings__b1_sources_group_daily_budget",
        local_b1_sources_group_daily_budget="settings__local_b1_sources_group_daily_budget",
        b1_sources_group_cpc_cc="settings__b1_sources_group_cpc_cc",
        local_b1_sources_group_cpc_cc="settings__local_b1_sources_group_cpc_cc",
        b1_sources_group_state="settings__b1_sources_group_state",
        cpm="settings__cpm",
        local_cpm="settings__local_cpm",
        delivery_type="settings__delivery_type",
        click_capping_daily_ad_group_max_clicks="settings__click_capping_daily_ad_group_max_clicks",
        click_capping_daily_click_budget="settings__click_capping_daily_click_budget",
        start_date="settings__start_date",
        end_date="settings__end_date",
        created_dt="created_dt",
    )


class RDSGeolocation(RDSModelization):
    MODEL = dash.features.geolocation.Geolocation
    TABLE = "mv_rds_geolocation"
    PK = "key"
    FIELDS = OrderedDict(
        type=RDSModelization._get_constant_value("type", dash.constants.LocationType),
        name="name",
        woeid="woeid",
        outbrain_id="outbrain_id",
        facebook_key="facebook_key",
    )


class RDSPublisherClassification(RDSModelization):
    MODEL = dash.features.publisher_classification.PublisherClassification
    TABLE = "mv_rds_publisher_classification"
    FIELDS = OrderedDict(
        publisher="publisher",
        category=RDSModelization._get_constant_value("category", dash.constants.InterestCategory),
        ignored="ignored",
    )


class RDSAgencyTag(RDSModelization):
    MODEL = core.models.EntityTag
    TABLE = "mv_rds_agency_tag"
    FIELDS = OrderedDict(agency="agency", name="name", slug="slug")
    EXCLUDE = dict(agency__isnull=True)


class RDSAccountTag(RDSModelization):
    MODEL = core.models.EntityTag
    TABLE = "mv_rds_account_tag"
    FIELDS = OrderedDict(account="account", name="name", slug="slug")
    EXCLUDE = dict(account__isnull=True)


class RDSCampaignTag(RDSModelization):
    MODEL = core.models.EntityTag
    TABLE = "mv_rds_campaign_tag"
    FIELDS = OrderedDict(campaign="campaign", name="name", slug="slug")
    EXCLUDE = dict(campaign__isnull=True)


class RDSAdgroupTag(RDSModelization):
    MODEL = core.models.EntityTag
    TABLE = "mv_rds_ad_group_tag"
    FIELDS = OrderedDict(adgroup="adgroup", name="name", slug="slug")
    EXCLUDE = dict(adgroup__isnull=True)


class RDSSourceTag(RDSModelization):
    MODEL = core.models.EntityTag
    TABLE = "mv_rds_source_tag"
    FIELDS = OrderedDict(source="source", name="name", slug="slug")
    EXCLUDE = dict(source__isnull=True)


class RDSCustomHack(RDSModelization):
    MODEL = dash.features.custom_hacks.CustomHack
    TABLE = "mv_rds_custom_hack"
    FIELDS = OrderedDict(
        agency_id="agency_id",
        account_id="account_id",
        campaign_id="campaign_id",
        ad_group_id="ad_group_id",
        source_id="source_id",
        rtb_only="rtb_only",
        summary="summary",
        service="service",
        trello_ticket_url="trello_ticket_url",
        created_dt="created_dt",
        removed_dt="removed_dt",
        confirmed_dt="confirmed_dt",
        client_id=Coalesce(
            "agency__id",
            "account__agency__id",
            "campaign__account__agency__id",
            "ad_group__campaign__account__agency__id",
            Value(0),
        ),
        client_name=Coalesce(
            "agency__name",
            "account__agency__name",
            "campaign__account__agency__name",
            "ad_group__campaign__account__agency__name",
            "account__name",
            "campaign__account__name",
            "ad_group__campaign__account__name",
        ),
    )


RDS_MATERIALIAZED_VIEW = [
    RDSAgency,
    RDSSource,
    RDSAccount,
    RDSCampaign,
    RDSCampaignGoal,
    RDSAdGroup,
    RDSContentAd,
    RDSGeolocation,
    RDSPublisherClassification,
    RDSAgencyTag,
    RDSAccountTag,
    RDSCampaignTag,
    RDSAdgroupTag,
    RDSSourceTag,
    RDSCustomHack,
]
