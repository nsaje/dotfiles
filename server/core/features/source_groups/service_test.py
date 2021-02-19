import mock
from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import service


class SourceGroupsServiceTest(TestCase):
    @mock.patch("django.conf.settings.SOURCE_GROUPS", {1: [3, 4], 2: [5, 6]})
    def test_source_id_slug_mapping(self):
        magic_mixer.cycle(7).blend(
            core.models.Source,
            id=(sid for sid in range(1, 8)),
            bidder_slug=("slug" + str(i) for i in range(1, 8)),
            tracking_slug=("track" + str(i) for i in range(1, 8)),
        )

        mapping = service.get_source_id_slugs_mapping()

        for i in range(3, 7):
            data = mapping[i]
            self.assertEqual(i, data["id"])
            self.assertEqual("slug" + str(i), data["bidder_slug"])
            self.assertEqual("track" + str(i), data["tracking_slug"])

    @mock.patch("django.conf.settings.SOURCE_GROUPS", {1: [3, 4], 2: [5, 6]})
    def test_source_slug_group_slug_mapping(self):
        magic_mixer.cycle(7).blend(
            core.models.Source, id=(sid for sid in range(1, 8)), bidder_slug=("slug" + str(i) for i in range(1, 8))
        )

        mapping = service.get_source_slug_group_slug_mapping()

        self.assertCountEqual({"slug3": "slug1", "slug4": "slug1", "slug5": "slug2", "slug6": "slug2"}, mapping)
