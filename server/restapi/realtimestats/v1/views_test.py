import collections

import mock
from django.urls import reverse

import core.models.ad_group
from restapi.common.views_base_test_case import RESTAPITestCase
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


@mock.patch("stats.api_realtimestats.count_rows", autospec=True)
@mock.patch("stats.api_realtimestats.groupby", autospec=True)
class GroupByViewTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        test_helper.add_permissions(self.user, ["can_use_realtimestats_api"])
        self.account = self.mix_account(self.user, permissions=[Permission.READ])
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=self.account)
        self.content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=self.ad_group)

    def test_get(self, mock_groupby, mock_count_rows):
        mock_groupby.return_value = [
            {
                "content_ad_id": "1234",
                "clicks": 12321,
                "impressions": 123321,
                "spend": 12.3,
                "ctr": 0.03,
                "cpc": 0.02,
                "cpm": 0.01,
            }
        ]
        mock_count_rows.return_value = 10

        r = self.client.get(
            reverse("restapi.realtimestats.v1:groupby")
            + f"?adGroupId={self.ad_group.id}&breakdown=contentAdId&marker=1234&limit=50"
        )

        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(
            resp_json,
            collections.OrderedDict(
                [
                    ("count", 10),
                    ("next", None),
                    (
                        "data",
                        [
                            {
                                "contentAdId": 1234,
                                "clicks": 12321,
                                "impressions": 123321,
                                "spend": "12.30",
                                "ctr": "0.030",
                                "cpc": "0.020",
                                "cpm": "0.010",
                            }
                        ],
                    ),
                ]
            ),
        )

        mock_groupby.assert_called_with(
            breakdown=["content_ad_id"], ad_group_id=self.ad_group.id, marker=1234, limit=50
        )

        mock_count_rows.assert_called_with(breakdown=["content_ad_id"], ad_group_id=self.ad_group.id)

    def test_get_pagination(self, mock_groupby, mock_count_rows):
        mock_groupby.return_value = [
            {
                "content_ad_id": str(1234 + i),
                "clicks": 12321,
                "impressions": 123321,
                "spend": 12.3,
                "ctr": 0.03,
                "cpc": 0.02,
                "cpm": 0.01,
            }
            for i in range(2)
        ]
        mock_count_rows.return_value = 2

        r = self.client.get(
            reverse("restapi.realtimestats.v1:groupby")
            + f"?adGroupId={self.ad_group.id}&breakdown=contentAdId&marker=1234&limit=2"
        )

        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(
            resp_json,
            collections.OrderedDict(
                [
                    ("count", 2),
                    (
                        "next",
                        "http://testserver/rest/v1/realtimestats/?adGroupId=%s&breakdown=contentAdId&limit=2&marker=1235"
                        % self.ad_group.id,
                    ),
                    (
                        "data",
                        [
                            {
                                "contentAdId": 1234,
                                "clicks": 12321,
                                "impressions": 123321,
                                "spend": "12.30",
                                "ctr": "0.030",
                                "cpc": "0.020",
                                "cpm": "0.010",
                            },
                            {
                                "contentAdId": 1235,
                                "clicks": 12321,
                                "impressions": 123321,
                                "spend": "12.30",
                                "ctr": "0.030",
                                "cpc": "0.020",
                                "cpm": "0.010",
                            },
                        ],
                    ),
                ]
            ),
        )

        mock_groupby.assert_called_with(breakdown=["content_ad_id"], ad_group_id=self.ad_group.id, marker=1234, limit=2)

        mock_count_rows.assert_called_with(breakdown=["content_ad_id"], ad_group_id=self.ad_group.id)

    def test_invalid_account_id(self, mock_groupby, mock_count_rows):
        account = self.mix_account()
        r = self.client.get(reverse("restapi.realtimestats.v1:groupby") + f"?account_id={account.id}")
        self.assertResponseError(r, "MissingDataError")

    def test_invalid_campaign_id(self, mock_groupby, mock_count_rows):
        account = self.mix_account()
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        r = self.client.get(reverse("restapi.realtimestats.v1:groupby") + f"?campaign_id={campaign.id}")
        self.assertResponseError(r, "MissingDataError")

    def test_invalid_ad_group_id(self, mock_groupby, mock_count_rows):
        account = self.mix_account()
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)
        r = self.client.get(reverse("restapi.realtimestats.v1:groupby") + f"?adGroupId={ad_group.id}")
        self.assertResponseError(r, "MissingDataError")

    def test_invalid_content_ad_id(self, mock_groupby, mock_count_rows):
        account = self.mix_account()
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group__campaign__account=account)
        r = self.client.get(reverse("restapi.realtimestats.v1:groupby") + f"?contentAdId={content_ad.id}")
        self.assertResponseError(r, "MissingDataError")

    def test_limit_too_high(self, mock_groupby, mock_count_rows):
        r = self.client.get(reverse("restapi.realtimestats.v1:groupby") + "?limit=9999999")
        self.assertResponseError(r, "ValidationError")
        response = self.assertResponseError(r, "ValidationError")
        self.assertEqual(response["details"]["limit"], ["Ensure this value is less than or equal to 100."])

    def test_topn_invalid_breakdown(self, mock_groupby, mock_count_rows):
        r = self.client.get(
            reverse("restapi.realtimestats.v1:topn") + f"?contentAdId={self.content_ad.id}&breakdown=foo"
        )
        response = self.assertResponseError(r, "ValidationError")
        self.assertCountEqual(
            response["details"]["breakdown"],
            ["Invalid choice foo! Valid choices: campaignId, adGroupId, contentAdId, mediaSource, publisher"],
        )

    def test_missing_permission(self, mock_groupby, mock_count_rows):
        test_helper.remove_permissions(self.user, ["can_use_realtimestats_api"])
        r = self.client.get(reverse("restapi.realtimestats.v1:groupby") + f"?contentAdId={self.content_ad.id}")

        self.assertResponseError(r, "PermissionDenied")

    def test_missing_filter(self, mock_groupby, mock_count_rows):
        r = self.client.get(reverse("restapi.realtimestats.v1:groupby"))

        response = self.assertResponseError(r, "ValidationError")
        self.assertCountEqual(
            response["details"],
            "No dimension filter provided. Expected at least one of: accountId, campaignId, adGroupId, contentAdId",
        )


