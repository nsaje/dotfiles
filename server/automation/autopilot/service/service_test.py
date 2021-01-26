import datetime
from collections import defaultdict
from decimal import Decimal
from unittest import mock

from django import test
from mock import call
from mock import patch

import dash.constants
import dash.models
from automation import models
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import service


class AutopilotTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    def mock_budget_recommender(
        self, campaign, daily_budget, ad_groups_data, bcm, campaign_goal, ignore_daily_budget_too_small=False
    ):
        result = {}
        for ag in ad_groups_data:
            result[ag] = {"old_budget": Decimal("10.0"), "new_budget": Decimal("20.0"), "budget_comments": []}
        return result

    def _update_budget_call(self, ad_group):
        return call(dash.models.AdGroup.objects.get(id=ad_group), Decimal("20.0"))

    def _metrics_input(self):
        entities = {
            campaign: list(dash.models.AdGroup.objects.filter(campaign=campaign))
            for campaign in dash.models.Campaign.objects.all()
        }
        campaign_daily_budgets = {campaign: Decimal("0") for campaign in dash.models.Campaign.objects.all()}
        return defaultdict(dict, entities), defaultdict(Decimal, campaign_daily_budgets)

    def assertLogExists(self, campaign=None, ad_group=None):
        models.AutopilotLog.objects.get(campaign_id=campaign, ad_group_id=ad_group)

    def setUp(self):
        dash.models.AdGroup.objects.get(pk=2).settings.update_unsafe(None, state=1)
        self.data = {ad_group: {"old_budget": Decimal("10.0")} for ad_group in dash.models.AdGroup.objects.all()}

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @patch(
        "django.utils.timezone.now",
        return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5),
    )
    @patch("automation.autopilot.service.service._update_autopilot_metrics")
    @patch("automation.autopilot.service.helpers.update_ad_group_daily_budget")
    @patch("automation.autopilot.service.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.service.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_daily_run(
        self, mock_budgets, mock_prefetch, mock_update_budget, mock_autopilot_metrics, mock_timezone_now
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        service.run_autopilot(daily_run=True, update_metrics=True)

        self.assertCountEqual(
            mock_update_budget.call_args_list,
            [
                self._update_budget_call(ad_group=1),
                self._update_budget_call(ad_group=2),
                self._update_budget_call(ad_group=3),
                self._update_budget_call(ad_group=4),
            ],
        )
        self.assertLogExists(campaign=1, ad_group=1)
        self.assertLogExists(campaign=2, ad_group=2)
        self.assertLogExists(campaign=3, ad_group=3)
        self.assertLogExists(campaign=4, ad_group=4)

        mock_autopilot_metrics.assert_called_once_with(*self._metrics_input())

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @patch(
        "django.utils.timezone.now",
        return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5),
    )
    @patch("automation.autopilot.service.helpers.update_ad_group_daily_budget")
    @patch("automation.autopilot.service.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.service.budgets.get_autopilot_daily_budget_recommendations")
    @patch("utils.slack.publish")
    def test_run_autopilot_daily_run_exceptions(
        self, mock_slack, mock_budgets, mock_prefetch, mock_update_budget, mock_timezone_now
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        original_save_changes = service._save_changes
        original_get_budget_predictions_for_campaign = service._get_budget_predictions_for_campaign

        def _failing_save_changes(*args, **kwargs):
            campaign = kwargs.get("campaign")
            if campaign and campaign.id == 2:
                raise Exception()
            else:
                return original_save_changes(*args, **kwargs)

        def _failing_get_budget_predictions_for_campaign(*args, **kwargs):
            campaign = args[0]
            if campaign and campaign.id == 2:
                raise Exception()
            else:
                return original_get_budget_predictions_for_campaign(*args, **kwargs)

        with patch("automation.autopilot.service.service._save_changes", side_effect=_failing_save_changes):
            with patch(
                "automation.autopilot.service.service._get_budget_predictions_for_campaign",
                side_effect=_failing_get_budget_predictions_for_campaign,
            ):
                service.run_autopilot(daily_run=True, update_metrics=False)

        self.assertCountEqual(
            mock_update_budget.call_args_list,
            [
                self._update_budget_call(ad_group=1),
                self._update_budget_call(ad_group=3),
                self._update_budget_call(ad_group=4),
            ],
        )
        self.assertLogExists(campaign=1, ad_group=1)
        self.assertLogExists(campaign=3, ad_group=3)
        self.assertLogExists(campaign=4, ad_group=4)

        mock_slack.assert_has_calls(
            [
                call(
                    "Autopilot run failed for the following campaigns:\n- <https://one.zemanta.com/v2/analytics/campaign/2/|Test Campaign 2>",
                    channel="rnd-z1-alerts-aux",
                    msg_type=":rage:",
                    username="Autopilot",
                )
            ]
        )

    @mock.patch("etl.materialization_run.etl_data_complete_for_date", mock.MagicMock(return_value=True))
    @patch(
        "utils.dates_helper.utc_now",
        return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5),
    )
    @patch("automation.autopilot.service.helpers.update_ad_group_daily_budget")
    @patch("automation.autopilot.service.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.service.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_daily_run_exclude_processed_entities(
        self, mock_budgets, mock_prefetch, mock_update_budget, mock_utc_now
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        with patch(
            "django.utils.timezone.now",
            return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) - datetime.timedelta(hours=15),
        ):
            # Create some logs from last yesterday's run (~14h)
            magic_mixer.blend(
                models.AutopilotLog,
                campaign=dash.models.Campaign.objects.get(id=1),
                ad_group=dash.models.AdGroup.objects.get(id=1),
                is_autopilot_job_run=True,
            )
            magic_mixer.blend(
                models.AutopilotLog,
                campaign=dash.models.Campaign.objects.get(id=2),
                ad_group=dash.models.AdGroup.objects.get(id=2),
                is_autopilot_job_run=True,
            )
            magic_mixer.blend(
                models.AutopilotLog,
                campaign=dash.models.Campaign.objects.get(id=3),
                ad_group=dash.models.AdGroup.objects.get(id=3),
                is_autopilot_job_run=True,
            )
            magic_mixer.blend(
                models.AutopilotLog,
                campaign=dash.models.Campaign.objects.get(id=4),
                ad_group=dash.models.AdGroup.objects.get(id=4),
                is_autopilot_job_run=True,
            )

        with patch(
            "django.utils.timezone.now",
            return_value=dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=4),
        ):
            # Create some logs from first today's run (~9h)
            magic_mixer.blend(
                models.AutopilotLog,
                campaign=dash.models.Campaign.objects.get(id=3),
                ad_group=dash.models.AdGroup.objects.get(id=3),
                is_autopilot_job_run=True,
            )
            magic_mixer.blend(
                models.AutopilotLog,
                campaign=dash.models.Campaign.objects.get(id=4),
                ad_group=dash.models.AdGroup.objects.get(id=4),
                is_autopilot_job_run=True,
            )

        service.run_autopilot(daily_run=True, update_metrics=False)

        self.assertCountEqual(
            mock_update_budget.call_args_list,
            [self._update_budget_call(ad_group=1), self._update_budget_call(ad_group=2)],
        )

        utc_now = dates_helper.get_midnight(dates_helper.utc_now())

        self.assertTrue(
            models.AutopilotLog.objects.filter(campaign_id=1, ad_group_id=1, created_dt__gte=utc_now).exists()
        )
        self.assertTrue(
            models.AutopilotLog.objects.filter(campaign_id=2, ad_group_id=2, created_dt__gte=utc_now).exists()
        )

    @patch("automation.autopilot.service.service.logger.info")
    def test_run_autopilot_daily_run_late_materialization(self, mock_logger_info):
        service.run_autopilot(daily_run=True, update_metrics=False)
        mock_logger_info.assert_called_once_with(
            "Autopilot daily run was aborted since materialized data is not yet available."
        )

    @patch("automation.autopilot.service.helpers.update_ad_group_daily_budget")
    @patch("automation.autopilot.service.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.service.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_intialize_campaign(self, mock_budgets, mock_prefetch, mock_update_allrtb):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        campaign = dash.models.Campaign.objects.get(pk=2)
        service.run_autopilot(campaign=campaign)

        self.assertCountEqual(mock_update_allrtb.call_args_list, [self._update_budget_call(ad_group=2)])
        self.assertLogExists(campaign=2, ad_group=2)

    @patch("automation.autopilot.service.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.service.helpers.get_autopilot_entities")
    @patch("automation.autopilot.service.service._set_autopilot_changes")
    @patch("automation.autopilot.service.service._persist_autopilot_changes_to_log")
    @patch("automation.autopilot.service.service._update_autopilot_campaign_changes_data")
    @patch("utils.k1_helper.update_ad_group")
    def test_dry_run(self, mock_k1, mock_get_changes, mock_log, mock_set, mock_entities, mock_prefetch):
        ad_groups = magic_mixer.cycle(4).blend(dash.models.AdGroup)
        mock_prefetch.return_value = (
            {ad_group: {} for ad_group in ad_groups},
            {},
            {
                ad_group.campaign: {"service_fee": Decimal("0.1"), "fee": Decimal("0.15"), "margin": Decimal("0.30")}
                for ad_group in ad_groups
            },
        )
        mock_entities.return_value = {ad_group.campaign: [ad_group] for ad_group in ad_groups}

        service.run_autopilot(update_metrics=False, dry_run=True)

        mock_k1.assert_not_called()
        self.assertEqual(4, mock_get_changes.call_count)
        mock_log.assert_not_called()
        mock_set.assert_not_called()

    @patch("automation.autopilot.service.helpers.update_ad_group_daily_budget")
    def test_set_autopilot_changes(self, mock_update_values):
        ad_group = magic_mixer.blend(dash.models.AdGroup)
        budget_changes = {"old_budget": Decimal("100"), "new_budget": Decimal("200")}
        service._set_autopilot_changes(ad_group, budget_changes)
        mock_update_values.assert_called_with(ad_group, Decimal("200"))
        mock_update_values.assert_called_once()

    @patch("automation.autopilot.service.helpers.update_ad_group_daily_budget")
    def test_set_autopilot_changes_no_change(self, mock_update_values):
        ad_group = magic_mixer.blend(dash.models.AdGroup)
        budget_changes = {"old_budget": Decimal("100"), "new_budget": Decimal("100")}
        service._set_autopilot_changes(ad_group, budget_changes)
        mock_update_values.assert_not_called()

    def test_set_autopilot_changes_history(self):
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account__agency__uses_realtime_autopilot=True)
        ad_group.settings.update(None, daily_budget=Decimal("10"), skip_validation=True)

        initial_history_records_count = dash.models.History.objects.filter(ad_group=ad_group).count()
        budget_changes = {"old_budget": Decimal("100"), "new_budget": Decimal("200")}

        service._set_autopilot_changes(budget_changes=budget_changes, ad_group=ad_group)

        self.assertEqual(
            dash.models.History.objects.filter(ad_group=ad_group).count(), initial_history_records_count + 1
        )
        history_records = dash.models.History.objects.filter(ad_group=ad_group).order_by("created_dt")[
            initial_history_records_count:
        ]

        # TODO: RTAP: local/daily_budget deliberately removed from history until it is ok for users to see that
        self.assertCountEqual(
            [(h.system_user, h.changes) for h in history_records],
            [
                (
                    dash.constants.SystemUserType.AUTOPILOT,
                    {
                        "local_daily_budget": "200.0000",
                        "local_autopilot_daily_budget": "200.0000",
                        "local_b1_sources_group_daily_budget": "200.0000",
                    },
                )
            ],
        )

    @patch("automation.autopilot.service.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_campaign_active(self, mock_run_autopilot):
        campaign = magic_mixer.blend(dash.models.Campaign)
        campaign.settings.update_unsafe(None, autopilot=True)
        service.recalculate_ad_group_budgets(campaign)
        mock_run_autopilot.assert_called_once_with(campaign=campaign, adjust_budgets=True)

    @patch("automation.autopilot.service.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_campaign_inactive(self, mock_run_autopilot):
        campaign = magic_mixer.blend(dash.models.Campaign)
        campaign.settings.update_unsafe(None, autopilot=False)
        service.recalculate_ad_group_budgets(campaign)
        mock_run_autopilot.assert_not_called()

    @patch("redshiftapi.api_breakdowns.query")
    @patch("utils.metrics_compat.gauge")
    def test_update_autopilot_metrics(self, mock_metrics_compat, mock_query):
        mock_query.return_value = [
            {"ad_group_id": 1, "etfm_cost": Decimal("15")},
            {"ad_group_id": 2, "etfm_cost": Decimal("12")},
            {"ad_group_id": 3, "etfm_cost": Decimal("10")},
            {"ad_group_id": 4, "etfm_cost": Decimal("20")},
        ]

        entities = {
            campaign: {ad_group: {} for ad_group in dash.models.AdGroup.objects.filter(campaign=campaign)}
            for campaign in dash.models.Campaign.objects.all()
        }
        campaign_daily_budgets = {campaign: Decimal("0") for campaign in dash.models.Campaign.objects.all()}
        campaign_daily_budgets[dash.models.Campaign.objects.get(pk=2)] = Decimal("13")

        service._update_autopilot_metrics(entities, campaign_daily_budgets)

        mock_metrics_compat.assert_has_calls(
            [
                call("automation.autopilot_plus.adgroups_on", 4, autopilot="campaign_autopilot"),
                call("automation.autopilot_plus.campaigns_on", 4, autopilot="campaign_autopilot"),
                call("automation.autopilot_plus.spend", Decimal("13"), autopilot="campaign_autopilot", type="expected"),
                call("automation.autopilot_plus.spend", Decimal("150"), autopilot="campaign_autopilot", type="actual"),
                call(
                    "automation.autopilot_plus.spend", Decimal("57"), autopilot="campaign_autopilot", type="yesterday"
                ),
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
