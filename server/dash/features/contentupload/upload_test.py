# -*- coding: utf-8 -*-
import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http.request import HttpRequest
from django.test import TestCase
from django.test import override_settings
from mock import Mock
from mock import patch

import core.features.videoassets
import utils.s3helpers
import zemauth.models
from dash import constants
from dash import forms
from dash import models
from dash.features import contentupload
from utils.magic_mixer import magic_mixer

valid_candidate = {
    "label": "test",
    "url": "http://zemanta.com/test-content-ad",
    "title": "test content ad",
    "image_url": "http://zemanta.com/test-image.jpg",
    "image_crop": "faces",
    "display_url": "zemanta.com",
    "brand_name": "zemanta",
    "description": "zemanta content ad",
    "call_to_action": "read more",
    "primary_tracker_url": "https://example.com/px1.png",
    "secondary_tracker_url": "https://example.com/px2.png",
    "additional_data": {"a": 1},
    "trackers": [
        {
            "event_type": constants.TrackerEventType.IMPRESSION,
            "method": constants.TrackerMethod.JS,
            "url": "https://t.test.com/tracker.js",
            "fallback_url": "https://t.test.com/fallback.png",
            "tracker_optional": True,
        },
        {
            "event_type": constants.TrackerEventType.VIEWABILITY,
            "method": constants.TrackerMethod.IMG,
            "url": "https://t.test.com/tracker.png",
            "tracker_optional": True,
        },
    ],
}

invalid_candidate = {
    "label": "repeat" * 61,
    "url": "ftp://zemanta.com/test-content-ad",
    "image_url": "file://zemanta.com/test-image.jpg",
    "image_crop": "landscape",
    "display_url": "zemanta.com" * 10,
    "primary_tracker_url": "http://example.com/px1.png",
    "secondary_tracker_url": "http://example.com/px2.png",
    "trackers": [
        {
            "event_type": constants.TrackerEventType.IMPRESSION,
            "method": constants.TrackerMethod.JS,
            "url": "https://t.test.com/tracker.js",
            "fallback_url": "https://t.test.com/fallback.png",
            "tracker_optional": True,
        },
        {
            "event_type": constants.TrackerEventType.VIEWABILITY,
            "method": constants.TrackerMethod.IMG,
            "url": "https://t.test.com/tracker.png",
            "tracker_optional": True,
        },
    ],
}

valid_display_candidate = {
    "label": "test",
    "type": constants.AdType.IMAGE,
    "url": "http://zemanta.com/test-content-ad",
    "title": "test content ad",
    "image_url": "http://zemanta.com/test-image.jpg",
    "display_url": "zemanta.com",
    "primary_tracker_url": "https://example.com/px1.png",
    "secondary_tracker_url": "https://example.com/px2.png",
    "trackers": [
        {
            "event_type": constants.TrackerEventType.IMPRESSION,
            "method": constants.TrackerMethod.JS,
            "url": "https://t.test.com/tracker.js",
            "fallback_url": "https://t.test.com/fallback.png",
            "tracker_optional": True,
        },
        {
            "event_type": constants.TrackerEventType.VIEWABILITY,
            "method": constants.TrackerMethod.IMG,
            "url": "https://t.test.com/tracker.png",
            "tracker_optional": True,
        },
    ],
}

invalid_display_candidate = {
    "label": "repeat" * 61,
    "type": constants.AdType.IMAGE,
    "url": "ftp://zemanta.com/test-content-ad",
    "image_url": "file://zemanta.com/test-image.jpg",
    "primary_tracker_url": "http://example.com/px1.png",
    "secondary_tracker_url": "http://example.com/px2.png",
    "trackers": [
        {
            "event_type": constants.TrackerEventType.IMPRESSION,
            "method": constants.TrackerMethod.JS,
            "url": "https://t.test.com/tracker.js",
            "fallback_url": "https://t.test.com/fallback.png",
            "tracker_optional": True,
        },
        {
            "event_type": constants.TrackerEventType.VIEWABILITY,
            "method": constants.TrackerMethod.IMG,
            "url": "https://t.test.com/tracker.png",
            "tracker_optional": True,
        },
    ],
}

valid_display_ad_tag_candidate = {
    "label": "test",
    "title": "Ad tag test",
    "type": constants.AdType.AD_TAG,
    "url": "http://zemanta.com/test-content-ad",
    "ad_tag": "<body></body>",
    "image_width": 300,
    "image_height": 250,
    "display_url": "zemanta.com",
    "primary_tracker_url": "https://example.com/px1.png",
    "secondary_tracker_url": "https://example.com/px2.png",
    "trackers": [
        {
            "event_type": constants.TrackerEventType.IMPRESSION,
            "method": constants.TrackerMethod.JS,
            "url": "https://t.test.com/tracker.js",
            "fallback_url": "https://t.test.com/fallback.png",
            "tracker_optional": True,
        },
        {
            "event_type": constants.TrackerEventType.VIEWABILITY,
            "method": constants.TrackerMethod.IMG,
            "url": "https://t.test.com/tracker.png",
            "tracker_optional": True,
        },
    ],
}

invalid_display_ad_tag_candidate = {
    "label": "repeat" * 61,
    "type": constants.AdType.AD_TAG,
    "url": "ftp://zemanta.com/test-content-ad",
    "image_height": 100,
    "primary_tracker_url": "http://example.com/px1.png",
    "secondary_tracker_url": "http://example.com/px2.png",
    "trackers": [
        {
            "event_type": constants.TrackerEventType.IMPRESSION,
            "method": constants.TrackerMethod.JS,
            "url": "http://t.test.com/tracker.js",
            "fallback_url": "https://t.test.com/fallback.png",
            "tracker_optional": True,
        },
        {
            "event_type": constants.TrackerEventType.VIEWABILITY,
            "method": constants.TrackerMethod.IMG,
            "url": "http://t.test.com/tracker.png",
            "tracker_optional": True,
        },
    ],
}


