import collections
import json
import urllib.error
import urllib.parse
import urllib.request
from operator import itemgetter

import mock
from django.test import override_settings
from django.urls import reverse

import dash.constants
import dash.features.custom_flags.constants
import dash.features.ga
import dash.features.geolocation
import dash.models
from core.models.settings.ad_group_source_settings.validation import AdGroupSourceSettingsValidatorMixin
from dash.features import custom_flags
from utils import dates_helper
from utils import zlogging
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest

logger = zlogging.getLogger(__name__)
logger.setLevel(zlogging.INFO)


@override_settings(AD_LOOKUP_AD_GROUP_ID=9999)
class AdGroupsSourcesTest(K1APIBaseTest):
    @mock.patch("automation.campaignstop.get_campaignstop_states")
    def test_get_ad_groups_sources(self, mock_get_campaignstop_states):
        mock_get_campaignstop_states.return_value = collections.defaultdict(
            lambda: {"allowed_to_run": True, "min_allowed_start_date": dates_helper.local_today()}
        )
        response = self.client.get(reverse("k1api.ad_groups.sources"), {"source_types": "b1"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 2)
        data = sorted(data, key=itemgetter("ad_group_id"))

        self.assertDictEqual(
            data[0],
            {
                "ad_group_id": 1,
                "source_id": 6,
                "slug": "b1_adiant",
                "state": 2,
                "daily_budget_cc": "1.5000",
                "source_campaign_key": ["fake"],
                "tracking_code": "tracking1&tracking2",
                "blockers": {},
            },
        )

        self.assertDictEqual(
            data[1],
            {
                "ad_group_id": 2,
                "source_id": 7,
                "slug": "b1_google",
                "state": 1,
                "daily_budget_cc": "1.6000",
                "source_campaign_key": ["fake"],
                "tracking_code": "tracking1&tracking2",
                "blockers": {},
            },
        )

    @mock.patch("automation.campaignstop.get_campaignstop_states")
    def test_get_ad_group_sources_campaignstop(self, mock_get_campaignstop_states):
        mock_get_campaignstop_states.return_value = collections.defaultdict(
            lambda: {"allowed_to_run": True, "min_allowed_start_date": dates_helper.local_today()}
        )
        source = magic_mixer.blend(dash.models.Source, source_type__type="abc")
        campaign = magic_mixer.blend(dash.models.Campaign, account_id=1, real_time_campaign_stop=True)
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupRunningStatus.ACTIVE, end_date=None)
        ad_group_source = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source=source)
        ad_group_source.settings.update_unsafe(
            None,
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            cpc_cc="0.12",
            cpm="0.12",
            daily_budget_cc="50.00",
            ad_group_source=ad_group_source,
        )

        response = self.client.get(reverse("k1api.ad_groups.sources"), {"ad_group_ids": str(ad_group.id)})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(1, len(data))
        self.assertEqual(dash.constants.AdGroupSourceSettingsState.ACTIVE, data[0]["state"])

        mock_get_campaignstop_states.return_value = collections.defaultdict(
            lambda: {"allowed_to_run": False, "min_allowed_start_date": dates_helper.local_today()}
        )

        response = self.client.get(reverse("k1api.ad_groups.sources"), {"ad_group_ids": str(ad_group.id)})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(dash.constants.AdGroupSourceSettingsState.INACTIVE, data[0]["state"])

    @mock.patch.object(AdGroupSourceSettingsValidatorMixin, "clean")
    def test_get_ad_groups_source(self, mock_validator):
        today = dates_helper.local_today()
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(dash.models.Account)
        credit_line_item = dash.models.CreditLineItem.objects.create(
            request,
            today,
            today,
            100,
            account=account,
            service_fee="0.1",
            license_fee="0.2",
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        dash.models.BudgetLineItem.objects.create(request, campaign, credit_line_item, today, today, 100, margin="0.1")
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign)
        source = dash.models.Source.objects.get(bidder_slug="b1_google")
        ad_group_source = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source=source)
        ad_group_source.settings.update_unsafe(None, daily_budget_cc="50.00", ad_group_source=ad_group_source)

        response = self.client.get(
            reverse("k1api.ad_groups.sources"), {"source_types": "b1", "ad_group_ids": [ad_group.id]}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 1)

        self.assertDictEqual(
            data[0],
            {
                "ad_group_id": ad_group.id,
                "source_id": 7,
                "slug": "b1_google",
                "state": 2,
                "daily_budget_cc": "32.4000",
                "source_campaign_key": {},
                "tracking_code": ad_group.settings.tracking_code,
                "blockers": {},
            },
        )

    @mock.patch.object(AdGroupSourceSettingsValidatorMixin, "clean")
    def test_get_ad_groups_source_adlookup(self, mock_validator):
        today = dates_helper.local_today()
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(dash.models.Account)
        credit_line_item = dash.models.CreditLineItem.objects.create(
            request,
            today,
            today,
            100,
            account=account,
            service_fee="0.1",
            license_fee="0.2",
            status=dash.constants.CreditLineItemStatus.SIGNED,
        )
        campaign = magic_mixer.blend(dash.models.Campaign, account=account)
        dash.models.BudgetLineItem.objects.create(request, campaign, credit_line_item, today, today, 100, margin="0.1")
        ad_group = magic_mixer.blend(dash.models.AdGroup, campaign=campaign, id=9999)
        source = dash.models.Source.objects.get(bidder_slug="b1_google")
        ad_group_source = magic_mixer.blend(dash.models.AdGroupSource, ad_group=ad_group, source=source)
        ad_group_source.settings.update_unsafe(None, daily_budget_cc="50.00", ad_group_source=ad_group_source)

        response = self.client.get(
            reverse("k1api.ad_groups.sources"), {"source_types": "b1", "ad_group_ids": [ad_group.id]}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 1)

        self.assertDictEqual(
            data[0],
            {
                "ad_group_id": ad_group.id,
                "source_id": 7,
                "slug": "b1_google",
                "state": 1,
                "daily_budget_cc": "32.4000",
                "source_campaign_key": {},
                "tracking_code": ad_group.settings.tracking_code,
                "blockers": {},
            },
        )

    def test_get_ad_groups_exchanges_with_id(self):
        response = self.client.get(reverse("k1api.ad_groups.sources"), {"ad_group_ids": 1, "source_types": "b1"})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        self.assertEqual(len(data), 1)

        self.assertDictEqual(
            data[0],
            {
                "ad_group_id": 1,
                "source_id": 6,
                "slug": "b1_adiant",
                "state": 2,
                "daily_budget_cc": "1.5000",
                "source_campaign_key": ["fake"],
                "tracking_code": "tracking1&tracking2",
                "blockers": {},
            },
        )

    def test_set_source_campaign_key(self):
        ags = dash.models.AdGroupSource.objects.get(pk=1)
        ags.source_campaign_key = None
        ags.save()

        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources"),
            json.dumps({"source_campaign_key": ["abc"]}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode({"ad_group_id": 1, "source_slug": "adblade"}),
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        ags = dash.models.AdGroupSource.objects.get(pk=1)
        self.assertEqual(ags.source_campaign_key, ["abc"])

    def test_update_ad_group_source(self):
        params = {"ad_group_id": 1, "source_slug": "adblade"}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources"),
            json.dumps({"state": 2}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        a = dash.models.AdGroupSource.objects.get(ad_group__id=1, source__bidder_slug="adblade")

        self.assertEqual(a.get_current_settings().state, 2)

    def test_update_ad_group_source_refuse_change(self):
        params = {"ad_group_id": 1, "source_slug": "adblade"}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources"),
            json.dumps({"source_campaign_key": ""}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot change", data["error"])

    def test_update_ad_group_source_state_no_ad_group(self):
        params = {"ad_group_id": 12345, "source_slug": "adblade"}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources"),
            json.dumps({"state": 2}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "No AdGroupSource exists for ad_group_id: 12345 with bidder_slug adblade")

    def test_update_ad_group_source_state_incorrect_body(self):
        params = {"slug": "adblade"}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources"),
            json.dumps({"state": 2}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["error"], "Must provide ad_group_id, source_slug and conf")

    def test_update_ad_group_source_blockers(self):
        params = {"ad_group_id": 1}
        put_body = {"adblade": {"interest-targeting": "Waiting for interest targeting to be set manually."}}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources.blockers"),
            json.dumps(put_body),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["response"], put_body)

        ad_group_source = dash.models.AdGroupSource.objects.get(ad_group_id=1, source__bidder_slug="adblade")
        self.assertEqual(ad_group_source.blockers, put_body["adblade"])

    def test_update_ad_group_source_blockers_ad_group_does_not_exist(self):
        params = {"ad_group_id": 1234}
        put_body = {"adblade": {"interest-targeting": "Waiting for interest targeting to be set manually."}}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources.blockers"),
            json.dumps(put_body),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["response"], {})

    def test_update_ad_group_source_blockers_ad_group_source_does_not_exist(self):
        params = {"ad_group_id": 1}
        put_body = {"asdf": {"interest-targeting": "Waiting for interest targeting to be set manually."}}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources.blockers"),
            json.dumps(put_body),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["response"], {})

    def test_update_ad_group_source_blockers_remove(self):
        ad_group_source = dash.models.AdGroupSource.objects.get(ad_group_id=1, source__bidder_slug="adblade")
        ad_group_source.blockers = {"interest-targeting": "Waiting for interest targeting to be set manually."}
        ad_group_source.save()

        params = {"ad_group_id": 1}
        put_body = {"adblade": {"interest-targeting": None}}
        response = self.client.generic(
            "PUT",
            reverse("k1api.ad_groups.sources.blockers"),
            json.dumps(put_body),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode(params),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["response"], {"adblade": {}})

        ad_group_source.refresh_from_db()
        self.assertEqual(ad_group_source.blockers, {})

    def test_update_ad_group_source_blockers_no_change(self):
        ad_group_source = dash.models.AdGroupSource.objects.get(ad_group_id=1, source__bidder_slug="adblade")
        ad_group_source.blockers = {}
        ad_group_source.save()

        with mock.patch.object(dash.models.AdGroupSource, "save") as mock_save:
            params = {"ad_group_id": 1}
            put_body = {"adblade": {"geo-exclusion": None}}
            response = self.client.generic(
                "PUT",
                reverse("k1api.ad_groups.sources.blockers"),
                json.dumps(put_body),
                "application/json",
                QUERY_STRING=urllib.parse.urlencode(params),
            )
            data = json.loads(response.content)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(data["response"], {"adblade": {}})

            ad_group_source.refresh_from_db()
            self.assertEqual(ad_group_source.blockers, {})
            mock_save.assert_not_called()

    @mock.patch("automation.campaignstop.get_campaignstop_states")
    def test_get_ad_groups_blocked_state(self, mock_get_campaignstop_states):
        ad_group = dash.models.AdGroup.objects.get(pk=2)
        mock_get_campaignstop_states.return_value = {
            ad_group.campaign_id: {"allowed_to_run": True, "min_allowed_start_date": dates_helper.local_today()}
        }
        self.assertFalse(ad_group.is_blocked_by_custom_flag())
        response = self.client.get(
            reverse("k1api.ad_groups.sources"), {"ad_group_ids": ad_group.id, "source_types": "b1"}
        )
        data = json.loads(response.content)["response"][0]
        self.assertEqual(data["ad_group_id"], ad_group.id)
        self.assertEqual(data["state"], dash.constants.AdGroupSourceSettingsState.ACTIVE)

        customer_block_flag = dash.models.CustomFlag.objects.create(id=custom_flags.constants.CUSTOMER_BLOCKED)
        ad_group.custom_flags = {customer_block_flag.id: True}
        ad_group.save(None)
        ad_group = dash.models.AdGroup.objects.get(pk=ad_group.id)
        self.assertTrue(ad_group.is_blocked_by_custom_flag())
        response = self.client.get(
            reverse("k1api.ad_groups.sources"), {"ad_group_ids": ad_group.id, "source_types": "b1"}
        )
        data = json.loads(response.content)["response"][0]
        self.assertEqual(data["ad_group_id"], ad_group.id)
        self.assertEqual(data["state"], dash.constants.AdGroupSourceSettingsState.INACTIVE)

        # test block by is_disabled
        ad_group.custom_flags = {}
        ad_group.save(None)
        account = ad_group.campaign.account
        account.is_disabled = True
        account.save(None)
        self.assertTrue(account.is_disabled)
        response = self.client.get(
            reverse("k1api.ad_groups.sources"), {"ad_group_ids": ad_group.id, "source_types": "b1"}
        )
        data = json.loads(response.content)["response"][0]
        self.assertEqual(data["ad_group_id"], ad_group.id)
        self.assertEqual(data["state"], dash.constants.AdGroupSourceSettingsState.INACTIVE)
