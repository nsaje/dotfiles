from django.test import TestCase

import core.features.creatives
import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import model


class CreativeCandidateManagerTestCase(TestCase):
    def setUp(self) -> None:
        super(CreativeCandidateManagerTestCase, self).setUp()
        self.agency = magic_mixer.blend(core.models.Agency)
        self.batch = magic_mixer.blend(core.features.creatives.CreativeBatch, agency=self.agency)

    def test_create(self):
        item = model.CreativeCandidate.objects.create(self.batch)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.batch, self.batch)

    def test_create_with_type(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, ad_type=dash.constants.AdType.VIDEO
        )
        item = model.CreativeCandidate.objects.create(batch)
        self.assertIsNotNone(item.id)
        self.assertEqual(item.type, dash.constants.AdType.VIDEO)
