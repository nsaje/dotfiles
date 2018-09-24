import os.path
from collections import OrderedDict

from django.db.models import F, Value, Case, When, CharField

import dash.constants
import dash.models
from dash.features import videoassets
from etl import s3, redshift


class RDSModelization(object):
    MODEL = None
    FIELDS = dict()
    BUCKET_NAME = "prodops-test"
    FOLDER = "rds-materialization"

    def __init__(self):
        self.rds_data = None
        self.file_name = "{}.csv".format(self.MODEL.__name__.lower())
        self.s3_path = os.path.join(self.FOLDER, self.file_name)

    @staticmethod
    def get_constant_value(field, constant, output_field=CharField):
        return Case(
            *[When(**{field: i, "then": Value(constant.get_text(i))}) for i in constant._VALUES],
            output_field=output_field()
        )

    def _get_rds_queryset(self):
        return self.MODEL.objects.values("id").annotate(
            **{
                k if not isinstance(v, Case) else k: F(v) if not isinstance(v, Case) else v
                for k, v in self.FIELDS.items()
            }
        )

    def put_csv_to_s3(self):
        return s3.upload_csv_without_job(self.TABLE, self.data_generator, self.s3_path, self.BUCKET_NAME)

    def data_generator(self):
        if not self.rds_data:
            self.rds_data = self._get_rds_queryset()
        columns = ["id"] + list(self.FIELDS.keys())
        for l in self.rds_data:
            yield [l.get(col) for col in columns]

    def empty_table(self):
        redshift.truncate_table(self.TABLE)

    def load_csv_from_s3(self):
        redshift.refresh_materialized_rds_table(self.s3_path, self.TABLE, bucket_name=self.BUCKET_NAME)

    def extract_load_data(self):
        self.put_csv_to_s3()
        self.empty_table()
        self.load_csv_from_s3()


class RDSAgency(RDSModelization):
    MODEL = dash.models.Agency
    TABLE = "mv_rds_agency"
    FIELDS = OrderedDict(
        name="name",
        whitelabel=RDSModelization.get_constant_value("whitelabel", dash.constants.Whitelabel),
        default_account_type=RDSModelization.get_constant_value("default_account_type", dash.constants.AccountType),
        sales_representative="sales_representative__email",
        cs_representative="cs_representative__email",
        ob_representative="ob_representative__email",
    )


class RDSSource(RDSModelization):
    MODEL = dash.models.Source
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
        content_ad_submission_policy=RDSModelization.get_constant_value(
            "content_ad_submission_policy", dash.constants.SourceSubmissionPolicy
        ),
        content_ad_submission_type=RDSModelization.get_constant_value(
            "content_ad_submission_type", dash.constants.SourceSubmissionType
        ),
        source_type="source_type__type",
    )


class RDSAccount(RDSModelization):
    MODEL = dash.models.Account
    TABLE = "mv_rds_account"
    FIELDS = OrderedDict(
        name="name",
        auto_archiving_enabled="auto_archiving_enabled",
        currency="currency",
        yahoo_account_id="yahoo_account",
        agency_id="agency",
        account_sales_representative="settings__default_sales_representative__email",
        account_account_manager="settings__default_account_manager__email",
        account_cs_representative="settings__default_cs_representative__email",
        account_ob_representative="settings__ob_representative__email",
        archived="settings__archived",
        account_type=RDSModelization.get_constant_value("settings__account_type", dash.constants.AccountType),
    )


