import json
from decimal import Decimal

import mock
from django.urls import reverse

import core.models.ad_group
from core.models import all_rtb
from dash import constants
from dash import models
from restapi.common.views_base_test_case import FutureRESTAPITestCase
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyAdGroupSourcesRTBTest(RESTAPITestCase):
    @classmethod
    def adgroupsourcertb_repr(
        cls,
        group_enabled=True,
        daily_budget=all_rtb.AllRTBSource.default_daily_budget_cc,
        state=constants.AdGroupSourceSettingsState.ACTIVE,
        cpc=all_rtb.AllRTBSource.default_cpc_cc,
        cpm=None,
    ):
        representation = {
            "groupEnabled": group_enabled,
            "dailyBudget": daily_budget,
            "state": constants.AdGroupSourceSettingsState.get_name(state),
            "cpc": cpc if cpm is None else None,
            "cpm": cpm,
        }
        return cls.normalize(representation)

    def validate_against_db(self, ad_group_id, agsrtb):
        settings_db = core.models.ad_group.AdGroup.objects.get(pk=ad_group_id).get_current_settings()
        if settings_db.ad_group.bidding_type == constants.BiddingType.CPM:
            expected = self.adgroupsourcertb_repr(
                group_enabled=settings_db.b1_sources_group_enabled,
                daily_budget=settings_db.b1_sources_group_daily_budget.quantize(Decimal("1.00")),
                state=settings_db.b1_sources_group_state,
                cpm=settings_db.b1_sources_group_cpm,
            )
        else:
            expected = self.adgroupsourcertb_repr(
                group_enabled=settings_db.b1_sources_group_enabled,
                daily_budget=settings_db.b1_sources_group_daily_budget.quantize(Decimal("1.00")),
                state=settings_db.b1_sources_group_state,
                cpc=settings_db.b1_sources_group_cpc_cc,
            )
        self.assertEqual(expected, agsrtb)

    def test_adgroups_sources_rtb_get_cpc(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPC
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_b1_sources_group_cpc_cc = Decimal("1.0100")
        settings.local_b1_sources_group_cpm = Decimal("1.0100")
        settings.save(None)

        r = self.client.get(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id})
        )
        resp_json = self.assertResponseValid(r)
        self.assertIsNotNone(resp_json["data"]["cpc"])
        self.assertIsNone(resp_json["data"]["cpm"])
        self.validate_against_db(ad_group.id, resp_json["data"])

    def test_adgroups_sources_rtb_get_cpm(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_b1_sources_group_cpc_cc = Decimal("1.0100")
        settings.local_b1_sources_group_cpm = Decimal("1.0100")
        settings.save(None)

        r = self.client.get(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id})
        )
        resp_json = self.assertResponseValid(r)
        self.assertIsNone(resp_json["data"]["cpc"])
        self.assertIsNotNone(resp_json["data"]["cpm"])
        self.validate_against_db(ad_group.id, resp_json["data"])

    def test_adgroups_sources_rtb_put_cpc(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPC
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_b1_sources_group_cpc_cc = Decimal("1.0100")
        settings.local_b1_sources_group_cpm = Decimal("1.0100")
        settings.save(None)

        test_rtbs = self.adgroupsourcertb_repr(
            group_enabled=True, daily_budget="12.38", state=constants.AdGroupSettingsState.ACTIVE, cpc="0.1230"
        )
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_rtbs,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEquals("0.1230", resp_json["data"]["cpc"])
        self.assertIsNone(resp_json["data"]["cpm"])
        self.validate_against_db(ad_group.id, resp_json["data"])
        self.assertEqual(test_rtbs, resp_json["data"])

    def test_adgroups_sources_rtb_put_cpm(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_b1_sources_group_cpc_cc = Decimal("1.0100")
        settings.local_b1_sources_group_cpm = Decimal("1.0100")
        settings.save(None)

        test_rtbs = self.adgroupsourcertb_repr(
            group_enabled=True, daily_budget="12.38", state=constants.AdGroupSettingsState.ACTIVE, cpm="1.1230"
        )
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_rtbs,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertIsNone(resp_json["data"]["cpc"])
        self.assertEquals("1.1230", resp_json["data"]["cpm"])
        self.validate_against_db(ad_group.id, resp_json["data"])
        self.assertEqual(test_rtbs, resp_json["data"])

    def test_adgroups_sources_rtb_put_default_values(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPC
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_b1_sources_group_cpc_cc = Decimal("1.0100")
        settings.local_b1_sources_group_cpm = Decimal("1.0100")
        settings.save(None)

        test_rtbs = self.adgroupsourcertb_repr(group_enabled=True, state=constants.AdGroupSettingsState.ACTIVE)
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_rtbs,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertIsNotNone(resp_json["data"]["cpc"])
        self.assertIsNone(resp_json["data"]["cpm"])
        self.validate_against_db(ad_group.id, resp_json["data"])
        self.assertEqual(test_rtbs, resp_json["data"])

    def test_adgroups_sources_rtb_bidding_type_fail(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPC
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.autopilot_state = constants.AdGroupSettingsAutopilotState.INACTIVE
        settings.local_b1_sources_group_cpc_cc = Decimal("1.0100")
        settings.local_b1_sources_group_cpm = Decimal("1.0100")
        settings.save(None)

        test_rtbs = self.adgroupsourcertb_repr()
        test_rtbs["cpm"] = "1.11"

        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_rtbs,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("cpm" in json.loads(r.content)["details"])

        ad_group.bidding_type = constants.BiddingType.CPM
        ad_group.save(None)

        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            data=test_rtbs,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("cpc" in json.loads(r.content)["details"])

    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_max_daily_budget", return_value=89.77)
    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_min_daily_budget", return_value=7.11)
    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_min_cpc", return_value=0.1211)
    def test_adgroups_sources_rtb_rounding_cpc(self, min_cpc_mock, min_daily_budget_mock, max_daily_budget_mock):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(models.AdGroup, campaign__account=account)
        ad_group.settings.update_unsafe(
            None, cpc=0.7792, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        # min cpc - would return 0.12 without rounding ceiling
        test_agsr = self.adgroupsourcertb_repr(cpc="0.1200")
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            test_agsr,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.13" in json.loads(r.content)["details"]["cpc"][0])

        # max cpc - over RTB sources CPC maximum
        test_agsr = self.adgroupsourcertb_repr(cpc="30.00")
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            test_agsr,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("Maximum CPC on RTB Sources is" in json.loads(r.content)["details"]["cpc"][0])

        # min daily budget - would return 7 without rounding ceiling
        test_agsr = self.adgroupsourcertb_repr(daily_budget="7")
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            test_agsr,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("8" in json.loads(r.content)["details"]["dailyBudget"][0])

        # max daily budget - would return 90 without rounding floor
        test_agsr = self.adgroupsourcertb_repr(daily_budget="90")
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            test_agsr,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("89" in json.loads(r.content)["details"]["dailyBudget"][0])

    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_min_cpm", return_value=0.1211)
    def test_adgroups_sources_rtb_rounding_cpm(self, min_cpm_mock):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM)
        ad_group.settings.update_unsafe(
            None, cpm=0.7792, autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE
        )

        # min cpm - would return 0.12 without rounding ceiling
        test_agsr = self.adgroupsourcertb_repr(cpm="0.1200")
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            test_agsr,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.13" in json.loads(r.content)["details"]["cpm"][0])

        # max cpm - over RTB sources CPM maximum
        test_agsr = self.adgroupsourcertb_repr(cpm="26.0")
        r = self.client.put(
            reverse("restapi.adgroupsourcesrtb.v1:adgroups_sources_rtb_details", kwargs={"ad_group_id": ad_group.id}),
            test_agsr,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("Maximum CPM on RTB Sources is" in json.loads(r.content)["details"]["cpm"][0])


class AdGroupSourcesRTBTest(FutureRESTAPITestCase, LegacyAdGroupSourcesRTBTest):
    pass
