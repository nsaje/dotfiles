from mock import patch

from django.test import TestCase

import core.entity
from utils.magic_mixer import magic_mixer


class InstanceTestCase(TestCase):

    @patch('utils.redirector_helper.insert_adgroup')
    @patch('utils.k1_helper.update_ad_groups')
    def test_r1_k1_propagation(self, mock_ping_adgroups, mock_insert_adgroup):
        campaign = magic_mixer.blend(core.entity.Campaign)
        magic_mixer.cycle(10).blend(core.entity.AdGroup, campaign=campaign)
        campaign.settings.update_unsafe(None, enable_ga_tracking=False)

        campaign.settings.update(None, name='abc')
        self.assertEqual(mock_insert_adgroup.call_count, 0)
        self.assertEqual(mock_ping_adgroups.call_count, 1)

        mock_ping_adgroups.reset_mock()
        campaign.settings.update(None, enable_ga_tracking=True)
        self.assertEqual(mock_insert_adgroup.call_count, 10)
        self.assertEqual(mock_ping_adgroups.call_count, 1)
