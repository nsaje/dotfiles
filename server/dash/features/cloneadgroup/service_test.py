# -*- coding: utf-8 -*-
from django.test import TestCase
from mock import patch

import core.models
from core.models.account.exceptions import AccountDoesNotMatch
from utils.magic_mixer import magic_mixer

from . import service


@patch.object(core.models.ContentAd.objects, "insert_redirects", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
class Clone(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)

        self.dest_campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.dest_campaign.get_current_settings().copy_settings().save()
        self.request = magic_mixer.blend_request_user()

    def test_clone(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        icon = magic_mixer.blend(core.models.ImageAsset, width=200, height=200)
        magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.ad_group, archived=False, icon=icon)

        cloned_ad_group = service.clone(self.request, self.ad_group, self.dest_campaign, "Something", clone_ads=True)

        self.assertNotEqual(self.ad_group, cloned_ad_group)
        cloned_ads = core.models.ContentAd.objects.filter(ad_group=cloned_ad_group)
        self.assertTrue(cloned_ads.exists())
        self.assertEqual(icon, cloned_ads[0].icon)

    def test_clone_unicode(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        self.ad_group.name = "Non–Gated"
        icon = magic_mixer.blend(core.models.ImageAsset, width=200, height=200)
        magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.ad_group, archived=False, icon=icon)

        cloned_ad_group = service.clone(self.request, self.ad_group, self.dest_campaign, "Something", clone_ads=True)

        self.assertNotEqual(self.ad_group, cloned_ad_group)
        self.assertTrue(core.models.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())

    def test_clone_no_content(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.ad_group, archived=True)

        cloned_ad_group = service.clone(self.request, self.ad_group, self.dest_campaign, "Something", clone_ads=True)

        self.assertNotEqual(self.ad_group, cloned_ad_group)
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())

    def test_clone_skip_content(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.ad_group, archived=False)

        cloned_ad_group = service.clone(self.request, self.ad_group, self.dest_campaign, "Something", clone_ads=False)

        self.assertNotEqual(self.ad_group, cloned_ad_group)
        self.assertFalse(core.models.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())

    def test_validate_other_account(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.ad_group, archived=False)

        other_account = magic_mixer.blend(core.models.Account)
        other_campaign = magic_mixer.blend(core.models.Campaign, account=other_account)
        other_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=other_campaign)

        try:
            service.clone(self.request, other_ad_group, self.campaign, "Something", clone_ads=True)
        except AccountDoesNotMatch as exc:
            self.assertEqual(exc.errors, {"account": "Can not clone into a different account"})
