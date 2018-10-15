from collections import defaultdict
from decimal import Decimal
import datetime
import json
from mock import patch, call
import traceback

from django import test

import dash.constants
import dash.models
from utils.magic_mixer import magic_mixer

from . import constants
from automation import models
from . import service


class AutopilotPlusTestCase(test.TestCase):
    fixtures = ["test_automation.yaml"]

    def mock_budget_recommender(
        self, ad_group, daily_budget, data, bcm, campaign_goal, rtb_as_one, ignore_daily_budget_too_small=False
    ):
        result = {}
        for ags in data:
            result[ags] = {"old_budget": Decimal("10.0"), "new_budget": Decimal("20.0"), "budget_comments": []}
        return result

    def mock_cpc_recommender(self, ad_group, data, bcm, budget_changes, adjust_rtb_sources):
        result = {}
        for ags in data:
            if ad_group.id != 3:
                self.assertEqual(
                    budget_changes.get(ags),
                    {"old_budget": Decimal("10.0"), "new_budget": Decimal("20.0"), "budget_comments": []},
                )
            result[ags] = {"old_cpc_cc": Decimal("0.1"), "new_cpc_cc": Decimal("0.2"), "cpc_comments": []}
        return result

    def _update_call(self, ad_group, source, budget=True, cpc=True):
        changes = {}
        if budget:
            changes["daily_budget_cc"] = Decimal("20.0")
        if cpc:
            changes["cpc_cc"] = Decimal("0.2")
        ad_group_source = dash.models.AdGroupSource.objects.get(ad_group_id=ad_group, source_id=source)
        return call(ad_group_source, changes, 2)

    def _update_allrtb_call(self, ad_group, budget=True, cpc=True):
        changes = {}
        if budget:
            changes["daily_budget_cc"] = Decimal("20.0")
        if cpc:
            changes["cpc_cc"] = Decimal("0.2")
        return call(dash.models.AdGroup.objects.get(id=ad_group), changes, 2)

    def _email_changes(self, budgets=[], cpc=[]):
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
                    if ad_group.id in cpc:
                        ags_data.update(
                            {"old_cpc_cc": Decimal("0.1"), "new_cpc_cc": Decimal("0.2"), "cpc_comments": []}
                        )
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
            ags = dash.models.AdGroupSource.objects.filter(ad_group_id=ad_group, source_id=source)
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

    @patch("automation.autopilot.service._report_new_budgets_on_ap_to_influx")
    @patch("automation.autopilot.service._report_adgroups_data_to_influx")
    @patch("automation.autopilot.helpers.send_autopilot_changes_emails")
    @patch("automation.autopilot.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    @patch("automation.autopilot.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.cpc.get_autopilot_cpc_recommendations")
    @patch("automation.autopilot.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_daily_run(
        self,
        mock_budgets,
        mock_cpc,
        mock_prefetch,
        mock_update,
        mock_update_allrtb,
        mock_send,
        mock_influx_adgroups,
        mock_influx_budgets,
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_cpc.side_effect = self.mock_cpc_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        service.run_autopilot(daily_run=True, send_mail=True, report_to_influx=True)

        self.maxDiff = None
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
        mock_send.assert_called_once_with(self._email_changes(budgets=(1, 2, 4), cpc=(1, 2, 3, 4)), {}, False)
        mock_influx_adgroups.assert_called_once_with(*self._influx_input())
        mock_influx_budgets.assert_called_once_with(self._influx_input()[0])

    @patch("automation.autopilot.helpers.send_autopilot_changes_emails")
    @patch("automation.autopilot.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    @patch("automation.autopilot.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.cpc.get_autopilot_cpc_recommendations")
    @patch("automation.autopilot.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_initialize_adgroup(
        self, mock_budgets, mock_cpc, mock_prefetch, mock_update, mock_update_allrtb, mock_send
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_cpc.side_effect = self.mock_cpc_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        ad_group = dash.models.AdGroup.objects.get(pk=4)
        service.run_autopilot(ad_group=ad_group, initialization=True, adjust_cpcs=False, send_mail=True)

        self.assertCountEqual(
            mock_update.call_args_list,
            [
                self._update_call(ad_group=4, source=1, cpc=False),
                self._update_call(ad_group=4, source=2, cpc=False),
                self._update_call(ad_group=4, source=3, cpc=False),
                self._update_call(ad_group=4, source=4, cpc=False),
            ],
        )
        self.assertCountEqual(mock_update_allrtb.call_args_list, [self._update_allrtb_call(ad_group=4, cpc=False)])
        self.assertLogExists(ad_group=4, source=1)
        self.assertLogExists(ad_group=4, source=2)
        self.assertLogExists(ad_group=4, source=3)
        self.assertLogExists(ad_group=4, source=4)
        self.assertLogExists(ad_group=4, source=None)
        mock_send.assert_called_once_with(self._email_changes(budgets=(4,)), {}, True)

    @patch("automation.autopilot.helpers.send_autopilot_changes_emails")
    @patch("automation.autopilot.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    @patch("automation.autopilot.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.cpc.get_autopilot_cpc_recommendations")
    @patch("automation.autopilot.budgets.get_autopilot_daily_budget_recommendations")
    def test_run_autopilot_intialize_campaign(
        self, mock_budgets, mock_cpc, mock_prefetch, mock_update, mock_update_allrtb, mock_send
    ):
        mock_budgets.side_effect = self.mock_budget_recommender
        mock_cpc.side_effect = self.mock_cpc_recommender
        mock_prefetch.return_value = (self.data, {}, {})

        campaign = dash.models.Campaign.objects.get(pk=2)
        service.run_autopilot(campaign=campaign, initialization=True, adjust_cpcs=False, send_mail=True)

        self.assertCountEqual(mock_update.call_args_list, [self._update_call(ad_group=2, source=1, cpc=False)])
        self.assertCountEqual(mock_update_allrtb.call_args_list, [self._update_allrtb_call(ad_group=2, cpc=False)])
        self.assertLogExists(campaign=2, ad_group=2, source=1)
        self.assertLogExists(campaign=2, ad_group=2, source=None)
        mock_send.assert_called_once_with(self._email_changes(budgets=(2,)), {}, True)

    @patch("urllib.request.urlopen")
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
            json.dumps(
                {
                    "service_key": "123abc",
                    "incident_key": "automation_autopilot_error",
                    "event_type": "trigger",
                    "description": desc,
                    "client": "Zemanta One - testhost",
                    "details": {"element": ""},  # '<AdGroup: Test AdGroup 1>'
                }
            ),
        )

    @patch("automation.autopilot.prefetch.prefetch_autopilot_data")
    @patch("automation.autopilot.helpers.get_autopilot_entities")
    @patch("automation.autopilot.helpers.get_active_ad_groups_on_autopilot")
    @patch("automation.autopilot.service._get_cpc_predictions")
    @patch("automation.autopilot.service._get_budget_predictions_for_adgroup")
    @patch("automation.autopilot.service.set_autopilot_changes")
    @patch("automation.autopilot.service.persist_autopilot_changes_to_log")
    @patch("automation.autopilot.service._get_autopilot_campaign_changes_data")
    @patch("automation.autopilot.service._report_autopilot_exception")
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
            {ad_group.campaign: {"fee": Decimal("0.15"), "margin": Decimal("0.30")} for ad_group in ad_groups},
        )
        mock_entities.return_value = {ad_group.campaign: {ad_group: []} for ad_group in ad_groups}
        mock_active.return_value = (ad_groups, [a.get_current_settings() for a in ad_groups])
        mock_predict1.return_value = {}
        mock_predict2.return_value = {}
        service.run_autopilot(send_mail=False, report_to_influx=False, dry_run=True)
        self.assertEqual(mock_exc.called, False)
        self.assertEqual(mock_k1.called, False)
        self.assertEqual(mock_log.called, False)

        self.assertEqual(mock_predict1.called, True)
        self.assertEqual(mock_predict2.called, True)
        self.assertEqual(mock_get_changes.called, True)
        mock_set.assert_not_called()

    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_only_cpc(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        cpc_changes = {ag_source: {"old_cpc_cc": Decimal("0.1"), "new_cpc_cc": Decimal("0.2")}}
        service.set_autopilot_changes(cpc_changes=cpc_changes)
        mock_update_values.assert_called_with(
            ag_source, {"cpc_cc": Decimal("0.2")}, dash.constants.SystemUserType.AUTOPILOT
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot.helpers.update_ad_group_b1_sources_group_values")
    def test_set_autopilot_changes_only_cpc_rtb_as_one(self, mock_update_values):
        ag = dash.models.AdGroup.objects.get(id=1)
        ag_source = dash.models.AllRTBAdGroupSource(ag)
        cpc_changes = {ag_source: {"old_cpc_cc": Decimal("0.1"), "new_cpc_cc": Decimal("0.2")}}
        service.set_autopilot_changes(cpc_changes=cpc_changes, ad_group=ag)
        mock_update_values.assert_called_with(ag, {"cpc_cc": Decimal("0.2")}, dash.constants.SystemUserType.AUTOPILOT)
        mock_update_values.assert_called_once()

    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_only_budget(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")}}
        service.set_autopilot_changes(budget_changes=budget_changes)
        mock_update_values.assert_called_with(
            ag_source, {"daily_budget_cc": Decimal("200")}, dash.constants.SystemUserType.AUTOPILOT
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpc(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")}}
        cpc_changes = {ag_source: {"old_cpc_cc": Decimal("0.1"), "new_cpc_cc": Decimal("0.2")}}
        service.set_autopilot_changes(cpc_changes=cpc_changes, budget_changes=budget_changes)
        mock_update_values.assert_called_with(
            ag_source,
            {"cpc_cc": Decimal("0.2"), "daily_budget_cc": Decimal("200")},
            dash.constants.SystemUserType.AUTOPILOT,
        )
        mock_update_values.assert_called_once()

    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpc_no_change(self, mock_update_values):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        budget_changes = {ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("100")}}
        cpc_changes = {ag_source: {"old_cpc_cc": Decimal("0.1"), "new_cpc_cc": Decimal("0.1")}}
        service.set_autopilot_changes(cpc_changes=cpc_changes, budget_changes=budget_changes)
        self.assertEqual(mock_update_values.called, False)

    @patch("automation.autopilot.helpers.update_ad_group_b1_sources_group_values")
    @patch("automation.autopilot.helpers.update_ad_group_source_values")
    def test_set_autopilot_changes_budget_and_cpc_rtb_as_one(self, mock_update_values, mock_update_rtb):
        ag_source = dash.models.AdGroupSource.objects.get(id=1)
        ag = dash.models.AdGroup.objects.get(id=1)
        ag_source_rtb = dash.models.AllRTBAdGroupSource(ag)
        budget_changes = {
            ag_source: {"old_budget": Decimal("100"), "new_budget": Decimal("200")},
            ag_source_rtb: {"old_budget": Decimal("10"), "new_budget": Decimal("20")},
        }
        cpc_changes = {
            ag_source: {"old_cpc_cc": Decimal("0.1"), "new_cpc_cc": Decimal("0.2")},
            ag_source_rtb: {"old_cpc_cc": Decimal("0.11"), "new_cpc_cc": Decimal("0.22")},
        }
        ap = dash.constants.SystemUserType.AUTOPILOT
        service.set_autopilot_changes(cpc_changes=cpc_changes, budget_changes=budget_changes, ad_group=ag)
        mock_update_values.assert_called_with(
            ag_source, {"cpc_cc": Decimal("0.2"), "daily_budget_cc": Decimal("200")}, ap
        )
        mock_update_values.assert_called_once()
        mock_update_rtb.assert_called_with(ag, {"cpc_cc": Decimal("0.22"), "daily_budget_cc": Decimal("20")}, ap)
        mock_update_rtb.assert_called_once()

    @patch("automation.autopilot.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("0.3"))
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
            adg, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )
        self.assertEqual(new_budgets.get(paused_ad_group_source)["old_budget"], Decimal("100."))
        self.assertEqual(new_budgets.get(paused_ad_group_source)["new_budget"], Decimal("9"))
        self.assertEqual(
            new_budgets.get(paused_ad_group_source)["budget_comments"],
            [constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE],
        )
        self.assertEqual(paused_ad_group_source.get_current_settings().daily_budget_cc, Decimal("9"))
        self.assertEqual(
            active_ad_group_source.get_current_settings().daily_budget_cc, active_ad_group_source_old_budget
        )
        self.assertTrue(active_ad_group_source not in new_budgets)

    @patch("automation.autopilot.settings.BUDGET_AP_MIN_SOURCE_BUDGET", Decimal("10"))
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
            adg, {"fee": Decimal("0.15"), "margin": Decimal("0.3")}
        )

        adg.settings.refresh_from_db()
        self.assertTrue(paused_ad_group_source not in new_budgets)
        self.assertTrue(active_ad_group_source not in new_budgets)
        self.assertEqual(new_budgets.get(all_rtb_ad_group_source)["old_budget"], Decimal("30."))
        self.assertEqual(new_budgets.get(all_rtb_ad_group_source)["new_budget"], Decimal("10.0"))
        self.assertEqual(
            new_budgets.get(all_rtb_ad_group_source)["budget_comments"],
            [constants.DailyBudgetChangeComment.INITIALIZE_PILOT_PAUSED_SOURCE],
        )
        self.assertEqual(paused_ad_group_source.get_current_settings().daily_budget_cc, Decimal("100.0"))
        self.assertEqual(
            active_ad_group_source.get_current_settings().daily_budget_cc, active_ad_group_source_old_budget
        )
        self.assertEqual(adg.get_current_settings().b1_sources_group_daily_budget, Decimal("10.0"))

    @patch("automation.autopilot.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot.service.run_autopilot")
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
            ad_group=adg, adjust_cpcs=False, adjust_budgets=True, initialization=True, send_mail=False
        )
        self.assertTrue(paused_ad_group_source in changed_sources)
        self.assertTrue(changed_source in changed_sources)
        self.assertTrue(not_changed_source not in changed_sources)

    @patch("automation.autopilot.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot.service.run_autopilot")
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
            campaign=adg.campaign, adjust_cpcs=False, adjust_budgets=True, initialization=True, send_mail=False
        )
        self.assertEqual(set(), changed_sources)
        self.assertFalse(mock_set_paused.called)

    @patch("automation.autopilot.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_campaign_inactive(self, mock_run_autopilot, mock_set_paused):
        campaign = dash.models.Campaign.objects.get(pk=4)
        service.recalculate_budgets_campaign(campaign)
        mock_run_autopilot.assert_called_once_with(
            campaign=campaign, adjust_cpcs=False, adjust_budgets=True, initialization=True, send_mail=False
        )
        self.assertTrue(mock_set_paused.called)

    @patch("automation.autopilot.service._set_paused_ad_group_sources_to_minimum_values")
    @patch("automation.autopilot.service.run_autopilot")
    def test_recalculate_budget_autopilot_on_campaign_active(self, mock_run_autopilot, mock_set_paused):
        campaign = dash.models.Campaign.objects.get(pk=4)
        campaign.settings.update_unsafe(None, autopilot=True)
        service.recalculate_budgets_campaign(campaign)
        mock_run_autopilot.assert_called_once_with(
            campaign=campaign, adjust_cpcs=False, adjust_budgets=True, initialization=True, send_mail=False
        )
        self.assertFalse(mock_set_paused.called)

    @patch("redshiftapi.api_breakdowns.query")
    @patch("influx.gauge")
    def test_report_adgroups_data_to_influx(self, mock_influx, mock_query):
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

        mock_influx.assert_has_calls(
            [
                call("automation.autopilot_plus.adgroups_on", 2, autopilot="budget_autopilot"),
                call("automation.autopilot_plus.adgroups_on", 1, autopilot="cpc_autopilot"),
                call("automation.autopilot_plus.adgroups_on", 1, autopilot="campaign_autopilot"),
                call("automation.autopilot_plus.campaigns_on", 1, autopilot="campaign_autopilot"),
                call("automation.autopilot_plus.spend", Decimal("50"), autopilot="budget_autopilot", type="expected"),
                call("automation.autopilot_plus.spend", Decimal("13"), autopilot="campaign_autopilot", type="expected"),
                call(
                    "automation.autopilot_plus.spend", Decimal("12"), autopilot="campaign_autopilot", type="yesterday"
                ),
                call("automation.autopilot_plus.spend", Decimal("35"), autopilot="budget_autopilot", type="yesterday"),
                call("automation.autopilot_plus.spend", Decimal("10"), autopilot="cpc_autopilot", type="yesterday"),
            ]
        )

    @patch("redshiftapi.api_breakdowns.query")
    @patch("influx.gauge")
    def test_report_new_budgets_on_ap_to_influx(self, mock_influx, mock_query):
        mock_query.return_value = [
            {"ad_group_id": 1, "billing_cost": Decimal("15")},
            {"ad_group_id": 3, "billing_cost": Decimal("10")},
            {"ad_group_id": 4, "billing_cost": Decimal("20")},
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

        mock_influx.assert_has_calls(
            [
                call("automation.autopilot_plus.spend", Decimal("50"), autopilot="cpc_autopilot", type="actual"),
                call("automation.autopilot_plus.spend", Decimal("210"), autopilot="budget_autopilot", type="actual"),
                call("automation.autopilot_plus.spend", Decimal("50"), autopilot="campaign_autopilot", type="actual"),
                call("automation.autopilot_plus.sources_on", 1, autopilot="cpc_autopilot"),
                call("automation.autopilot_plus.sources_on", 4, autopilot="budget_autopilot"),
                call("automation.autopilot_plus.sources_on", 1, autopilot="campaign_autopilot"),
            ]
        )

    @patch("utils.dates_helper.local_today", return_value=datetime.date(2018, 1, 2))
    def test_adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled(self, mock_local_today):
        campaign = magic_mixer.blend(dash.models.Campaign)
        ad_groups = magic_mixer.cycle(3).blend(dash.models.AdGroup, campaign=campaign)
        ad_groups[0].settings.update(None, start_date=datetime.date(2018, 1, 1), end_date=datetime.date(2018, 2, 1))
        ad_groups[1].settings.update(None, start_date=datetime.date(2018, 1, 3), end_date=datetime.date(2018, 2, 1))
        ad_groups[2].settings.update(None, start_date=datetime.date(2018, 1, 3), end_date=None)

        with patch("dash.models.AdGroupSettings.update") as mock_settings_update:
            service.adjust_ad_groups_flight_times_on_campaign_budget_autopilot_enabled(campaign)
            mock_settings_update.assert_has_calls(
                [
                    call(
                        None, end_date=None, skip_automation=True, system_user=dash.constants.SystemUserType.AUTOPILOT
                    ),
                    call(
                        None,
                        start_date=datetime.date(2018, 1, 2),
                        end_date=None,
                        skip_automation=True,
                        system_user=dash.constants.SystemUserType.AUTOPILOT,
                    ),
                    call(
                        None,
                        start_date=datetime.date(2018, 1, 2),
                        end_date=None,
                        skip_automation=True,
                        system_user=dash.constants.SystemUserType.AUTOPILOT,
                    ),
                ]
            )
