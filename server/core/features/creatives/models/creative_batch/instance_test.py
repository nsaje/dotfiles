from django.test import TestCase
from parameterized import param
from parameterized import parameterized

import core.features.creatives.models
import core.models
import core.models.tags.creative.shortcuts
import dash.constants
from utils.magic_mixer import magic_mixer

from . import exceptions
from . import model

TEST_CASES = [
    param("set_name", field_name="name", field_value="before", field_new_value="after"),
    param("set_original_filename", field_name="original_filename", field_value="before", field_new_value="after"),
    param("set_image_crop", field_name="image_crop", field_value="before", field_new_value="after"),
    param("set_display_url", field_name="display_url", field_value="before", field_new_value="after"),
    param("set_brand_name", field_name="brand_name", field_value="before", field_new_value="after"),
    param("set_description", field_name="description", field_value="before", field_new_value="after"),
    param("set_call_to_action", field_name="call_to_action", field_value="before", field_new_value="after"),
]


class CreativeBatchInstanceTestCase(core.models.tags.creative.shortcuts.CreativeTagTestCaseMixin, TestCase):
    def setUp(self) -> None:
        super(CreativeBatchInstanceTestCase, self).setUp()
        self.agency = magic_mixer.blend(core.models.Agency)

    @parameterized.expand(TEST_CASES)
    def test_update(self, _, *, field_name, field_value, field_new_value):
        item = magic_mixer.blend(model.CreativeBatch, **{field_name: field_value, "agency": self.agency})
        self.assertEqual(getattr(item, field_name), field_value)

        item.update(None, **{field_name: field_new_value})
        item.refresh_from_db()

        self.assertEqual(getattr(item, field_name), field_new_value)

    def test_delete(self):
        batch = magic_mixer.blend(model.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.VIDEO)
        with self.assertRaises(AssertionError):
            batch.delete()

    def test_mark_done(self):
        batch = magic_mixer.blend(
            model.CreativeBatch, agency=self.agency, status=dash.constants.CreativeBatchStatus.IN_PROGRESS
        )
        self.assertEqual(batch.status, dash.constants.CreativeBatchStatus.IN_PROGRESS)

        batch.mark_done(None)
        self.assertEqual(batch.status, dash.constants.CreativeBatchStatus.DONE)

    def test_mark_done_with_error(self):
        batch = magic_mixer.blend(
            model.CreativeBatch, agency=self.agency, status=dash.constants.CreativeBatchStatus.DONE
        )
        self.assertEqual(batch.status, dash.constants.CreativeBatchStatus.DONE)

        with self.assertRaises(exceptions.BatchStatusInvalid):
            batch.mark_done(None)

    def test_mark_failed(self):
        batch = magic_mixer.blend(
            model.CreativeBatch, agency=self.agency, status=dash.constants.CreativeBatchStatus.IN_PROGRESS
        )
        self.assertEqual(batch.status, dash.constants.CreativeBatchStatus.IN_PROGRESS)

        batch.mark_failed(None)
        self.assertEqual(batch.status, dash.constants.CreativeBatchStatus.FAILED)

    def test_mark_failed_with_error(self):
        batch = magic_mixer.blend(
            model.CreativeBatch, agency=self.agency, status=dash.constants.CreativeBatchStatus.DONE
        )
        self.assertEqual(batch.status, dash.constants.CreativeBatchStatus.DONE)

        with self.assertRaises(exceptions.BatchStatusInvalid):
            batch.mark_failed(None)

    def _get_model_with_agency_scope(self, agency: core.models.Agency):
        return magic_mixer.blend(model.CreativeBatch, name="test_agency_batch", agency=agency)

    def _get_model_with_account_scope(self, account: core.models.Account):
        return magic_mixer.blend(model.CreativeBatch, name="test_account_batch", account=account)
