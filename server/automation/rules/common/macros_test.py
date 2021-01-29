import decimal
import textwrap

from django.test import TestCase
from mock import patch

import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from .. import constants
from .. import exceptions
from . import macros


class ValidateTestCase(TestCase):
    def test_fixed_window_macros(self):
        macros.validate("This is a macro test {ACCOUNT_NAME} ({ACCOUNT_ID})")
        with self.assertRaises(exceptions.InvalidMacros):
            macros.validate("This is a macro test {INVALID_MACRO}")
        with self.assertRaises(exceptions.InvalidMacros):
            macros.validate("This is a macro test {ACCOUNT_NAME ({ACCOUNT_ID}})")
        with self.assertRaises(exceptions.InvalidMacros):
            macros.validate("This is a macro test {ACCOUNT_NAME_LAST_30_DAYS}")

    def test_adjustable_window_macros(self):
        macros.validate("This is a macro test {TOTAL_SPEND_LAST_30_DAYS}")
        with self.assertRaises(exceptions.InvalidMacros):
            macros.validate("This is a macro test {TOTAL_SPEND}")
        with self.assertRaises(exceptions.InvalidMacros):
            macros.validate("This is a macro test {TOTAL_SPEND_LAST_30_DAYS {ACCOUNT_NAME}}")


