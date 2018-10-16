import datetime
import itertools
import json
import logging
import urllib.error
import urllib.parse


import urllib.request

import mock
from django.core.urlresolvers import reverse

import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models
from utils.magic_mixer import magic_mixer
from utils import sspd_client
from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@mock.patch("utils.sspd_client.get_approval_status", mock.MagicMock())
class ContentAdsTest(K1APIBaseTest):
    def test_get_content_ad_source_mapping(self):
        test_source_filters = [["adblade"], ["adblade", "outbrain", "yahoo"]]
        test_source_content_ads = [["987654321"], ["987654321", "123456789"]]
        test_cases = itertools.product(test_source_filters, test_source_content_ads)
        for source_types, source_content_ad_ids in test_cases:
            self._test_content_ad_source_ids_filters(source_types, source_content_ad_ids)

    def _test_content_ad_source_ids_filters(self, source_types=None, source_content_ad_ids=None):
        response = self.client.get(
            reverse("k1api.content_ads.sources"),
            data=dict(source_slugs=",".join(source_types), source_content_ad_ids=",".join(source_content_ad_ids)),
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        expected_count = dash.models.ContentAdSource.objects.filter(
            source__bidder_slug__in=source_types, source_content_ad_id__in=source_content_ad_ids
        ).count()
        self.assertEqual(expected_count, len(data))
        self.assertGreater(len(data), 0)
        for content_ad_source in data:
            db_cas = dash.models.ContentAdSource.objects.get(
                content_ad_id=content_ad_source["content_ad_id"], source__bidder_slug=content_ad_source["source_slug"]
            )
            self.assertEqual(content_ad_source["source_content_ad_id"], db_cas.source_content_ad_id)
            self.assertEqual(content_ad_source["content_ad_id"], db_cas.content_ad_id)
            self.assertEqual(content_ad_source["ad_group_id"], db_cas.content_ad.ad_group_id)
            self.assertEqual(content_ad_source["source_slug"], db_cas.source.bidder_slug)

        contentadsources = dash.models.ContentAdSource.objects
        if source_content_ad_ids:
            contentadsources = contentadsources.filter(source_content_ad_id__in=source_content_ad_ids)
        if source_types:
            contentadsources = contentadsources.filter(source__source_type__type__in=source_types)
        self.assertEqual(len(data), contentadsources.count())

    def test_get_content_ad_sources_for_ad_group(self):
        test_cases = [(1, None), (1, 1)]
        for ad_group_id, content_ad_id in test_cases:
            self._test_get_content_ad_sources_for_ad_group(ad_group_id, content_ad_id)

    def _test_get_content_ad_sources_for_ad_group(self, ad_group_id, content_ad_id):
        response = self.client.get(reverse("k1api.content_ads.sources"), {"source_type": "adblade", "ad_group_id": 1})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        required_fields = {
            "content_ad_id",
            "ad_group_id",
            "source_content_ad_id",
            "submission_status",
            "tracking_slug",
            "source_slug",
            "state",
        }

        db_ags = dash.models.ContentAdSource.objects.filter(content_ad__ad_group_id=ad_group_id)
        if content_ad_id:
            db_ags = db_ags.filter(content_ad_id=content_ad_id)

        for cas in data:
            self.assertLessEqual(required_fields, set(cas.keys()))

    def test_get_content_ad_sources_for_ad_group_no_adgroupsource(self):
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"source_types": "outbrain", "ad_group_ids": 1}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]
        self.assertEqual(data, [])

    def test_get_content_ads_by_id(self):
        response = self.client.get(reverse("k1api.content_ads"), {"content_ad_ids": 1, "ad_group_ids": 1})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        expected = [
            {
                "image_crop": "center",
                "image_hash": None,
                "description": "",
                "ad_group_id": 1,
                "campaign_id": 1,
                "account_id": 1,
                "agency_id": 20,
                "language": "en",
                "call_to_action": "",
                "url": "http://testurl.com",
                "title": "Test Article 1",
                "brand_name": "",
                "image_width": None,
                "image_id": "123456789",
                "video_asset": None,
                "image_height": None,
                "display_url": "",
                "redirect_id": None,
                "id": 1,
                "tracker_urls": None,
                "label": "Label_123",
                "additional_data": None,
            }
        ]
        self.assertEqual(data, expected)

    def test_get_content_ads_video_asset(self):
        formats = [
            {"width": 1920, "height": 1080, "bitrate": 4500, "mime": "video/mp4", "filename": "xyz_1080p.mp4"},
            {"width": 1920, "height": 1080, "bitrate": 4500, "mime": "video/flv", "filename": "xyz_1080p.flv"},
        ]
        content_ad = dash.models.ContentAd.objects.get(pk=1)
        video_asset = magic_mixer.blend(dash.models.VideoAsset)
        video_asset.update_progress(0, duration=31, formats=formats)
        content_ad.video_asset = video_asset
        content_ad.save()

        response = self.client.get(reverse("k1api.content_ads"), {"content_ad_ids": 1, "ad_group_ids": 1})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        expected_video_asset = {"id": str(video_asset.id), "duration": 31, "formats": formats, "vasturi": None}
        self.assertEqual(data[0]["video_asset"], expected_video_asset)

    def test_get_content_ads(self):
        response = self.client.get(reverse("k1api.content_ads"), {"include_archived": False})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data_without_archived = data["response"]

        response = self.client.get(reverse("k1api.content_ads"), {"include_archived": True})

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data_with_archived = data["response"]

        self.assertEqual(5, len(data_without_archived))
        self.assertEqual(6, len(data_with_archived))

    def test_get_content_ads_sources(self):
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"content_ad_ids": 1, "ad_group_ids": 1, "source_slugs": "adblade"}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        expected = [
            {
                "id": 1,
                "content_ad_id": 1,
                "ad_group_id": 1,
                "source_id": 1,
                "submission_status": 1,
                "source_content_ad_id": "987654321",
                "tracking_slug": "adblade",
                "state": 1,
                "source_slug": "adblade",
            }
        ]

        self.assertEqual(data, expected)

    # def test_get_content_ads_sources_sspd_rejected(self):
    #     content_ad_source = dash.models.ContentAdSource.objects.get(source_id=1, content_ad_id=1)
    #     sspd_client.get_approval_status.return_value = {
    #         content_ad_source.id: dash.constants.ContentAdSspdStatus.BLOCKED
    #     }

    #     response = self.client.get(
    #         reverse("k1api.content_ads.sources"), {"content_ad_ids": 1, "ad_group_ids": 1, "source_slugs": "adblade"}
    #     )

    #     data = json.loads(response.content)
    #     self.assert_response_ok(response, data)
    #     data = data["response"]

    #     expected = [
    #         {
    #             "id": 1,
    #             "content_ad_id": 1,
    #             "ad_group_id": 1,
    #             "source_id": 1,
    #             "submission_status": 1,
    #             "source_content_ad_id": "987654321",
    #             "tracking_slug": "adblade",
    #             "state": 2,
    #             "source_slug": "adblade",
    #         }
    #     ]

    #     self.assertEqual(data, expected)

    # def test_get_content_ads_sources_sspd_rejected_status_none(self):
    #     sspd_client.get_approval_status.return_value = {}

    #     response = self.client.get(
    #         reverse("k1api.content_ads.sources"), {"content_ad_ids": 1, "ad_group_ids": 1, "source_slugs": "adblade"}
    #     )

    #     data = json.loads(response.content)
    #     self.assert_response_ok(response, data)
    #     data = data["response"]

    #     expected = [
    #         {
    #             "id": 1,
    #             "content_ad_id": 1,
    #             "ad_group_id": 1,
    #             "source_id": 1,
    #             "submission_status": 1,
    #             "source_content_ad_id": "987654321",
    #             "tracking_slug": "adblade",
    #             "state": 2,
    #             "source_slug": "adblade",
    #         }
    #     ]

    #     self.assertEqual(data, expected)

    def test_get_content_ads_sources_with_amplify_review(self):
        new_ad_group = magic_mixer.blend(dash.models.AdGroup, amplify_review=True)
        outbrain_source = dash.models.Source.objects.get(bidder_slug="outbrain")
        magic_mixer.blend(dash.models.AdGroupSource, ad_group=new_ad_group, source=outbrain_source)
        other_ad_group_source = magic_mixer.blend(
            dash.models.AdGroupSource,
            source__bidder_slug="newsource",
            source__content_ad_submission_policy=dash.constants.SourceSubmissionPolicy.AUTOMATIC_WITH_AMPLIFY_APPROVAL,
        )
        content_ads = magic_mixer.cycle(3).blend(
            dash.models.ContentAd, ad_group=new_ad_group, amplify_review=(val for val in [True, True, False])
        )
        magic_mixer.cycle(3).blend(
            dash.models.ContentAdSource,
            state=dash.constants.ContentAdSourceState.ACTIVE,
            content_ad=(ca for ca in content_ads),
            source=outbrain_source,
            submission_status=(
                val
                for val in [
                    dash.constants.ContentAdSubmissionStatus.APPROVED,
                    dash.constants.ContentAdSubmissionStatus.REJECTED,
                    dash.constants.ContentAdSubmissionStatus.REJECTED,
                ]
            ),
        )
        content_ad_sources = magic_mixer.cycle(3).blend(
            dash.models.ContentAdSource,
            content_ad=(ca for ca in content_ads),
            source=other_ad_group_source.source,
            state=dash.constants.ContentAdSourceState.ACTIVE,
            submission_status=dash.constants.ContentAdSubmissionStatus.APPROVED,
        )
        sspd_client.get_approval_status.return_value = {
            content_ad_sources[0].id: dash.constants.ContentAdSspdStatus.APPROVED,
            content_ad_sources[1].id: dash.constants.ContentAdSspdStatus.APPROVED,
            content_ad_sources[2].id: dash.constants.ContentAdSspdStatus.APPROVED,
        }
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"ad_group_ids": new_ad_group.id, "source_slugs": "newsource"}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]

        expected = [
            {
                "id": content_ad_sources[0].id,
                "ad_group_id": content_ads[0].ad_group_id,
                "content_ad_id": content_ads[0].id,
                "source_id": other_ad_group_source.source_id,
                "source_content_ad_id": content_ad_sources[0].source_content_ad_id,
                "source_slug": "newsource",
                "state": dash.constants.ContentAdSourceState.ACTIVE,
                "submission_status": dash.constants.ContentAdSubmissionStatus.APPROVED,
                "tracking_slug": content_ad_sources[0].source.tracking_slug,
            },
            {
                "id": content_ad_sources[1].id,
                "ad_group_id": content_ads[1].ad_group_id,
                "content_ad_id": content_ads[1].id,
                "source_id": other_ad_group_source.source_id,
                "source_content_ad_id": content_ad_sources[1].source_content_ad_id,
                "source_slug": "newsource",
                "state": dash.constants.ContentAdSourceState.INACTIVE,
                "submission_status": dash.constants.ContentAdSubmissionStatus.APPROVED,
                "tracking_slug": content_ad_sources[1].source.tracking_slug,
            },
            {
                "id": content_ad_sources[2].id,
                "ad_group_id": content_ads[2].ad_group_id,
                "content_ad_id": content_ads[2].id,
                "source_id": other_ad_group_source.source_id,
                "source_content_ad_id": content_ad_sources[2].source_content_ad_id,
                "source_slug": "newsource",
                "state": dash.constants.ContentAdSourceState.ACTIVE,
                "submission_status": dash.constants.ContentAdSubmissionStatus.APPROVED,
                "tracking_slug": content_ad_sources[2].source.tracking_slug,
            },
        ]
        self.assertCountEqual(data, expected)

    def test_update_content_ad_status(self):
        cas = dash.models.ContentAdSource.objects.get(pk=1)
        cas.source_content_ad_id = None
        cas.save()
        response = self.client.generic(
            "PUT",
            reverse("k1api.content_ads.sources"),
            json.dumps({"submission_status": 2, "submission_errors": "my-errors", "source_content_ad_id": 123}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode({"content_ad_id": 1, "source_slug": "adblade"}),
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        cas = dash.models.ContentAdSource.objects.filter(content_ad_id=1, source__bidder_slug="adblade")[0]
        self.assertEqual(cas.submission_status, 2)
        self.assertEqual(cas.submission_errors, "my-errors")
        self.assertEqual(cas.source_content_ad_id, "123")

        response = self.client.put(
            reverse("k1api.content_ads.sources"),
            json.dumps(
                {
                    "content_ad_id": 1000,
                    "source_slug": "adblade",
                    "submission_status": 2,
                    "submission_errors": "my-errors",
                    "source_content_ad_id": 123,
                }
            ),
            "application/json",
        )
        self.assertEqual(response.status_code, 404)

    def test_update_content_ad_status_refuse_delete(self):
        response = self.client.generic(
            "PUT",
            reverse("k1api.content_ads.sources"),
            json.dumps({"submission_status": 2, "submission_errors": "my-errors", "source_content_ad_id": ""}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode({"content_ad_id": 1, "source_slug": "adblade"}),
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Cannot change", data["error"])

    @mock.patch("influx.timing")
    @mock.patch("utils.dates_helper.utc_now")
    def test_update_content_ad_status_influx(self, mock_now, mock_influx_timing):

        mock_now.return_value = datetime.datetime(2018, 9, 7, 13, 41, 24, 394696)
        response = self.client.generic(
            "PUT",
            reverse("k1api.content_ads.sources"),
            json.dumps({"submission_status": 2, "submission_errors": "my-errors"}),
            "application/json",
            QUERY_STRING=urllib.parse.urlencode({"content_ad_id": 1, "source_slug": "adblade"}),
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        cas = dash.models.ContentAdSource.objects.filter(content_ad_id=1, source__bidder_slug="adblade")[0]
        self.assertEqual(cas.submission_status, 2)
        self.assertEqual(cas.source_content_ad_id, "987654321")
        mock_influx_timing.assert_any_call(
            "content_ads_source.submission_processing_time", 111678084.394696, exchange="adblade"
        )
