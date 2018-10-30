from django.test import TestCase
from mock import patch

import core.models
from utils.magic_mixer import magic_mixer

from . import serializers


@patch.object(core.models.ContentAd.objects, "insert_redirects", autospec=True)
@patch("automation.autopilot.recalculate_budgets_ad_group", autospec=True)
@patch("utils.redirector_helper.insert_adgroup", autospec=True)
class CloneForm(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.content_ads = magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.ad_group, archived=False)
        self.dest_campaign = magic_mixer.blend(core.models.Campaign, account=self.account)

    def test_clone_valid(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        form = serializers.CloneAdGroupSerializer(
            data={
                "ad_group_id": self.ad_group.pk,
                "destination_campaign_id": self.dest_campaign.pk,
                "destination_ad_group_name": "Test",
            }
        )
        self.assertTrue(form.is_valid())

    def test_name_too_long(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        form = serializers.CloneAdGroupSerializer(
            data={
                "ad_group_id": self.ad_group.pk,
                "destination_campaign_id": self.dest_campaign.pk,
                "destination_ad_group_name": 128 * "x",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertDictEqual(
            form.errors, {"destination_ad_group_name": ["Ensure this field has no more than 127 characters."]}
        )