class ExpandTestCase(TestCase):
    def setUp(self):
        patcher = patch("automation.autopilot_legacy.recalculate_budgets_ad_group")
        patcher.start()
        self.addCleanup(patcher.stop)

        today = dates_helper.local_today()
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account, agency=self.agency, currency=dash.constants.Currency.USD)
        self.credit = magic_mixer.blend(
            dash.models.CreditLineItem,
            account=self.account,
            start_date=today,
            end_date=dates_helper.day_after(today),
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=100000,
            license_fee=decimal.Decimal("0.1"),
        )
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        magic_mixer.blend(dash.models.CampaignGoal, campaign=self.campaign, primary=True)
        self.budget = magic_mixer.blend(
            dash.models.BudgetLineItem,
            campaign=self.campaign,
            credit=self.credit,
            start_date=today,
            end_date=dates_helper.day_after(today),
            amount=10000,
        )
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group_source = magic_mixer.blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source__source_type__type="b1"
        )
        self.ad_group_source.settings.update(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.ad_group.settings.update(
            None,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE,
            b1_sources_group_enabled=True,
            b1_sources_group_state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            b1_sources_group_daily_budget=500,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
        )
        self.content = textwrap.dedent(
            """\
            AGENCY_ID: {AGENCY_ID}
            AGENCY_NAME: {AGENCY_NAME}
            ACCOUNT_ID: {ACCOUNT_ID}
            ACCOUNT_NAME: {ACCOUNT_NAME}
            CAMPAIGN_ID: {CAMPAIGN_ID}
            CAMPAIGN_NAME: {CAMPAIGN_NAME}
            AD_GROUP_ID: {AD_GROUP_ID}
            AD_GROUP_NAME: {AD_GROUP_NAME}
            AD_GROUP_DAILY_CAP: {AD_GROUP_DAILY_CAP}
            CAMPAIGN_BUDGET: {CAMPAIGN_BUDGET}
            TOTAL_SPEND_LAST_30_DAYS: {TOTAL_SPEND_LAST_30_DAYS}
            CLICKS_LAST_30_DAYS: {CLICKS_LAST_30_DAYS}
            IMPRESSIONS_LAST_30_DAYS: {IMPRESSIONS_LAST_30_DAYS}
            AVG_CPC_LAST_30_DAYS: {AVG_CPC_LAST_30_DAYS}
            AVG_CPM_LAST_30_DAYS: {AVG_CPM_LAST_30_DAYS}
            VISITS_LAST_30_DAYS: {VISITS_LAST_30_DAYS}
            UNIQUE_USERS_LAST_30_DAYS: {UNIQUE_USERS_LAST_30_DAYS}
            NEW_USERS_LAST_30_DAYS: {NEW_USERS_LAST_30_DAYS}
            RETURNING_USERS_LAST_30_DAYS: {RETURNING_USERS_LAST_30_DAYS}
            PERCENT_NEW_USERS_LAST_30_DAYS: {PERCENT_NEW_USERS_LAST_30_DAYS}
            CLICK_DISCREPANCY_LAST_30_DAYS: {CLICK_DISCREPANCY_LAST_30_DAYS}
            PAGEVIEWS_LAST_30_DAYS: {PAGEVIEWS_LAST_30_DAYS}
            PAGEVIEWS_PER_VISIT_LAST_30_DAYS: {PAGEVIEWS_PER_VISIT_LAST_30_DAYS}
            BOUNCED_VISITS_LAST_30_DAYS: {BOUNCED_VISITS_LAST_30_DAYS}
            NON_BOUNCED_VISITS_LAST_30_DAYS: {NON_BOUNCED_VISITS_LAST_30_DAYS}
            BOUNCE_RATE_LAST_30_DAYS: {BOUNCE_RATE_LAST_30_DAYS}
            TOTAL_SECONDS_LAST_30_DAYS: {TOTAL_SECONDS_LAST_30_DAYS}
            AVG_TIME_ON_SITE_LAST_30_DAYS: {AVG_TIME_ON_SITE_LAST_30_DAYS}
            AVG_COST_PER_VISIT_LAST_30_DAYS: {AVG_COST_PER_VISIT_LAST_30_DAYS}
            AVG_COST_PER_NEW_VISITOR_LAST_30_DAYS: {AVG_COST_PER_NEW_VISITOR_LAST_30_DAYS}
            AVG_COST_PER_PAGEVIEW_LAST_30_DAYS: {AVG_COST_PER_PAGEVIEW_LAST_30_DAYS}
            AVG_COST_PER_NON_BOUNCED_VISIT_LAST_30_DAYS: {AVG_COST_PER_NON_BOUNCED_VISIT_LAST_30_DAYS}
            AVG_COST_PER_MINUTE_LAST_30_DAYS: {AVG_COST_PER_MINUTE_LAST_30_DAYS}
            AVG_COST_PER_UNIQUE_USER_LAST_30_DAYS: {AVG_COST_PER_UNIQUE_USER_LAST_30_DAYS}
            VIDEO_START_LAST_30_DAYS: {VIDEO_START_LAST_30_DAYS}
            VIDEO_FIRST_QUARTILE_LAST_30_DAYS: {VIDEO_FIRST_QUARTILE_LAST_30_DAYS}
            VIDEO_MIDPOINT_LAST_30_DAYS: {VIDEO_MIDPOINT_LAST_30_DAYS}
            VIDEO_THIRD_QUARTILE_LAST_30_DAYS: {VIDEO_THIRD_QUARTILE_LAST_30_DAYS}
            VIDEO_COMPLETE_LAST_30_DAYS: {VIDEO_COMPLETE_LAST_30_DAYS}
            AVG_CPV_LAST_30_DAYS: {AVG_CPV_LAST_30_DAYS}
            AVG_CPCV_LAST_30_DAYS: {AVG_CPCV_LAST_30_DAYS}
            VIDEO_START_PERCENT_LAST_30_DAYS: {VIDEO_START_PERCENT_LAST_30_DAYS}
            VIDEO_FIRST_QUARTILE_PERCENT_LAST_30_DAYS: {VIDEO_FIRST_QUARTILE_PERCENT_LAST_30_DAYS}
            VIDEO_MIDPOINT_PERCENT_LAST_30_DAYS: {VIDEO_MIDPOINT_PERCENT_LAST_30_DAYS}
            VIDEO_THIRD_QUARTILE_PERCENT_LAST_30_DAYS: {VIDEO_THIRD_QUARTILE_PERCENT_LAST_30_DAYS}
            VIDEO_COMPLETE_PERCENT_LAST_30_DAYS: {VIDEO_COMPLETE_PERCENT_LAST_30_DAYS}
            MRC50_MEASURABLE_LAST_30_DAYS: {MRC50_MEASURABLE_LAST_30_DAYS}
            MRC50_VIEWABLE_LAST_30_DAYS: {MRC50_VIEWABLE_LAST_30_DAYS}
            MRC50_MEASURABLE_PERCENT_LAST_30_DAYS: {MRC50_MEASURABLE_PERCENT_LAST_30_DAYS}
            MRC50_VIEWABLE_PERCENT_LAST_30_DAYS: {MRC50_VIEWABLE_PERCENT_LAST_30_DAYS}
            MRC50_VCPM_LAST_30_DAYS: {MRC50_VCPM_LAST_30_DAYS}"""
        )

        self.target_stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_30_DAYS: 20},
            "clicks": {constants.MetricWindow.LAST_30_DAYS: 2000},
            "impressions": {constants.MetricWindow.LAST_30_DAYS: 200000},
            "local_etfm_cpc": {constants.MetricWindow.LAST_30_DAYS: 0.5},
            "local_etfm_cpm": {constants.MetricWindow.LAST_30_DAYS: 0.7},
            "visits": {constants.MetricWindow.LAST_30_DAYS: 300},
            "unique_users": {constants.MetricWindow.LAST_30_DAYS: 202},
            "new_users": {constants.MetricWindow.LAST_30_DAYS: 15},
            "returning_users": {constants.MetricWindow.LAST_30_DAYS: 89},
            "percent_new_users": {constants.MetricWindow.LAST_30_DAYS: 0.75},
            "click_discrepancy": {constants.MetricWindow.LAST_30_DAYS: 0.17},
            "pageviews": {constants.MetricWindow.LAST_30_DAYS: 1231},
            "pv_per_visit": {constants.MetricWindow.LAST_30_DAYS: 5.2},
            "bounced_visits": {constants.MetricWindow.LAST_30_DAYS: 300},
            "non_bounced_visits": {constants.MetricWindow.LAST_30_DAYS: 55},
            "bounce_rate": {constants.MetricWindow.LAST_30_DAYS: 0.89},
            "total_seconds": {constants.MetricWindow.LAST_30_DAYS: 30200},
            "avg_tos": {constants.MetricWindow.LAST_30_DAYS: 25.2},
            "local_avg_etfm_cost_per_visit": {constants.MetricWindow.LAST_30_DAYS: 0.33},
            "local_avg_etfm_cost_per_new_visitor": {constants.MetricWindow.LAST_30_DAYS: 0.55},
            "local_avg_etfm_cost_per_pageview": {constants.MetricWindow.LAST_30_DAYS: 0.11},
            "local_avg_etfm_cost_per_non_bounced_visit": {constants.MetricWindow.LAST_30_DAYS: 0.44},
            "local_avg_etfm_cost_per_minute": {constants.MetricWindow.LAST_30_DAYS: 2.22},
            "local_avg_etfm_cost_per_unique_user": {constants.MetricWindow.LAST_30_DAYS: 8.12},
            "video_start": {constants.MetricWindow.LAST_30_DAYS: 31},
            "video_first_quartile": {constants.MetricWindow.LAST_30_DAYS: 32},
            "video_midpoint": {constants.MetricWindow.LAST_30_DAYS: 33},
            "video_third_quartile": {constants.MetricWindow.LAST_30_DAYS: 34},
            "video_complete": {constants.MetricWindow.LAST_30_DAYS: 35},
            "local_video_etfm_cpv": {constants.MetricWindow.LAST_30_DAYS: 36},
            "local_video_etfm_cpcv": {constants.MetricWindow.LAST_30_DAYS: 37},
            "video_start_percent": {constants.MetricWindow.LAST_30_DAYS: 38},
            "video_first_quartile_percent": {constants.MetricWindow.LAST_30_DAYS: 39},
            "video_midpoint_percent": {constants.MetricWindow.LAST_30_DAYS: 40},
            "video_third_quartile_percent": {constants.MetricWindow.LAST_30_DAYS: 41},
            "video_complete_percent": {constants.MetricWindow.LAST_30_DAYS: 42},
            "mrc50_measurable": {constants.MetricWindow.LAST_30_DAYS: 43},
            "mrc50_viewable": {constants.MetricWindow.LAST_30_DAYS: 44},
            "mrc50_measurable_percent": {constants.MetricWindow.LAST_30_DAYS: 45},
            "mrc50_viewable_percent": {constants.MetricWindow.LAST_30_DAYS: 46},
            "local_etfm_mrc50_vcpm": {constants.MetricWindow.LAST_30_DAYS: 47},
        }

    def test_expand_macros(self):
        expanded = macros.expand(self.content, self.ad_group, self.target_stats)
        expected = textwrap.dedent(
            f"""\
            AGENCY_ID: {self.agency.id}
            AGENCY_NAME: {self.agency.name}
            ACCOUNT_ID: {self.account.id}
            ACCOUNT_NAME: {self.account.name}
            CAMPAIGN_ID: {self.campaign.id}
            CAMPAIGN_NAME: {self.campaign.name}
            AD_GROUP_ID: {self.ad_group.id}
            AD_GROUP_NAME: {self.ad_group.name}
            AD_GROUP_DAILY_CAP: $500.00
            CAMPAIGN_BUDGET: $10,000.00
            TOTAL_SPEND_LAST_30_DAYS: $20.00
            CLICKS_LAST_30_DAYS: 2000
            IMPRESSIONS_LAST_30_DAYS: 200000
            AVG_CPC_LAST_30_DAYS: $0.50
            AVG_CPM_LAST_30_DAYS: $0.70
            VISITS_LAST_30_DAYS: 300
            UNIQUE_USERS_LAST_30_DAYS: 202
            NEW_USERS_LAST_30_DAYS: 15
            RETURNING_USERS_LAST_30_DAYS: 89
            PERCENT_NEW_USERS_LAST_30_DAYS: 0.75%
            CLICK_DISCREPANCY_LAST_30_DAYS: 0.17
            PAGEVIEWS_LAST_30_DAYS: 1231
            PAGEVIEWS_PER_VISIT_LAST_30_DAYS: 5.2
            BOUNCED_VISITS_LAST_30_DAYS: 300
            NON_BOUNCED_VISITS_LAST_30_DAYS: 55
            BOUNCE_RATE_LAST_30_DAYS: 0.89
            TOTAL_SECONDS_LAST_30_DAYS: 30200
            AVG_TIME_ON_SITE_LAST_30_DAYS: $25.20
            AVG_COST_PER_VISIT_LAST_30_DAYS: $0.33
            AVG_COST_PER_NEW_VISITOR_LAST_30_DAYS: $0.55
            AVG_COST_PER_PAGEVIEW_LAST_30_DAYS: $0.11
            AVG_COST_PER_NON_BOUNCED_VISIT_LAST_30_DAYS: $0.44
            AVG_COST_PER_MINUTE_LAST_30_DAYS: $2.22
            AVG_COST_PER_UNIQUE_USER_LAST_30_DAYS: $8.12
            VIDEO_START_LAST_30_DAYS: 31
            VIDEO_FIRST_QUARTILE_LAST_30_DAYS: 32
            VIDEO_MIDPOINT_LAST_30_DAYS: 33
            VIDEO_THIRD_QUARTILE_LAST_30_DAYS: 34
            VIDEO_COMPLETE_LAST_30_DAYS: 35
            AVG_CPV_LAST_30_DAYS: $36.00
            AVG_CPCV_LAST_30_DAYS: $37.00
            VIDEO_START_PERCENT_LAST_30_DAYS: 38
            VIDEO_FIRST_QUARTILE_PERCENT_LAST_30_DAYS: 39
            VIDEO_MIDPOINT_PERCENT_LAST_30_DAYS: 40
            VIDEO_THIRD_QUARTILE_PERCENT_LAST_30_DAYS: 41
            VIDEO_COMPLETE_PERCENT_LAST_30_DAYS: 42
            MRC50_MEASURABLE_LAST_30_DAYS: 43
            MRC50_VIEWABLE_LAST_30_DAYS: 44
            MRC50_MEASURABLE_PERCENT_LAST_30_DAYS: 45
            MRC50_VIEWABLE_PERCENT_LAST_30_DAYS: 46
            MRC50_VCPM_LAST_30_DAYS: $47.00"""
        )

        self.assertEqual(expected, expanded)
        self.assertTrue(all(macro in expanded for macro in constants.EmailActionMacro.get_all()))

    def test_missing_window(self):
        target_stats = {
            "local_etfm_cost": {constants.MetricWindow.LAST_30_DAYS: 20},
            "local_etfm_cpc": {constants.MetricWindow.LAST_30_DAYS: 0.5},
        }
        content = textwrap.dedent(
            """\
            TOTAL SPEND: {TOTAL_SPEND_LAST_7_DAYS}
            AVG CPC: {AVG_CPC_LAST_7_DAYS}"""
        )
        expected = textwrap.dedent(
            """\
            TOTAL SPEND: $0.00
            AVG CPC: N/A"""
        )
        expanded = macros.expand(content, self.ad_group, target_stats)
        self.assertEqual(expected, expanded)
