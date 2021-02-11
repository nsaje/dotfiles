from django.test import TestCase
from parameterized import param
from parameterized import parameterized

import core.features.creatives.models
import core.features.videoassets.models
import core.models
import core.models.tags.creative.shortcuts
import dash.constants
from utils.magic_mixer import magic_mixer

from . import exceptions
from . import model

TEST_CASES = [
    param("set_url", field_name="url", field_value="before", field_new_value="after"),
    param("set_title", field_name="title", field_value="before", field_new_value="after"),
    param("set_display_url", field_name="display_url", field_value="before", field_new_value="after"),
    param("set_brand_name", field_name="brand_name", field_value="before", field_new_value="after"),
    param("set_description", field_name="description", field_value="before", field_new_value="after"),
    param("set_call_to_action", field_name="call_to_action", field_value="before", field_new_value="after"),
    param("set_image_url", field_name="image_url", field_value="before", field_new_value="after"),
    param("set_image_crop", field_name="image_crop", field_value="before", field_new_value="after"),
    param("set_icon_url", field_name="image_url", field_value="before", field_new_value="after"),
    param("set_ad_tag", field_name="ad_tag", field_value="before", field_new_value="after"),
    param("set_trackers", field_name="trackers", field_value={"value": "before"}, field_new_value={"value": "after"}),
    param(
        "set_trackers_status",
        field_name="trackers_status",
        field_value={"value": "before"},
        field_new_value={"value": "after"},
    ),
    param(
        "set_image_status",
        field_name="image_status",
        field_value=dash.constants.AsyncUploadJobStatus.WAITING_RESPONSE,
        field_new_value=dash.constants.AsyncUploadJobStatus.OK,
    ),
    param(
        "set_icon_status",
        field_name="icon_status",
        field_value=dash.constants.AsyncUploadJobStatus.WAITING_RESPONSE,
        field_new_value=dash.constants.AsyncUploadJobStatus.OK,
    ),
    param(
        "set_url_status",
        field_name="url_status",
        field_value=dash.constants.AsyncUploadJobStatus.WAITING_RESPONSE,
        field_new_value=dash.constants.AsyncUploadJobStatus.OK,
    ),
    param("set_image_id", field_name="image_id", field_value="before", field_new_value="after"),
    param("set_image_width", field_name="image_width", field_value=128, field_new_value=256),
    param("set_image_height", field_name="image_height", field_value=128, field_new_value=256),
    param("set_image_hash", field_name="image_hash", field_value="before", field_new_value="after"),
    param("set_image_file_size", field_name="image_file_size", field_value=128, field_new_value=256),
    param("set_icon_id", field_name="icon_id", field_value="before", field_new_value="after"),
    param("set_icon_width", field_name="icon_width", field_value=128, field_new_value=256),
    param("set_icon_height", field_name="icon_height", field_value=128, field_new_value=256),
    param("set_icon_hash", field_name="icon_hash", field_value="before", field_new_value="after"),
    param("set_icon_file_size", field_name="icon_file_size", field_value=128, field_new_value=256),
    param(
        "set_additional_data",
        field_name="additional_data",
        field_value={"value": "before"},
        field_new_value={"value": "after"},
    ),
]


class CreativeCandidateInstanceTestCase(core.models.tags.creative.shortcuts.CreativeTagTestCaseMixin, TestCase):
    def setUp(self) -> None:
        super(CreativeCandidateInstanceTestCase, self).setUp()
        self.agency = magic_mixer.blend(core.models.Agency)
        self.batch = magic_mixer.blend(core.features.creatives.models.CreativeBatch, agency=self.agency)

    @parameterized.expand(TEST_CASES)
    def test_update(self, _, *, field_name, field_value, field_new_value):
        item = magic_mixer.blend(model.CreativeCandidate, **{field_name: field_value, "batch": self.batch})
        self.assertEqual(getattr(item, field_name), field_value)

        item.update(None, **{field_name: field_new_value})
        item.refresh_from_db()

        self.assertEqual(getattr(item, field_name), field_new_value)

    def test_update_type(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.DISPLAY
        )
        item = magic_mixer.blend(
            core.features.creatives.CreativeCandidate, batch=batch, type=dash.constants.AdType.IMAGE
        )
        self.assertEqual(item.type, dash.constants.AdType.IMAGE)

        item.update(None, type=dash.constants.AdType.AD_TAG)
        item.refresh_from_db()

        self.assertEqual(item.type, dash.constants.AdType.AD_TAG)

    def test_validate_type(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.VIDEO
        )
        item = magic_mixer.blend(
            core.features.creatives.CreativeCandidate, batch=batch, type=dash.constants.AdType.VIDEO
        )
        self.assertEqual(item.type, dash.constants.AdType.VIDEO)

        with self.assertRaises(exceptions.AdTypeInvalid):
            item.update(None, type=dash.constants.AdType.AD_TAG)

    def _get_model_with_agency_scope(self, agency: core.models.Agency):
        batch = magic_mixer.blend(core.features.creatives.models.CreativeBatch, agency=agency, account=None)
        return magic_mixer.blend(model.CreativeCandidate, batch=batch)

    def _get_model_with_account_scope(self, account: core.models.Account):
        batch = magic_mixer.blend(core.features.creatives.models.CreativeBatch, agency=None, account=account)
        return magic_mixer.blend(model.CreativeCandidate, batch=batch)
