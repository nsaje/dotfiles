# -*- coding: utf-8 -*-
from django.test import TestCase
from mock import patch
from utils.magic_mixer import magic_mixer

import core.entity
import core.source
import utils.exc

from . import service


@patch.object(core.entity.ContentAd.objects, 'insert_redirects', autospec=True)
@patch('automation.autopilot.initialize_budget_autopilot_on_ad_group', autospec=True)
@patch('utils.redirector_helper.insert_adgroup', autospec=True)
@patch('automation.campaign_stop.perform_landing_mode_check', autospec=True)
class Clone(TestCase):

    def test_clone(self, mock_landing, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, 'Something', clone_ads=True)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertTrue(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())
        self.assertEqual(mock_landing.called, 1)

    def test_clone_into_landing(self, mock_landing, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)

        dest_campaign_settings = dest_campaign.get_current_settings().copy_settings()
        dest_campaign_settings.landing_mode = True
        dest_campaign_settings.save()

        request = magic_mixer.blend_request_user()

        with self.assertRaises(utils.exc.ValidationError):
            service.clone(request, ad_group, dest_campaign, 'Something', clone_ads=True)

    def test_clone_unicode(self, mock_landing, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        ad_group.name = 'Non–Gated'
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, 'Something', clone_ads=True)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertTrue(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())
        self.assertEqual(mock_landing.called, 1)

    def test_clone_landing(self, mock_landing, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        ad_group.name = 'Non–Gated'

        request = magic_mixer.blend_request_user()

        ags = ad_group.get_current_settings().copy_settings()
        ags.landing_mode = True
        ags.save(request)

        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, 'Something', clone_ads=False)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertFalse(cloned_ad_group.get_current_settings().landing_mode)
        self.assertEqual(mock_landing.called, 1)

    def test_clone_no_content(self, mock_landing, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=True)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, 'Something', clone_ads=True)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertFalse(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())
        self.assertEqual(mock_landing.called, 1)

    def test_clone_skip_content(self, mock_landing, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        dest_campaign.get_current_settings().copy_settings().save()
        request = magic_mixer.blend_request_user()

        cloned_ad_group = service.clone(request, ad_group, dest_campaign, 'Something', clone_ads=False)

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertFalse(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())
        self.assertEqual(mock_landing.called, 1)
