import datetime
import traceback
from collections import defaultdict
from decimal import Decimal
from unittest import mock

from django import test
from mock import call
from mock import patch

import dash.constants
import dash.models
from automation import models
from core.features.goals import campaign_goal
from utils import dates_helper
from utils import pagerduty_helper
from utils.magic_mixer import magic_mixer

from . import constants
from . import service


class AutopilotPlusTestCase(test.TestCase):
    fixtures = ["test_automation_legacy.yaml"]

    def mock_budget_recommender(
        self, ad_group, daily_budget, data, bcm, campaign_goal, ignore_daily_budget_too_small=False
    ):
        result = {}
        for ags in data:
            result[ags] = {"old_budget": Decimal("10.0"), "new_budget": Decimal("20.0"), "budget_comments": []}
        return result

    def mock_bid_recommender(self, ad_group, data, bcm, campaign_goal, budget_changes, adjust_rtb_sources):
        result = {}
        for ags in data:
            if ad_group.id != 3:
                self.assertEqual(
                    budget_changes.get(ags),
                    {"old_budget": Decimal("10.0"), "new_budget": Decimal("20.0"), "budget_comments": []},
                )
            result[ags] = {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2"), "bid_comments": []}
        return result

    def _update_call(self, ad_group, source, budget=True, bid=True, bidding_type=dash.constants.BiddingType.CPC):
        changes = {}
        if budget:
            changes["daily_budget_cc"] = Decimal("20.0")
        if bid and bidding_type == dash.constants.BiddingType.CPM:
            changes["cpm"] = Decimal("0.2")
        elif bid:
            changes["cpc_cc"] = Decimal("0.2")
        ad_group_source = dash.models.AdGroupSource.objects.get(ad_group_id=ad_group, source_id=source)
        return call(ad_group_source, changes, 2)

    def _update_allrtb_call(self, ad_group, budget=True, bid=True, bidding_type=dash.constants.BiddingType.CPC):
        changes = {}
        if budget:
            changes["daily_budget_cc"] = Decimal("20.0")
        if bid and bidding_type == dash.constants.BiddingType.CPM:
            changes["cpm"] = Decimal("0.2")
        elif bid:
            changes["cpc_cc"] = Decimal("0.2")
        return call(dash.models.AdGroup.objects.get(id=ad_group), changes, 2)

    def _email_changes(self, budgets=[], bid=[]):
        result = {}
        for campaign in dash.models.Campaign.objects.all():
            campaign_data = {}
            for ad_group in dash.models.AdGroup.objects.filter(campaign=campaign):
                ad_group_data = {}
                for ags in list(dash.models.AdGroupSource.objects.filter(ad_group=ad_group)) + [
                    dash.models.AllRTBAdGroupSource(ad_group)
                ]:
                    ags_data = {}
                    if ad_group.id in budgets:
                        ags_data.update(
                            {"old_budget": Decimal("10.0"), "new_budget": Decimal("20.0"), "budget_comments": []}
                        )
                    if ad_group.id in bid:
                        ags_data.update({"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2"), "bid_comments": []})
                    if ags_data:
                        ad_group_data[ags] = ags_data
                if ad_group_data:
                    campaign_data[ad_group] = ad_group_data
            if campaign_data:
                result[campaign] = campaign_data
        return result

    def _influx_input(self):
        entities = {
            campaign: {
                ad_group: list(
                    dash.models.AdGroupSource.objects.filter(ad_group=ad_group)
                    .filter(settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
                    .order_by("pk")
                )
                for ad_group in dash.models.AdGroup.objects.filter(campaign=campaign)
            }
            for campaign in dash.models.Campaign.objects.all()
        }
        campaign_daily_budgets = {dash.models.Campaign.objects.get(pk=2): Decimal("0")}
        return defaultdict(dict, entities), defaultdict(Decimal, campaign_daily_budgets)

    def assertLogExists(self, campaign=None, ad_group=None, source=None):
        ags = None
        if source is not None:
            ags = dash.models.AdGroupSource.objects.filter(ad_group_id=ad_group, source_id=source).first()
        models.AutopilotLog.objects.get(campaign_id=campaign, ad_group_id=ad_group, ad_group_source=ags)

    def setUp(self):
        dash.models.AdGroup.objects.get(pk=2).settings.update_unsafe(None, state=1)
        self.data = {
            ad_group: {
                ags: {"old_budget": Decimal("10.0")}
                for ags in (
                    list(dash.models.AdGroupSource.objects.filter(ad_group=ad_group))
                    + [dash.models.AllRTBAdGroupSource(ad_group)]
                )
            }
            for ad_group in dash.models.AdGroup.objects.all()
        }

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @patch(
        "django.utils.timezone.now",
        return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5),
    )
    @patch("automation.autopilot_legacy.service._report_new_budgets_on_ap_to_influx")
    @patch("automation.autopilot_legacy.service._report_adgroups_data_to_influx")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    @patch("automation.autopilot_legacy.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot_legacy.bid.get_autopilot_bid_recommendations")
    @patch("automation.autopilot_legacy.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_daily_run(
        self,
        mock_budgets,
        mock_bid,
        mock_prefetch,
        mock_update,
        mock_update_allrtb,
        mock_influx_adgroups,
        mock_influx_budgets,
        mock_timezone_now,
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_bid.side_effect = self.mock_bid_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        service.run_autopilot(daily_run=True, report_to_influx=True)

        self.assertCountEqual(
            mock_update.call_args_list,
            [
                self._update_call(ad_group=1, source=1),
                self._update_call(ad_group=2, source=1),
                self._update_call(ad_group=3, source=1, budget=False),
                self._update_call(ad_group=4, source=1),
                self._update_call(ad_group=4, source=2),
                self._update_call(ad_group=4, source=3),
                self._update_call(ad_group=4, source=4),
            ],
        )
        self.assertCountEqual(
            mock_update_allrtb.call_args_list,
            [
                self._update_allrtb_call(ad_group=1),
                self._update_allrtb_call(ad_group=2),
                self._update_allrtb_call(ad_group=3, budget=False),
                self._update_allrtb_call(ad_group=4),
            ],
        )
        self.assertLogExists(ad_group=1, source=1)
        self.assertLogExists(campaign=2, ad_group=2, source=1)
        self.assertLogExists(ad_group=3, source=1)
        self.assertLogExists(ad_group=4, source=1)
        self.assertLogExists(ad_group=4, source=2)
        self.assertLogExists(ad_group=4, source=3)
        self.assertLogExists(ad_group=4, source=4)
        self.assertLogExists(ad_group=1, source=None)
        self.assertLogExists(campaign=2, ad_group=2, source=None)
        self.assertLogExists(ad_group=3, source=None)
        self.assertLogExists(ad_group=4, source=None)
        mock_influx_adgroups.assert_called_once_with(*self._influx_input())
        mock_influx_budgets.assert_called_once_with(self._influx_input()[0])

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @patch(
        "django.utils.timezone.now",
        return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5),
    )
    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    @patch("automation.autopilot_legacy.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot_legacy.bid.get_autopilot_bid_recommendations")
    @patch("automation.autopilot_legacy.budgets.get_autopilot_daily_budget_recommendations")
    @patch("utils.slack.publish")
    def test_run_autopilot_daily_run_exceptions(
        self, mock_slack, mock_budgets, mock_bid, mock_prefetch, mock_update, mock_update_allrtb, mock_timezone_now
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_bid.side_effect = self.mock_bid_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        original_save_changes = service._save_changes
        original_get_budget_predictions_for_campaign = service._get_budget_predictions_for_campaign

        def _failing_save_changes(*args, **kwargs):
            ad_group = args[2]
            campaign = kwargs.get("campaign")

            if (campaign and campaign.id == 2) or (ad_group and ad_group.id == 4):
                raise Exception()
            else:
                return original_save_changes(*args, **kwargs)

        def _failing_get_budget_predictions_for_campaign(*args, **kwargs):
            campaign = args[0]

            if campaign and campaign.id == 2:
                raise Exception()
            else:
                return original_get_budget_predictions_for_campaign(*args, **kwargs)

        with patch("automation.autopilot_legacy.service._save_changes", side_effect=_failing_save_changes):
            with patch(
                "automation.autopilot_legacy.service._get_budget_predictions_for_campaign",
                side_effect=_failing_get_budget_predictions_for_campaign,
            ):
                service.run_autopilot(daily_run=True, report_to_influx=False)

        self.assertCountEqual(
            mock_update.call_args_list,
            [self._update_call(ad_group=1, source=1), self._update_call(ad_group=3, source=1, budget=False)],
        )
        self.assertCountEqual(
            mock_update_allrtb.call_args_list,
            [self._update_allrtb_call(ad_group=1), self._update_allrtb_call(ad_group=3, budget=False)],
        )
        self.assertLogExists(ad_group=1, source=1)
        self.assertLogExists(ad_group=3, source=1)
        self.assertLogExists(ad_group=1, source=None)
        self.assertLogExists(ad_group=3, source=None)

        mock_slack.assert_has_calls(
            [
                call(
                    "Autopilot run failed for the following campaigns:\n- <https://one.zemanta.com/v2/analytics/campaign/2/|Test Campaign 2>",
                    channel="rnd-z1-alerts-aux",
                    msg_type=":rage:",
                    username="Autopilot",
                ),
                call(
                    "Autopilot run failed for the following ad groups:\n- <https://one.zemanta.com/v2/analytics/adgroup/4/sources|Test AdGroup 4>",
                    channel="rnd-z1-alerts-aux",
                    msg_type=":rage:",
                    username="Autopilot",
                ),
            ]
        )

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @patch(
        "django.utils.timezone.now",
        return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5),
    )
    @patch(
        "utils.dates_helper.utc_now",
        return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5),
    )
    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    @patch("automation.autopilot_legacy.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot_legacy.bid.get_autopilot_bid_recommendations")
    @patch("automation.autopilot_legacy.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_daily_run_exclude_processed_entities(
        self, mock_budgets, mock_bid, mock_prefetch, mock_update, mock_update_allrtb, mock_utc_now, mock_timezone_now
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_bid.side_effect = self.mock_bid_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        models.AutopilotLog(
            campaign=dash.models.Campaign.objects.get(id=3),
            ad_group=dash.models.AdGroup.objects.get(id=3),
            is_autopilot_job_run=True,
        ).save()
        models.AutopilotLog(ad_group=dash.models.AdGroup.objects.get(id=4), is_autopilot_job_run=True).save()

        service.run_autopilot(daily_run=True, report_to_influx=False)

        self.assertCountEqual(
            mock_update.call_args_list,
            [self._update_call(ad_group=1, source=1), self._update_call(ad_group=2, source=1)],
        )
        self.assertCountEqual(
            mock_update_allrtb.call_args_list,
            [self._update_allrtb_call(ad_group=1), self._update_allrtb_call(ad_group=2)],
        )
        self.assertLogExists(ad_group=1, source=1)
        self.assertLogExists(campaign=2, ad_group=2, source=1)
        self.assertLogExists(ad_group=1, source=None)
        self.assertLogExists(campaign=2, ad_group=2, source=None)

    @patch("automation.autopilot_legacy.service.logger.info")
    def test_run_autopilot_daily_run_late_materialization(self, mock_logger_info):
        service.run_autopilot(daily_run=True, report_to_influx=False)
        mock_logger_info.assert_called_once_with(
            "Autopilot daily run was aborted since materialized data is not yet available."
        )

    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    @patch("automation.autopilot_legacy.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot_legacy.bid.get_autopilot_bid_recommendations")
    @patch("automation.autopilot_legacy.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_initialize_adgroup(
        self, mock_budgets, mock_bid, mock_prefetch, mock_update, mock_update_allrtb
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_bid.side_effect = self.mock_bid_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        ad_group = dash.models.AdGroup.objects.get(pk=4)
        service.run_autopilot(ad_group=ad_group, initialization=True, adjust_bids=False)

        self.assertCountEqual(
            mock_update.call_args_list,
            [
                self._update_call(ad_group=4, source=1, bid=False),
                self._update_call(ad_group=4, source=2, bid=False),
                self._update_call(ad_group=4, source=3, bid=False),
                self._update_call(ad_group=4, source=4, bid=False),
            ],
        )
        self.assertCountEqual(mock_update_allrtb.call_args_list, [self._update_allrtb_call(ad_group=4, bid=False)])
        self.assertLogExists(ad_group=4, source=1)
        self.assertLogExists(ad_group=4, source=2)
        self.assertLogExists(ad_group=4, source=3)
        self.assertLogExists(ad_group=4, source=4)
        self.assertLogExists(ad_group=4, source=None)

    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    @patch("automation.autopilot_legacy.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot_legacy.bid.get_autopilot_bid_recommendations")
    @patch("automation.autopilot_legacy.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_intialize_campaign(
        self, mock_budgets, mock_bid, mock_prefetch, mock_update, mock_update_allrtb
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_bid.side_effect = self.mock_bid_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        campaign = dash.models.Campaign.objects.get(pk=2)
        service.run_autopilot(campaign=campaign, initialization=True, adjust_bids=False)

        self.assertCountEqual(mock_update.call_args_list, [self._update_call(ad_group=2, source=1, bid=False)])
        self.assertCountEqual(mock_update_allrtb.call_args_list, [self._update_allrtb_call(ad_group=2, bid=False)])
        self.assertLogExists(campaign=2, ad_group=2, source=1)
        self.assertLogExists(campaign=2, ad_group=2, source=None)

    @patch("utils.pagerduty_helper.requests.post")
    @test.override_settings(
        HOSTNAME="testhost",
        PAGER_DUTY_ENABLED=True,
        PAGER_DUTY_URL="http://pagerduty.example.com",
        PAGER_DUTY_ENGINEERS_SERVICE_KEY="123abc",
    )
    def test_report_autopilot_exception(self, mock_urlopen):
        ad_group = dash.models.AdGroup.objects.get(id=1)
        ex = Exception()
        service._report_autopilot_exception(ad_group, ex)
        desc = "Autopilot failed operating on element because an exception was raised: {}".format(
            traceback.format_exc()
        )
        mock_urlopen.assert_called_with(
            "http://pagerduty.example.com",
            json={
                "routing_key": "123abc",
                "dedup_key": "automation_autopilot_legacy_error",
                "event_action": "trigger",
                "payload": {
                    "summary": desc,
                    "source": "Zemanta One - testhost",
                    "severity": pagerduty_helper.PagerDutyEventSeverity.CRITICAL,
                    "custom_details": {"element": ""},  # '<AdGroup: Test AdGroup 1>'
                },
            },
            timeout=60,
        )

    @patch("automation.autopilot_legacy.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot_legacy.helpers.get_autopilot_entities")
    @patch("automation.autopilot_legacy.helpers.get_active_ad_groups_on_autopilot")
    @patch("automation.autopilot_legacy.service._get_bid_predictions")
    @patch("automation.autopilot_legacy.service._get_budget_predictions_for_adgroup")
    @patch("automation.autopilot_legacy.service.set_autopilot_changes")
    @patch("automation.autopilot_legacy.service.persist_autopilot_changes_to_log")
    @patch("automation.autopilot_legacy.service._get_autopilot_campaign_changes_data")
    @patch("automation.autopilot_legacy.service._report_autopilot_exception")
    @patch("utils.k1_helper.update_ad_group")
    def test_dry_run(
        self,
        mock_k1,
        mock_exc,
        mock_get_changes,
        mock_log,
        mock_set,
        mock_predict1,
        mock_predict2,
        mock_active,
        mock_entities,
        mock_prefetch,
    ):
        ad_groups = list(dash.models.AdGroup.objects.all())
        mock_prefetch.return_value = (
            {ad_group: {} for ad_group in ad_groups},
            {},
            {
                ad_group.campaign: {"service_fee": Decimal("0.1"), "fee": Decimal("0.15"), "margin": Decimal("0.30")}
                for ad_group in ad_groups
            },
        )
        mock_entities.return_value = {ad_group.campaign: {ad_group: []} for ad_group in ad_groups}
        mock_active.return_value = (ad_groups, [a.get_current_settings() for a in ad_groups])
        mock_predict1.return_value = {}
        mock_predict2.return_value = {}
        service.run_autopilot(report_to_influx=False, dry_run=True)
        self.assertEqual(mock_exc.called, False)
        self.assertEqual(mock_k1.called, False)
        self.assertEqual(mock_log.called, False)

        self.assertEqual(mock_predict1.called, True)
        self.assertEqual(mock_predict2.called, True)
        self.assertEqual(mock_get_changes.called, True)
        mock_set.assert_not_called()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_only_cpc(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        cpc_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")}}
        service.set_autopilot_changes(bid_changes=cpc_changes)
        mock_update_values.assert_called_with(
            ag_source, {"cpc_cc": Decimal("0.2")}, dash.constants.SystemUserType.AUTOPILOT
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_only_cpm(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag_source.ad_group.bidding_type = dash.constants.BiddingType.CPM
        ag_source.ad_group.save(None)
        cpm_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")}}
        service.set_autopilot_changes(bid_changes=cpm_changes, ad_group=ag_source.ad_group)
        mock_update_values.assert_called_with(
            ag_source, {"cpm": Decimal("0.2")}, dash.constants.SystemUserType.AUTOPILOT
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    def test_set_autopilot_changes_only_cpc_rtb_as_one(self, mock_update_values):
        ag = dash.models.AdGroup.objects.get(id=1)
        ag_source = dash.models.AllRTBAdGroupSource(ag)
        cpc_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")}}
        service.set_autopilot_changes(bid_changes=cpc_changes, ad_group=ag)
        mock_update_values.assert_called_with(ag, {"cpc_cc": Decimal("0.2")}, dash.constants.SystemUserType.AUTOPILOT)
        mock_update_values.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    def test_set_autopilot_changes_only_cpm_rtb_as_one(self, mock_update_values):
        ag = dash.models.AdGroup.objects.get(id=1)
        ag.bidding_type = dash.constants.BiddingType.CPM
        ag.save(None)
        ag_source = dash.models.AllRTBAdGroupSource(ag)
        cpm_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")}}
        service.set_autopilot_changes(bid_changes=cpm_changes, ad_group=ag)
        mock_update_values.assert_called_with(ag, {"cpm": Decimal("0.2")}, dash.constants.SystemUserType.AUTOPILOT)
        mock_update_values.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_only_budget(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")}}
        service.set_autopilot_changes(budget_changes=budget_changes)
        mock_update_values.assert_called_with(
            ag_source, {"daily_budget_cc": Decimal("200")}, dash.constants.SystemUserType.AUTOPILOT
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpc(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")}}
        cpc_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")}}
        service.set_autopilot_changes(bid_changes=cpc_changes, budget_changes=budget_changes)
        mock_update_values.assert_called_with(
            ag_source,
            {"cpc_cc": Decimal("0.2"), "daily_budget_cc": Decimal("200")},
            dash.constants.SystemUserType.AUTOPILOT,
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpm(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag_source.ad_group.bidding_type = dash.constants.BiddingType.CPM
        ag_source.ad_group.save(None)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")}}
        cpm_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")}}
        service.set_autopilot_changes(
            bid_changes=cpm_changes, budget_changes=budget_changes, ad_group=ag_source.ad_group
        )
        mock_update_values.assert_called_with(
            ag_source,
            {"cpm": Decimal("0.2"), "daily_budget_cc": Decimal("200")},
            dash.constants.SystemUserType.AUTOPILOT,
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpc_no_change(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("100")}}
        cpc_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.1")}}
        service.set_autopilot_changes(bid_changes=cpc_changes, budget_changes=budget_changes)
        self.assertEqual(mock_update_values.called, False)

    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpm_no_change(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag_source.ad_group.bidding_type = dash.constants.BiddingType.CPM
        ag_source.ad_group.save(None)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("100")}}
        cpm_changes = {ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.1")}}
        service.set_autopilot_changes(
            bid_changes=cpm_changes, budget_changes=budget_changes, ad_group=ag_source.ad_group
        )
        self.assertEqual(mock_update_values.called, False)

    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpc_rtb_as_one(self, mock_update_values, mock_update_rtb):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag = dash.models.AdGroup.objects.get(id=1)
        ag_source_rtb = dash.models.AllRTBAdGroupSource(ag)
        budget_changes = {
            ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")},
            ag_source_rtb: {"old_budget": Decimal("10"), "new_budget": Decimal("20")},
        }
        cpc_changes = {
            ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")},
            ag_source_rtb: {"old_bid": Decimal("0.11"), "new_bid": Decimal("0.22")},
        }
        ap = dash.constants.SystemUserType.AUTOPILOT
        service.set_autopilot_changes(bid_changes=cpc_changes, budget_changes=budget_changes, ad_group=ag)
        mock_update_values.assert_called_with(
            ag_source, {"cpc_cc": Decimal("0.2"), "daily_budget_cc": Decimal("200")}, ap
        )
        mock_update_values.assert_called_once()
        mock_update_rtb.assert_called_with(ag, {"cpc_cc": Decimal("0.22"), "daily_budget_cc": Decimal("20")}, ap)
        mock_update_rtb.assert_called_once()

    @patch("automation.autopilot_legacy.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot_legacy.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpm_rtb_as_one(self, mock_update_values, mock_update_rtb):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag = dash.models.AdGroup.objects.get(id=1)
        ag.bidding_type = dash.constants.BiddingType.CPM
        ag.save(None)
        ag_source_rtb = dash.models.AllRTBAdGroupSource(ag)
        budget_changes = {
            ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")},
            ag_source_rtb: {"old_budget": Decimal("10"), "new_budget": Decimal("20")},
        }
        cpm_changes = {
            ag_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")},
            ag_source_rtb: {"old_bid": Decimal("0.11"), "new_bid": Decimal("0.22")},
        }
        ap = dash.constants.SystemUserType.AUTOPILOT
        service.set_autopilot_changes(bid_changes=cpm_changes, budget_changes=budget_changes, ad_group=ag)
        mock_update_values.assert_called_with(ag_source, {"cpm": Decimal("0.2"), "daily_budget_cc": Decimal("200")}, ap)
        mock_update_values.assert_called_once()
        mock_update_rtb.assert_called_with(ag, {"cpm": Decimal("0.22"), "daily_budget_cc": Decimal("20")}, ap)
        mock_update_rtb.assert_called_once()

    def test_set_autopilot_changes_rtb_as_one_history(self):
        campaign = magic_mixer.blend(dash.models.Campaign)
        campaign_goal.CampaignGoal.objects.create_unsafe(
            campaign=campaign, type=dash.constants.CampaignGoalKPI.CPC, primary=True
        )
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        ad_group.settings.update(
            None,
            b1_sources_group_enabled=True,
            b1_sources_group_cpc_cc=Decimal("0.11"),
            b1_sources_group_daily_budget=Decimal("10"),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            skip_validation=True,
        )
        b1_source_type = dash.models.SourceType.objects.get(id=3)
        b1_source = magic_mixer.blend(dash.models.Source, name="Outbrain RTB", source_type=b1_source_type)
        ad_group_source_b1 = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source=b1_source)
        ad_group_source_b1.settings.update(
            None,
            cpc_cc=Decimal("0.11"),
            daily_budget_cc=Decimal("10"),
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            skip_automation=True,
            k1_sync=False,
            skip_validation=True,
            skip_notification=True,
        )
        outbrain_source = dash.models.Source.objects.get(id=4)
        ad_group_source = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source=outbrain_source)
        ad_group_source.settings.update(
            None,
            cpc_cc=Decimal("0.1"),
            daily_budget_cc=Decimal("100"),
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            skip_automation=True,
            k1_sync=False,
            skip_validation=True,
            skip_notification=True,
        )

        ag_source_rtb = dash.models.AllRTBAdGroupSource(ad_group)

        initial_history_records_count = dash.models.History.objects.filter(ad_group=ad_group).count()

        budget_changes = {
            ad_group_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")},
            ag_source_rtb: {"old_budget": Decimal("10"), "new_budget": Decimal("20")},
        }
        cpc_changes = {
            ad_group_source: {"old_bid": Decimal("0.1"), "new_bid": Decimal("0.2")},
            ag_source_rtb: {"old_bid": Decimal("0.11"), "new_bid": Decimal("0.22")},
        }

        service.set_autopilot_changes(bid_changes=cpc_changes, budget_changes=budget_changes, ad_group=ad_group)

        self.assertEqual(
            dash.models.History.objects.filter(ad_group=ad_group).count(), initial_history_records_count + 4
        )

        history_records = dash.models.History.objects.filter(ad_group=ad_group).order_by("created_dt")[
            initial_history_records_count:
        ]

        self.assertCountEqual(
            [
                (h.system_user, h.changes)
                for h in history_records
                if h.action_type != dash.constants.HistoryActionType.BID_MODIFIER_UPDATE
            ],
            [
                (
                    dash.constants.SystemUserType.AUTOPILOT,
                    {"local_cpc_cc": "0.2000", "local_daily_budget_cc": "200.0000"},
                ),
                (
                    dash.constants.SystemUserType.AUTOPILOT,
                    {
                        "local_b1_sources_group_cpc_cc": "0.2200",
                        "local_b1_sources_group_daily_budget": "20.0000",
                        "local_daily_budget": "20.0000",
                    },
                ),
            ],
        )

    @patch("automation.autopilot_legacy.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("0.3"))
    def test_set_paused_ad_group_sources_to_minimum_values(self):
        adg = dash.models.AdGroup.objects.get(id=4)
        paused_ad_group_source_setting = dash.models.AdGroupSourceSettings.objects.get(id=6).copy_settings()
        paused_ad_group_source_setting.state = 2
        paused_ad_group_source_setting.daily_budget_cc = Decimal("100.")
        paused_ad_group_source_setting.save(None)
        paused_ad_group_source = paused_ad_group_source_setting.ad_group_source
        active_ad_group_source = dash.models.AdGroupSource.objects.get(id=6)
        active_ad_group_source_old_budget = active_ad_group_source.get_current_settings().daily_budget_cc
        new_budgets = service._set_paused_ad_group_sources_to_minimum_values(
            adg, {"service_fee": Decimal("0.1"), "fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        self.assertEqual(new_budgets.get(paused_ad_group_source)["old_budget"], Decimal("100."))
        self.assertEqual(new_budgets.get(paused_ad_group_source)["new_budget"], Decimal("10"))
        self.assertEqual(
            new_budgets.get(paused_ad_group_source)["budget_comments"],
            [constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE],
        )
        self.assertEqual(paused_ad_group_source.get_current_settings().daily_budget_cc, Decimal("10"))
        self.assertEqual(
            active_ad_group_source.get_current_settings().daily_budget_cc, active_ad_group_source_old_budget
        )
        self.assertTrue(active_ad_group_source not in new_budgets)

    @patch("automation.autopilot_legacy.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("10"))
    def test_set_paused_ad_group_sources_to_minimum_values_rtb_as_one(self):
        adg = dash.models.AdGroup.objects.get(id=4)
        adg_settings = adg.get_current_settings().copy_settings()
        adg_settings.b1_sources_group_enabled = True
        adg_settings.b1_sources_group_state = dash.constants.AdGroupSourceSettingsState.INACTIVE
        adg_settings.b1_sources_group_daily_budget = Decimal("30.00")
        adg_settings.autopilot_state = dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET
        adg_settings.save(None)

        paused_ad_group_source_setting = dash.models.AdGroupSourceSettings.objects.get(id=6).copy_settings()
        paused_ad_group_source_setting.state = dash.constants.AdGroupSourceSettingsState.INACTIVE
        paused_ad_group_source_setting.daily_budget_cc = Decimal("100.")
        paused_ad_group_source_setting.save(None)
        paused_ad_group_source = paused_ad_group_source_setting.ad_group_source

        s = paused_ad_group_source.source
        s.source_type = dash.models.SourceType.objects.get(id=3)
        s.save()

        active_ad_group_source = dash.models.AdGroupSource.objects.get(id=6)

        active_ad_group_source_old_budget = active_ad_group_source.get_current_settings().daily_budget_cc
        all_rtb_ad_group_source = dash.models.AllRTBAdGroupSource(adg)
        new_budgets = service._set_paused_ad_group_sources_to_minimum_values(
            adg, {"service_fee": Decimal("0.1"), "fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )

        adg.settings.refresh_from_db()
        self.assertTrue(paused_ad_group_source not in new_budgets)
        self.assertTrue(active_ad_group_source not in new_budgets)
        self.assertEqual(new_budgets.get(all_rtb_ad_group_source)["old_budget"], Decimal("30."))
        self.assertEqual(new_budgets.get(all_rtb_ad_group_source)["new_budget"], Decimal("19.0"))
        self.assertEqual(
            new_budgets.get(all_rtb_ad_group_source)["budget_comments"],
            [constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE],
        )
        self.assertEqual(paused_ad_group_source.get_current_settings().daily_budget_cc, Decimal("100.0"))
        self.assertEqual(
            active_ad_group_source.get_current_settings().daily_budget_cc, active_ad_group_source_old_budget
        )
        self.assertEqual(adg.get_current_settings().b1_sources_group_daily_budget, Decimal("19.0"))

    @patch("automation.autopilot_legacy.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot_legacy.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_ad_group(self, mock_run_autopilot, mock_set_paused):
        adg = dash.models.AdGroup.objects.get(id=4)
        changed_source = dash.models.AdGroupSource.objects.get(id=1)
        not_changed_source = dash.models.AdGroupSource.objects.get(id=2)
        paused_ad_group_source = dash.models.AdGroupSource.objects.get(id=3)
        mock_run_autopilot.return_value = {
            adg.campaign: {
                adg: {
                    changed_source: {"old_budget": Decimal("20"), "new_budget": Decimal("30")},
                    not_changed_source: {"old_budget": Decimal("20"), "new_budget": Decimal("20")},
                }
            }
        }
        mock_set_paused.return_value = {
            paused_ad_group_source: {"old_budget": Decimal("20"), "new_budget": Decimal("5")}
        }
        changed_sources = service.recalculate_budgets_ad_group(adg)
        mock_run_autopilot.assert_called_once_with(
            ad_group=adg, adjust_bids=False, adjust_budgets=True, initialization=True
        )
        self.assertTrue(paused_ad_group_source in changed_sources)
        self.assertTrue(changed_source in changed_sources)
        self.assertTrue(not_changed_source not in changed_sources)

    @patch("automation.autopilot_legacy.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot_legacy.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_ad_group_campaign_ap(self, mock_run_autopilot, mock_set_paused):
        adg = dash.models.AdGroup.objects.get(id=4)
        adg.campaign.settings.update_unsafe(None, autopilot=True)
        changed_source = dash.models.AdGroupSource.objects.get(id=1)
        not_changed_source = dash.models.AdGroupSource.objects.get(id=2)
        mock_run_autopilot.return_value = {
            adg.campaign: {
                adg: {
                    changed_source: {"old_budget": Decimal("20"), "new_budget": Decimal("30")},
                    not_changed_source: {"old_budget": Decimal("20"), "new_budget": Decimal("20")},
                }
            }
        }
        changed_sources = service.recalculate_budgets_ad_group(adg)
        mock_run_autopilot.assert_called_once_with(
            campaign=adg.campaign, adjust_bids=False, adjust_budgets=True, initialization=True
        )
        self.assertEqual(set(), changed_sources)
        self.assertFalse(mock_set_paused.called)

    @patch("automation.autopilot_legacy.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot_legacy.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_campaign_inactive(self, mock_run_autopilot, mock_set_paused):
        campaign = dash.models.Campaign.objects.get(pk=4)
        service.recalculate_budgets_campaign(campaign)
        mock_run_autopilot.assert_called_once_with(
            campaign=campaign, adjust_bids=False, adjust_budgets=True, initialization=True
        )
        self.assertTrue(mock_set_paused.called)

    @patch("automation.autopilot_legacy.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot_legacy.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_campaign_active(self, mock_run_autopilot, mock_set_paused):
        campaign = dash.models.Campaign.objects.get(pk=4)
        campaign.settings.update_unsafe(None, autopilot=True)
        service.recalculate_budgets_campaign(campaign)
        mock_run_autopilot.assert_called_once_with(
            campaign=campaign, adjust_bids=False, adjust_budgets=True, initialization=True
        )
        self.assertFalse(mock_set_paused.called)

    @patch("redshiftapi.api_breakdowns.query")
    @patch("utils.metrics_compat.gauge")
    def test_report_adgroups_data_to_influx(self, mock_metrics_compat, mock_query):
        mock_query.return_value = [
            {"ad_group_id": 1, "et_cost": Decimal("15"), "etfm_cost": Decimal("15")},
            {"ad_group_id": 2, "et_cost": Decimal("12"), "etfm_cost": Decimal("12")},
            {"ad_group_id": 3, "et_cost": Decimal("10"), "etfm_cost": Decimal("10")},
            {"ad_group_id": 4, "et_cost": Decimal("20"), "etfm_cost": Decimal("20")},
        ]

        entities = {
            campaign: {ad_group: {} for ad_group in dash.models.AdGroup.objects.filter(campaign=campaign)}
            for campaign in dash.models.Campaign.objects.all()
        }
        campaign_daily_budgets = {dash.models.Campaign.objects.get(pk=2): Decimal("13")}
        service._report_adgroups_data_to_influx(entities, campaign_daily_budgets)

        mock_metrics_compat.assert_has_calls(
            [
                call("automation.autopilot_plus_legacy.adgroups_on", 2, autopilot="budget_autopilot"),
                call("automation.autopilot_plus_legacy.adgroups_on", 1, autopilot="bid_autopilot"),
                call("automation.autopilot_plus_legacy.adgroups_on", 1, autopilot="campaign_autopilot"),
                call("automation.autopilot_plus_legacy.campaigns_on", 1, autopilot="campaign_autopilot"),
                call(
                    "automation.autopilot_plus_legacy.spend",
                    Decimal("50"),
                    autopilot="budget_autopilot",
                    type="expected",
                ),
                call(
                    "automation.autopilot_plus_legacy.spend",
                    Decimal("13"),
                    autopilot="campaign_autopilot",
                    type="expected",
                ),
                call(
                    "automation.autopilot_plus_legacy.spend",
                    Decimal("12"),
                    autopilot="campaign_autopilot",
                    type="yesterday",
                ),
                call(
                    "automation.autopilot_plus_legacy.spend",
                    Decimal("35"),
                    autopilot="budget_autopilot",
                    type="yesterday",
                ),
                call(
                    "automation.autopilot_plus_legacy.spend", Decimal("10"), autopilot="bid_autopilot", type="yesterday"
                ),
            ]
        )

    @patch("redshiftapi.api_breakdowns.query")
    @patch("utils.metrics_compat.gauge")
    def test_report_new_budgets_on_ap_to_influx(self, mock_metrics_compat, mock_query):
        mock_query.return_value = [
            {"ad_group_id": 1, "etf_cost": Decimal("15")},
            {"ad_group_id": 3, "etf_cost": Decimal("10")},
            {"ad_group_id": 4, "etf_cost": Decimal("20")},
        ]

        entities = {
            campaign: {
                ad_group: [
                    ags
                    for ags in dash.models.AdGroupSource.objects.filter(
                        ad_group=ad_group, settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE
                    )
                ]
                for ad_group in dash.models.AdGroup.objects.filter(campaign=campaign)
            }
            for campaign in dash.models.Campaign.objects.all()
        }
        service._report_new_budgets_on_ap_to_influx(entities)

        mock_metrics_compat.assert_has_calls(
            [
                call("automation.autopilot_plus_legacy.spend", Decimal("50"), autopilot="bid_autopilot", type="actual"),
                call(
                    "automation.autopilot_plus_legacy.spend",
                    Decimal("210"),
                    autopilot="budget_autopilot",
                    type="actual",
                ),
                call(
                    "automation.autopilot_plus_legacy.spend",
                    Decimal("50"),
                    autopilot="campaign_autopilot",
                    type="actual",
                ),
                call("automation.autopilot_plus_legacy.sources_on", 1, autopilot="bid_autopilot"),
                call("automation.autopilot_plus_legacy.sources_on", 4, autopilot="budget_autopilot"),
                call("automation.autopilot_plus_legacy.sources_on", 1, autopilot="campaign_autopilot"),
            ]
        )

    @patch("utils.dates_helper.local_today", return_value=datetime.date(2018, 1, 2))
    def test_adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled_past_start_date(self, mock_local_today):
        campaign = magic_mixer.blend(dash.models.Campaign)
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        ad_group.settings.update(None, start_date=datetime.date(2018, 1, 1), end_date=datetime.date(2018, 2, 1))

        with patch("dash.models.AdGroupSettings.update") as mock_settings_update:
            service.adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled(campaign)
            mock_settings_update.assert_called_once_with(
                None,
                end_date=None,
                skip_automation=True,
                skip_field_change_validation_autopilot=True,
                system_user=dash.constants.SystemUserType.AUTOPILOT,
            )

    @patch("utils.dates_helper.local_today", return_value=datetime.date(2018, 1, 2))
    def test_adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled_future_start_date(
        self, mock_local_today
    ):
        campaign = magic_mixer.blend(dash.models.Campaign)
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        ad_group.settings.update(None, start_date=datetime.date(2018, 1, 3), end_date=datetime.date(2018, 2, 1))

        with patch("dash.models.AdGroupSettings.update") as mock_settings_update:
            service.adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled(campaign)
            mock_settings_update.assert_called_once_with(
                None,
                start_date=datetime.date(2018, 1, 2),
                end_date=None,
                skip_automation=True,
                skip_field_change_validation_autopilot=True,
                system_user=dash.constants.SystemUserType.AUTOPILOT,
            )

    @patch("utils.dates_helper.local_today", return_value=datetime.date(2018, 1, 2))
    def test_adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled_archived(self, mock_local_today):
        campaign = magic_mixer.blend(dash.models.Campaign)
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        ad_group.settings.update(
            None, start_date=datetime.date(2018, 1, 1), end_date=datetime.date(2018, 2, 1), archived=True
        )

        with patch("dash.models.AdGroupSettings.update") as mock_settings_update:
            service.adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled(campaign)
            mock_settings_update.assert_not_called()
