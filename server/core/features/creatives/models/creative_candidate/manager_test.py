from django.test import TestCase
from parameterized import param
from parameterized import parameterized

import core.features.creatives
import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import exceptions
from . import model

CREATE_TEST_CASES = [
    param("set_image_crop", field_name="image_crop", field_value="test"),
    param("set_display_url", field_name="display_url", field_value="test"),
    param("set_brand_name", field_name="brand_name", field_value="test"),
    param("set_description", field_name="description", field_value="test"),
    param("set_call_to_action", field_name="call_to_action", field_value="test"),
]

CREATE_FOR_TYPE_TEST_CASES = [
    param(
        "set_native", batch_type=dash.constants.CreativeBatchType.NATIVE, candidate_type=dash.constants.AdType.CONTENT
    ),
    param("set_video", batch_type=dash.constants.CreativeBatchType.VIDEO, candidate_type=dash.constants.AdType.VIDEO),
    param(
        "set_display", batch_type=dash.constants.CreativeBatchType.DISPLAY, candidate_type=dash.constants.AdType.IMAGE
    ),
]


class CreativeCandidateManagerTestCase(TestCase):
    def setUp(self) -> None:
        super(CreativeCandidateManagerTestCase, self).setUp()
        self.agency = magic_mixer.blend(core.models.Agency)

    @parameterized.expand(CREATE_TEST_CASES)
    def test_create(self, _, *, field_name, field_value):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch,
            **{field_name: field_value, "agency": self.agency},
        )
        item = model.CreativeCandidate.objects.create(batch)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.batch, batch)
        self.assertEqual(getattr(item, field_name), field_value)

    @parameterized.expand(CREATE_FOR_TYPE_TEST_CASES)
    def test_create_for_type(self, _, *, batch_type, candidate_type):
        batch = magic_mixer.blend(core.features.creatives.CreativeBatch, type=batch_type, agency=self.agency)
        item = model.CreativeCandidate.objects.create(batch)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.batch, batch)
        self.assertEqual(item.type, candidate_type)

    def test_validate_batch_status(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, status=dash.constants.CreativeBatchStatus.DONE
        )
        with self.assertRaises(exceptions.BatchStatusInvalid):
            model.CreativeCandidate.objects.create(batch)
