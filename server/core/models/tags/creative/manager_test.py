from django.test import TestCase

import core.models
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer

from . import model


class CreativeTagManagerTestCase(TestCase):
    def setUp(self):
        super(CreativeTagManagerTestCase, self).setUp()
        self.agency = magic_mixer.blend(core.models.Agency)
        self.account = magic_mixer.blend(core.models.Account)

    def test_create_for_agency(self):
        name = "test_tag"
        tag = model.CreativeTag.objects.create(name, agency=self.agency)
        self.assertEqual(tag.name, name)
        self.assertEqual(tag.agency.id, self.agency.id)
        self.assertIsNone(tag.account)

    def test_create_for_account(self):
        name = "test_tag"
        tag = model.CreativeTag.objects.create(name, account=self.account)
        self.assertEqual(tag.name, name)
        self.assertEqual(tag.account.id, self.account.id)
        self.assertIsNone(tag.agency)

    def test_create_with_agency_and_account(self):
        name = "test_tag"
        with self.assertRaises(ValidationError):
            model.CreativeTag.objects.create(name, agency=self.agency, account=self.account)

    def test_create_without_agency_and_account(self):
        name = "test_tag"
        with self.assertRaises(ValidationError):
            model.CreativeTag.objects.create(name, agency=None, account=None)

    def test_get_or_create(self):
        name = "test_tag"
        tag_one = model.CreativeTag.objects.create(name, agency=self.agency)
        tag_two = model.CreativeTag.objects.create(name, agency=self.agency)
        self.assertEqual(tag_one.id, tag_two.id)

    def test_tag_uniqueness(self):
        name = "test_tag"
        tag_one = model.CreativeTag.objects.create(name, agency=self.agency)
        tag_two = model.CreativeTag.objects.create(name, account=self.account)
        self.assertNotEqual(tag_one.id, tag_two.id)
        self.assertEqual(tag_one.name, tag_two.name)
