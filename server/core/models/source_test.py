from django.test import TestCase

import core.models
from dash import constants
from utils import test_helper
from utils.magic_mixer import magic_mixer


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
