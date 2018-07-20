# -*- coding: utf-8 -*-
from django.test import TestCase
from mock import patch
from utils.magic_mixer import magic_mixer

import core.entity
import core.source

from . import service


@patch.object(core.entity.ContentAd.objects, "insert_redirects", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
class Clone(TestCase):
    def test_clone(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, "Something", clone_ads=True)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertTrue(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())

    def test_clone_unicode(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        ad_group.name = "Non–Gated"
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, "Something", clone_ads=True)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertTrue(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())

    def test_clone_no_content(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=True)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, "Something", clone_ads=True)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertFalse(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())

    def test_clone_skip_content(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, "Something", clone_ads=False)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertFalse(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())
