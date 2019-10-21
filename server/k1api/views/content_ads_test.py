import itertools
import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from datetime import timedelta

import mock
import structlog
from django.urls import reverse
from rest_framework.test import APIClient

import dash.constants
import dash.features.ga
import dash.features.geolocation
import dash.models
from utils import sspd_client
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import content_ads
from .base_test import K1APIBaseTest

logger = structlog.get_logger(__name__)
logger.setLevel(structlog.stdlib.INFO)


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
                "type": dash.constants.AdType.CONTENT,
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
                "document_id": None,
                "document_features": None,
                "ad_tag": None,
                "icon_id": "987654321",
                "icon_hash": None,
                "icon_size": None,
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

    def test_update_content_ad(self):
        client = APIClient()

        cad = dash.models.ContentAd.objects.get(pk=1)
        cad.document_id = None
        cad.document_features = None
        cad.save()
        response = client.put(
            reverse("k1api.content_ads_details", kwargs={"content_ad_id": 1}),
            data={
                "document_id": 1234,
                "document_features": {
                    "categories": [
                        {"confidence": 0.92, "value": "1809"},
                        {"confidence": 0.01, "value": "1808"},
                        {"confidence": 0.01, "value": "1904"},
                    ],
                    "language": [{"confidence": 0.9990000128746033, "value": "es"}],
                },
            },
            format="json",
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        cad = dash.models.ContentAd.objects.get(id=1)
        self.assertEqual(cad.document_id, 1234)
        self.assertEqual(
            cad.document_features,
            {
                "categories": [
                    {"confidence": 0.92, "value": "1809"},
                    {"confidence": 0.01, "value": "1808"},
                    {"confidence": 0.01, "value": "1904"},
                ],
                "language": [{"confidence": 0.9990000128746033, "value": "es"}],
            },
        )

        response = client.put(
            reverse("k1api.content_ads_details", kwargs={"content_ad_id": 1000}),
            data={"document_id": 1234, "document_features": {"language": "en"}},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_get_content_ads_sources_smoke(self):
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

    def test_get_content_ads_sources_sspd_rejected(self):
        content_ad_source = dash.models.ContentAdSource.objects.get(source_id=1, content_ad_id=1)
        sspd_client.get_approval_status.return_value = {
            content_ad_source.id: dash.constants.ContentAdSspdStatus.BLOCKED
        }

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
                "state": 2,
                "source_slug": "adblade",
            }
        ]

        self.assertEqual(data, expected)

    def test_get_content_ads_sources_sspd_rejected_status_none(self):
        sspd_client.get_approval_status.return_value = {}

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
                "state": 2,
                "source_slug": "adblade",
            }
        ]

        self.assertEqual(data, expected)

    def test_get_content_ads_sources_with_modified_dt(self):
        with test_helper.disable_auto_now_add(dash.models.ContentAdSource, "created_dt"):
            with test_helper.disable_auto_now(dash.models.ContentAdSource, "modified_dt"):
                ad_group = magic_mixer.blend(dash.models.AdGroup)
                outbrain_source = dash.models.Source.objects.get(bidder_slug="outbrain")

                content_ad_one = magic_mixer.blend(dash.models.ContentAd, ad_group=ad_group)
                content_ad_two = magic_mixer.blend(dash.models.ContentAd, ad_group=ad_group)

                magic_mixer.blend(
                    dash.models.ContentAdSource,
                    state=dash.constants.ContentAdSourceState.ACTIVE,
                    content_ad=content_ad_one,
                    source=outbrain_source,
                    submission_status=dash.constants.ContentAdSubmissionStatus.APPROVED,
                    created_dt=(datetime.utcnow() - timedelta(days=10)),
                    modified_dt=(datetime.utcnow() - timedelta(days=10)),
                )

                magic_mixer.blend(
                    dash.models.ContentAdSource,
                    state=dash.constants.ContentAdSourceState.ACTIVE,
                    content_ad=content_ad_two,
                    source=outbrain_source,
                    submission_status=dash.constants.ContentAdSubmissionStatus.APPROVED,
                    created_dt=datetime.utcnow(),
                    modified_dt=datetime.utcnow(),
                )

                response = self.client.get(
                    reverse("k1api.content_ads.sources"),
                    {"modified_dt_from": (datetime.utcnow() - timedelta(days=5)).strftime("%Y-%m-%dT%H:%M:%SZ")},
                )

                data = json.loads(response.content)
                self.assert_response_ok(response, data)
                data = data["response"]

                self.assertEqual(len(data), 1)

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

        with self.assertNumQueries(3):
            response = self.client.get(
                reverse("k1api.content_ads.sources"),
                {"ad_group_ids": new_ad_group.id, "source_slugs": "newsource", "use_filters": "true"},
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

    def test_get_content_ads_sources_filters(self):
        sources = magic_mixer.cycle(3).blend(dash.models.Source, bidder_slug=(s for s in ("s1", "s2", "s3")))
        ad_groups = magic_mixer.cycle(3).blend(dash.models.AdGroup)
        content_ads = magic_mixer.cycle(9).blend(
            dash.models.ContentAd, ad_group=(ag for ag in itertools.cycle(ad_groups))
        )
        for ca in content_ads:
            magic_mixer.cycle(len(sources)).blend(
                dash.models.ContentAdSource, content_ad=ca, source=(s for s in sources)
            )

        # test content_ad_ids filter
        content_ad_ids = [ca.id for ca in content_ads[:3]]
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"content_ad_ids": ",".join(map(str, content_ad_ids))}
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set(content_ad_ids), set([ca["content_ad_id"] for ca in data["response"]]))

        # test ad_group_ids filter
        ad_group_ids = [ag.id for ag in ad_groups[:2]]
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"ad_group_ids": ",".join(map(str, ad_group_ids))}
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set(ad_group_ids), set([ca["ad_group_id"] for ca in data["response"]]))

        # test source_types filter
        source_types_strs = [s.source_type.type for s in sources[:2]]
        source_ids = [s.id for s in sources[:2]]
        response = self.client.get(reverse("k1api.content_ads.sources"), {"source_types": ",".join(source_types_strs)})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set(source_ids), set([ca["source_id"] for ca in data["response"]]))

        # test source_slugs filter
        source_slugs = [s.bidder_slug for s in sources[:2]]
        source_ids = [s.id for s in sources[:2]]
        response = self.client.get(reverse("k1api.content_ads.sources"), {"source_slugs": ",".join(source_slugs)})
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set(source_ids), set([ca["source_id"] for ca in data["response"]]))

    @mock.patch.object(content_ads.ContentAdSourcesView, "_is_blocked_by_sspd")
    @mock.patch.object(content_ads.ContentAdSourcesView, "_is_blocked_by_amplify")
    def test_get_content_ads_non_blocked(self, mock_sspd, mock_amplify):
        cad = magic_mixer.blend(dash.models.ContentAd)
        cadss = magic_mixer.cycle(4).blend(dash.models.ContentAdSource, content_ad=cad)

        def set_blocked(mock_obj, content_ad_sources):
            blocked_ids = set(cas.id for cas in content_ad_sources)

            def side_effect(content_ad_source_values, _):
                return content_ad_source_values["id"] in blocked_ids

            mock_obj.side_effect = side_effect

        # include blocked - all blocked, all returned
        set_blocked(mock_sspd, cadss)
        set_blocked(mock_amplify, cadss)
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"content_ad_ids": cad.id, "include_blocked": "true"}
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set(cads.id for cads in cadss), set([ca["id"] for ca in data["response"]]))

        # do not include blocked - all blocked, none returned
        set_blocked(mock_sspd, cadss)
        set_blocked(mock_amplify, cadss)
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"content_ad_ids": cad.id, "include_blocked": "false"}
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set(), set([ca["id"] for ca in data["response"]]))

        # do not include blocked - none blocked, all returned
        set_blocked(mock_sspd, [])
        set_blocked(mock_amplify, [])
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"content_ad_ids": cad.id, "include_blocked": "false"}
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set(cads.id for cads in cadss), set([ca["id"] for ca in data["response"]]))

        # do not include blocked - some blocked, some returned
        set_blocked(mock_sspd, cadss[0:2])
        set_blocked(mock_amplify, cadss[1:3])
        response = self.client.get(
            reverse("k1api.content_ads.sources"), {"content_ad_ids": cad.id, "include_blocked": "false"}
        )
        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        self.assertEqual(set([cadss[3].id]), set([ca["id"] for ca in data["response"]]))

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

    @mock.patch("utils.metrics_compat.timing")
    @mock.patch("utils.dates_helper.utc_now")
    def test_update_content_ad_status_influx(self, mock_now, mock_influx_timing):

        mock_now.return_value = datetime(2018, 9, 7, 13, 41, 24, 394696)
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

    def test_get_content_ads_exclude_display(self):
        campaign_native = magic_mixer.blend(dash.models.Campaign, type=dash.constants.CampaignType.CONTENT)
        campaign_display = magic_mixer.blend(dash.models.Campaign, type=dash.constants.CampaignType.DISPLAY)

        ad_group_native = magic_mixer.blend(dash.models.AdGroup, campaign=campaign_native)
        ad_group_display = magic_mixer.blend(dash.models.AdGroup, campaign=campaign_display)

        content_ads_native = magic_mixer.cycle(10).blend(
            dash.models.ContentAd, ad_group=ad_group_native, type=dash.constants.AdType.CONTENT
        )
        magic_mixer.cycle(10).blend(dash.models.ContentAd, ad_group=ad_group_display, type=dash.constants.AdType.IMAGE)

        response = self.client.get(
            reverse("k1api.content_ads"),
            {
                "ad_group_ids": ",".join(str(ag.id) for ag in [ad_group_native, ad_group_display]),
                "exclude_display": "true",
            },
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]
        self.assertEqual(set([obj["id"] for obj in data]), set([obj.id for obj in content_ads_native]))

    def test_get_content_ad_sources_exclude_display(self):
        campaign_native = magic_mixer.blend(dash.models.Campaign, type=dash.constants.CampaignType.CONTENT)
        campaign_display = magic_mixer.blend(dash.models.Campaign, type=dash.constants.CampaignType.DISPLAY)

        ad_group_native = magic_mixer.blend(dash.models.AdGroup, campaign=campaign_native)
        ad_group_display = magic_mixer.blend(dash.models.AdGroup, campaign=campaign_display)

        content_ad_native = magic_mixer.blend(
            dash.models.ContentAd, ad_group=ad_group_native, type=dash.constants.AdType.CONTENT
        )
        content_ad_display = magic_mixer.blend(
            dash.models.ContentAd, ad_group=ad_group_display, type=dash.constants.AdType.IMAGE
        )

        sources = magic_mixer.cycle(10).blend(dash.models.Source)

        content_ad_sources_native = magic_mixer.cycle(len(sources)).blend(
            dash.models.ContentAdSource, content_ad=content_ad_native, source=(s for s in sources)
        )
        magic_mixer.cycle(len(sources)).blend(
            dash.models.ContentAdSource, content_ad=content_ad_display, source=(s for s in sources)
        )

        response = self.client.get(
            reverse("k1api.content_ads.sources"),
            {
                "content_ad_ids": ",".join(str(ca.id) for ca in [content_ad_native, content_ad_display]),
                "include_state": "false",
                "exclude_display": "true",
            },
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data["response"]
        self.assertEqual(set([obj["id"] for obj in data]), set([obj.id for obj in content_ad_sources_native]))
