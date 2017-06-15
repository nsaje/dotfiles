from django.test import TestCase
from mock import patch
from utils.magic_mixer import magic_mixer

from dash.features import cloneadgroup
import core.entity
import core.source


@patch.object(core.entity.ContentAd.objects, 'insert_redirects')
@patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group')
class Clone(TestCase):

    def test_clone(self, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        request = magic_mixer.blend_request_user()

        cloned_ad_group = cloneadgroup.service.clone(request, ad_group, dest_campaign, 'Something')

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertTrue(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())

    def test_clone_no_content(self, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=True)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)
        request = magic_mixer.blend_request_user()

        cloned_ad_group = cloneadgroup.service.clone(request, ad_group, dest_campaign, 'Something')

        self.assertNotEqual(ad_group, cloned_ad_group)
        self.assertFalse(core.entity.ContentAd.objects.filter(ad_group=cloned_ad_group).exists())