class RDSCampaign(RDSModelization):
    MODEL = dash.models.Campaign
    TABLE = "mv_rds_campaign"
    FIELDS = OrderedDict(
        name="name",
        type=RDSModelization.get_constant_value("type", dash.constants.CampaignType),
        account_id="account__id",
        real_time_campaign_stop="real_time_campaign_stop",
        campaign_manager="settings__campaign_manager__email",
        language=RDSModelization.get_constant_value("settings__language", dash.constants.Language),
        iab_category=RDSModelization.get_constant_value("settings__iab_category", dash.constants.IABCategory),
        campaign_promotion_goal=RDSModelization.get_constant_value(
            "settings__promotion_goal", dash.constants.PromotionGoal
        ),
        campaign_goal=RDSModelization.get_constant_value("settings__campaign_goal", dash.constants.CampaignGoal),
        goal_quantity="settings__goal_quantity",
        target_devices="settings__target_devices",
        target_placements="settings__target_placements",
        target_os="settings__target_os",
        target_region="settings__target_regions",
        exclusion_target_regions="settings__exclusion_target_regions",
        automatic_campaign_stop="settings__automatic_campaign_stop",
        landing_mode="settings__landing_mode",
        autopilot="settings__autopilot",
        enable_ga_tracking="settings__enable_ga_tracking",
        ga_tracking_type=RDSModelization.get_constant_value(
            "settings__ga_tracking_type", dash.constants.GATrackingType
        ),
        enable_adobe_tracking="settings__enable_adobe_tracking",
        archived="settings__archived",
    )


class RDSCampaignGoal(RDSModelization):
    MODEL = dash.models.CampaignGoal
    TABLE = "mv_rds_campaign_goal"
    FIELDS = OrderedDict(
        campaign_goal_type=RDSModelization.get_constant_value("type", dash.constants.CampaignGoalKPI),
        campaign_goal_primary="primary",
        conversion_goal_id="conversion_goal__id",
        conversion_goal_pixel_slug="conversion_goal__pixel__slug",
        impressions="conversion_goal__pixel__impressions",
    )


class RDSContentAd(RDSModelization):
    MODEL = dash.models.ContentAd
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
        video_status=RDSModelization.get_constant_value("video_asset__status", videoassets.constants.VideoAssetStatus),
        video_name="video_asset__name",
        video_duration="video_asset__duration",
        video_formats="video_asset__formats",
        video_type=RDSModelization.get_constant_value("video_asset__type", videoassets.constants.VideoAssetType),
        video_vast_url="video_asset__vast_url",
    )


class RDSAdGroup(RDSModelization):
    MODEL = dash.models.AdGroup
    TABLE = "mv_rds_ad_group"
    FIELDS = OrderedDict(
        campaign_id="campaign_id",
        amplify_review="amplify_review",
        state="settings__state",
        cpc_cc="settings__cpc_cc",
        local_cpc_cc="settings__local_cpc_cc",
        daily_budget_cc="settings__daily_budget_cc",
        target_devices="settings__target_devices",
        target_placements="settings__target_placements",
        target_os="settings__target_os",
        target_browsers="settings__target_browsers",
        exclusion_target_regions="settings__exclusion_target_regions",
        retargeting_ad_groups="settings__retargeting_ad_groups",
        exclusion_retargeting_ad_groups="settings__exclusion_retargeting_ad_groups",
        bluekai_targeting="settings__bluekai_targeting",
        interest_targeting="settings__interest_targeting",
        exclusion_interest_targeting="settings__exclusion_interest_targeting",
        audience_targeting="settings__audience_targeting",
        exclusion_audience_targeting="settings__exclusion_audience_targeting",
        archived="settings__archived",
        brand_name="settings__brand_name",
        call_to_action="settings__call_to_action",
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
        max_cpm="settings__max_cpm",
        local_max_cpm="settings__local_max_cpm",
        delivery_type="settings__delivery_type",
        click_capping_daily_ad_group_max_clicks="settings__click_capping_daily_ad_group_max_clicks",
        click_capping_daily_click_budget="settings__click_capping_daily_click_budget",
    )


RDS_MATERIALIAZED_VIEW = [RDSAgency, RDSSource, RDSAccount, RDSCampaign, RDSCampaignGoal, RDSContentAd, RDSAdGroup]
