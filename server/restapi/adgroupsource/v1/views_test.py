import json
from decimal import Decimal

import mock
from django.urls import reverse

import core.models.source_type.model
import dash.models
from dash import constants
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class AdGroupSourcesTest(RESTAPITestCase):
    @classmethod
    def adgroupsource_repr(
        cls,
        source="yahoo",
        cpc="0.600",
        cpm=None,
        daily_budget="50.00",
        state=constants.AdGroupSourceSettingsState.ACTIVE,
    ):
        representation = {
            "source": source,
            "cpc": cpc if cpm is None else None,
            "cpm": cpm,
            "dailyBudget": daily_budget,
            "state": constants.AdGroupSourceSettingsState.get_name(state),
        }
        return cls.normalize(representation)

    def validate_against_db(self, ad_group_id, adgroupsourcesettings):
        slug = adgroupsourcesettings["source"]
        agss_db = dash.models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id, source__bidder_slug=slug
        ).get_current_settings()

        if agss_db.ad_group_source.ad_group.bidding_type == constants.BiddingType.CPM:
            expected = self.adgroupsource_repr(
                source=slug, cpm=agss_db.local_cpm_proxy, daily_budget=agss_db.daily_budget_cc, state=agss_db.state
            )
        else:
            expected = self.adgroupsource_repr(
                source=slug, cpc=agss_db.local_cpc_cc_proxy, daily_budget=agss_db.daily_budget_cc, state=agss_db.state
            )

        self.assertEqual(expected, adgroupsourcesettings)

    def test_adgroups_sources_list_cpc(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPC
        )

        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=(slug for slug in ["a", "b", "c"])
        )
        for ad_group_source in ad_group_sources:
            settings = ad_group_source.get_current_settings().copy_settings()
            settings.state = constants.AdGroupSettingsState.ACTIVE
            settings.local_cpc_cc = Decimal("0.1200")
            settings.local_cpm = Decimal("1.1200")
            settings.save(None)

        r = self.client.get(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.assertIsNotNone(item["cpc"])
            self.assertIsNone(item["cpm"])
            self.validate_against_db(ad_group.id, item)

    def test_adgroups_sources_list_cpm(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group = magic_mixer.blend(
            core.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM
        )

        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=(slug for slug in ["a", "b", "c"])
        )
        for ad_group_source in ad_group_sources:
            settings = ad_group_source.get_current_settings().copy_settings()
            settings.state = constants.AdGroupSettingsState.ACTIVE
            settings.local_cpc_cc = Decimal("0.1200")
            settings.local_cpm = Decimal("1.1200")
            settings.save(None)

        r = self.client.get(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.assertIsNone(item["cpc"])
            self.assertIsNotNone(item["cpm"])
            self.validate_against_db(ad_group.id, item)

    def test_adgroups_sources_put_cpc(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            dash.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPC
        )
        ad_group.settings.update_unsafe(None, b1_sources_group_enabled=False)
        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource,
            ad_group=ad_group,
            source__bidder_slug=(slug for slug in ["a", "b", "c"]),
            source__source_type__min_daily_budget=Decimal("0.0"),
            source__source_type__max_daily_budget=Decimal("1000.0"),
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
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.validate_against_db(ad_group.id, resp_json["data"][0])
        self.validate_against_db(ad_group.id, resp_json["data"][1])
        self.validate_against_db(ad_group.id, resp_json["data"][2])

        resp_a = next(x for x in resp_json["data"] if x["source"] == "a")
        resp_c = next(x for x in resp_json["data"] if x["source"] == "c")
        self.assertEqual(test_ags[0], resp_a)
        self.assertEqual(test_ags[1], resp_c)

    def test_adgroups_sources_put_cpm(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            dash.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM
        )
        ad_group.settings.update_unsafe(None, b1_sources_group_enabled=False)
        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource,
            ad_group=ad_group,
            source__bidder_slug=(slug for slug in ["a", "b", "c"]),
            source__source_type__min_daily_budget=Decimal("0.0"),
            source__source_type__max_daily_budget=Decimal("1000.0"),
        )
        test_ags = [
            self.adgroupsource_repr(
                source=ad_group_sources[0].source.bidder_slug,
                daily_budget="12.3800",
                cpm="0.6120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=ad_group_sources[2].source.bidder_slug,
                daily_budget="15.3800",
                cpm="0.5120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
        ]
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.validate_against_db(ad_group.id, resp_json["data"][0])
        self.validate_against_db(ad_group.id, resp_json["data"][1])

        resp_a = next(x for x in resp_json["data"] if x["source"] == "a")
        resp_c = next(x for x in resp_json["data"] if x["source"] == "c")
        self.assertEqual(test_ags[0], resp_a)
        self.assertEqual(test_ags[1], resp_c)

    def test_adgroups_sources_put_cpc_source_not_present(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)
        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource,
            ad_group=ad_group,
            source__bidder_slug=(slug for slug in ["a", "b", "c"]),
            source__source_type__min_daily_budget=Decimal("0.0"),
            source__source_type__max_daily_budget=Decimal("1000.0"),
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
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_sources_put_cpm_source_not_present(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            dash.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM
        )
        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource,
            ad_group=ad_group,
            source__bidder_slug=(slug for slug in ["a", "b", "c"]),
            source__source_type__min_daily_budget=Decimal("0.0"),
            source__source_type__max_daily_budget=Decimal("1000.0"),
        )
        ad_group_source_not_present = magic_mixer.blend(dash.models.AdGroupSource, source__bidder_slug="d")
        test_ags = [
            self.adgroupsource_repr(
                source=ad_group_sources[0].source.bidder_slug,
                daily_budget="12.3800",
                cpm="0.6120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=ad_group_source_not_present.source.bidder_slug,
                daily_budget="15.3800",
                cpm="0.5120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
        ]
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def text_adgroups_sources_put_cpc_bidding_type_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            dash.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPC
        )
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
        test_ags[1]["cpm"] = 1.3
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def text_adgroups_sources_put_cpm_bidding_type_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            dash.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM
        )
        ad_group_sources = magic_mixer.cycle(3).blend(
            dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=(slug for slug in ["a", "b", "c"])
        )
        test_ags = [
            self.adgroupsource_repr(
                source=ad_group_sources[0].source.bidder_slug,
                daily_budget="12.3800",
                cpm="0.6120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=ad_group_sources[2].source.bidder_slug,
                daily_budget="15.3800",
                cpm="0.5120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
        ]
        test_ags[1]["cpc"] = 1.3
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_adgroups_sources_post(self):
        credentials = magic_mixer.blend(dash.models.SourceCredentials)
        source = magic_mixer.blend(dash.models.Source, source_credentials=credentials, bidder_slug="a")
        magic_mixer.blend(dash.models.DefaultSourceSettings, credentials=credentials, source=source)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account.allowed_sources.add(source)
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)

        test_ags = self.adgroupsource_repr(
            source=source.bidder_slug,
            daily_budget="12.3800",
            cpc="0.6120",
            state=constants.AdGroupSourceSettingsState.INACTIVE,
        )
        r = self.client.post(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        resp_json = self.assertResponseValid(r)

        self.validate_against_db(ad_group.id, resp_json["data"])
        self.assertEqual(test_ags, resp_json["data"])

    def test_adgroups_sources_post_error(self):
        source = magic_mixer.blend(dash.models.Source, bidder_slug="a")
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)

        test_ags = self.adgroupsource_repr(
            source=source.bidder_slug,
            daily_budget="12.3800",
            cpc="0.6120",
            state=constants.AdGroupSourceSettingsState.INACTIVE,
        )
        r = self.client.post(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn("media source can not be added because it is not allowed on this account", resp_json["details"])

    def test_adgroups_sources_post_multiple(self):
        credentials = magic_mixer.blend(dash.models.SourceCredentials)
        sources = magic_mixer.cycle(3).blend(
            dash.models.Source, source_credentials=credentials, bidder_slug=(slug for slug in ["a", "b", "c"])
        )
        magic_mixer.cycle(3).blend(
            dash.models.DefaultSourceSettings, credentials=credentials, source=(s for s in sources)
        )
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account.allowed_sources.add(*sources)
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)

        test_ags = [
            self.adgroupsource_repr(
                source=sources[0].bidder_slug,
                daily_budget="12.3800",
                cpc="0.6120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=sources[1].bidder_slug,
                daily_budget="15.3800",
                cpc="0.5120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=sources[2].bidder_slug,
                daily_budget="12.3400",
                cpc="0.1234",
                state=constants.AdGroupSourceSettingsState.ACTIVE,
            ),
        ]

        r = self.client.post(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.validate_against_db(ad_group.id, resp_json["data"][0])
        self.validate_against_db(ad_group.id, resp_json["data"][1])
        self.validate_against_db(ad_group.id, resp_json["data"][2])

        resp_a = next(x for x in resp_json["data"] if x["source"] == "a")
        resp_b = next(x for x in resp_json["data"] if x["source"] == "b")
        resp_c = next(x for x in resp_json["data"] if x["source"] == "c")
        self.assertEqual(test_ags[0], resp_a)
        self.assertEqual(test_ags[1], resp_b)
        self.assertEqual(test_ags[2], resp_c)

    def test_adgroups_sources_post_multiple_error(self):
        sources = magic_mixer.cycle(2).blend(dash.models.Source, bidder_slug=(slug for slug in ["a", "b"]))
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)

        test_ags = [
            self.adgroupsource_repr(
                source=sources[0].bidder_slug,
                daily_budget="12.3800",
                cpc="0.6120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
            self.adgroupsource_repr(
                source=sources[1].bidder_slug,
                daily_budget="15.3800",
                cpc="0.5120",
                state=constants.AdGroupSourceSettingsState.INACTIVE,
            ),
        ]

        r = self.client.post(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")

        for error_msg in resp_json["details"]:
            self.assertIn("media source can not be added because it is not allowed on this account", error_msg)

    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_max_daily_budget", return_value=89.77)
    @mock.patch.object(core.models.source_type.model.SourceType, "get_etfm_min_daily_budget", return_value=7.11)
    @mock.patch.object(core.models.source_type.model.SourceType, "get_min_cpc", return_value=0.1211)
    def test_adgroups_sources_cpc_daily_budget_rounding(
        self, min_cpc_mock, min_daily_budget_mock, max_daily_budget_mock
    ):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=account)
        ad_group.settings.update_unsafe(None, cpc=0.7792, b1_sources_group_enabled=False)
        ad_group_sources = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=("a",))

        # min cpc - would return 0.12 without rounding ceiling
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, cpc="0.1200")]
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.13" in json.loads(r.content)["details"]["cpc"][0])

        # min daily budget - would return 7 without rounding ceiling
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, daily_budget="7")]
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("8" in json.loads(r.content)["details"]["dailyBudget"][0])

        # max daily budget - would return 90 without rounding floor
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, daily_budget="90")]
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("89" in json.loads(r.content)["details"]["dailyBudget"][0])

    @mock.patch.object(core.models.source_type.model.SourceType, "get_min_cpm", return_value=0.1211)
    def test_adgroups_sources_cpm_rounding(self, min_cpm_mock):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(
            dash.models.AdGroup, campaign__account=account, bidding_type=constants.BiddingType.CPM
        )
        ad_group.settings.update_unsafe(None, cpm=0.7792)
        ad_group_sources = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source__bidder_slug=("a",))

        # min cpm - would return 0.12 without rounding ceiling
        test_ags = [self.adgroupsource_repr(source=ad_group_sources.source.bidder_slug, cpm="0.1200")]
        r = self.client.put(
            reverse("restapi.adgroupsource.v1:adgroups_sources_list", kwargs={"ad_group_id": ad_group.id}),
            test_ags,
            format="json",
        )
        self.assertResponseError(r, "ValidationError")
        self.assertTrue("0.13" in json.loads(r.content)["details"]["cpm"][0])
