from decimal import Decimal
from django.core.urlresolvers import reverse

from restapi.common.views_base_test import RESTAPITest
from dash import constants, models
from core import source
import core.entity.adgroup

from utils.magic_mixer import magic_mixer
import mock
import json


class AdGroupSourcesRTBTest(RESTAPITest):
    @classmethod
    def adgroupsourcertb_repr(
        cls,
        group_enabled=True,
        daily_budget=source.AllRTBSource.default_daily_budget_cc,
        state=constants.AdGroupSourceSettingsState.ACTIVE,
        cpc=source.AllRTBSource.default_cpc_cc,
    ):
        representation = {
            "groupEnabled": group_enabled,
            "dailyBudget": daily_budget,
            "state": constants.AdGroupSourceSettingsState.get_name(state),
            "cpc": cpc,
        }
        return cls.normalize(representation)

    def validate_against_db(self, ad_group_id, agsrtb):
        settings_db = core.entity.adgroup.AdGroup.objects.get(pk=ad_group_id).get_current_settings()
        expected = self.adgroupsourcertb_repr(
            group_enabled=settings_db.b1_sources_group_enabled,
            daily_budget=settings_db.b1_sources_group_daily_budget.quantize(Decimal("1.00")),
            state=settings_db.b1_sources_group_state,
            cpc=settings_db.b1_sources_group_cpc_cc,
        )
        self.assertEqual(expected, agsrtb)

    def test_adgroups_sources_rtb_get(self):
        r = self.client.get(reverse("adgroups_sources_rtb_details", kwargs={"ad_group_id": 2040}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json["data"])

    def test_adgroups_sources_rtb_put(self):
        test_rtbs = self.adgroupsourcertb_repr(
            group_enabled=True, daily_budget="12.38", state=constants.AdGroupSettingsState.ACTIVE, cpc="0.1230"
        )
        r = self.client.put(
            reverse("adgroups_sources_rtb_details", kwargs={"ad_group_id": 2040}), data=test_rtbs, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json["data"])
        self.assertEqual(test_rtbs, resp_json["data"])

    def test_adgroups_sources_rtb_put_default_values(self):
        test_rtbs = self.adgroupsourcertb_repr(group_enabled=True, state=constants.AdGroupSettingsState.ACTIVE)
        r = self.client.put(
            reverse("adgroups_sources_rtb_details", kwargs={"ad_group_id": 2040}), data=test_rtbs, format="json"
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json["data"])
        self.assertEqual(test_rtbs, resp_json["data"])

    @mock.patch.object(core.source.source_type.model.SourceType, "get_etfm_max_daily_budget", return_value=89.77)
    @mock.patch.object(core.source.source_type.model.SourceType, "get_etfm_min_daily_budget", return_value=7.11)
    @mock.patch.object(core.source.source_type.model.SourceType, "get_etfm_min_cpc", return_value=0.1211)
    def test_adgroups_sources_rtb_rounding(self, min_cpc_mock, min_daily_budget_mock, max_daily_budget_mock):
        ad_group = magic_mixer.blend(models.AdGroup, campaign__account__users=[self.user])
        ad_group.settings.update_unsafe(
            None, cpc_cc=0.7792, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        # min cpc - would return 0.12 without rounding ceiling
        test_agsr = self.adgroupsourcertb_repr(cpc="0.1200")
        r = self.client.put(
            reverse("adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}), test_agsr, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.13" in json.loads(r.content)["details"]["cpc"][0])

        # max cpc - would return 0.78 without rounding floor
        test_agsr = self.adgroupsourcertb_repr(cpc="0.78")
        r = self.client.put(
            reverse("adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}), test_agsr, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.77" in json.loads(r.content)["details"]["cpc"][0])

        # min daily budget - would return 7 without rounding ceiling
        test_agsr = self.adgroupsourcertb_repr(daily_budget="7")
        r = self.client.put(
            reverse("adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}), test_agsr, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("8" in json.loads(r.content)["details"]["dailyBudget"][0])

        # max daily budget - would return 90 without rounding floor
        test_agsr = self.adgroupsourcertb_repr(daily_budget="90")
        r = self.client.put(
            reverse("adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}), test_agsr, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("89" in json.loads(r.content)["details"]["dailyBudget"][0])
