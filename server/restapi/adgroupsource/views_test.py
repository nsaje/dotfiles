from django.urls import reverse

import dash.models
import core.models.source_type.model
from dash import constants
from utils.magic_mixer import magic_mixer

import mock
import json

from restapi.common.views_base_test import RESTAPITest


class AdGroupSourcesTest(RESTAPITest):
    @classmethod
    def adgroupsource_repr(
        cls, source="yahoo", cpc="0.600", daily_budget="50.00", state=constants.AdGroupSourceSettingsState.ACTIVE
    ):
        representation = {
            "source": source,
            "cpc": cpc,
            "dailyBudget": daily_budget,
            "state": constants.AdGroupSourceSettingsState.get_name(state),
        }
        return cls.normalize(representation)

    def validate_against_db(self, ad_group_id, adgroupsourcesettings):
        slug = adgroupsourcesettings["source"]
        agss_db = dash.models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id, source__bidder_slug=slug
        ).get_current_settings()
        expected = self.adgroupsource_repr(
            source=slug, cpc=agss_db.cpc_cc, daily_budget=agss_db.daily_budget_cc, state=agss_db.state
        )
        self.assertEqual(expected, adgroupsourcesettings)

    def test_adgroups_sources_list(self):
        r = self.client.get(reverse("adgroups_sources_list", kwargs={"ad_group_id": 2040}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(2040, item)

    def test_adgroups_sources_put(self):
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account__users=[self.user])
        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=(slug for slug in ["a", "b", "c"])
        )
        test_ags = [
            self.adgroupsource_repr(
                source=ad_group_sources[0].source.bidder_slug,
                daily_budget="12.3800",
                cpc="0.6120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=ad_group_sources[2].source.bidder_slug,
                daily_budget="15.3800",
                cpc="0.5120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
        ]
        r = self.client.put(
            reverse("adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}), test_ags, format="json"
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.validate_against_db(ad_group.id, resp_json["data"][0])
        self.validate_against_db(ad_group.id, resp_json["data"][1])
        self.validate_against_db(ad_group.id, resp_json["data"][2])

        resp_a = next(x for x in resp_json["data"] if x["source"] == "a")
        resp_c = next(x for x in resp_json["data"] if x["source"] == "c")
        self.assertEqual(test_ags[0], resp_a)
        self.assertEqual(test_ags[1], resp_c)

    def test_adgroups_sources_put_source_not_present(self):
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account__users=[self.user])
        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=(slug for slug in ["a", "b", "c"])
        )
        ad_group_source_not_present = magic_mixer.blend(dash.models.AdGroupSource, source__bidder_slug="d")
        test_ags = [
            self.adgroupsource_repr(
                source=ad_group_sources[0].source.bidder_slug,
                daily_budget="12.3800",
                cpc="0.6120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=ad_group_source_not_present.source.bidder_slug,
                daily_budget="15.3800",
                cpc="0.5120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
        ]
        r = self.client.put(
            reverse("adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}), test_ags, format="json"
        )
        self.assertResponseError(r, "ValidationError")

    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_max_daily_budget", return_value=89.77)
    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_min_daily_budget", return_value=7.11)
    @mock.patch.object(core.models.source_type.model.SourceType, "get_min_cpc", return_value=0.1211)
    def test_adgroups_sources_rounding(self, min_cpc_mock, min_daily_budget_mock, max_daily_budget_mock):
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account__users=[self.user])
        ad_group.settings.update_unsafe(None, cpc_cc=0.7792)
        ad_group_sources = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=("a",))
        # min cpc - would return 0.12 without rounding ceiling
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, cpc="0.1200")]
        r = self.client.put(
            reverse("adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}), test_ags, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.13" in json.loads(r.content)["details"]["cpc"][0])

        # max cpc - would return 0.78 without rounding floor
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, cpc="0.78")]
        r = self.client.put(
            reverse("adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}), test_ags, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.77" in json.loads(r.content)["details"]["cpc"][0])

        # min daily budget - would return 7 without rounding ceiling
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, daily_budget="7")]
        r = self.client.put(
            reverse("adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}), test_ags, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("8" in json.loads(r.content)["details"]["dailyBudget"][0])

        # max daily budget - would return 90 without rounding floor
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, daily_budget="90")]
        r = self.client.put(
            reverse("adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}), test_ags, format="json"
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("89" in json.loads(r.content)["details"]["dailyBudget"][0])
