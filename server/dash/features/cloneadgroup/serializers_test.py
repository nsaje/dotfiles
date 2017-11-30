from django.test import TestCase
from mock import patch
from utils.magic_mixer import magic_mixer

import core.entity
import core.source
import serializers


@patch.object(core.entity.ContentAd.objects, 'insert_redirects', autospec=True)
@patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group', autospec=True)
@patch('utils.redirector_helper.insert_adgroup', autospec=True)
class CloneForm(TestCase):

    def test_clone_valid(self, mock_insert_adgroup, mock_redirects, mock_autopilot):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        magic_mixer.cycle(5).blend(core.entity.ContentAd, ad_group=ad_group, archived=False)
        dest_campaign = magic_mixer.blend(core.entity.Campaign)

        form = serializers.CloneAdGroupSerializer(data={
            'ad_group_id': ad_group.pk,
            'destination_campaign_id': dest_campaign.pk,
            'destination_ad_group_name': 'Test'
        })
        self.assertTrue(form.is_valid())
