from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class CreateContentAd(TestCase):
    def test_create_ad_group_archived(self):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=True)
        with self.assertRaises(exceptions.AdGroupIsArchived):
            core.models.ContentAdCandidate.objects.create(ad_group=ad_group)