class InsertCandidatesTestCase(TestCase):
    fixtures = ["test_upload.yaml"]

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_insert_candidates(self):
        data = [valid_candidate]

        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        batch_name = "batch1"
        filename = "test_upload.csv"
        self.assertEqual(0, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        contentupload.upload.insert_candidates(None, account, data, ad_group, batch_name, filename)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(filename, batch.original_filename)

        candidate = models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual(valid_candidate["label"], candidate.label)
        self.assertEqual(valid_candidate["url"], candidate.url)
        self.assertEqual(valid_candidate["title"], candidate.title)
        self.assertEqual(valid_candidate["image_url"], candidate.image_url)
        self.assertEqual(valid_candidate["image_crop"], candidate.image_crop)
        self.assertEqual(valid_candidate["display_url"], candidate.display_url)
        self.assertEqual(valid_candidate["brand_name"], candidate.brand_name)
        self.assertEqual(valid_candidate["description"], candidate.description)
        self.assertEqual(valid_candidate["call_to_action"], candidate.call_to_action)
        self.assertEqual(valid_candidate["primary_tracker_url"], candidate.primary_tracker_url)
        self.assertEqual(valid_candidate["secondary_tracker_url"], candidate.secondary_tracker_url)
        self.assertEqual(
            [
                {
                    "event_type": constants.TrackerEventType.IMPRESSION,
                    "method": constants.TrackerMethod.JS,
                    "url": "https://t.test.com/tracker.js",
                    "fallback_url": "https://t.test.com/fallback.png",
                    "tracker_optional": True,
                    "supported_privacy_frameworks": [],
                },
                {
                    "event_type": constants.TrackerEventType.VIEWABILITY,
                    "method": constants.TrackerMethod.IMG,
                    "url": "https://t.test.com/tracker.png",
                    "fallback_url": None,
                    "tracker_optional": True,
                    "supported_privacy_frameworks": [],
                },
            ],
            candidate.trackers,
        )
        self.assertEqual(
            {
                "https://t.test.com/tracker.js__js": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                "https://t.test.com/fallback.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                "https://t.test.com/tracker.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
            },
            candidate.trackers_status,
        )
        self.assertEqual(valid_candidate["additional_data"], candidate.additional_data)
        self.assertEqual(None, candidate.ad_tag)

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_empty_candidate(self):
        data = [{}]

        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        batch_name = "batch1"
        filename = "test_upload.csv"
        self.assertEqual(0, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        contentupload.upload.insert_candidates(None, account, data, ad_group, batch_name, filename)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(filename, batch.original_filename)

        candidate = models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual("", candidate.label)
        self.assertEqual("", candidate.url)
        self.assertEqual("", candidate.title)
        self.assertEqual("", candidate.image_url)
        self.assertEqual("center", candidate.image_crop)
        self.assertEqual("", candidate.display_url)
        self.assertEqual("", candidate.brand_name)
        self.assertEqual("", candidate.description)
        self.assertEqual("Read more", candidate.call_to_action)
        self.assertEqual("", candidate.primary_tracker_url)
        self.assertEqual("", candidate.secondary_tracker_url)
        self.assertEqual(None, candidate.ad_tag)

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_automatic_fields(self):
        test_candidate = {
            "url": "http://zemanta.com/test-content-ad",
            "title": "test content ad",
            "image_url": "http://zemanta.com/test-image.jpg",
            "description": "zemanta content ad",
        }

        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        batch_name = "batch1"
        filename = "test_upload.csv"
        self.assertEqual(0, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        contentupload.upload.insert_candidates(None, account, [test_candidate], ad_group, batch_name, filename)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(filename, batch.original_filename)

        candidate = models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual("", candidate.label)
        self.assertEqual(test_candidate["url"], candidate.url)
        self.assertEqual(test_candidate["title"], candidate.title)
        self.assertEqual(test_candidate["image_url"], candidate.image_url)
        self.assertEqual("center", candidate.image_crop)
        self.assertEqual("", candidate.display_url)
        self.assertEqual("", candidate.brand_name)
        self.assertEqual(test_candidate["description"], candidate.description)
        self.assertEqual("Read more", candidate.call_to_action)
        self.assertEqual("", candidate.primary_tracker_url)
        self.assertEqual("", candidate.secondary_tracker_url)
        self.assertEqual(None, candidate.ad_tag)

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_insert_display_candidates(self):
        data = [valid_display_candidate]

        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        batch_name = "batch1"
        filename = "test_upload.csv"
        self.assertEqual(0, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        contentupload.upload.insert_candidates(None, account, data, ad_group, batch_name, filename)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(filename, batch.original_filename)

        candidate = models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual(valid_display_candidate["label"], candidate.label)
        self.assertEqual(valid_display_candidate["url"], candidate.url)
        self.assertEqual(valid_display_candidate["title"], candidate.title)
        self.assertEqual(valid_display_candidate["image_url"], candidate.image_url)
        self.assertEqual("center", candidate.image_crop)
        self.assertEqual(valid_display_candidate["display_url"], candidate.display_url)
        self.assertEqual("", candidate.brand_name)
        self.assertEqual("", candidate.description)
        self.assertEqual("Read more", candidate.call_to_action)
        self.assertEqual(valid_display_candidate["primary_tracker_url"], candidate.primary_tracker_url)
        self.assertEqual(valid_display_candidate["secondary_tracker_url"], candidate.secondary_tracker_url)
        self.assertEqual(None, candidate.additional_data)
        self.assertEqual(None, candidate.ad_tag)

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_insert_display_ad_tag_candidates(self):
        data = [valid_display_ad_tag_candidate]

        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        batch_name = "batch1"
        filename = "test_upload.csv"
        self.assertEqual(0, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(0, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        contentupload.upload.insert_candidates(None, account, data, ad_group, batch_name, filename)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())
        self.assertEqual(1, models.ContentAdCandidate.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(batch_name, batch.name)
        self.assertEqual(ad_group, batch.ad_group)
        self.assertEqual(filename, batch.original_filename)

        candidate = models.ContentAdCandidate.objects.filter(ad_group=ad_group).get()
        self.assertEqual(valid_display_ad_tag_candidate["label"], candidate.label)
        self.assertEqual(valid_display_ad_tag_candidate["url"], candidate.url)
        self.assertEqual(valid_display_ad_tag_candidate["title"], candidate.title)
        self.assertEqual("", candidate.image_url)
        self.assertEqual("center", candidate.image_crop)
        self.assertEqual(valid_display_ad_tag_candidate["display_url"], candidate.display_url)
        self.assertEqual("", candidate.brand_name)
        self.assertEqual("", candidate.description)
        self.assertEqual("Read more", candidate.call_to_action)
        self.assertEqual(valid_display_ad_tag_candidate["primary_tracker_url"], candidate.primary_tracker_url)
        self.assertEqual(valid_display_ad_tag_candidate["secondary_tracker_url"], candidate.secondary_tracker_url)
        self.assertEqual(None, candidate.additional_data)
        self.assertEqual(valid_display_ad_tag_candidate["ad_tag"], candidate.ad_tag)


class InsertEditCandidatesTestCase(TestCase):
    fixtures = ["test_upload.yaml"]

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_insert_edit_candidates(self):
        ad_group = models.AdGroup.objects.get(id=5)
        content_ads = ad_group.contentad_set.all()
        in_progress_before = ad_group.uploadbatch_set.filter(status=constants.UploadBatchStatus.IN_PROGRESS).count()

        contentupload.upload.insert_edit_candidates(None, content_ads, ad_group)
        in_progress_after = ad_group.uploadbatch_set.filter(status=constants.UploadBatchStatus.IN_PROGRESS).count()
        self.assertEqual(in_progress_before + 1, in_progress_after)

        batch = ad_group.uploadbatch_set.get(status=constants.UploadBatchStatus.IN_PROGRESS)
        self.assertEqual(constants.UploadBatchType.EDIT, batch.type)
        self.assertEqual(1, batch.contentadcandidate_set.count())

        candidate = batch.contentadcandidate_set.get()
        self.assertEqual(content_ads[0].ad_group_id, candidate.ad_group_id)
        self.assertNotEqual(content_ads[0].batch_id, candidate.batch_id)
        self.assertEqual(constants.AsyncUploadJobStatus.WAITING_RESPONSE, candidate.image_status)
        self.assertEqual(constants.AsyncUploadJobStatus.WAITING_RESPONSE, candidate.url_status)
        self.assertEqual(content_ads[0].label, candidate.label)
        self.assertEqual(content_ads[0].title, candidate.title)
        self.assertEqual(content_ads[0].url, candidate.url)
        self.assertEqual(content_ads[0].get_image_url(), candidate.image_url)
        self.assertEqual(content_ads[0].image_crop, candidate.image_crop)
        self.assertEqual(content_ads[0].display_url, candidate.display_url)
        self.assertEqual(content_ads[0].brand_name, candidate.brand_name)
        self.assertEqual(content_ads[0].description, candidate.description)
        self.assertEqual(content_ads[0].call_to_action, candidate.call_to_action)
        self.assertEqual(content_ads[0].tracker_urls[0], candidate.primary_tracker_url)
        self.assertEqual(content_ads[0].tracker_urls[1], candidate.secondary_tracker_url)
        self.assertEqual(None, candidate.image_id)
        self.assertEqual(None, candidate.image_width)
        self.assertEqual(None, candidate.image_height)
        self.assertEqual(None, candidate.image_hash)
        self.assertEqual(content_ads[0], candidate.original_content_ad)

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_insert_edit_display_candidates(self):
        ad_group = models.AdGroup.objects.get(id=8)
        content_ads = ad_group.contentad_set.all()
        in_progress_before = ad_group.uploadbatch_set.filter(status=constants.UploadBatchStatus.IN_PROGRESS).count()

        contentupload.upload.insert_edit_candidates(None, content_ads, ad_group)
        in_progress_after = ad_group.uploadbatch_set.filter(status=constants.UploadBatchStatus.IN_PROGRESS).count()
        self.assertEqual(in_progress_before + 1, in_progress_after)

        batch = ad_group.uploadbatch_set.get(status=constants.UploadBatchStatus.IN_PROGRESS)
        self.assertEqual(constants.UploadBatchType.EDIT, batch.type)
        self.assertEqual(1, batch.contentadcandidate_set.count())

        candidate = batch.contentadcandidate_set.get()
        self.assertEqual(content_ads[0].ad_group_id, candidate.ad_group_id)
        self.assertNotEqual(content_ads[0].batch_id, candidate.batch_id)
        self.assertEqual(constants.AsyncUploadJobStatus.WAITING_RESPONSE, candidate.image_status)
        self.assertEqual(constants.AsyncUploadJobStatus.WAITING_RESPONSE, candidate.url_status)
        self.assertEqual(content_ads[0].label, candidate.label)
        self.assertEqual(content_ads[0].title, candidate.title)
        self.assertEqual(content_ads[0].url, candidate.url)
        self.assertEqual(content_ads[0].get_image_url(), candidate.image_url)
        self.assertEqual(content_ads[0].image_crop, candidate.image_crop)
        self.assertEqual(content_ads[0].display_url, candidate.display_url)
        self.assertEqual(content_ads[0].brand_name, candidate.brand_name)
        self.assertEqual(content_ads[0].description, candidate.description)
        self.assertEqual(content_ads[0].call_to_action, candidate.call_to_action)
        self.assertEqual(content_ads[0].tracker_urls[0], candidate.primary_tracker_url)
        self.assertEqual(content_ads[0].tracker_urls[1], candidate.secondary_tracker_url)
        self.assertEqual(content_ads[0].ad_tag, candidate.ad_tag)
        self.assertEqual(None, candidate.image_id)
        self.assertEqual(None, candidate.image_width)
        self.assertEqual(None, candidate.image_height)
        self.assertEqual(None, candidate.image_hash)
        self.assertEqual(content_ads[0], candidate.original_content_ad)


class PersistBatchTestCase(TestCase):
    fixtures = ["test_upload.yaml"]

    @override_settings(IMAGE_THUMBNAIL_URL="http://test.com")
    @patch("utils.sspd_client.sync_batch", Mock())
    @patch.object(utils.s3helpers.S3Helper, "put")
    def test_valid_candidates(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=2)

        candidate = batch.contentadcandidate_set.get()
        candidate.type = constants.AdType.VIDEO
        candidate.save()
        candidate.ad_group.campaign.type = constants.CampaignType.VIDEO
        candidate.ad_group.campaign.save()

        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        contentupload.upload.persist_batch(batch)
        self.assertEqual(0, batch.contentadcandidate_set.count())
        self.assertEqual(1, batch.contentad_set.count())
        self.assertFalse(mock_s3helper_put.called)

        content_ad = batch.contentad_set.get()
        self.assertEqual(1, len(content_ad.contentadsource_set.all()))

        self.assertEqual(candidate.label, content_ad.label)
        self.assertEqual(candidate.url, content_ad.url)
        self.assertEqual(candidate.title, content_ad.title)
        self.assertEqual(candidate.display_url, content_ad.display_url)
        self.assertEqual(candidate.description, content_ad.description)
        self.assertEqual(candidate.brand_name, content_ad.brand_name)
        self.assertEqual(candidate.call_to_action, content_ad.call_to_action)
        self.assertEqual([candidate.primary_tracker_url, candidate.secondary_tracker_url], content_ad.tracker_urls)
        self.assertEqual(candidate.image_id, content_ad.image_id)
        self.assertEqual(candidate.image_width, content_ad.image_width)
        self.assertEqual(candidate.image_height, content_ad.image_height)
        self.assertEqual(candidate.image_hash, content_ad.image_hash)
        self.assertEqual(candidate.icon_id, content_ad.icon.image_id)
        self.assertEqual(candidate.icon_width, content_ad.icon.width)
        self.assertEqual(candidate.icon_height, content_ad.icon.height)
        self.assertEqual(candidate.icon_hash, content_ad.icon.image_hash)
        self.assertEqual(candidate.icon_file_size, content_ad.icon.file_size)
        self.assertEqual(candidate.icon_url, content_ad.icon.origin_url)
        self.assertEqual(candidate.ad_tag, content_ad.ad_tag)
        self.assertEqual(candidate.state, content_ad.state)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

        ad_group = magic_mixer.blend(models.AdGroup, campaign__type=constants.CampaignType.VIDEO)
        batch2 = magic_mixer.blend(models.UploadBatch, ad_group=ad_group)
        video_asset2 = magic_mixer.blend(
            core.features.videoassets.models.VideoAsset,
            account=ad_group.campaign.account,
            id="12345678-abcd-1234-abcd-123abcd12345",
            type=core.features.videoassets.constants.VideoAssetType.DIRECT_UPLOAD,
        )
        candidate2 = magic_mixer.blend(
            models.ContentAdCandidate,
            batch=batch2,
            ad_group=ad_group,
            type=constants.AdType.VIDEO,
            url_status=constants.AsyncUploadJobStatus.OK,
            image_status=constants.AsyncUploadJobStatus.OK,
            icon_status=constants.AsyncUploadJobStatus.OK,
            call_to_action="call to action",
            url="http://url.com",
            title="test",
            image_url="https://image.url",
            display_url="https://display.url",
            brand_name="test",
            description="test",
            image_id=candidate.image_id,
            image_hash=candidate.image_hash,
            image_width=candidate.image_width,
            image_height=candidate.image_height,
            image_file_size=candidate.image_file_size,
            icon_id=candidate.icon_id,
            icon_hash=candidate.icon_hash,
            icon_width=candidate.icon_width,
            icon_height=candidate.icon_height,
            icon_file_size=candidate.icon_file_size,
            icon_url="https://test2.com",
            original_content_ad=None,
            video_asset_id=video_asset2.id,
        )

        contentupload.upload.persist_batch(batch2)
        self.assertEqual(0, batch2.contentadcandidate_set.count())
        self.assertEqual(1, batch2.contentad_set.count())

        content_ad2 = batch2.contentad_set.get()
        self.assertEqual(candidate2.icon_id, content_ad2.icon.image_id)
        self.assertEqual(candidate2.icon_width, content_ad2.icon.width)
        self.assertEqual(candidate2.icon_height, content_ad2.icon.height)
        self.assertEqual(candidate2.icon_hash, content_ad2.icon.image_hash)
        self.assertEqual(candidate2.icon_file_size, content_ad2.icon.file_size)
        self.assertEqual(candidate2.state, content_ad2.state)
        self.assertEqual(candidate.icon_url, content_ad2.icon.origin_url)

        self.assertEqual(1, models.ImageAsset.objects.all().count())

    @override_settings(IMAGE_THUMBNAIL_URL="http://test.com")
    @patch("utils.sspd_client.sync_batch", Mock())
    def test_valid_candidates_with_inactive_state(self):
        batch = models.UploadBatch.objects.get(id=12)

        candidate = batch.contentadcandidate_set.get()
        candidate.type = constants.AdType.VIDEO
        candidate.save()
        candidate.ad_group.campaign.type = constants.CampaignType.VIDEO
        candidate.ad_group.campaign.save()

        contentupload.upload.persist_batch(batch)

        self.assertEqual(constants.ContentAdSourceState.INACTIVE, candidate.state)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

        ad_group = magic_mixer.blend(models.AdGroup, campaign__type=constants.CampaignType.VIDEO)
        batch2 = magic_mixer.blend(models.UploadBatch, ad_group=ad_group)
        video_asset2 = magic_mixer.blend(
            core.features.videoassets.models.VideoAsset,
            account=ad_group.campaign.account,
            id="12345678-abcd-1234-abcd-123abcd12345",
            type=core.features.videoassets.constants.VideoAssetType.DIRECT_UPLOAD,
        )
        candidate2 = magic_mixer.blend(
            models.ContentAdCandidate,
            batch=batch2,
            ad_group=ad_group,
            type=constants.AdType.VIDEO,
            url_status=constants.AsyncUploadJobStatus.OK,
            image_status=constants.AsyncUploadJobStatus.OK,
            icon_status=constants.AsyncUploadJobStatus.OK,
            state=constants.ContentAdSourceState.INACTIVE,
            call_to_action="Call to action",
            url="http://url.com",
            title="test",
            image_url="https://image.url",
            display_url="https://display.url",
            brand_name="test",
            description="test",
            image_id=candidate.image_id,
            image_hash=candidate.image_hash,
            image_width=candidate.image_width,
            image_height=candidate.image_height,
            image_file_size=candidate.image_file_size,
            icon_id=candidate.icon_id,
            icon_hash=candidate.icon_hash,
            icon_width=candidate.icon_width,
            icon_height=candidate.icon_height,
            icon_file_size=candidate.icon_file_size,
            icon_url="https://test2.com",
            original_content_ad=None,
            video_asset_id=video_asset2.id,
        )

        contentupload.upload.persist_batch(batch2)

        content_ad2 = batch2.contentad_set.get()
        self.assertEqual(candidate2.state, content_ad2.state)
        self.assertEqual(1, models.ImageAsset.objects.all().count())

    @override_settings(IMAGE_THUMBNAIL_URL="http://test.com")
    @patch("utils.sspd_client.sync_batch", Mock())
    @patch.object(utils.s3helpers.S3Helper, "put")
    def test_valid_cloned_candidates_bid_modifier(self, mock_s3helper_put):
        source_ad_group = magic_mixer.blend(models.AdGroup)
        source_content_ad = magic_mixer.blend(models.ContentAd, ad_group=source_ad_group)
        magic_mixer.blend(
            core.features.bid_modifiers.models.BidModifier,
            ad_group=source_ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.AD,
            target=str(source_content_ad.id),
            modifier=1.5,
        )

        ad_group = magic_mixer.blend(models.AdGroup)
        batch = magic_mixer.blend(models.UploadBatch, ad_group=ad_group)
        magic_mixer.blend(
            models.ContentAdCandidate,
            batch=batch,
            ad_group=ad_group,
            url_status=constants.AsyncUploadJobStatus.OK,
            image_status=constants.AsyncUploadJobStatus.OK,
            icon_status=constants.AsyncUploadJobStatus.OK,
            call_to_action="Call to action",
            url="http://url.com",
            title="test",
            image_url="https://image.url",
            display_url="https://display.url",
            brand_name="test",
            description="test",
            image_id="image",
            image_hash="hash",
            image_width=300,
            image_height=300,
            image_file_size=1000,
            icon_id="icon",
            icon_hash="iconhash",
            icon_width=150,
            icon_height=150,
            icon_file_size=1000,
            icon_url="https://test.com",
            video_asset_id=None,
            original_content_ad=source_content_ad,
        )

        contentupload.upload.persist_batch(batch)
        self.assertEqual(0, batch.contentadcandidate_set.count())
        self.assertEqual(1, batch.contentad_set.count())

        content_ad = batch.contentad_set.get()
        bid_modifier = core.features.bid_modifiers.BidModifier.objects.get(
            ad_group=ad_group, type=core.features.bid_modifiers.constants.BidModifierType.AD, target=str(content_ad.id)
        )
        self.assertEqual(1.5, bid_modifier.modifier)

    @patch.object(utils.s3helpers.S3Helper, "put")
    def test_valid_display_ad_candidates(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=11)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        candidate = batch.contentadcandidate_set.get()
        candidate.ad_group.campaign.type = constants.CampaignType.DISPLAY
        candidate.ad_group.campaign.save()

        contentupload.upload.persist_batch(batch)
        self.assertEqual(0, batch.contentadcandidate_set.count())
        self.assertEqual(1, batch.contentad_set.count())
        self.assertFalse(mock_s3helper_put.called)

        content_ad = batch.contentad_set.get()
        self.assertEqual(1, len(content_ad.contentadsource_set.all()))

        self.assertEqual(candidate.label, content_ad.label)
        self.assertEqual(candidate.url, content_ad.url)
        self.assertEqual(candidate.title, content_ad.title)
        self.assertEqual(candidate.display_url, content_ad.display_url)
        self.assertEqual(candidate.description, content_ad.description)
        self.assertEqual(candidate.brand_name, content_ad.brand_name)
        self.assertEqual(candidate.call_to_action, content_ad.call_to_action)
        self.assertEqual([candidate.primary_tracker_url, candidate.secondary_tracker_url], content_ad.tracker_urls)
        self.assertEqual(candidate.image_id, content_ad.image_id)
        self.assertEqual(candidate.image_width, content_ad.image_width)
        self.assertEqual(candidate.image_height, content_ad.image_height)
        self.assertEqual(candidate.image_hash, content_ad.image_hash)
        self.assertEqual(candidate.image_file_size, content_ad.image_file_size)
        self.assertEqual(candidate.ad_tag, content_ad.ad_tag)
        self.assertEqual(candidate.state, content_ad.state)
        self.assertFalse(candidate.ad_tag)
        self.assertIsNone(content_ad.icon)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

    @patch.object(utils.s3helpers.S3Helper, "put")
    def test_valid_display_ad_tag_candidates(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=10)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        candidate = batch.contentadcandidate_set.get()
        candidate.ad_group.campaign.type = constants.CampaignType.DISPLAY
        candidate.ad_group.campaign.save()

        contentupload.upload.persist_batch(batch)
        self.assertEqual(0, batch.contentadcandidate_set.count())
        self.assertEqual(1, batch.contentad_set.count())
        self.assertFalse(mock_s3helper_put.called)

        content_ad = batch.contentad_set.get()
        self.assertEqual(1, len(content_ad.contentadsource_set.all()))

        self.assertEqual(candidate.label, content_ad.label)
        self.assertEqual(candidate.url, content_ad.url)
        self.assertEqual(candidate.title, content_ad.title)
        self.assertEqual(candidate.display_url, content_ad.display_url)
        self.assertEqual(candidate.description, content_ad.description)
        self.assertEqual(candidate.brand_name, content_ad.brand_name)
        self.assertEqual(candidate.call_to_action, content_ad.call_to_action)
        self.assertEqual([candidate.primary_tracker_url, candidate.secondary_tracker_url], content_ad.tracker_urls)
        self.assertEqual(candidate.image_id, content_ad.image_id)
        self.assertEqual(candidate.image_width, content_ad.image_width)
        self.assertEqual(candidate.image_height, content_ad.image_height)
        self.assertEqual(candidate.image_hash, content_ad.image_hash)
        self.assertEqual(candidate.image_file_size, content_ad.image_file_size)
        self.assertEqual(candidate.ad_tag, content_ad.ad_tag)
        self.assertEqual(candidate.state, content_ad.state)
        self.assertTrue(candidate.ad_tag)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.DONE, batch.status)

    def test_edit_batch(self):
        batch = models.UploadBatch.objects.get(id=7)
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        with self.assertRaises(contentupload.exc.ChangeForbidden):
            contentupload.upload.persist_batch(batch)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

    @patch.object(utils.s3helpers.S3Helper, "put")
    def test_invalid_candidates(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=3)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        with self.assertRaises(contentupload.exc.CandidateErrorsRemaining):
            contentupload.upload.persist_batch(batch)

        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)

    @patch.object(utils.s3helpers.S3Helper, "put")
    def test_invalid_batch_status(self, mock_s3helper_put):
        batch = models.UploadBatch.objects.get(id=2)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        batch.status = constants.UploadBatchStatus.CANCELLED
        batch.save()

        with self.assertRaises(contentupload.exc.InvalidBatchStatus):
            contentupload.upload.persist_batch(batch)

        # check that nothing changed
        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.CANCELLED, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())
        self.assertFalse(mock_s3helper_put.called)

    def test_ad_group_not_set(self):
        batch = models.UploadBatch.objects.get(id=2)
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())

        batch.ad_group = None
        batch.save()

        with self.assertRaises(contentupload.exc.ChangeForbidden):
            contentupload.upload.persist_batch(batch)

        # check that nothing changed
        batch.refresh_from_db()
        self.assertEqual(1, batch.contentadcandidate_set.count())
        self.assertEqual(0, batch.contentad_set.count())


class PersistEditBatchTestCase(TestCase):

    fixtures = ["test_upload.yaml"]

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = zemauth.models.User.objects.get(id=1)

    @patch("utils.sspd_client.sync_batch", Mock())
    def test_persist_edit_batch(self):
        batch = models.UploadBatch.objects.get(id=7)

        content_ad = models.ContentAd.objects.get(id=2)
        candidate = batch.contentadcandidate_set.get()
        candidate.ad_group.campaign.type = constants.CampaignType.VIDEO
        candidate.ad_group.campaign.save()

        content_ads = contentupload.upload.persist_edit_batch(self.request, batch)
        new_content_ad = models.ContentAd.objects.get(id=content_ad.id)
        self.assertEqual(1, len(content_ads))
        self.assertEqual(new_content_ad, content_ads[0])

        for field in contentupload.upload.VALID_UPDATE_FIELDS:
            if field in ["primary_tracker_url", "secondary_tracker_url"]:
                self.assertTrue(getattr(candidate, field) in new_content_ad.tracker_urls)
                self.assertFalse(getattr(candidate, field) in content_ad.tracker_urls)
                continue
            self.assertNotEqual(getattr(content_ad, field), getattr(new_content_ad, field))
            self.assertEqual(getattr(candidate, field), getattr(new_content_ad, field))

        for field in set(forms.ContentAdCandidateForm.Meta.fields) - contentupload.upload.VALID_UPDATE_FIELDS:
            if field in ["image_url", "icon_url", "state", "trackers_status"]:
                continue
            self.assertEqual(getattr(content_ad, field), getattr(new_content_ad, field))
            if field != "type":
                self.assertNotEqual(getattr(candidate, field), getattr(new_content_ad, field))

        with self.assertRaises(models.UploadBatch.DoesNotExist):
            batch.refresh_from_db()

        with self.assertRaises(models.ContentAdCandidate.DoesNotExist):
            candidate.refresh_from_db()

    def test_invalid_batch_status(self):
        batch = models.UploadBatch.objects.get(id=7)
        batch.status = constants.UploadBatchStatus.CANCELLED

        with self.assertRaises(contentupload.exc.InvalidBatchStatus):
            contentupload.upload.persist_edit_batch(self.request, batch)

    def test_invalid_batch_type(self):
        batch = models.UploadBatch.objects.get(id=7)
        batch.type = constants.UploadBatchType.INSERT

        with self.assertRaises(contentupload.exc.ChangeForbidden):
            contentupload.upload.persist_edit_batch(self.request, batch)

    def test_candidate_without_content_ad(self):
        candidate = models.ContentAdCandidate.objects.filter(id=6).select_related("batch").get()
        candidate.original_content_ad = None
        candidate.save()

        with self.assertRaises(contentupload.exc.ChangeForbidden):
            contentupload.upload.persist_edit_batch(self.request, candidate.batch)

    def test_candidate_with_errors(self):
        candidate = models.ContentAdCandidate.objects.filter(id=6).select_related("batch").get()
        candidate.title = ""
        candidate.save()

        with self.assertRaises(contentupload.exc.CandidateErrorsRemaining):
            contentupload.upload.persist_edit_batch(self.request, candidate.batch)


class CancelUploadTestCase(TestCase):
    fixtures = ["test_upload.yaml"]

    def test_cancel(self):
        ad_group = models.AdGroup.objects.get(id=2)
        self.assertEqual(1, models.UploadBatch.objects.filter(ad_group=ad_group).count())

        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()
        self.assertEqual(constants.UploadBatchStatus.IN_PROGRESS, batch.status)
        self.assertEqual(1, batch.contentadcandidate_set.count())

        contentupload.upload.cancel_upload(batch)

        batch.refresh_from_db()
        self.assertEqual(constants.UploadBatchStatus.CANCELLED, batch.status)
        self.assertEqual(0, batch.contentadcandidate_set.count())

    def test_invalid_status(self):
        ad_group = models.AdGroup.objects.get(id=2)
        batch = models.UploadBatch.objects.filter(ad_group=ad_group).get()

        batch.status = constants.UploadBatchStatus.DONE
        batch.save()

        with self.assertRaises(contentupload.exc.InvalidBatchStatus):
            contentupload.upload.cancel_upload(batch)


class AddCandidateTestCase(TestCase):
    fixtures = ["test_upload.yaml"]

    def test_add_candidate(self):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        new_batch = models.UploadBatch.objects.create(None, account, "test", ad_group)

        candidate = contentupload.upload.add_candidate(new_batch)
        self.assertEqual(ad_group.id, candidate.ad_group_id)
        self.assertEqual(new_batch.id, candidate.batch_id)
        self.assertEqual(
            {
                "id": candidate.id,
                "label": "",
                "state": constants.ContentAdSourceState.ACTIVE,
                "url": "",
                "title": "",
                "type": constants.AdType.CONTENT,
                "image_url": None,
                "image_crop": constants.ImageCrop.CENTER,
                "icon_url": None,
                "display_url": "",
                "brand_name": "",
                "description": "",
                "call_to_action": "",
                "primary_tracker_url": None,
                "secondary_tracker_url": None,
                "image_hash": None,
                "image_height": None,
                "image_width": None,
                "image_id": None,
                "image_file_size": None,
                "image_status": constants.AsyncUploadJobStatus.PENDING_START,
                "icon_hash": None,
                "icon_height": None,
                "icon_width": None,
                "icon_id": None,
                "icon_file_size": None,
                "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                "hosted_icon_url": "/d/icons/IAB24.jpg?w=300&h=300&fit=crop&crop=center",
                "url_status": constants.AsyncUploadJobStatus.PENDING_START,
                "hosted_image_url": None,
                "landscape_hosted_image_url": None,
                "portrait_hosted_image_url": None,
                "display_hosted_image_url": None,
                "video_asset_id": None,
                "ad_tag": None,
                "additional_data": None,
                "primary_tracker_url_status": constants.AsyncUploadJobStatus.PENDING_START,
                "secondary_tracker_url_status": constants.AsyncUploadJobStatus.PENDING_START,
                "can_append_tracking_codes": False,
                "trackers": None,
                "trackers_status": None,
            },
            candidate.to_dict(True),
        )

    def test_with_defaults(self):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        new_batch = models.UploadBatch.objects.create(None, account, "test", ad_group)
        new_batch.default_image_crop = "abc"
        new_batch.default_display_url = "example.com"
        new_batch.default_brand_name = "Example"
        new_batch.default_description = "description"
        new_batch.default_call_to_action = "Contact us!"

        candidate = contentupload.upload.add_candidate(new_batch)
        self.assertEqual(ad_group.id, candidate.ad_group_id)
        self.assertEqual(new_batch.id, candidate.batch_id)
        self.assertEqual(
            {
                "id": candidate.id,
                "label": "",
                "state": constants.ContentAdSourceState.ACTIVE,
                "url": "",
                "title": "",
                "type": constants.AdType.CONTENT,
                "image_url": None,
                "image_crop": "abc",
                "icon_url": None,
                "display_url": "example.com",
                "brand_name": "Example",
                "description": "description",
                "call_to_action": "Contact us!",
                "primary_tracker_url": None,
                "secondary_tracker_url": None,
                "image_hash": None,
                "image_height": None,
                "image_width": None,
                "image_id": None,
                "image_file_size": None,
                "image_status": constants.AsyncUploadJobStatus.PENDING_START,
                "icon_hash": None,
                "icon_height": None,
                "icon_width": None,
                "icon_id": None,
                "icon_file_size": None,
                "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                "hosted_icon_url": "/d/icons/IAB24.jpg?w=300&h=300&fit=crop&crop=center",
                "url_status": constants.AsyncUploadJobStatus.PENDING_START,
                "hosted_image_url": None,
                "landscape_hosted_image_url": None,
                "portrait_hosted_image_url": None,
                "display_hosted_image_url": None,
                "video_asset_id": None,
                "ad_tag": None,
                "additional_data": None,
                "primary_tracker_url_status": constants.AsyncUploadJobStatus.PENDING_START,
                "secondary_tracker_url_status": constants.AsyncUploadJobStatus.PENDING_START,
                "can_append_tracking_codes": False,
                "trackers": None,
                "trackers_status": None,
            },
            candidate.to_dict(True),
        )


class GetCandidatesWithErrorsTestCase(TestCase):
    fixtures = ["test_upload.yaml"]

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_valid_candidate(self):
        data = [valid_candidate]

        # prepare candidate
        request = magic_mixer.blend_request_user()
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group.campaign.type = constants.CampaignType.VIDEO
        video_asset = magic_mixer.blend(
            core.features.videoassets.models.VideoAsset,
            account=account,
            type=core.features.videoassets.constants.VideoAssetType.DIRECT_UPLOAD,
        )
        data[0]["video_asset_id"] = video_asset.id

        batch, candidates = contentupload.upload.insert_candidates(
            None, account, data, ad_group, "batch1", "test_upload.csv"
        )
        result = contentupload.upload.get_candidates_with_errors(request, candidates)

        self.assertEqual(
            [
                {
                    "label": "test",
                    "url": "http://zemanta.com/test-content-ad",
                    "title": "test content ad",
                    "type": constants.AdType.VIDEO,
                    "state": constants.ContentAdSourceState.ACTIVE,
                    "image_url": "http://zemanta.com/test-image.jpg",
                    "image_crop": "faces",
                    "icon_url": None,
                    "display_url": "zemanta.com",
                    "brand_name": "zemanta",
                    "description": "zemanta content ad",
                    "call_to_action": "read more",
                    "primary_tracker_url": "https://example.com/px1.png",
                    "secondary_tracker_url": "https://example.com/px2.png",
                    "hosted_image_url": None,
                    "landscape_hosted_image_url": None,
                    "portrait_hosted_image_url": None,
                    "display_hosted_image_url": None,
                    "image_hash": None,
                    "errors": {"__all__": ["Content ad still processing"]},
                    "image_width": None,
                    "label": "test",
                    "image_id": None,
                    "image_height": None,
                    "url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_file_size": None,
                    "hosted_icon_url": "/d/icons/IAB24.jpg?w=300&h=300&fit=crop&crop=center",
                    "icon_hash": None,
                    "icon_height": None,
                    "icon_width": None,
                    "icon_id": None,
                    "icon_file_size": None,
                    "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "id": candidates[0].id,
                    "video_asset_id": str(video_asset.id),
                    "ad_tag": None,
                    "additional_data": {"a": 1},
                    "primary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "secondary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "can_append_tracking_codes": False,
                    "trackers": [
                        {
                            "event_type": constants.TrackerEventType.IMPRESSION,
                            "method": constants.TrackerMethod.JS,
                            "url": "https://t.test.com/tracker.js",
                            "fallback_url": "https://t.test.com/fallback.png",
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                        {
                            "event_type": constants.TrackerEventType.VIEWABILITY,
                            "method": constants.TrackerMethod.IMG,
                            "url": "https://t.test.com/tracker.png",
                            "fallback_url": None,
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                    ],
                    "trackers_status": {
                        "https://t.test.com/tracker.js__js": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/fallback.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/tracker.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    },
                }
            ],
            result,
        )

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_invalid_candidate(self):
        data = [invalid_candidate]

        # prepare candidate
        request = magic_mixer.blend_request_user()
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(id=1)
        ad_group.campaign.type = constants.CampaignType.VIDEO
        video_asset = magic_mixer.blend(
            core.features.videoassets.models.VideoAsset,
            account=account,
            type=core.features.videoassets.constants.VideoAssetType.VAST_UPLOAD,
        )
        data[0]["video_asset_id"] = video_asset.id

        batch, candidates = contentupload.upload.insert_candidates(
            None, account, data, ad_group, "batch1", "test_upload.csv"
        )
        result = contentupload.upload.get_candidates_with_errors(request, candidates)

        self.assertEqual(
            [
                {
                    "hosted_image_url": None,
                    "landscape_hosted_image_url": None,
                    "portrait_hosted_image_url": None,
                    "display_hosted_image_url": None,
                    "image_crop": "landscape",
                    "state": constants.ContentAdSourceState.ACTIVE,
                    "primary_tracker_url": "http://example.com/px1.png",
                    "image_hash": None,
                    "description": "",
                    "call_to_action": "Read more",
                    "title": "",
                    "type": constants.AdType.VIDEO,
                    "url": "ftp://zemanta.com/test-content-ad",
                    "errors": {
                        "image_crop": ["Choose a valid image crop"],
                        "description": ["Missing description"],
                        "__all__": ["Content ad still processing"],
                        "title": ["Missing title"],
                        "url": ["Invalid URL"],
                        "display_url": ["Display URL too long (max 35 characters)"],
                        "label": ["Label too long (max 256 characters)"],
                        "image_url": ["Invalid image URL"],
                        "brand_name": ["Missing brand name"],
                        "primary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
                        "secondary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
                        "video_asset_id": ["Invalid server response"],
                    },
                    "display_url": "zemanta.comzemanta.comzemanta.comzemanta.comzemanta.com"
                    "zemanta.comzemanta.comzemanta.comzemanta.comzemanta.com",
                    "brand_name": "",
                    "image_width": None,
                    "label": "repeat" * 61,
                    "image_id": None,
                    "image_height": None,
                    "image_url": "file://zemanta.com/test-image.jpg",
                    "url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_file_size": None,
                    "hosted_icon_url": "/d/icons/IAB24.jpg?w=300&h=300&fit=crop&crop=center",
                    "icon_hash": None,
                    "icon_id": None,
                    "icon_height": None,
                    "icon_width": None,
                    "icon_url": None,
                    "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "icon_file_size": None,
                    "secondary_tracker_url": "http://example.com/px2.png",
                    "id": candidates[0].id,
                    "video_asset_id": str(video_asset.id),
                    "ad_tag": None,
                    "additional_data": None,
                    "primary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "secondary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "can_append_tracking_codes": False,
                    "trackers": [
                        {
                            "event_type": constants.TrackerEventType.IMPRESSION,
                            "method": constants.TrackerMethod.JS,
                            "url": "https://t.test.com/tracker.js",
                            "fallback_url": "https://t.test.com/fallback.png",
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                        {
                            "event_type": constants.TrackerEventType.VIEWABILITY,
                            "method": constants.TrackerMethod.IMG,
                            "url": "https://t.test.com/tracker.png",
                            "fallback_url": None,
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                    ],
                    "trackers_status": {
                        "https://t.test.com/tracker.js__js": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/fallback.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/tracker.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    },
                }
            ],
            result,
        )

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_valid_display_candidate(self):
        data = [valid_display_candidate]
        # prepare candidate
        request = magic_mixer.blend_request_user()
        account = models.Account.objects.get(id=1)
        campaign = magic_mixer.blend(models.Campaign, type=constants.CampaignType.DISPLAY, account=account)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        batch, candidates = contentupload.upload.insert_candidates(
            None, account, data, ad_group, "batch1", "test_upload.csv"
        )

        result = contentupload.upload.get_candidates_with_errors(request, candidates)
        self.assertEqual(
            [
                {
                    "label": "test",
                    "url": "http://zemanta.com/test-content-ad",
                    "title": "test content ad",
                    "type": constants.AdType.IMAGE,
                    "state": constants.ContentAdSourceState.ACTIVE,
                    "image_url": "http://zemanta.com/test-image.jpg",
                    "image_crop": "center",
                    "display_url": "zemanta.com",
                    "brand_name": "",
                    "description": "",
                    "call_to_action": "Read more",
                    "primary_tracker_url": "https://example.com/px1.png",
                    "secondary_tracker_url": "https://example.com/px2.png",
                    "hosted_image_url": None,
                    "landscape_hosted_image_url": None,
                    "portrait_hosted_image_url": None,
                    "display_hosted_image_url": None,
                    "image_hash": None,
                    "errors": {"__all__": ["Content ad still processing"]},
                    "image_width": None,
                    "image_id": None,
                    "image_height": None,
                    "url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_file_size": None,
                    "hosted_icon_url": None,
                    "icon_hash": None,
                    "icon_id": None,
                    "icon_height": None,
                    "icon_width": None,
                    "icon_url": None,
                    "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "icon_file_size": None,
                    "id": candidates[0].id,
                    "video_asset_id": None,
                    "ad_tag": None,
                    "additional_data": None,
                    "primary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "secondary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "can_append_tracking_codes": False,
                    "trackers": [
                        {
                            "event_type": constants.TrackerEventType.IMPRESSION,
                            "method": constants.TrackerMethod.JS,
                            "url": "https://t.test.com/tracker.js",
                            "fallback_url": "https://t.test.com/fallback.png",
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                        {
                            "event_type": constants.TrackerEventType.VIEWABILITY,
                            "method": constants.TrackerMethod.IMG,
                            "url": "https://t.test.com/tracker.png",
                            "fallback_url": None,
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                    ],
                    "trackers_status": {
                        "https://t.test.com/tracker.js__js": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/fallback.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/tracker.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    },
                }
            ],
            result,
        )

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_invalid_display_candidate(self):
        data = [invalid_display_candidate]

        # prepare candidate
        request = magic_mixer.blend_request_user()
        account = models.Account.objects.get(id=1)
        campaign = magic_mixer.blend(models.Campaign, type=constants.CampaignType.DISPLAY, account=account)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        batch, candidates = contentupload.upload.insert_candidates(
            None, account, data, ad_group, "batch1", "test_upload.csv"
        )

        result = contentupload.upload.get_candidates_with_errors(request, candidates)
        self.assertEqual(
            [
                {
                    "hosted_image_url": None,
                    "landscape_hosted_image_url": None,
                    "portrait_hosted_image_url": None,
                    "display_hosted_image_url": None,
                    "image_crop": "center",
                    "primary_tracker_url": "http://example.com/px1.png",
                    "image_hash": None,
                    "description": "",
                    "state": constants.ContentAdSourceState.ACTIVE,
                    "call_to_action": "Read more",
                    "title": "",
                    "type": constants.AdType.IMAGE,
                    "url": "ftp://zemanta.com/test-content-ad",
                    "errors": {
                        "__all__": ["Content ad still processing"],
                        "title": ["Missing ad name"],
                        "url": ["Invalid URL"],
                        "label": ["Label too long (max 256 characters)"],
                        "image_url": ["Invalid image URL"],
                        "display_url": ["Missing display URL"],
                        "primary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
                        "secondary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
                    },
                    "display_url": "",
                    "brand_name": "",
                    "image_width": None,
                    "label": "repeat" * 61,
                    "image_id": None,
                    "image_height": None,
                    "image_url": "file://zemanta.com/test-image.jpg",
                    "url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_file_size": None,
                    "hosted_icon_url": None,
                    "icon_hash": None,
                    "icon_id": None,
                    "icon_height": None,
                    "icon_width": None,
                    "icon_url": None,
                    "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "icon_file_size": None,
                    "secondary_tracker_url": "http://example.com/px2.png",
                    "id": candidates[0].id,
                    "video_asset_id": None,
                    "ad_tag": None,
                    "additional_data": None,
                    "primary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "secondary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "can_append_tracking_codes": False,
                    "trackers": [
                        {
                            "event_type": constants.TrackerEventType.IMPRESSION,
                            "method": constants.TrackerMethod.JS,
                            "url": "https://t.test.com/tracker.js",
                            "fallback_url": "https://t.test.com/fallback.png",
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                        {
                            "event_type": constants.TrackerEventType.VIEWABILITY,
                            "method": constants.TrackerMethod.IMG,
                            "url": "https://t.test.com/tracker.png",
                            "fallback_url": None,
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                    ],
                    "trackers_status": {
                        "https://t.test.com/tracker.js__js": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/fallback.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/tracker.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    },
                }
            ],
            result,
        )

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_valid_display_ad_tag_candidate(self):
        data = [valid_display_ad_tag_candidate]
        # prepare candidate
        request = magic_mixer.blend_request_user()
        account = models.Account.objects.get(id=1)
        campaign = magic_mixer.blend(models.Campaign, type=constants.CampaignType.DISPLAY, account=account)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        batch, candidates = contentupload.upload.insert_candidates(
            None, account, data, ad_group, "batch1", "test_upload.csv"
        )

        result = contentupload.upload.get_candidates_with_errors(request, candidates)
        self.assertEqual(
            [
                {
                    "label": "test",
                    "url": "http://zemanta.com/test-content-ad",
                    "title": "Ad tag test",
                    "state": constants.ContentAdSourceState.ACTIVE,
                    "type": constants.AdType.AD_TAG,
                    "image_url": "",
                    "image_crop": "center",
                    "display_url": "zemanta.com",
                    "brand_name": "",
                    "description": "",
                    "call_to_action": "Read more",
                    "primary_tracker_url": "https://example.com/px1.png",
                    "secondary_tracker_url": "https://example.com/px2.png",
                    "hosted_image_url": None,
                    "landscape_hosted_image_url": None,
                    "portrait_hosted_image_url": None,
                    "display_hosted_image_url": None,
                    "image_hash": None,
                    "errors": {"__all__": ["Content ad still processing"]},
                    "image_width": 300,
                    "image_id": None,
                    "image_height": 250,
                    "url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "image_file_size": None,
                    "hosted_icon_url": None,
                    "icon_hash": None,
                    "icon_id": None,
                    "icon_height": None,
                    "icon_width": None,
                    "icon_url": None,
                    "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "icon_file_size": None,
                    "id": candidates[0].id,
                    "video_asset_id": None,
                    "ad_tag": "<body></body>",
                    "additional_data": None,
                    "primary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "secondary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "can_append_tracking_codes": False,
                    "trackers": [
                        {
                            "event_type": constants.TrackerEventType.IMPRESSION,
                            "method": constants.TrackerMethod.JS,
                            "url": "https://t.test.com/tracker.js",
                            "fallback_url": "https://t.test.com/fallback.png",
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                        {
                            "event_type": constants.TrackerEventType.VIEWABILITY,
                            "method": constants.TrackerMethod.IMG,
                            "url": "https://t.test.com/tracker.png",
                            "fallback_url": None,
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                    ],
                    "trackers_status": {
                        "https://t.test.com/tracker.js__js": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/fallback.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/tracker.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    },
                }
            ],
            result,
        )

    @patch("utils.lambda_helper.invoke_lambda", Mock())
    def test_invalid_display_ad_tag_candidate(self):
        data = [invalid_display_ad_tag_candidate]

        # prepare candidate
        request = magic_mixer.blend_request_user()
        account = models.Account.objects.get(id=1)
        campaign = magic_mixer.blend(models.Campaign, type=constants.CampaignType.DISPLAY, account=account)
        ad_group = magic_mixer.blend(models.AdGroup, campaign=campaign)
        batch, candidates = contentupload.upload.insert_candidates(
            None, account, data, ad_group, "batch1", "test_upload.csv"
        )

        result = contentupload.upload.get_candidates_with_errors(request, candidates)
        self.assertEqual(
            [
                {
                    "hosted_image_url": None,
                    "landscape_hosted_image_url": None,
                    "portrait_hosted_image_url": None,
                    "display_hosted_image_url": None,
                    "image_crop": "center",
                    "primary_tracker_url": "http://example.com/px1.png",
                    "image_hash": None,
                    "state": constants.ContentAdSourceState.ACTIVE,
                    "description": "",
                    "call_to_action": "Read more",
                    "title": "",
                    "type": constants.AdType.AD_TAG,
                    "url": "ftp://zemanta.com/test-content-ad",
                    "errors": {
                        "__all__": ["Content ad still processing"],
                        "title": ["Missing ad name"],
                        "url": ["Invalid URL"],
                        "label": ["Label too long (max 256 characters)"],
                        "ad_tag": ["Missing ad tag"],
                        "image_width": ["Missing ad width"],
                        "display_url": ["Missing display URL"],
                        "primary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
                        "secondary_tracker_url": ["Impression tracker URLs have to be HTTPS"],
                        "trackers": [
                            '[{"url": "Impression tracker URLs have to be HTTPS"}, {"url": "Impression tracker URLs have to be HTTPS"}]'
                        ],
                    },
                    "display_url": "",
                    "brand_name": "",
                    "image_width": None,
                    "label": "repeat" * 61,
                    "image_id": None,
                    "image_height": 100,
                    "image_url": "",
                    "url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "image_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "image_file_size": None,
                    "secondary_tracker_url": "http://example.com/px2.png",
                    "hosted_icon_url": None,
                    "icon_hash": None,
                    "icon_id": None,
                    "icon_height": None,
                    "icon_width": None,
                    "icon_url": None,
                    "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
                    "icon_file_size": None,
                    "id": candidates[0].id,
                    "video_asset_id": None,
                    "ad_tag": None,
                    "additional_data": None,
                    "primary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "secondary_tracker_url_status": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    "can_append_tracking_codes": False,
                    "trackers": [
                        {
                            "event_type": constants.TrackerEventType.IMPRESSION,
                            "method": constants.TrackerMethod.JS,
                            "url": "http://t.test.com/tracker.js",
                            "fallback_url": "https://t.test.com/fallback.png",
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                        {
                            "event_type": constants.TrackerEventType.VIEWABILITY,
                            "method": constants.TrackerMethod.IMG,
                            "url": "http://t.test.com/tracker.png",
                            "fallback_url": None,
                            "tracker_optional": True,
                            "supported_privacy_frameworks": [],
                        },
                    ],
                    "trackers_status": {
                        "http://t.test.com/tracker.js__js": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "https://t.test.com/fallback.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                        "http://t.test.com/tracker.png__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
                    },
                }
            ],
            result,
        )


class UpdateCandidateTest(TestCase):

    fixtures = ["test_upload.yaml"]

    def setUp(self):
        candidate_id = 4
        self.candidate = models.ContentAdCandidate.objects.get(id=candidate_id)
        self.other_candidate = self.candidate.batch.contentadcandidate_set.exclude(id=candidate_id).get()
        self.new_candidate = {
            "id": candidate_id,
            "label": "new label",
            "state": constants.ContentAdSourceState.ACTIVE,
            "url": "http://zemanta.com/blog",
            "title": "New title",
            "image_url": "http://zemanta.com/img.jpg",
            "image_crop": "center",
            "display_url": "newurl.com",
            "brand_name": "New brand name",
            "description": "New description",
            "call_to_action": "New cta",
            "primary_tracker_url": "https://primaryTrackerUrl.com",
            "secondary_tracker_url": "",
        }
        self.defaults = ["image_crop", "display_url", "brand_name", "description", "call_to_action"]

    def test_update_candidate(self):
        contentupload.upload.update_candidate(self.new_candidate, [], self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.label, self.new_candidate["label"])
        self.assertEqual(self.candidate.url, self.new_candidate["url"])
        self.assertEqual(self.candidate.title, self.new_candidate["title"])
        self.assertEqual(self.candidate.image_url, self.new_candidate["image_url"])
        self.assertEqual(self.candidate.image_crop, self.new_candidate["image_crop"])
        self.assertEqual(self.candidate.display_url, self.new_candidate["display_url"])
        self.assertEqual(self.candidate.brand_name, self.new_candidate["brand_name"])
        self.assertEqual(self.candidate.description, self.new_candidate["description"])
        self.assertEqual(self.candidate.call_to_action, self.new_candidate["call_to_action"])
        self.assertEqual(self.candidate.primary_tracker_url, self.new_candidate["primary_tracker_url"])
        self.assertEqual(self.candidate.secondary_tracker_url, self.new_candidate["secondary_tracker_url"])
        self.assertEqual(self.candidate.state, self.new_candidate["state"])

        self.other_candidate.refresh_from_db()
        self.assertNotEqual(self.other_candidate.image_crop, self.new_candidate["image_crop"])
        self.assertNotEqual(self.other_candidate.display_url, self.new_candidate["display_url"])
        self.assertNotEqual(self.other_candidate.brand_name, self.new_candidate["brand_name"])
        self.assertNotEqual(self.other_candidate.description, self.new_candidate["description"])
        self.assertNotEqual(self.other_candidate.call_to_action, self.new_candidate["call_to_action"])

    def test_update_with_defaults(self):
        contentupload.upload.update_candidate(self.new_candidate, self.defaults, self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.label, self.new_candidate["label"])
        self.assertEqual(self.candidate.url, self.new_candidate["url"])
        self.assertEqual(self.candidate.title, self.new_candidate["title"])
        self.assertEqual(self.candidate.state, self.new_candidate["state"])

        self.assertEqual(self.candidate.image_url, self.new_candidate["image_url"])
        self.assertEqual(self.candidate.image_crop, self.new_candidate["image_crop"])
        self.assertEqual(self.candidate.display_url, self.new_candidate["display_url"])
        self.assertEqual(self.candidate.brand_name, self.new_candidate["brand_name"])
        self.assertEqual(self.candidate.description, self.new_candidate["description"])
        self.assertEqual(self.candidate.call_to_action, self.new_candidate["call_to_action"])
        self.assertEqual(self.candidate.primary_tracker_url, self.new_candidate["primary_tracker_url"])
        self.assertEqual(self.candidate.secondary_tracker_url, self.new_candidate["secondary_tracker_url"])

        self.other_candidate.refresh_from_db()
        self.assertEqual(self.other_candidate.image_crop, self.new_candidate["image_crop"])
        self.assertEqual(self.other_candidate.display_url, self.new_candidate["display_url"])
        self.assertEqual(self.other_candidate.brand_name, self.new_candidate["brand_name"])
        self.assertEqual(self.other_candidate.description, self.new_candidate["description"])
        self.assertEqual(self.other_candidate.call_to_action, self.new_candidate["call_to_action"])

        self.assertEqual(self.candidate.batch.default_image_crop, self.new_candidate["image_crop"])
        self.assertEqual(self.candidate.batch.default_display_url, self.new_candidate["display_url"])
        self.assertEqual(self.candidate.batch.default_brand_name, self.new_candidate["brand_name"])
        self.assertEqual(self.candidate.batch.default_description, self.new_candidate["description"])
        self.assertEqual(self.candidate.batch.default_call_to_action, self.new_candidate["call_to_action"])

    def test_unknown_defaults(self):
        defaults = ["title", "url", "label", "image_url", "primary_tracker_url", "secondary_tracker_url"]
        contentupload.upload.update_candidate(self.new_candidate, defaults, self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.label, self.new_candidate["label"])
        self.assertEqual(self.candidate.url, self.new_candidate["url"])
        self.assertEqual(self.candidate.title, self.new_candidate["title"])
        self.assertEqual(self.candidate.image_url, self.new_candidate["image_url"])
        self.assertEqual(self.candidate.image_crop, self.new_candidate["image_crop"])
        self.assertEqual(self.candidate.display_url, self.new_candidate["display_url"])
        self.assertEqual(self.candidate.brand_name, self.new_candidate["brand_name"])
        self.assertEqual(self.candidate.description, self.new_candidate["description"])
        self.assertEqual(self.candidate.call_to_action, self.new_candidate["call_to_action"])
        self.assertEqual(self.candidate.primary_tracker_url, self.new_candidate["primary_tracker_url"])
        self.assertEqual(self.candidate.secondary_tracker_url, self.new_candidate["secondary_tracker_url"])
        self.assertEqual(self.candidate.state, self.new_candidate["state"])

        self.other_candidate.refresh_from_db()
        self.assertNotEqual(self.other_candidate.label, self.new_candidate["label"])
        self.assertNotEqual(self.other_candidate.url, self.new_candidate["url"])
        self.assertNotEqual(self.other_candidate.title, self.new_candidate["title"])
        self.assertNotEqual(self.other_candidate.image_url, self.new_candidate["image_url"])
        self.assertNotEqual(self.other_candidate.primary_tracker_url, self.new_candidate["primary_tracker_url"])
        self.assertNotEqual(self.other_candidate.secondary_tracker_url, self.new_candidate["secondary_tracker_url"])

    def test_non_updatable_field(self):
        edit_candidate = models.ContentAdCandidate.objects.get(id=6)
        data = {"id": edit_candidate.id, "title": "new title 123"}

        with self.assertRaises(contentupload.exc.ChangeForbidden):
            contentupload.upload.update_candidate(data, [], edit_candidate.batch)

    def test_partial_update(self):
        data = {"id": self.candidate.id, "title": "new title 123"}

        updated_fields, errors = contentupload.upload.update_candidate(data, [], self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.title, "new title 123")
        self.assertEqual(updated_fields, {"title": "new title 123"})
        self.assertEqual(errors, {})

    def test_invalid_partial_update(self):
        data = {"id": self.candidate.id, "display_url": "new display url 123"}

        updated_fields, errors = contentupload.upload.update_candidate(data, [], self.candidate.batch)

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.display_url, "new display url 123")
        self.assertEqual(updated_fields, {"display_url": "new display url 123"})
        self.assertEqual(errors, {"display_url": ["Enter a valid URL."]})

    @patch("dash.features.contentupload.upload.invoke_external_validation", Mock())
    @patch("dash.image_helper.upload_image_to_s3")
    def test_image_file(self, mock_upload_to_s3):
        mock_upload_to_s3.return_value = "http://example.com/path/to/image"
        files = {
            "image": SimpleUploadedFile(
                name="test.jpg", content=open("./dash/test_files/test.jpg", "rb").read(), content_type="image/jpg"
            )
        }
        updated_fields, errors = contentupload.upload.update_candidate(
            {"id": self.candidate.id}, [], self.candidate.batch, files=files
        )

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.image_url, "http://example.com/path/to/image")
        self.assertEqual(updated_fields, {"image_url": "http://example.com/path/to/image"})
        self.assertEqual(errors, {})

    @patch("dash.features.contentupload.upload.invoke_external_validation", Mock())
    @patch("dash.image_helper.upload_image_to_s3")
    def test_invalid_image_file(self, mock_upload_to_s3):
        mock_upload_to_s3.return_value = "http://example.com/path/to/image"
        files = {
            "image": SimpleUploadedFile(
                name="test.csv", content=open("./dash/test_files/test.csv", "rb").read(), content_type="text/csv"
            )
        }
        updated_fields, errors = contentupload.upload.update_candidate(
            {"id": self.candidate.id}, [], self.candidate.batch, files=files
        )

        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.image_url, None)
        self.assertEqual(updated_fields, {"image_url": None})
        self.assertEqual(errors, {"image": ["Invalid image file"]})

    def test_invalid_candidate_fields(self):
        new_candidate = {
            "id": self.candidate.id,
            "ad_group_id": 55,
            "batch_id": 1234,
            "label": "new label",
            "url": "http://zemanta.com/blog",
            "title": "New title",
            "image_url": "http://zemanta.com/img.jpg",
            "image_crop": "center",
            "display_url": "newurl.com",
            "brand_name": "New brand name",
            "description": "New description",
            "call_to_action": "New cta",
            "primary_tracker_url": "",
            "secondary_tracker_url": "",
        }

        contentupload.upload.update_candidate(new_candidate, self.defaults, self.candidate.batch)
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.ad_group_id, 4)
        self.assertEqual(self.candidate.batch_id, 5)

    @patch("dash.features.contentupload.upload.invoke_external_validation")
    def test_invoke_external_validation(self, mock_invoke):
        contentupload.upload.update_candidate(self.new_candidate, [], self.candidate.batch)
        self.assertFalse(mock_invoke.called)

        new_candidate = {
            "id": self.candidate.id,
            "label": "new label",
            "url": "http://zemanta.com/new-blog",
            "title": "New title",
            "image_url": "http://zemanta.com/new-img.jpg",
            "image_crop": "center",
            "display_url": "newurl.com",
            "brand_name": "New brand name",
            "description": "New description",
            "call_to_action": "New cta",
            "primary_tracker_url": "",
            "secondary_tracker_url": "https://secondaryTrackerUrl.com",
        }

        contentupload.upload.update_candidate(new_candidate, [], self.candidate.batch)
        self.assertTrue(mock_invoke.called)


class GetCandidatesCsvTestCase(TestCase):

    fixtures = ["test_upload.yaml"]

    def setUp(self):
        self.request = magic_mixer.blend_request_user(permissions=["can_use_3rdparty_js_trackers"])

    def test_candidates_csv_unprocessed(self):
        batch = models.UploadBatch.objects.get(id=1)
        content = contentupload.upload.get_candidates_csv(self.request, batch)
        self.assertEqual(
            '"URL","Title","Image URL","Brand Logo URL","Display URL","Brand name","Description","Call to action",'
            '"Label","Image crop","Primary impression tracker URL","Secondary impression tracker URL",'
            '"Tracker 1 Event type","Tracker 1 Method","Tracker 1 URL","Tracker 1 Fallback URL","Tracker 1 Optional",'
            '"Tracker 2 Event type","Tracker 2 Method","Tracker 2 URL","Tracker 2 Fallback URL","Tracker 2 Optional",'
            '"Tracker 3 Event type","Tracker 3 Method","Tracker 3 URL","Tracker 3 Fallback URL","Tracker 3 Optional"\r\n'
            '"http://zemanta.com/blog","Zemanta blog čšž","http://zemanta.com/img.jpg","http://zemanta.com/icon.jpg",'
            '"zemanta.com","Zemanta","Zemanta blog","Read more","content ad 1","entropy","","","","","","","","","","","","","","","","",""\r\n',
            content,
        )

    def test_candidates_csv_unprocessed_display(self):
        batch = models.UploadBatch.objects.get(id=1)
        batch.ad_group.campaign.type = constants.CampaignType.DISPLAY
        batch.ad_group.campaign.save(None)
        content = contentupload.upload.get_candidates_csv(self.request, batch)
        self.assertEqual(
            '"URL","Title","Image URL","Display URL","Brand name","Description","Call to action",'
            '"Label","Image crop","Primary impression tracker URL","Secondary impression tracker URL",'
            '"Creative size","Ad tag",'
            '"Tracker 1 Event type","Tracker 1 Method","Tracker 1 URL","Tracker 1 Fallback URL","Tracker 1 Optional",'
            '"Tracker 2 Event type","Tracker 2 Method","Tracker 2 URL","Tracker 2 Fallback URL","Tracker 2 Optional",'
            '"Tracker 3 Event type","Tracker 3 Method","Tracker 3 URL","Tracker 3 Fallback URL","Tracker 3 Optional"\r\n'
            '"http://zemanta.com/blog","Zemanta blog čšž","http://zemanta.com/img.jpg","zemanta.com","Zemanta","Zemanta blog",'
            '"Read more","content ad 1","entropy","","","","","","","","","","","","","","","","","","",""\r\n',
            content,
        )

    def test_candidates_csv_processed(self):
        batch = models.UploadBatch.objects.get(id=2)
        content = contentupload.upload.get_candidates_csv(self.request, batch)
        self.assertEqual(
            '"URL","Title","Image URL","Brand Logo URL","Display URL","Brand name","Description","Call to action",'
            '"Label","Image crop","Primary impression tracker URL","Secondary impression tracker URL",'
            '"Tracker 1 Event type","Tracker 1 Method","Tracker 1 URL","Tracker 1 Fallback URL","Tracker 1 Optional",'
            '"Tracker 2 Event type","Tracker 2 Method","Tracker 2 URL","Tracker 2 Fallback URL","Tracker 2 Optional",'
            '"Tracker 3 Event type","Tracker 3 Method","Tracker 3 URL","Tracker 3 Fallback URL","Tracker 3 Optional"\r\n'
            '"http://zemanta.com/blog","Zemanta blog čšž","http://zemanta.com/img.jpg","http://zemanta.com/icon.jpg","zemanta.com",'
            '"Zemanta","Zemanta blog","Read more","content ad 1","entropy","https://t.zemanta.com/px1.png","https://t.zemanta.com/px2.png",'
            '"impression","img","https://t.zemanta.com/px1.png","","true","impression","img","https://t.zemanta.com/px2.png","","true","","","","",""\r\n',
            content,
        )

    def test_candidates_csv_processed_display(self):
        batch = models.UploadBatch.objects.get(id=2)
        batch.ad_group.campaign.type = constants.CampaignType.DISPLAY
        batch.ad_group.campaign.save(None)
        content = contentupload.upload.get_candidates_csv(self.request, batch)
        self.assertEqual(
            '"URL","Title","Image URL","Display URL","Brand name","Description","Call to action","Label",'
            '"Image crop","Primary impression tracker URL","Secondary impression tracker URL","Creative size","Ad tag",'
            '"Tracker 1 Event type","Tracker 1 Method","Tracker 1 URL","Tracker 1 Fallback URL","Tracker 1 Optional",'
            '"Tracker 2 Event type","Tracker 2 Method","Tracker 2 URL","Tracker 2 Fallback URL","Tracker 2 Optional",'
            '"Tracker 3 Event type","Tracker 3 Method","Tracker 3 URL","Tracker 3 Fallback URL","Tracker 3 Optional"\r\n'
            '"http://zemanta.com/blog","Zemanta blog čšž","http://zemanta.com/img.jpg","zemanta.com","Zemanta","Zemanta blog",'
            '"Read more","content ad 1","entropy","https://t.zemanta.com/px1.png","https://t.zemanta.com/px2.png","500x500","",'
            '"impression","img","https://t.zemanta.com/px1.png","","true","impression","img","https://t.zemanta.com/px2.png","","true","","","","",""\r\n',
            content,
        )


@patch("utils.lambda_helper.invoke_lambda")
class UploadTest(TestCase):
    fixtures = ["test_api.yaml"]

    @override_settings(
        LAMBDA_CONTENT_UPLOAD_FUNCTION_NAME="content-upload", LAMBDA_CONTENT_UPLOAD_NAMESPACE="name/space"
    )
    def test_lambda_invoke(self, mock_lambda):
        content_ads_data = [
            {
                "url": "http://test.url.com/page1",
                "image_url": "http://test.url.com/image1.png",
                "icon_url": "http://test.url.com/icon1.png",
            },
            {"url": "http://test.url.com/page2", "image_url": "http://test.url.com/image2.png"},
        ]

        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        batch, candidates = contentupload.upload.insert_candidates(
            None, account, content_ads_data, ad_group, "Test batch", "test_upload.csv"
        )

        self.assertEqual(mock_lambda.call_count, 2)

        (lambda_name1, lambda_data1), _ = mock_lambda.call_args_list[0]
        (lambda_name2, lambda_data2), _ = mock_lambda.call_args_list[1]

        self.assertEqual(lambda_name1, "content-upload")
        self.assertEqual(lambda_data1["adGroupID"], 1)
        self.assertEqual(lambda_data1["imageUrls"], ["http://test.url.com/image1.png", "http://test.url.com/icon1.png"])
        self.assertEqual(lambda_data1["pageUrl"], "http://test.url.com/page1")
        self.assertEqual(lambda_data1["namespace"], "name/space")
        self.assertTrue(lambda_data1["candidateID"])

        self.assertEqual(lambda_name2, "content-upload")
        self.assertEqual(lambda_data2["adGroupID"], 1)
        self.assertEqual(lambda_data2["imageUrls"], ["http://test.url.com/image2.png"])
        self.assertEqual(lambda_data2["pageUrl"], "http://test.url.com/page2")
        self.assertEqual(lambda_data2["namespace"], "name/space")
        self.assertTrue(lambda_data2["candidateID"])

    def test_process_callback(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "primary_tracker_url": "https://someImpressionTracker.com",
                    "secondary_tracker_url": None,
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].primary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].secondary_tracker_url_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].trackers_status = {
            "https://someImpressionTracker.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE
        }
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {
                    "http://static1.squarespace.com/image.jpg": {
                        "valid": True,
                        "width": 1500,
                        "file_size": 120000,
                        "hash": "0000000000000000",
                        "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e14",
                        "height": 245,
                    }
                },
                "impressionTrackers": [{"valid": True, "originUrl": "https://someImpressionTracker.com"}],
                "trackers": [
                    {
                        "valid": True,
                        "originUrl": "https://someImpressionTracker.com",
                        "method": constants.TrackerMethod.IMG,
                    }
                ],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.primary_tracker_url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.secondary_tracker_url_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(
            candidate.trackers_status, {"https://someImpressionTracker.com__img": constants.AsyncUploadJobStatus.OK}
        )

    def test_process_callback_candidate_doesnt_exist(self, *mocks):
        with self.assertRaises(contentupload.upload.exc.CandidateDoesNotExist):
            contentupload.upload.process_callback({"id": -1})

    def test_process_callback_icon(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "icon_url": "http://static1.squarespace.com/icon.jpg",
                    "primary_tracker_url": "https://someImpressionTracker.com",
                    "secondary_tracker_url": None,
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].primary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].secondary_tracker_url_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].trackers_status = {
            "https://someImpressionTracker.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE
        }
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {
                    "http://static1.squarespace.com/image.jpg": {
                        "valid": True,
                        "width": 1500,
                        "file_size": 120000,
                        "hash": "0000000000000000",
                        "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e14",
                        "height": 245,
                    },
                    "http://static1.squarespace.com/icon.jpg": {
                        "valid": True,
                        "width": 400,
                        "file_size": 100000,
                        "hash": "111111111111111",
                        "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e15",
                        "height": 800,
                    },
                },
                "impressionTrackers": [{"valid": True, "originUrl": "https://someImpressionTracker.com"}],
                "trackers": [
                    {
                        "valid": True,
                        "originUrl": "https://someImpressionTracker.com",
                        "method": constants.TrackerMethod.IMG,
                    }
                ],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.primary_tracker_url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.secondary_tracker_url_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(
            candidate.trackers_status, {"https://someImpressionTracker.com__img": constants.AsyncUploadJobStatus.OK}
        )

    def test_process_ad_tag_callback(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "type": constants.AdType.AD_TAG,
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "impressionTrackers": [],
                "trackers": [],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)

    def test_process_callback_url_pending_start(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {"originUrl": "", "valid": False},
                "images": {
                    "http://static1.squarespace.com/image.jpg": {
                        "valid": True,
                        "width": 1500,
                        "file_size": 120000,
                        "hash": "0000000000000000",
                        "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e14",
                        "height": 245,
                    }
                },
                "impressionTrackers": [],
                "trackers": [],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)

    def test_process_callback_image_url_pending_start(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )
        self.assertEqual(candidates[0].url_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidates[0].image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidates[0].icon_status, constants.AsyncUploadJobStatus.PENDING_START)

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {},
                "impressionTrackers": [],
                "trackers": [],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)

    def test_process_callback_icon_url_pending_start(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "icon_url": "http://static1.squarespace.com/icon.jpg",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )
        self.assertEqual(candidates[0].url_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidates[0].image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidates[0].icon_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {
                    "http://static1.squarespace.com/image.jpg": {
                        "valid": True,
                        "width": 1500,
                        "file_size": 120000,
                        "hash": "0000000000000000",
                        "id": "demo/demo-123/srv/some-batch/31eb9a632e3547039169d1b650155e14",
                        "height": 245,
                    }
                },
                "impressionTrackers": [],
                "trackers": [],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)

    def test_process_callback_image_url_data_incomplete(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )

        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {"http://static1.squarespace.com/image.jpg": {"valid": True, "width": 300, "hash": "1234"}},
                "impressionTrackers": [],
                "trackers": [],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)

        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.FAILED)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)

    def test_process_callback_trackers_url_not_set(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "impressionTrackers": [],
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )

        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].primary_tracker_url_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].secondary_tracker_url_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {},
                "impressionTrackers": [],
                "trackers": [],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.primary_tracker_url_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.secondary_tracker_url_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.trackers_status, None)

    def test_process_callback_trackers_url_valid(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "primary_tracker_url": "https://primaryTrackerUrl.com",
                    "secondary_tracker_url": "https://secondaryTrackerUrl.com",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )

        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].primary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].secondary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].trackers_status = {
            "https://primaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
            "https://secondaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
        }
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {},
                "impressionTrackers": [
                    {"valid": True, "originUrl": "https://primaryTrackerUrl.com"},
                    {"valid": True, "originUrl": "https://secondaryTrackerUrl.com"},
                ],
                "trackers": [
                    {
                        "valid": True,
                        "originUrl": "https://primaryTrackerUrl.com",
                        "method": constants.TrackerMethod.IMG,
                    },
                    {
                        "valid": True,
                        "originUrl": "https://secondaryTrackerUrl.com",
                        "method": constants.TrackerMethod.IMG,
                    },
                ],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.primary_tracker_url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.secondary_tracker_url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(
            candidate.trackers_status,
            {
                "https://primaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.OK,
                "https://secondaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.OK,
            },
        )

    def test_process_callback_trackers_url_invalid(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "primary_tracker_url": "https://primaryTrackerUrl.com",
                    "secondary_tracker_url": "https://secondaryTrackerUrl.com",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )

        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].primary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].secondary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].trackers_status = {
            "https://primaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
            "https://secondaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
        }
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {},
                "impressionTrackers": [
                    {"valid": False, "originUrl": "https://primaryTrackerUrl.com"},
                    {"valid": False, "originUrl": "https://secondaryTrackerUrl.com"},
                ],
                "trackers": [
                    {
                        "valid": False,
                        "originUrl": "https://primaryTrackerUrl.com",
                        "method": constants.TrackerMethod.IMG,
                    },
                    {
                        "valid": False,
                        "originUrl": "https://secondaryTrackerUrl.com",
                        "method": constants.TrackerMethod.IMG,
                    },
                ],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.primary_tracker_url_status, constants.AsyncUploadJobStatus.FAILED)
        self.assertEqual(candidate.secondary_tracker_url_status, constants.AsyncUploadJobStatus.FAILED)
        self.assertEqual(
            candidate.trackers_status,
            {
                "https://primaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.FAILED,
                "https://secondaryTrackerUrl.com__img": constants.AsyncUploadJobStatus.FAILED,
            },
        )

    def test_process_callback_trackers_url_pending_start(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "primary_tracker_url": "https://primaryImpressionTracker.com",
                    "secondary_tracker_url": "https://secondaryImpressionTracker.com",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )

        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].primary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].secondary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].trackers_status = {
            "https://primaryImpressionTracker.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
            "https://secondaryImpressionTracker.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE,
        }
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {},
                "impressionTrackers": [
                    {"originUrl": "https://primaryImpressionTracker.com", "valid": True},
                    {"originUrl": "https://secondaryImpressionTracker.com", "valid": True},
                ],
                "trackers": [
                    {
                        "originUrl": "https://primaryImpressionTracker.com",
                        "valid": True,
                        "method": constants.TrackerMethod.IMG,
                    },
                    {
                        "originUrl": "https://secondaryImpressionTracker.com",
                        "valid": True,
                        "method": constants.TrackerMethod.IMG,
                    },
                ],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)
        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.primary_tracker_url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.secondary_tracker_url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(
            candidate.trackers_status,
            {
                "https://primaryImpressionTracker.com__img": constants.AsyncUploadJobStatus.OK,
                "https://secondaryImpressionTracker.com__img": constants.AsyncUploadJobStatus.OK,
            },
        )

    def test_process_callback_trackers_url_differs(self, *mocks):
        account = models.Account.objects.get(id=1)
        ad_group = models.AdGroup.objects.get(pk=1)
        _, candidates = contentupload.upload.insert_candidates(
            None,
            account,
            [
                {
                    "url": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "image_url": "http://static1.squarespace.com/image.jpg",
                    "primary_tracker_url": "https://primaryImpressionTracker.com",
                    "secondary_tracker_url": "https://secondaryImpressionTracker.com",
                }
            ],
            ad_group,
            "Test batch",
            "test_upload.csv",
        )

        candidates[0].url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].image_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].icon_status = constants.AsyncUploadJobStatus.PENDING_START
        candidates[0].primary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].secondary_tracker_url_status = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        candidates[0].primary_tracker_url = "https://AnOtherImpressionTrackerUrl.com"
        candidates[0].secondary_tracker_url = None
        candidates[0].trackers_status = {
            "https://AnOtherImpressionTrackerUrl.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE
        }
        candidates[0].save()

        contentupload.upload.process_callback(
            {
                "id": candidates[0].pk,
                "url": {
                    "originUrl": "http://www.zemanta.com/insights/2016/5/23/fighting-the-ad-fraud-one-impression-at-a-time",
                    "valid": True,
                },
                "images": {},
                "impressionTrackers": [
                    {"originUrl": "https://primaryImpressionTracker.com", "valid": True},
                    {"originUrl": "https://secondaryImpressionTracker.com", "valid": True},
                ],
                "trackers": [
                    {
                        "originUrl": "https://primaryImpressionTracker.com",
                        "valid": True,
                        "method": constants.TrackerMethod.IMG,
                    },
                    {
                        "originUrl": "https://secondaryImpressionTracker.com",
                        "valid": True,
                        "method": constants.TrackerMethod.IMG,
                    },
                ],
            }
        )

        candidate = models.ContentAdCandidate.objects.get(pk=candidates[0].pk)

        self.assertEqual(candidate.url_status, constants.AsyncUploadJobStatus.OK)
        self.assertEqual(candidate.image_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.icon_status, constants.AsyncUploadJobStatus.PENDING_START)
        self.assertEqual(candidate.primary_tracker_url_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(candidate.secondary_tracker_url_status, constants.AsyncUploadJobStatus.WAITING_RESPONSE)
        self.assertEqual(
            candidate.trackers_status,
            {"https://AnOtherImpressionTrackerUrl.com__img": constants.AsyncUploadJobStatus.WAITING_RESPONSE},
        )


class AutoSaveTest(TestCase):
    @patch("dash.features.contentupload.upload.persist_batch")
    def test_not_in_progress(self, mock_persist_batch):
        batch = models.UploadBatch(status=constants.UploadBatchStatus.FAILED, auto_save=True)
        contentupload.upload._handle_auto_save(batch)
        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        mock_persist_batch.assert_not_called()

    @patch("dash.features.contentupload.upload.get_clean_candidates_and_errors")
    @patch("dash.features.contentupload.upload.persist_batch")
    def test_batch_should_fail(self, mock_persist_batch, mockget_clean_candidates_and_errors):
        mockget_clean_candidates_and_errors.return_value = (None, {1: {"title": "too long"}})
        batch = models.UploadBatch(status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=True)
        contentupload.upload._handle_auto_save(batch)
        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        mock_persist_batch.assert_not_called()

    @patch("dash.features.contentupload.upload.get_clean_candidates_and_errors")
    @patch("dash.features.contentupload.upload.persist_batch")
    def test_batch_should_succeed(self, mock_persist_batch, mockget_clean_candidates_and_errors):
        mockget_clean_candidates_and_errors.return_value = (None, {})
        batch = models.UploadBatch(status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=True)
        contentupload.upload._handle_auto_save(batch)
        mock_persist_batch.assert_called_with(batch)


class InProgressTest(TestCase):
    def setUp(self):
        self.created_before = datetime.datetime(year=2018, month=1, day=1, minute=30)
        self.time_delta = datetime.timedelta(minutes=10)

    def test_not_in_progress(self):
        batch = magic_mixer.blend(models.UploadBatch, status=constants.UploadBatchStatus.CANCELLED, auto_save=True)

        batch.created_dt = self.created_before - self.time_delta
        batch.save()

        count = contentupload.upload.clean_up_old_in_progress_batches(self.created_before)
        batch.refresh_from_db()
        self.assertEqual(batch.status, constants.UploadBatchStatus.CANCELLED)
        self.assertTrue(batch.auto_save)
        self.assertEqual(count, 0)

    def test_in_progress(self):
        batch = magic_mixer.blend(models.UploadBatch, status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=True)

        batch.created_dt = self.created_before - self.time_delta
        batch.save()

        count = contentupload.upload.clean_up_old_in_progress_batches(self.created_before)
        batch.refresh_from_db()
        self.assertEqual(batch.status, constants.UploadBatchStatus.FAILED)
        self.assertTrue(batch.auto_save)
        self.assertEqual(count, 1)

    def test_auto_save_false(self):
        batch = magic_mixer.blend(models.UploadBatch, status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=False)

        batch.created_dt = self.created_before - self.time_delta
        batch.save()

        count = contentupload.upload.clean_up_old_in_progress_batches(self.created_before)
        batch.refresh_from_db()
        self.assertEqual(batch.status, constants.UploadBatchStatus.IN_PROGRESS)
        self.assertFalse(batch.auto_save)
        self.assertEqual(count, 0)

    def test_new_batches(self):
        batch = magic_mixer.blend(models.UploadBatch, status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=True)

        batch.created_dt = self.created_before + self.time_delta
        batch.save()

        count = contentupload.upload.clean_up_old_in_progress_batches(self.created_before)
        batch.refresh_from_db()
        self.assertEqual(batch.status, constants.UploadBatchStatus.IN_PROGRESS)
        self.assertTrue(batch.auto_save)
        self.assertEqual(count, 0)

    def test_old_count(self):
        for i in range(10):
            batch = magic_mixer.blend(
                models.UploadBatch, status=constants.UploadBatchStatus.IN_PROGRESS, auto_save=True
            )

            batch.created_dt = self.created_before - self.time_delta
            batch.save()

        count = contentupload.upload.clean_up_old_in_progress_batches(self.created_before)
        self.assertEqual(count, 10)
