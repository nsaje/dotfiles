from django.forms.models import model_to_dict
from django.test import TestCase

import core.features.creatives
import core.features.videoassets.models
import core.models
import dash.constants
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer

from . import model


class CreativeManagerTestCase(TestCase):
    def setUp(self) -> None:
        super(CreativeManagerTestCase, self).setUp()
        self.request = magic_mixer.blend_request_user()
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account)

    def test_create_with_request(self):
        item = model.Creative.objects.create(self.request, agency=self.agency)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.created_by, self.request.user)

    def test_create_for_agency(self):
        item = model.Creative.objects.create(None, agency=self.agency)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.agency, self.agency)
        self.assertIsNone(item.account)

    def test_create_for_account(self):
        item = model.Creative.objects.create(None, account=self.account)
        self.assertIsNotNone(item.id)
        self.assertIsNone(item.agency)
        self.assertEqual(item.account, self.account)

    def test_create_with_type(self):
        item = model.Creative.objects.create(None, agency=self.agency, type=dash.constants.AdType.VIDEO)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.type, dash.constants.AdType.VIDEO)

    def test_validate_agency_account(self):
        with self.assertRaises(ValidationError):
            model.Creative.objects.create(None)
        with self.assertRaises(ValidationError):
            model.Creative.objects.create(None, agency=self.agency, account=self.account)

    def test_bulk_create_from_candidates_native(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.NATIVE
        )
        batch.set_creative_tags(None, ["tag_one"])

        self.assertEqual(model.Creative.objects.filter(batch=batch).count(), 0)

        candidate = self._get_native_representation(tags=["tag_two", "tag_three"])
        model.Creative.objects.bulk_create_from_candidates(None, batch, [candidate])

        creatives = list(model.Creative.objects.filter(batch=batch).all())
        self.assertEqual(len(creatives), 1)

        creative = creatives[0]
        self.assertEqual(creative.batch, batch)
        self.assertEqual(creative.agency, batch.agency)
        self.assertEqual(creative.account, batch.account)

        self.assertIsNotNone(creative.image)
        self.assertIsNotNone(creative.icon)
        self.assertIsNone(creative.video_asset)
        self.assertIsNone(creative.ad_tag)

        tags = creative.get_creative_tags()
        self.assertEqual(len(tags), 3)
        self.assertCountEqual(["tag_one", "tag_two", "tag_three"], [tag.name for tag in tags])

        creative_dict = model_to_dict(
            creative, exclude=["batch", "agency", "account", "image", "icon", "video_asset", "ad_tag", "tags"]
        )
        for key, value in creative_dict.items():
            if key in candidate.keys():
                self.assertEqual(value, candidate.get(key))

    def test_bulk_create_from_candidates_video(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.VIDEO
        )
        batch.set_creative_tags(None, ["tag_one"])

        video_asset = magic_mixer.blend(core.features.videoassets.models.VideoAsset)

        self.assertEqual(model.Creative.objects.filter(batch=batch).count(), 0)

        candidate = self._get_video_representation(video_asset=video_asset, tags=["tag_two", "tag_three"])
        model.Creative.objects.bulk_create_from_candidates(None, batch, [candidate])

        creatives = list(model.Creative.objects.filter(batch=batch).all())
        self.assertEqual(len(creatives), 1)

        creative = creatives[0]
        self.assertEqual(creative.batch, batch)
        self.assertEqual(creative.agency, batch.agency)
        self.assertEqual(creative.account, batch.account)

        self.assertIsNotNone(creative.image)
        self.assertIsNotNone(creative.icon)
        self.assertEqual(creative.video_asset, video_asset)
        self.assertIsNone(creative.ad_tag)

        tags = creative.get_creative_tags()
        self.assertEqual(len(tags), 3)
        self.assertCountEqual(["tag_one", "tag_two", "tag_three"], [tag.name for tag in tags])

        creative_dict = model_to_dict(
            creative, exclude=["batch", "agency", "account", "image", "icon", "video_asset", "ad_tag", "tags"]
        )
        for key, value in creative_dict.items():
            if key in candidate.keys():
                self.assertEqual(value, candidate.get(key))

    def test_bulk_create_from_candidates_image(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.DISPLAY
        )
        batch.set_creative_tags(None, ["tag_one"])

        self.assertEqual(model.Creative.objects.filter(batch=batch).count(), 0)

        candidate = self._get_image_representation(tags=["tag_two", "tag_three"])
        model.Creative.objects.bulk_create_from_candidates(None, batch, [candidate])

        creatives = list(model.Creative.objects.filter(batch=batch).all())
        self.assertEqual(len(creatives), 1)

        creative = creatives[0]
        self.assertEqual(creative.batch, batch)
        self.assertEqual(creative.agency, batch.agency)
        self.assertEqual(creative.account, batch.account)

        self.assertIsNotNone(creative.image)
        self.assertIsNone(creative.icon)
        self.assertIsNone(creative.video_asset)
        self.assertIsNone(creative.ad_tag)

        tags = creative.get_creative_tags()
        self.assertEqual(len(tags), 3)
        self.assertCountEqual(["tag_one", "tag_two", "tag_three"], [tag.name for tag in tags])

        creative_dict = model_to_dict(
            creative, exclude=["batch", "agency", "account", "image", "icon", "video_asset", "ad_tag", "tags"]
        )
        for key, value in creative_dict.items():
            if key in candidate.keys():
                self.assertEqual(value, candidate.get(key))

    def test_bulk_create_from_candidates_ad_tag(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.DISPLAY
        )
        batch.set_creative_tags(None, ["tag_one"])

        self.assertEqual(model.Creative.objects.filter(batch=batch).count(), 0)

        candidate = self._get_ad_tag_representation(tags=["tag_two", "tag_three"])
        model.Creative.objects.bulk_create_from_candidates(None, batch, [candidate])

        creatives = list(model.Creative.objects.filter(batch=batch).all())
        self.assertEqual(len(creatives), 1)

        creative = creatives[0]
        self.assertEqual(creative.batch, batch)
        self.assertEqual(creative.agency, batch.agency)
        self.assertEqual(creative.account, batch.account)

        self.assertIsNone(creative.image)
        self.assertIsNone(creative.icon)
        self.assertIsNone(creative.video_asset)
        self.assertIsNotNone(creative.ad_tag)

        tags = creative.get_creative_tags()
        self.assertEqual(len(tags), 3)
        self.assertCountEqual(["tag_one", "tag_two", "tag_three"], [tag.name for tag in tags])

        creative_dict = model_to_dict(
            creative, exclude=["batch", "agency", "account", "image", "icon", "video_asset", "ad_tag", "tags"]
        )
        for key, value in creative_dict.items():
            if key in candidate.keys():
                self.assertEqual(value, candidate.get(key))

    def _get_candidate_representation(
        self,
        *,
        type=None,
        url=None,
        title=None,
        display_url=None,
        brand_name=None,
        description=None,
        call_to_action=None,
        image_crop=None,
        image_id=None,
        image_width=None,
        image_height=None,
        image_hash=None,
        image_file_size=None,
        image_url=None,
        icon_id=None,
        icon_width=None,
        icon_height=None,
        icon_hash=None,
        icon_file_size=None,
        icon_url=None,
        video_asset=None,
        ad_tag=None,
        trackers=None,
        tags=None,
        additional_data=None,
    ):
        candidate = {
            "type": type,
            "url": url,
            "title": title,
            "display_url": display_url,
            "brand_name": brand_name,
            "description": description,
            "call_to_action": call_to_action,
            "image_crop": image_crop,
            "image_id": image_id,
            "image_width": image_width,
            "image_height": image_height,
            "image_hash": image_hash,
            "image_file_size": image_file_size,
            "image_url": image_url,
            "icon_id": icon_id,
            "icon_width": icon_width,
            "icon_height": icon_height,
            "icon_hash": icon_hash,
            "icon_file_size": icon_file_size,
            "icon_url": icon_url,
            "video_asset": video_asset,
            "ad_tag": ad_tag,
            "trackers": trackers,
            "tags": tags,
            "additional_data": additional_data,
        }
        return {k: v for k, v in candidate.items() if v is not None}

    def _get_native_representation(
        self,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        brand_name="My brand",
        description="My description",
        call_to_action="Read more...",
        image_crop="center",
        image_id="123456",
        image_width=350,
        image_height=350,
        image_hash="123456",
        image_file_size=256,
        image_url="http://example.com/path/to/image",
        icon_id="7891011",
        icon_width=200,
        icon_height=200,
        icon_hash="7891011",
        icon_file_size=128,
        icon_url="http://example.com/path/to/icon",
        trackers=None,
        tags=None,
        additional_data=None,
    ):
        return self._get_candidate_representation(
            type=dash.constants.AdType.CONTENT,
            url=url,
            title=title,
            display_url=display_url,
            brand_name=brand_name,
            description=description,
            call_to_action=call_to_action,
            image_crop=image_crop,
            image_id=image_id,
            image_width=image_width,
            image_height=image_height,
            image_hash=image_hash,
            image_file_size=image_file_size,
            image_url=image_url,
            icon_id=icon_id,
            icon_width=icon_width,
            icon_height=icon_height,
            icon_hash=icon_hash,
            icon_file_size=icon_file_size,
            icon_url=icon_url,
            trackers=trackers,
            tags=tags,
            additional_data=additional_data,
        )

    def _get_video_representation(
        self,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        brand_name="My brand",
        description="My description",
        call_to_action="Read more...",
        image_crop="center",
        image_id="123456",
        image_width=350,
        image_height=350,
        image_hash="123456",
        image_file_size=256,
        image_url="http://example.com/path/to/image",
        icon_id="7891011",
        icon_width=200,
        icon_height=200,
        icon_hash="7891011",
        icon_file_size=128,
        icon_url="http://example.com/path/to/icon",
        video_asset=None,
        trackers=None,
        tags=None,
        additional_data=None,
    ):
        return self._get_candidate_representation(
            type=dash.constants.AdType.VIDEO,
            url=url,
            title=title,
            display_url=display_url,
            brand_name=brand_name,
            description=description,
            call_to_action=call_to_action,
            image_crop=image_crop,
            image_id=image_id,
            image_width=image_width,
            image_height=image_height,
            image_hash=image_hash,
            image_file_size=image_file_size,
            image_url=image_url,
            icon_id=icon_id,
            icon_width=icon_width,
            icon_height=icon_height,
            icon_hash=icon_hash,
            icon_file_size=icon_file_size,
            icon_url=icon_url,
            video_asset=video_asset,
            trackers=trackers,
            tags=tags,
            additional_data=additional_data,
        )

    def _get_image_representation(
        self,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        image_id="123456",
        image_width=350,
        image_height=350,
        image_hash="123456",
        image_file_size=256,
        image_url="http://example.com/path/to/image",
        trackers=None,
        tags=None,
        additional_data=None,
    ):
        return self._get_candidate_representation(
            type=dash.constants.AdType.IMAGE,
            url=url,
            title=title,
            display_url=display_url,
            image_id=image_id,
            image_width=image_width,
            image_height=image_height,
            image_hash=image_hash,
            image_file_size=image_file_size,
            image_url=image_url,
            trackers=trackers,
            tags=tags,
            additional_data=additional_data,
        )

    def _get_ad_tag_representation(
        self,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        ad_tag="Test ad tag",
        trackers=None,
        tags=None,
        additional_data=None,
    ):
        return self._get_candidate_representation(
            type=dash.constants.AdType.AD_TAG,
            url=url,
            title=title,
            display_url=display_url,
            ad_tag=ad_tag,
            trackers=trackers,
            tags=tags,
            additional_data=additional_data,
        )
