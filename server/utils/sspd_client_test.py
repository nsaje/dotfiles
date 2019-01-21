import datetime
import json

from django.test import TestCase
from mock import ANY
from mock import Mock
from mock import call
from mock import patch
from requests import Response

from dash import constants
from dash import models
from utils.magic_mixer import magic_mixer

from . import sspd_client


@patch("django.conf.settings.SSPD_BASE_URL", "http://testssp.zemanta.com")
class SSPDClientTestCase(TestCase):
    @patch("requests.request")
    @patch("utils.dates_helper.utc_now", Mock(return_value=datetime.datetime(2018, 10, 1, 12)))
    @patch("django.conf.settings.SSPD_AUTH_SECRET", "qwerty")
    def test_get_approval_status(self, mock_request):
        response = Response()
        response._content = b'{"1234": "APPROVED", "9876": "BLOCKED", "5555": "PENDING"}'
        response.status_code = 200
        mock_request.return_value = response
        approval_statuses = sspd_client.get_approval_status(content_ad_source_ids=[1234, 9876, 5555])
        mock_request.assert_called_once_with(
            "post",
            "http://testssp.zemanta.com/service/approvalstatus",
            data=json.dumps(
                {
                    "adGroupIds": None,
                    "contentAdIds": None,
                    "sourceTypes": None,
                    "slugs": None,
                    "contentAdSourceIds": [1234, 9876, 5555],
                }
            ),
            headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJaMSIsImV4cCI6MTUzODM5NTI2MH0.Xn_HgLj_5Hn6mezRcj58zPJn236hCIm-rE1KDLRiVUg",
                "Content-type": "application/json",
            },
            params={},
            timeout=None,
        )

        self.assertEqual(
            {
                1234: constants.ContentAdSubmissionStatus.APPROVED,
                9876: constants.ContentAdSubmissionStatus.REJECTED,
                5555: constants.ContentAdSubmissionStatus.PENDING,
            },
            approval_statuses,
        )

    def _create_requests_response(self, content, status_code=200):
        response = Response()
        response._content = content
        response.status_code = status_code
        return response

    @patch("requests.request")
    @patch("utils.dates_helper.utc_now", Mock(return_value=datetime.datetime(2018, 10, 1, 12)))
    @patch("django.conf.settings.SSPD_AUTH_SECRET", "qwerty")
    def test_get_content_ad_status(self, mock_request):
        source = magic_mixer.blend(models.Source)

        response_content = {
            "1234": [{"status": "APPROVED", "reason": "", "sourceId": source.id}],
            "9876": [{"status": "BLOCKED", "reason": "Inappropriate content", "sourceId": source.id}],
            "5555": [{"status": "PENDING", "reason": "", "sourceId": source.id}],
        }

        response = Response()
        response._content = json.dumps(response_content).encode()
        response.status_code = 200
        mock_request.return_value = response
        sspd_client.TIMEOUT = (10, 10)
        approval_statuses = sspd_client.get_content_ad_status([1234, 9876, 5555])
        mock_request.assert_called_once_with(
            "get",
            "http://testssp.zemanta.com/service/contentadstatus",
            data={},
            headers={
                "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJaMSIsImV4cCI6MTUzODM5NTI2MH0.Xn_HgLj_5Hn6mezRcj58zPJn236hCIm-rE1KDLRiVUg"
            },
            params={"contentAdIds": "1234,9876,5555"},
            timeout=sspd_client.TIMEOUT,
        )

        self.assertEqual(
            {
                1234: {source.id: {"status": constants.ContentAdSubmissionStatus.APPROVED, "reason": ""}},
                9876: {
                    source.id: {
                        "status": constants.ContentAdSubmissionStatus.REJECTED,
                        "reason": "Inappropriate content",
                    }
                },
                5555: {source.id: {"status": constants.ContentAdSubmissionStatus.PENDING, "reason": ""}},
            },
            approval_statuses,
        )

    @patch("requests.request")
    @patch("utils.dates_helper.utc_now", Mock(return_value=datetime.datetime(2018, 10, 1, 12)))
    @patch("django.conf.settings.SSPD_AUTH_SECRET", "qwerty")
    @patch("utils.sspd_client.MAX_REQUEST_IDS", 10)
    def test_paginate_request(self, mock_request):
        mock_request.side_effect = [
            self._create_requests_response(json.dumps({k: "APPROVED" for k in range(10)}).encode("utf-8")),
            self._create_requests_response(json.dumps({k: "BLOCKED" for k in range(10, 20)}).encode("utf-8")),
            self._create_requests_response(json.dumps({k: "PENDING" for k in range(20, 25)}).encode("utf-8")),
        ]
        sspd_client_timeout = (10, 10)
        approval_statuses = sspd_client._paginate_request(
            "get",
            "http://testssp.zemanta.com/test",
            {"testIds": [i for i in range(25)]},
            paginate_key="testIds",
            timeout=sspd_client_timeout,
        )
        mock_request.assert_has_calls(
            [
                call(
                    "get",
                    "http://testssp.zemanta.com/test",
                    data={},
                    headers=ANY,
                    params={"testIds": "{}".format(",".join(str(x) for x in range(10)))},
                    timeout=sspd_client_timeout,
                ),
                call(
                    "get",
                    "http://testssp.zemanta.com/test",
                    data={},
                    headers=ANY,
                    params={"testIds": "{}".format(",".join(str(x) for x in range(10, 20)))},
                    timeout=sspd_client_timeout,
                ),
                call(
                    "get",
                    "http://testssp.zemanta.com/test",
                    data={},
                    headers=ANY,
                    params={"testIds": "{}".format(",".join(str(x) for x in range(20, 25)))},
                    timeout=sspd_client_timeout,
                ),
            ]
        )
        for i in range(10):
            self.assertEqual("APPROVED", approval_statuses[str(i)])
        for i in range(10, 20):
            self.assertEqual("BLOCKED", approval_statuses[str(i)])
        for i in range(20, 25):
            self.assertEqual("PENDING", approval_statuses[str(i)])

    @patch("utils.sspd_client.sync_content_ad_sources")
    @patch("utils.sspd_client.sync_content_ads")
    @patch("utils.sspd_client.sync_ad_groups")
    @patch("utils.sspd_client.sync_sources")
    def test_sync_batch(
        self, mock_sync_source, mock_sync_ad_groups, mock_sync_content_ads, mock_sync_content_ad_sources
    ):

        mock_sync_source.return_value = True
        mock_sync_ad_groups.return_value = True
        mock_sync_content_ads.return_value = True
        mock_sync_content_ad_sources.return_value = True

        source = magic_mixer.blend(models.Source)
        agency = magic_mixer.blend(models.Agency)
        account = magic_mixer.blend(models.Account, agency=agency)
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.CONTENT)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        batch = magic_mixer.blend(models.UploadBatch, ad_group=ad_group)

        content_ads = magic_mixer.cycle(3).blend(models.ContentAd, ad_group=ad_group, batch=batch)
        content_ad_sources = magic_mixer.cycle(3).blend(
            models.ContentAdSource,
            content_ad=(ca for ca in content_ads),
            source=source,
            state=constants.ContentAdSourceState.ACTIVE,
            submission_status=constants.ContentAdSubmissionStatus.APPROVED,
        )

        sspd_client.sync_batch(batch)

        mock_sync_source.assert_called_once_with({source})
        mock_sync_ad_groups.assert_called_once_with({ad_group})
        mock_sync_content_ads.assert_called_once_with(set(content_ads))
        mock_sync_content_ad_sources.assert_called_once_with(set(content_ad_sources))

    @patch("utils.sspd_client._make_request")
    def test_sync_sources(self, mock_request):
        source_type = magic_mixer.blend(models.SourceType)
        source = magic_mixer.blend(models.Source, source_type=source_type)

        sspd_client.sync_sources({source})

        data = [
            {
                "id": source.id,
                "name": source.name,
                "sourceType": source.source_type.type,
                "bidderSlug": source.bidder_slug,
            }
        ]

        mock_request.assert_called_once_with(
            "post", "http://testssp.zemanta.com/service/source", data=json.dumps(data), timeout=sspd_client.TIMEOUT
        )

    @patch("utils.sspd_client._make_request")
    def test_sync_ad_groups(self, mock_request):
        agency = magic_mixer.blend(models.Agency)
        account = magic_mixer.blend(models.Account, agency=agency)
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.CONTENT)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)

        sspd_client.sync_ad_groups({ad_group})

        data = [
            {
                "id": ad_group.id,
                "name": ad_group.name,
                "campaignId": ad_group.campaign.id,
                "campaignName": ad_group.campaign.name,
                "accountId": ad_group.campaign.account.id,
                "accountName": ad_group.campaign.account.name,
                "agencyId": ad_group.campaign.account.agency.id,
                "agencyName": ad_group.campaign.account.agency.name,
            }
        ]

        mock_request.assert_called_once_with(
            "post", "http://testssp.zemanta.com/service/adgroup", data=json.dumps(data), timeout=sspd_client.TIMEOUT
        )

    @patch("utils.sspd_client._make_request")
    def test_sync_content_ads(self, mock_request):
        agency = magic_mixer.blend(models.Agency)
        account = magic_mixer.blend(models.Account, agency=agency)
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.CONTENT)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        content_ad = magic_mixer.blend(models.ContentAd, ad_group=ad_group)

        sspd_client.sync_content_ads({content_ad})

        data = [
            {
                "id": content_ad.id,
                "adGroupId": content_ad.ad_group_id,
                "title": content_ad.title,
                "description": content_ad.description,
                "brandName": content_ad.brand_name,
                "imageId": content_ad.image_id,
            }
        ]

        mock_request.assert_called_once_with(
            "post", "http://testssp.zemanta.com/service/contentad", data=json.dumps(data), timeout=sspd_client.TIMEOUT
        )

    @patch("utils.sspd_client._make_request")
    def test_sync_content_ad_sources(self, mock_request):
        source = magic_mixer.blend(models.Source)
        agency = magic_mixer.blend(models.Agency)
        account = magic_mixer.blend(models.Account, agency=agency)
        campaign = magic_mixer.blend(models.Campaign, account=account, type=constants.CampaignType.CONTENT)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        content_ad = magic_mixer.blend(models.ContentAd, ad_group=ad_group)
        content_ad_source = magic_mixer.blend(
            models.ContentAdSource,
            content_ad=content_ad,
            source=source,
            state=constants.ContentAdSourceState.ACTIVE,
            submission_status=constants.ContentAdSubmissionStatus.APPROVED,
        )

        sspd_client.sync_content_ad_sources({content_ad_source})

        data = [
            {
                "id": content_ad_source.id,
                "contentAdId": content_ad_source.content_ad_id,
                "sourceId": content_ad_source.source_id,
                "sourceContentAdId": content_ad_source.source_content_ad_id,
            }
        ]

        mock_request.assert_called_once_with(
            "post",
            "http://testssp.zemanta.com/service/contentadsource",
            data=json.dumps(data),
            timeout=sspd_client.TIMEOUT,
        )
