from django.test import TestCase

import core
from utils.magic_mixer import magic_mixer

from . import model


class ContentAdQuerysetTest(TestCase):
    def test_archived_parent_ad_group(self):
        adgroup_archived = magic_mixer.blend(core.models.AdGroup, archived=True)
        magic_mixer.blend(core.models.ContentAd, archived=False, ad_group=adgroup_archived)
        magic_mixer.blend(core.models.ContentAd, archived=True, ad_group=adgroup_archived)

        groups = model.ContentAd.objects.exclude_archived(show_archived=False)
        self.assertEqual(len(groups), 0)

        groups = model.ContentAd.objects.exclude_archived(show_archived=True)
        self.assertEqual(len(groups), 2)
