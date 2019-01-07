import datetime
import json
from decimal import Decimal

import unicodecsv as csv
from django import test
from mock import patch

import core.features.bcm
import core.features.goals.campaign_goal
import core.models
import core.models.settings
import zemauth.models
from analytics import demand_report
from automation import campaignstop
from automation.campaignstop import constants as campaignstop_constants
from dash import constants
from utils.magic_mixer import magic_mixer


def _repr_bool_normalized_value(val):
    return demand_report._bool_repr(demand_report._normalize_value(val))


def _create_daily_budget_statements(budget, dates, **kwargs):
    create_kwargs = {
        "media_spend_nano": 25000000000,
        "data_spend_nano": 25000000000,
        "license_fee_nano": 25000000000,
        "margin_nano": 25000000000,
    }
    create_kwargs.update(**kwargs)

    for date in dates:
        magic_mixer.blend(core.features.bcm.BudgetDailyStatement, budget=budget, date=date, **create_kwargs)


class DemandReportTestCase(test.TestCase):
    def _assert_row_data(
        self,
        ad_group,
        row,
        whitelist_publisher_groups="FALSE",
        blacklist_publisher_groups="FALSE",
        impressions="0",
        clicks="0",
        spend="0",
        calculated_daily_budget="0",
        calculated_cpc="0",
        target_regions=None,
        world_region="N/A",
        geo_targeting_type=None,
    ):

        target_regions = target_regions or []
        geo_targeting_type = geo_targeting_type or []

        checks = {
            "date": (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
            "agency_id": ad_group.campaign.account.agency.id,
            "agency_name": ad_group.campaign.account.agency.name,
            "agency_created_dt": ad_group.campaign.account.agency.created_dt,
            "account_id": ad_group.campaign.account.id,
            "account_name": ad_group.campaign.account.name,
            "account_created_dt": ad_group.campaign.account.created_dt,
            "account_type": ad_group.campaign.account.settings.account_type,
            "campaign_id": ad_group.campaign.id,
            "campaign_name": ad_group.campaign.name,
            "campaign_created_dt": ad_group.campaign.created_dt,
            "type": constants.CampaignType.get_name(ad_group.campaign.type),
            "adgroup_id": ad_group.id,
            "adgroup_name": ad_group.name,
            "adgroup_created_dt": ad_group.created_dt,
            "whitelabel": ad_group.campaign.account.agency.whitelabel,
            "whitelist_publisher_groups": whitelist_publisher_groups,
            "blacklist_publisher_groups": blacklist_publisher_groups,
            "real_time_campaign_stop": demand_report._bool_repr(ad_group.campaign.real_time_campaign_stop),
            "currency": ad_group.campaign.account.currency,
            "auto_add_new_sources": demand_report._bool_repr(ad_group.campaign.account.settings.auto_add_new_sources),
            "iab_category": ad_group.campaign.settings.iab_category,
            "automatic_campaign_stop": demand_report._bool_repr(ad_group.campaign.settings.automatic_campaign_stop),
            "enable_adobe_tracking": demand_report._bool_repr(ad_group.campaign.settings.enable_adobe_tracking),
            "enable_ga_tracking": demand_report._bool_repr(ad_group.campaign.settings.enable_ga_tracking),
            "ga_tracking_type": ad_group.campaign.settings.ga_tracking_type,
            "language": ad_group.campaign.settings.language,
            "autopilot": demand_report._bool_repr(ad_group.campaign.settings.autopilot),
            "impressions": impressions,
            "clicks": clicks,
            "spend": spend,
            "calculated_daily_budget": calculated_daily_budget,
            "calculated_cpc": calculated_cpc,
            "start_date": ad_group.settings.start_date,
            "end_date": ad_group.settings.end_date,
            "cpc_cc": ad_group.settings.cpc_cc,
            "target_devices": ad_group.settings.target_devices,
            "target_regions": target_regions,
            "world_region": world_region,
            "geo_targeting_type": geo_targeting_type,
            "autopilot_daily_budget": ad_group.settings.autopilot_daily_budget,
            "autopilot_state": ad_group.settings.autopilot_state,
            "retargeting_ad_groups": _repr_bool_normalized_value(ad_group.settings.retargeting_ad_groups),
            "exclusion_retargeting_ad_groups": _repr_bool_normalized_value(
                ad_group.settings.exclusion_retargeting_ad_groups
            ),
            "bluekai_targeting": _repr_bool_normalized_value(ad_group.settings.bluekai_targeting),
            "exclusion_interest_targeting": _repr_bool_normalized_value(ad_group.settings.exclusion_interest_targeting),
            "interest_targeting": _repr_bool_normalized_value(ad_group.settings.interest_targeting),
            "audience_targeting": _repr_bool_normalized_value(ad_group.settings.audience_targeting),
            "exclusion_audience_targeting": _repr_bool_normalized_value(ad_group.settings.exclusion_audience_targeting),
            "b1_sources_group_daily_budget": ad_group.settings.b1_sources_group_daily_budget,
            "b1_sources_group_enabled": demand_report._bool_repr(ad_group.settings.b1_sources_group_enabled),
            "b1_sources_group_state": ad_group.settings.b1_sources_group_state,
            "dayparting": _repr_bool_normalized_value(json.dumps(ad_group.settings.dayparting)),
            "b1_sources_group_cpc_cc": ad_group.settings.b1_sources_group_cpc_cc,
            "exclusion_target_regions": _repr_bool_normalized_value(ad_group.settings.exclusion_target_regions),
            "target_os": _repr_bool_normalized_value(ad_group.settings.target_os),
            "target_placements": demand_report._normalize_array_value(ad_group.settings.target_placements),
            "delivery_type": ad_group.settings.delivery_type,
            "click_capping_daily_ad_group_max_clicks": ad_group.settings.click_capping_daily_ad_group_max_clicks,
            "b1_sources_group_cpm": ad_group.settings.b1_sources_group_cpm,
            "modified_by_id": ad_group.campaign.modified_by_id,
            "sales_representative_id": ad_group.campaign.account.agency.sales_representative_id,
            "cs_representative_id": ad_group.campaign.account.agency.cs_representative_id,
            "sales_email": ad_group.campaign.account.agency.sales_representative.email,
            "cs_email": ad_group.campaign.account.agency.cs_representative.email,
            "frequency_capping": demand_report._bool_repr(ad_group.campaign.account.settings.frequency_capping),
        }

        for column, value in checks.items():
            if isinstance(value, Decimal):
                actual = Decimal(row[column])
                expected = value
            elif isinstance(value, list):
                actual = set(row[column].split(","))
                expected = set(value)
            else:
                actual = row[column]
                expected = str(value) if value is not None else ""

            self.assertEqual(actual, expected, msg=column)

    def setUp(self):
        self._create_entities()

    @patch("automation.autopilot.recalculate_budgets_ad_group")
    def _create_entities(self, mock_autopilot):
        self.source_type_outbrain = magic_mixer.blend(core.models.SourceType, type=constants.SourceType.OUTBRAIN)
        self.source_type_yahoo = magic_mixer.blend(core.models.SourceType, type=constants.SourceType.YAHOO)
        self.source_outbrain = magic_mixer.blend(core.models.Source, source_type=self.source_type_outbrain)
        self.source_yahoo = magic_mixer.blend(core.models.Source, source_type=self.source_type_yahoo)

        self.user_1 = magic_mixer.blend(zemauth.models.User)
        self.user_2 = magic_mixer.blend(zemauth.models.User)

        self.agency_1 = magic_mixer.blend(
            core.models.Agency, sales_representative=self.user_1, cs_representative=self.user_2
        )
        self.agency_1.settings.update(None, whitelist_publisher_groups=[], blacklist_publisher_groups=[1, 2, 3])

        self.account_1 = magic_mixer.blend(core.models.Account, agency=self.agency_1)
        self.account_1.settings.update(
            None,
            account_type=constants.AccountType.ACTIVATED,
            blacklist_publisher_groups=[],
            whitelist_publisher_groups=[],
            auto_add_new_sources=False,
            frequency_capping=7,
            archived=False,
        )

        self.campaign_1 = magic_mixer.blend(core.models.Campaign, account=self.account_1)
        self.campaign_1.settings.update(
            None,
            iab_category=constants.IABCategory.IAB1_2,
            automatic_campaign_stop=False,
            enable_adobe_tracking=True,
            enable_ga_tracking=True,
            ga_tracking_type=constants.GATrackingType.EMAIL,
            autopilot=False,
            frequency_capping=5,
            archived=False,
        )

        self.campaign_2 = magic_mixer.blend(core.models.Campaign, account=self.account_1)
        self.campaign_2.settings.update(
            None,
            iab_category=constants.IABCategory.IAB2_8,
            automatic_campaign_stop=False,
            enable_adobe_tracking=True,
            enable_ga_tracking=True,
            ga_tracking_type=constants.GATrackingType.EMAIL,
            autopilot=False,
            frequency_capping=5,
            archived=False,
        )

        self.campaign_stop_state = magic_mixer.blend(
            campaignstop.CampaignStopState,
            campaign=self.campaign_1,
            state=campaignstop_constants.CampaignStopState.ACTIVE,
        )

        self.goal_1 = core.features.goals.campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=self.campaign_1, type=constants.CampaignGoalKPI.TIME_ON_SITE, primary=True
        )

        self.goal_2 = core.features.goals.campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=self.campaign_2, type=constants.CampaignGoalKPI.CPA, primary=True
        )

        self.start_date = datetime.date.today() - datetime.timedelta(days=3)
        self.end_date = datetime.date.today() + datetime.timedelta(days=5)

        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account_id=self.account_1.id,
            status=constants.CreditLineItemStatus.SIGNED,
            start_date=self.start_date,
            end_date=self.end_date,
            amount=100000,
        )
        self.budget_1_1 = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign_1, credit=self.credit, amount=450, start_date=self.start_date, end_date=self.end_date
        )

        self.ad_group_1_1 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign_1)
        self.ad_group_1_1.settings.update(
            None,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_budget=Decimal("1000.0"),
            b1_sources_group_daily_budget=Decimal("1000.0"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
            autopilot_daily_budget=Decimal("1000.0"),
        )

        self.ad_group_source_1_1_1 = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group_1_1)
        self.ad_group_source_1_1_1.settings.update_unsafe(
            None,
            state=constants.AdGroupSourceSettingsState.ACTIVE,
            cpc_cc=Decimal("2.3"),
            daily_budget_cc=Decimal("1000.0"),
        )

        self.ad_group_1_2 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign_1)
        self.ad_group_1_2.settings.update(
            None,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_budget=Decimal("5000.0"),
            b1_sources_group_daily_budget=Decimal("5000.0"),
            autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
            autopilot_daily_budget=Decimal("5000.0"),
        )

        self.ad_group_source_1_2_1 = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group_1_2)
        self.ad_group_source_1_2_1.settings.update_unsafe(
            None,
            state=constants.AdGroupSourceSettingsState.ACTIVE,
            cpc_cc=Decimal("7.5"),
            daily_budget_cc=Decimal("2000.0"),
        )

        self.ad_group_source_1_2_2 = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group_1_2)
        self.ad_group_source_1_2_2.settings.update_unsafe(
            None,
            state=constants.AdGroupSourceSettingsState.ACTIVE,
            cpc_cc=Decimal("10.0"),
            daily_budget_cc=Decimal("3000.0"),
        )

        _create_daily_budget_statements(
            self.budget_1_1, [datetime.date.today() - datetime.timedelta(days=n) for n in range(4)]
        )

        self.budget_2_1 = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign_2,
            credit=self.credit,
            amount=1000,
            start_date=self.start_date,
            end_date=self.end_date,
        )

        self.ad_group_2_1 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign_2)
        self.ad_group_2_1.settings.update(
            None,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_budget=Decimal("100.0"),
            autopilot_daily_budget=Decimal("100.0"),
        )

        self.ad_group_source_2_1_1 = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group_2_1)
        self.ad_group_source_2_1_1.settings.update_unsafe(
            None,
            state=constants.AdGroupSourceSettingsState.ACTIVE,
            cpc_cc=Decimal("0.2"),
            daily_budget_cc=Decimal("100.0"),
        )

        self.ad_group_2_2 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign_2)
        self.ad_group_2_2.settings.update(
            None,
            archived=False,
            state=constants.AdGroupSettingsState.ACTIVE,
            start_date=self.start_date,
            end_date=self.end_date,
            daily_budget=Decimal("50.0"),
            autopilot_daily_budget=Decimal("50.0"),
        )

        self.ad_group_source_2_2_1 = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group_2_2)
        self.ad_group_source_2_2_1.settings.update_unsafe(
            None,
            state=constants.AdGroupSourceSettingsState.ACTIVE,
            cpc_cc=Decimal("0.5"),
            daily_budget_cc=Decimal("20.0"),
        )

        self.ad_group_source_2_2_2 = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group_2_2)
        self.ad_group_source_2_2_2.settings.update_unsafe(
            None,
            state=constants.AdGroupSourceSettingsState.ACTIVE,
            cpc_cc=Decimal("1.0"),
            daily_budget_cc=Decimal("30.0"),
        )

        _create_daily_budget_statements(
            self.budget_2_1, [datetime.date.today() - datetime.timedelta(days=n) for n in range(4)]
        )

    @patch("analytics.demand_report._get_ad_group_spend")
    @patch("utils.bigquery_helper.query")
    @patch("utils.bigquery_helper.upload_csv_file")
    @patch("redshiftapi.db.get_stats_cursor")
    def test_create_report(self, mock_db, mock_upload, mock_query, mock_spend):
        spend_rows = [
            [self.ad_group_1_1.id, 318199, 75, 143754891637],
            [self.ad_group_1_2.id, 405265, 407, 152348436441],
            [self.ad_group_2_1.id, 308172, 75, 143785991637],
            # no spend for ad_group_2_2
        ]
        columns = ["ad_group_id", "impressions", "clicks", "spend_nano"]

        mock_spend.return_value = [dict(zip(columns, row)) for row in spend_rows]

        with self.assertNumQueries(7):
            demand_report.create_report()

        calls = mock_upload.call_args_list
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertEqual(args[1], demand_report.DATASET_NAME)
        self.assertEqual(args[2], demand_report.TABLE_NAME)
        self.assertEqual(kwargs["timeout"], demand_report.BIGQUERY_TIMEOUT)
        self.assertEqual(kwargs["skip_leading_rows"], 1)

        csv_reader = csv.DictReader(args[0])

        rows = sorted([row for row in csv_reader], key=lambda x: int(x["adgroup_id"]))

        self.assertEqual(len(rows), 4)

        self._assert_row_data(
            self.ad_group_1_1,
            rows[0],
            blacklist_publisher_groups="TRUE",
            impressions="318199",
            clicks="75",
            spend="143.754891637",
            calculated_daily_budget="168.7548916369999858488881728",
            calculated_cpc="",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

        self._assert_row_data(
            self.ad_group_1_2,
            rows[1],
            blacklist_publisher_groups="TRUE",
            impressions="405265",
            clicks="407",
            spend="152.348436441",
            calculated_daily_budget="277.3484364409999898271053098",
            calculated_cpc="0.4500",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

        self._assert_row_data(
            self.ad_group_2_1,
            rows[2],
            blacklist_publisher_groups="TRUE",
            impressions="308172",
            clicks="75",
            spend="143.785991637",
            calculated_daily_budget="100.0000",
            calculated_cpc="",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

        self._assert_row_data(
            self.ad_group_2_2,
            rows[3],
            blacklist_publisher_groups="TRUE",
            impressions="0",
            clicks="0",
            spend="0",
            calculated_daily_budget="50.0000",
            calculated_cpc="",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

    @patch("analytics.demand_report._get_ad_group_spend")
    @patch("utils.bigquery_helper.query")
    @patch("utils.bigquery_helper.upload_csv_file")
    @patch("redshiftapi.db.get_stats_cursor")
    def test_create_report_missing_ad_group_ids(self, mock_db, mock_upload, mock_query, mock_spend):

        with patch("automation.autopilot.recalculate_budgets_ad_group"):
            self.ad_group_2_3 = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign_2)
            self.ad_group_2_3.settings.update(
                None,
                archived=True,
                state=constants.AdGroupSettingsState.INACTIVE,
                start_date=self.start_date,
                end_date=self.end_date,
                daily_budget=Decimal("10.0"),
                autopilot_daily_budget=Decimal("10.0"),
            )

            self.ad_group_source_2_3_1 = magic_mixer.blend(core.models.AdGroupSource, ad_group=self.ad_group_2_3)
            self.ad_group_source_2_3_1.settings.update_unsafe(
                None,
                state=constants.AdGroupSourceSettingsState.ACTIVE,
                cpc_cc=Decimal("1.0"),
                daily_budget_cc=Decimal("10.0"),
            )

        spend_rows = [
            [self.ad_group_1_1.id, 318199, 75, 143754891637],
            [self.ad_group_1_2.id, 405265, 407, 152348436441],
            [self.ad_group_2_1.id, 308172, 75, 143785991637],
            # no spend for ad_group_2_2
            [self.ad_group_2_3.id, 3, 1, 0],
        ]
        columns = ["ad_group_id", "impressions", "clicks", "spend_nano"]

        mock_spend.return_value = [dict(zip(columns, row)) for row in spend_rows]

        with self.assertNumQueries(13):
            demand_report.create_report()

        calls = mock_upload.call_args_list
        self.assertEqual(len(calls), 1)
        args, kwargs = calls[0]
        self.assertEqual(args[1], demand_report.DATASET_NAME)
        self.assertEqual(args[2], demand_report.TABLE_NAME)
        self.assertEqual(kwargs["timeout"], demand_report.BIGQUERY_TIMEOUT)
        self.assertEqual(kwargs["skip_leading_rows"], 1)

        csv_reader = csv.DictReader(args[0])

        rows = sorted([row for row in csv_reader], key=lambda x: int(x["adgroup_id"]))

        self.assertEqual(len(rows), 5)

        self._assert_row_data(
            self.ad_group_1_1,
            rows[0],
            blacklist_publisher_groups="TRUE",
            impressions="318199",
            clicks="75",
            spend="143.754891637",
            calculated_daily_budget="168.7548916369999858488881728",
            calculated_cpc="",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

        self._assert_row_data(
            self.ad_group_1_2,
            rows[1],
            blacklist_publisher_groups="TRUE",
            impressions="405265",
            clicks="407",
            spend="152.348436441",
            calculated_daily_budget="277.3484364409999898271053098",
            calculated_cpc="0.4500",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

        self._assert_row_data(
            self.ad_group_2_1,
            rows[2],
            blacklist_publisher_groups="TRUE",
            impressions="308172",
            clicks="75",
            spend="143.785991637",
            calculated_daily_budget="100.0000",
            calculated_cpc="",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

        self._assert_row_data(
            self.ad_group_2_2,
            rows[3],
            blacklist_publisher_groups="TRUE",
            impressions="0",
            clicks="0",
            spend="0",
            calculated_daily_budget="50.0000",
            calculated_cpc="",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )

        self._assert_row_data(
            self.ad_group_2_3,
            rows[4],
            blacklist_publisher_groups="TRUE",
            impressions="3",
            clicks="1",
            spend="0.0",
            calculated_daily_budget="10.0000",
            calculated_cpc="",
            target_regions=["US"],
            world_region="North America",
            geo_targeting_type=["country"],
        )


class BudgetDataTestCase(test.TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)

        self.credit = magic_mixer.blend(
            core.features.bcm.CreditLineItem,
            account=self.account,
            status=constants.CreditLineItemStatus.SIGNED,
            start_date=datetime.date.today() - datetime.timedelta(days=10),
            end_date=datetime.date.today() + datetime.timedelta(days=10),
            amount=100000,
        )

        self.campaign_1 = magic_mixer.blend(core.models.Campaign, account=self.account)

        self.budget_1_1 = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign_1,
            credit=self.credit,
            amount=420,
            start_date=datetime.date.today() - datetime.timedelta(days=4),
            end_date=datetime.date.today() - datetime.timedelta(days=1),
        )

        _create_daily_budget_statements(
            self.budget_1_1, [datetime.date.today() - datetime.timedelta(days=n) for n in range(1, 5)]
        )

        self.budget_1_2 = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign_1,
            credit=self.credit,
            amount=1000,
            start_date=datetime.date.today() - datetime.timedelta(days=2),
            end_date=datetime.date.today() + datetime.timedelta(days=2),
        )

        _create_daily_budget_statements(
            self.budget_1_2, [datetime.date.today() - datetime.timedelta(days=n) for n in range(3)]
        )

        self.campaign_2 = magic_mixer.blend(core.models.Campaign, account=self.account)

        self.budget_2_1 = core.features.bcm.BudgetLineItem.objects.create_unsafe(
            campaign=self.campaign_2,
            credit=self.credit,
            amount=500,
            start_date=datetime.date.today() - datetime.timedelta(days=2),
            end_date=datetime.date.today() + datetime.timedelta(days=1),
        )

        _create_daily_budget_statements(
            self.budget_2_1, [datetime.date.today() - datetime.timedelta(days=n) for n in range(3)]
        )

    def test_get_budget_data(self):
        budget_data = demand_report._get_budget_data([self.campaign_1.id, self.campaign_2.id])
        self.assertEqual(
            sorted(budget_data, key=lambda x: x["id"]),
            [
                {
                    "id": self.budget_1_1.id,
                    "amount": 420,
                    "campaign_id": self.campaign_1.id,
                    "spend_data_etfm_total": Decimal("400000000000"),
                },
                {
                    "id": self.budget_1_2.id,
                    "amount": 1000,
                    "campaign_id": self.campaign_1.id,
                    "spend_data_etfm_total": Decimal("200000000000"),
                },
                {
                    "id": self.budget_2_1.id,
                    "amount": 500,
                    "campaign_id": self.campaign_2.id,
                    "spend_data_etfm_total": Decimal("200000000000"),
                },
            ],
        )


class SourceIdMapTestCase(test.TestCase):
    def setUp(self):
        self.source_type_outbrain = magic_mixer.blend(core.models.SourceType, type=constants.SourceType.OUTBRAIN)
        self.source_type_yahoo = magic_mixer.blend(core.models.SourceType, type=constants.SourceType.YAHOO)
        self.source_outbrain = magic_mixer.blend(core.models.Source, source_type=self.source_type_outbrain)
        self.source_yahoo = magic_mixer.blend(core.models.Source, source_type=self.source_type_yahoo)

    def test_all(self):
        source_id_map = demand_report._source_id_map(constants.SourceType.OUTBRAIN, constants.SourceType.YAHOO)
        self.assertDictEqual(
            source_id_map,
            {constants.SourceType.OUTBRAIN: self.source_outbrain.id, constants.SourceType.YAHOO: self.source_yahoo.id},
        )

    def test_some(self):
        source_id_map = demand_report._source_id_map(constants.SourceType.OUTBRAIN)
        self.assertDictEqual(source_id_map, {constants.SourceType.OUTBRAIN: self.source_outbrain.id})

    def test_missing(self):
        with self.assertRaises(ValueError):
            demand_report._source_id_map(constants.SourceType.OUTBRAIN, constants.SourceType.YAHOO, "missing")
