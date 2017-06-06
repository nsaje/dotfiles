import mock

from django.test import TestCase

import core.entity
from dash.features.realtimestats import service
from utils.magic_mixer import magic_mixer


class RealtimestatsServiceTest(TestCase):

    @mock.patch('utils.redirector_helper.get_adgroup_realtimestats')
    @mock.patch('utils.k1_helper.get_adgroup_realtimestats')
    def test_get_ad_group_stats(self, mock_k1_get, mock_redirector_get):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        mock_k1_get.return_value = [{
            'spend': 3.0,
        }, {
            'spend': 1.1,
        }]
        mock_redirector_get.return_value = {
            'clicks': 13,
        }

        result = service.get_ad_group_stats(ad_group)
        self.assertEqual(result, {'clicks': 13, 'spend': 4.1})

        mock_k1_get.assert_called_once_with(ad_group.id)
        mock_redirector_get.assert_called_once_with(ad_group.id)

    @mock.patch('utils.k1_helper.get_adgroup_realtimestats')
    def test_get_ad_group_sources_stats(self, mock_k1_get):
        ad_group = magic_mixer.blend(core.entity.AdGroup)
        sources = magic_mixer.cycle(2).blend(core.source.Source, bidder_slug=magic_mixer.RANDOM)
        mock_k1_get.return_value = [{
            'source_slug': sources[0].bidder_slug,
            'spend': 1.1,
        }, {
            'source_slug': sources[1].bidder_slug,
            'spend': 3.0,
        }]

        result = service.get_ad_group_sources_stats(ad_group)
        self.assertEqual(result, [
            {
                'source_slug': sources[1].bidder_slug,
                'source': sources[1].name,
                'spend': 3.0,
            },
            {
                'source_slug': sources[0].bidder_slug,
                'source': sources[0].name,
                'spend': 1.1,
            },
        ])

        mock_k1_get.assert_called_once_with(ad_group.id)
