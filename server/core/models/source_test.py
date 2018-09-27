from django.test import TestCase
from utils.magic_mixer import magic_mixer
from utils import test_helper

from dash import constants

import core.models


class CanManageContentAds(TestCase):
    def test_filter_can(self):
        source = magic_mixer.blend(
            core.models.Source,
            maintenance=False,
            deprecated=False,
            source_type__available_actions=[constants.SourceAction.CAN_MANAGE_CONTENT_ADS],
        )

        self.assertTrue(source.can_manage_content_ads())
        self.assertEqual(
            test_helper.QuerySetMatcher(core.models.Source.objects.all().filter_can_manage_content_ads()), [source]
        )

    def test_filter_cannot(self):
        source = magic_mixer.blend(
            core.models.Source, maintenance=False, deprecated=False, source_type__available_actions=[]
        )

        self.assertFalse(source.can_manage_content_ads())
        self.assertEqual(
            test_helper.QuerySetMatcher(core.models.Source.objects.all().filter_can_manage_content_ads()), []
        )