@mock.patch("stats.api_realtimestats.topn", autospec=True)
class TopNViewTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        test_helper.add_permissions(self.user, ["can_use_realtimestats_api"])
        self.account = self.mix_account(self.user, permissions=[Permission.READ])
        self.content_ad = magic_mixer.blend(core.models.ContentAd, ad_group__campaign__account=self.account)

    def test_get(self, mock_topn):
        mock_topn.return_value = [
            {
                "content_ad_id": "1234",
                "clicks": 12321,
                "impressions": 123321,
                "spend": 12.3,
                "ctr": 0.03,
                "cpc": 0.02,
                "cpm": 0.01,
            }
        ]
        r = self.client.get(
            reverse("restapi.realtimestats.v1:topn") + f"?contentAdId={self.content_ad.id}&breakdown=contentAdId"
        )

        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(
            resp_json["data"],
            [
                {
                    "contentAdId": 1234,
                    "clicks": 12321,
                    "impressions": 123321,
                    "spend": "12.30",
                    "ctr": "0.030",
                    "cpc": "0.020",
                    "cpm": "0.010",
                }
            ],
        )

        mock_topn.assert_called_with(
            breakdown=["content_ad_id"], content_ad_id=self.content_ad.id, order="-impressions"
        )

    def test_invalid_campaign_id(self, mock_topn):
        account = self.mix_account()
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        r = self.client.get(reverse("restapi.realtimestats.v1:topn") + f"?campaign_id={campaign.id}")
        self.assertResponseError(r, "MissingDataError")

    def test_invalid_ad_group_id(self, mock_topn):
        account = self.mix_account()
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)
        r = self.client.get(reverse("restapi.realtimestats.v1:topn") + f"?adGroupId={ad_group.id}")
        self.assertResponseError(r, "MissingDataError")

    def test_invalid_content_ad_id(self, mock_topn):
        account = self.mix_account()
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group__campaign__account=account)
        r = self.client.get(reverse("restapi.realtimestats.v1:topn") + f"?contentAdId={content_ad.id}")
        self.assertResponseError(r, "MissingDataError")

    def test_topn_invalid_breakdown(self, mock_topn):
        r = self.client.get(
            reverse("restapi.realtimestats.v1:topn") + f"?contentAdId={self.content_ad.id}&breakdown=foo"
        )
        response = self.assertResponseError(r, "ValidationError")
        self.assertCountEqual(
            response["details"]["breakdown"],
            ["Invalid choice foo! Valid choices: campaignId, adGroupId, contentAdId, mediaSource, publisher"],
        )

    def test_missing_permission(self, mock_topn):
        test_helper.remove_permissions(self.user, ["can_use_realtimestats_api"])
        r = self.client.get(reverse("restapi.realtimestats.v1:topn") + f"?contentAdId={self.content_ad.id}")

        self.assertResponseError(r, "PermissionDenied")

    def test_missing_filter(self, mock_topn):
        r = self.client.get(reverse("restapi.realtimestats.v1:topn"))

        response = self.assertResponseError(r, "ValidationError")
        self.assertCountEqual(
            response["details"],
            "No dimension filter provided. Expected at least one of: accountId, campaignId, adGroupId, contentAdId",
        )
