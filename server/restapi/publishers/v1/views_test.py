import json
from unittest import mock

from django.urls import reverse

import core.features.bid_modifiers
import core.features.publisher_groups
import core.models
import dash.constants
import restapi.common.views_base_test_case
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class PublisherBlacklistTest(restapi.common.views_base_test_case.RESTAPITestCase):
    def setUp(self):
        super(PublisherBlacklistTest, self).setUp()
        self.test_request = get_request_mock(self.user)
        self.source = magic_mixer.blend(core.models.Source)
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.test_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=self.account)

    def _get_resp_json(self, ad_group_id):
        r = self.client.get(reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": ad_group_id}))
        resp_json = json.loads(r.content)
        return resp_json

    def test_adgroups_publishers_list(self):
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn.com", "source": self.source, "include_subdomains": True}],
            self.test_ad_group,
        )
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn2.com", "source": self.source, "include_subdomains": True}],
            self.test_ad_group.campaign,
        )
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn3.com", "source": self.source, "include_subdomains": True}],
            self.test_ad_group.campaign.account,
        )

        r = self.client.get(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id})
        )

        resp_json = json.loads(r.content)
        self.assertEqual(
            resp_json["data"],
            [
                {
                    "name": "cnn.com",
                    "source": self.source.bidder_slug,
                    "status": "BLACKLISTED",
                    "level": "ADGROUP",
                    "modifier": None,
                    "placement": None,
                },
                {
                    "name": "cnn2.com",
                    "source": self.source.bidder_slug,
                    "status": "BLACKLISTED",
                    "level": "CAMPAIGN",
                    "modifier": None,
                    "placement": None,
                },
                {
                    "name": "cnn3.com",
                    "source": self.source.bidder_slug,
                    "status": "BLACKLISTED",
                    "level": "ACCOUNT",
                    "modifier": None,
                    "placement": None,
                },
            ],
        )

    def test_adgroups_placements_list(self):
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn.com", "placement": "plac", "source": self.source, "include_subdomains": True}],
            self.test_ad_group,
        )

        r = self.client.get(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id})
        )

        resp_json = json.loads(r.content)
        self.assertEqual(
            resp_json["data"],
            [
                {
                    "name": "cnn.com",
                    "placement": "plac",
                    "source": self.source.bidder_slug,
                    "status": "BLACKLISTED",
                    "level": "ADGROUP",
                    "modifier": None,
                }
            ],
        )

    def test_adgroups_placements_list_no_permission(self):
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn.com", "placement": "plac", "source": self.source, "include_subdomains": True}],
            self.test_ad_group,
        )

        r = self.client.get(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id})
        )

        resp_json = json.loads(r.content)
        self.assertEqual(
            resp_json["data"],
            [
                {
                    "name": "cnn.com",
                    "source": self.source.bidder_slug,
                    "status": "BLACKLISTED",
                    "level": "ADGROUP",
                    "modifier": None,
                    "placement": "plac",
                }
            ],
        )

    @mock.patch("utils.k1_helper.update_ad_group")
    def test_adgroups_publishers_put(self, mock_k1_update):
        test_blacklist = [
            {
                "name": "cnn2.com",
                "source": self.source.bidder_slug,
                "status": "BLACKLISTED",
                "level": "ADGROUP",
                "modifier": None,
                "placement": None,
            },
            {
                "name": "cnn3.com",
                "source": self.source.bidder_slug,
                "status": "BLACKLISTED",
                "level": "CAMPAIGN",
                "modifier": None,
                "placement": None,
            },
            {
                "name": "cnn4.com",
                "source": self.source.bidder_slug,
                "status": "BLACKLISTED",
                "level": "ACCOUNT",
                "modifier": None,
                "placement": None,
            },
        ]
        self.test_ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.ACTIVE)

        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_blacklist,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], test_blacklist)

        self.assertEqual(
            [
                mock.call(mock.ANY, "publisher_group.create"),
                mock.call(mock.ANY, msg="publisher_group.create", priority=False),
                mock.call(mock.ANY, msg="publisher_group.create", priority=False),
                mock.call(mock.ANY, msg="restapi.publishers.set", priority=True),
            ],
            mock_k1_update.call_args_list,
        )
        self.assertEqual(4, mock_k1_update.call_count)
        self.assertEqual(self._get_resp_json(self.test_ad_group.id)["data"], test_blacklist)

    def test_adgroups_publishers_put_no_modifier(self):
        # The modifier attribute is not required on input.
        test_blacklist = [
            {
                "name": "cnn2.com",
                "source": self.source.bidder_slug,
                "status": "BLACKLISTED",
                "level": "ADGROUP",
                "placement": None,
            },
            {
                "name": "cnn3.com",
                "source": self.source.bidder_slug,
                "status": "BLACKLISTED",
                "level": "CAMPAIGN",
                "placement": None,
            },
            {
                "name": "cnn4.com",
                "source": self.source.bidder_slug,
                "status": "BLACKLISTED",
                "level": "ACCOUNT",
                "placement": None,
            },
        ]
        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_blacklist,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # The modifier attribute is always present on output.
        for elm in test_blacklist:
            elm["modifier"] = None

        self.assertEqual(resp_json["data"], test_blacklist)

        self.assertEqual(self._get_resp_json(self.test_ad_group.id)["data"], test_blacklist)

    def test_adgroups_publishers_put_unlist(self):
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn.com", "source": self.source, "include_subdomains": True}],
            self.test_ad_group,
        )
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn2.com", "source": self.source, "include_subdomains": True}],
            self.test_ad_group.campaign,
        )
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "cnn3.com", "source": self.source, "include_subdomains": True}],
            self.test_ad_group.campaign.account,
        )

        put_data = [
            {
                "name": "cnn.com",
                "source": self.source.bidder_slug,
                "status": "ENABLED",
                "level": "ADGROUP",
                "modifier": None,
                "placement": None,
            },
            {
                "name": "cnn2.com",
                "source": self.source.bidder_slug,
                "status": "ENABLED",
                "level": "CAMPAIGN",
                "modifier": None,
                "placement": None,
            },
            {
                "name": "cnn3.com",
                "source": self.source.bidder_slug,
                "status": "ENABLED",
                "level": "ACCOUNT",
                "modifier": None,
                "placement": None,
            },
        ]
        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], put_data)

        self.assertEqual(self._get_resp_json(self.test_ad_group.id)["data"], [])

    def test_modifiers_get(self):
        core.features.publisher_groups.blacklist_publishers(
            self.test_request,
            [{"publisher": "testpub1", "source": self.source, "include_subdomains": True}],
            self.test_ad_group,
        )
        core.features.bid_modifiers.set(
            self.test_ad_group, core.features.bid_modifiers.BidModifierType.PUBLISHER, "testpub1", self.source, 0.5
        )
        core.features.bid_modifiers.set(
            self.test_ad_group, core.features.bid_modifiers.BidModifierType.PUBLISHER, "testpub2", self.source, 4.6
        )

        self.assertEqual(
            self._get_resp_json(self.test_ad_group.id)["data"],
            [
                {
                    "level": "ADGROUP",
                    "name": "testpub1",
                    "source": self.source.bidder_slug,
                    "status": "BLACKLISTED",
                    "modifier": 0.5,
                    "placement": None,
                },
                {
                    "level": "ADGROUP",
                    "name": "testpub2",
                    "source": self.source.bidder_slug,
                    "status": "ENABLED",
                    "modifier": 4.6,
                    "placement": None,
                },
            ],
        )

    def test_modifiers_set(self):
        test_put = [
            {
                "level": "ADGROUP",
                "name": "tEsTpUB1",
                "source": self.source.bidder_slug,
                "status": "ENABLED",
                "modifier": 0.5,
                "placement": None,
            },
            {
                "level": "ADGROUP",
                "name": "testpub2",
                "source": self.source.bidder_slug,
                "status": "ENABLED",
                "modifier": 4.6,
                "placement": None,
            },
        ]
        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_put,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], test_put)

        self.assertEqual(
            self._convert_bid_modifiers_service_get_result(
                core.features.bid_modifiers.get(
                    self.test_ad_group, include_types=[core.features.bid_modifiers.BidModifierType.PUBLISHER]
                )
            ),
            [
                {"publisher": "testpub1", "source": self.source, "modifier": 0.5},
                {"publisher": "testpub2", "source": self.source, "modifier": 4.6},
            ],
        )

    def test_modifiers_unset(self):
        core.features.bid_modifiers.set(
            self.test_ad_group, core.features.bid_modifiers.BidModifierType.PUBLISHER, "testpub1", self.source, 0.5
        )
        core.features.bid_modifiers.set(
            self.test_ad_group, core.features.bid_modifiers.BidModifierType.PUBLISHER, "testpub2", self.source, 4.6
        )
        test_put = [
            {
                "level": "ADGROUP",
                "name": "testpub1",
                "source": self.source.bidder_slug,
                "status": "ENABLED",
                "modifier": None,
                "placement": None,
            }
        ]
        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_put,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["data"], test_put)

        self.assertEqual(
            self._convert_bid_modifiers_service_get_result(
                core.features.bid_modifiers.get(
                    self.test_ad_group, include_types=[core.features.bid_modifiers.BidModifierType.PUBLISHER]
                )
            ),
            [{"publisher": "testpub2", "source": self.source, "modifier": 4.6}],
        )

    def test_modifiers_set_no_source(self):
        test_put = [{"level": "ADGROUP", "name": "testpub1", "source": None, "status": "ENABLED", "modifier": 0.5}]
        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_put,
            format="json",
        )
        self.assertEqual(r.status_code, 400)
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(resp_json["details"], "Modifier can only be set if source is defined")

    def test_modifiers_set_no_source_no_modifier(self):
        test_put = [
            {"level": "ADGROUP", "name": "testpub1", "source": None, "status": "BLACKLISTED", "placement": None}
        ]
        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_put,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        # The modifier attribute is always present on output.
        for elm in test_put:
            elm["modifier"] = None
        self.assertEqual(resp_json["data"], test_put)

        self.assertEqual(self._get_resp_json(self.test_ad_group.id)["data"], test_put)

    def test_modifiers_set_no_source_null_modifier(self):
        test_put = [
            {
                "level": "ADGROUP",
                "name": "testpub1",
                "source": None,
                "status": "BLACKLISTED",
                "modifier": None,
                "placement": None,
            }
        ]
        r = self.client.put(
            reverse("restapi.publishers.v1:publishers_list", kwargs={"ad_group_id": self.test_ad_group.id}),
            data=test_put,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(resp_json["data"], test_put)
        self.assertEqual(self._get_resp_json(self.test_ad_group.id)["data"], test_put)

    def _convert_bid_modifiers_service_get_result(self, bm_list):
        new_bm_list = []
        for bm in bm_list:
            new_bm = bm.copy()
            new_bm["publisher"] = new_bm["target"]
            del new_bm["target"]
            del new_bm["type"]
            new_bm_list.append(new_bm)

        return new_bm_list
