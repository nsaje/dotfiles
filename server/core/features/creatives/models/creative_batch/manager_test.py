from django.test import TestCase

import core.models
import dash.constants
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer

from . import model


class CreativeBatchManagerTestCase(TestCase):
    def setUp(self) -> None:
        super(CreativeBatchManagerTestCase, self).setUp()
        self.request = magic_mixer.blend_request_user()
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account)

    def test_create_with_request(self):
        item = model.CreativeBatch.objects.create(self.request, "test", agency=self.agency)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.created_by, self.request.user)

    def test_create_for_agency(self):
        item = model.CreativeBatch.objects.create(None, "test", agency=self.agency)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.agency, self.agency)
        self.assertIsNone(item.account)

    def test_create_for_account(self):
        item = model.CreativeBatch.objects.create(None, "test", account=self.account)
        self.assertIsNotNone(item.id)
        self.assertIsNone(item.agency)
        self.assertEqual(item.account, self.account)

    def test_create_with_mode(self):
        item = model.CreativeBatch.objects.create(
            None, "test", agency=self.agency, mode=dash.constants.CreativeBatchMode.EDIT
        )
        self.assertIsNotNone(item.id)
        self.assertEqual(item.mode, dash.constants.CreativeBatchMode.EDIT)

    def test_create_with_type(self):
        item = model.CreativeBatch.objects.create(
            None, "test", agency=self.agency, type=dash.constants.CreativeBatchType.VIDEO
        )
        self.assertIsNotNone(item.id)
        self.assertEqual(item.type, dash.constants.CreativeBatchType.VIDEO)

    def test_validate_agency_account(self):
        with self.assertRaises(ValidationError):
            model.CreativeBatch.objects.create(None, "test")
        with self.assertRaises(ValidationError):
            model.CreativeBatch.objects.create(None, "test", agency=self.agency, account=self.account)
