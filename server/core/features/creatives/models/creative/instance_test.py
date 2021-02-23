from django.test import TestCase
from parameterized import param
from parameterized import parameterized

import core.features.creatives.models
import core.features.videoassets.models
import core.models
import core.models.tags.creative.shortcuts
from utils.magic_mixer import magic_mixer

from . import model

UPDATE_TEST_CASES = [
    param("set_url", field_name="url", field_value="before", field_new_value="after"),
    param("set_title", field_name="title", field_value="before", field_new_value="after"),
    param("set_display_url", field_name="display_url", field_value="before", field_new_value="after"),
    param("set_brand_name", field_name="brand_name", field_value="before", field_new_value="after"),
    param("set_description", field_name="description", field_value="before", field_new_value="after"),
    param("set_call_to_action", field_name="call_to_action", field_value="before", field_new_value="after"),
    param("set_image_crop", field_name="image_crop", field_value="before", field_new_value="after"),
    param("set_image_width", field_name="image_width", field_value=128, field_new_value=256),
    param("set_image_height", field_name="image_height", field_value=128, field_new_value=256),
    param("set_ad_tag", field_name="ad_tag", field_value="before", field_new_value="after"),
    param("set_trackers", field_name="trackers", field_value={"value": "before"}, field_new_value={"value": "after"}),
    param(
        "set_additional_data",
        field_name="additional_data",
        field_value={"value": "before"},
        field_new_value={"value": "after"},
    ),
]

UPDATE_IMAGE_ASSET_TEST_CASES = [
    param("set_image", field_name="image"),
    param("set_icon", field_name="icon"),
]


class CreativeInstanceTestCase(core.models.tags.creative.shortcuts.CreativeTagTestCaseMixin, TestCase):
    def setUp(self) -> None:
        super(CreativeInstanceTestCase, self).setUp()
        self.agency = magic_mixer.blend(core.models.Agency)

    @parameterized.expand(UPDATE_TEST_CASES)
    def test_update(self, _, *, field_name, field_value, field_new_value):
        item = magic_mixer.blend(model.Creative, **{field_name: field_value, "agency": self.agency})
        self.assertEqual(getattr(item, field_name), field_value)

        item.update(None, **{field_name: field_new_value})
        item.refresh_from_db()

        self.assertEqual(getattr(item, field_name), field_new_value)

    @parameterized.expand(UPDATE_IMAGE_ASSET_TEST_CASES)
    def test_update_image_asset(self, _, *, field_name):
        item = magic_mixer.blend(model.Creative, agency=self.agency)
        item.update(None, **{field_name: None})
        item.refresh_from_db()
        self.assertIsNone(getattr(item, field_name))

        asset = magic_mixer.blend(core.models.ImageAsset)
        item.update(None, **{field_name: asset})
        item.refresh_from_db()
        self.assertEqual(getattr(item, field_name), asset)

    def test_update_video_asset(self):
        item = magic_mixer.blend(model.Creative, agency=self.agency)
        item.update(None, video_asset=None)
        item.refresh_from_db()
        self.assertIsNone(item.video_asset)

        video_asset = magic_mixer.blend(core.features.videoassets.models.VideoAsset)
        item.update(None, video_asset=video_asset)
        item.refresh_from_db()
        self.assertEqual(item.video_asset, video_asset)

    def _get_model_with_agency_scope(self, agency: core.models.Agency):
        return magic_mixer.blend(model.Creative, agency=agency)

    def _get_model_with_account_scope(self, account: core.models.Account):
        return magic_mixer.blend(model.Creative, account=account)
