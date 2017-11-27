import decimal
import mock
import urllib2

from django.test import TestCase

import core.entity
import dash.constants
from dash.features.realtimestats import service
from utils.magic_mixer import magic_mixer
from utils import dates_helper, test_helper


class RealtimestatsServiceTest(TestCase):
    def setUp(self):
        ad_group_sources = [{
            'type': 'outbrain',
            'source_campaign_key': {'campaign_id': 'test_outbrain_1'},
        }, {
            'type': 'yahoo',
            'source_campaign_key': 'test_yahoo_1',
        }, {
            'type': 'facebook',
            'source_campaign_key': 'test_facebook_1',
        }]
        self.account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=True)
        self.campaign = magic_mixer.blend(core.entity.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)
        magic_mixer.cycle(len(ad_group_sources)).blend(
            core.entity.AdGroupSource,
            ad_group=self.ad_group,
            source__source_type__type=(ags['type'] for ags in ad_group_sources),
            source_campaign_key=(ags['source_campaign_key'] for ags in ad_group_sources),
        )
        self.expected_params = {
            'outbrain_campaign_id': 'test_outbrain_1',
            'yahoo_campaign_id': 'test_yahoo_1',
            'facebook_campaign_id': 'test_facebook_1',
        }

        self._set_up_budgets()

    def _set_up_budgets(self):
        today = dates_helper.local_today()

        credit = magic_mixer.blend(
            core.bcm.CreditLineItem,
            account=self.account,
            start_date=today,
            end_date=today,
            status=dash.constants.CreditLineItemStatus.SIGNED,
            amount=decimal.Decimal('1000.0'),
            flat_fee_cc=0,
            license_fee=decimal.Decimal('0.3333'))

        magic_mixer.blend(
            core.bcm.BudgetLineItem,
            campaign=self.campaign,
            start_date=today,
            end_date=today,
            credit=credit,
            amount=decimal.Decimal('200'),
            margin=decimal.Decimal('0.2200'))

    @mock.patch('utils.redirector_helper.get_adgroup_realtimestats')
    @mock.patch('utils.k1_helper.get_adgroup_realtimestats')
    def test_get_ad_group_stats(self, mock_k1_get, mock_redirector_get):
        mock_k1_get.return_value = [{
            'spend': 3.0,
        }, {
            'spend': 1.1,
        }]
        mock_redirector_get.return_value = {
            'clicks': 13,
        }

        result = service.get_ad_group_stats(self.ad_group)
        self.assertEqual(result, {'clicks': 13, 'spend': test_helper.AlmostMatcher(decimal.Decimal('7.8842'))})

        mock_k1_get.assert_called_once_with(self.ad_group.id, self.expected_params)
        mock_redirector_get.assert_called_once_with(self.ad_group.id)

    @mock.patch('utils.k1_helper.get_adgroup_realtimestats')
    def test_get_ad_group_sources_stats(self, mock_k1_get):
        sources = magic_mixer.cycle(2).blend(core.source.Source, bidder_slug=magic_mixer.RANDOM)
        mock_k1_get.return_value = [{
            'source_slug': sources[0].bidder_slug,
            'spend': 1.1,
        }, {
            'source_slug': sources[1].bidder_slug,
            'spend': 3.0,
        }]

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual(result, [
            {
                'source_slug': sources[1].bidder_slug,
                'source': sources[1],
                'spend': test_helper.AlmostMatcher(decimal.Decimal('5.7689')),
            },
            {
                'source_slug': sources[0].bidder_slug,
                'source': sources[0],
                'spend': test_helper.AlmostMatcher(decimal.Decimal('2.1153')),
            },
        ])

        mock_k1_get.assert_called_once_with(self.ad_group.id, self.expected_params)

    @mock.patch('dash.features.realtimestats.service.influx')
    @mock.patch('dash.features.realtimestats.service.logger')
    @mock.patch('utils.k1_helper.get_adgroup_realtimestats')
    def test_k1_exception(self, mock_k1_get, mock_logger, mock_influx):
        e = Exception('test')
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual([], result)

        mock_logger.exception.assert_called_once_with(e)
        mock_influx.incr.assert_called_once_with('dash.realtimestats.error', 1, type='exception')

    @mock.patch('dash.features.realtimestats.service.influx')
    @mock.patch('dash.features.realtimestats.service.logger')
    @mock.patch('utils.k1_helper.get_adgroup_realtimestats')
    def test_k1_http_exception(self, mock_k1_get, mock_logger, mock_influx):
        e = urllib2.HTTPError('url', 400, 'msg', None, None)
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual([], result)

        mock_logger.exception.assert_not_called()
        mock_influx.incr.assert_called_once_with('dash.realtimestats.error', 1, type='http', status='400')

    @mock.patch('dash.features.realtimestats.service.influx')
    @mock.patch('dash.features.realtimestats.service.logger')
    @mock.patch('utils.k1_helper.get_adgroup_realtimestats')
    def test_k1_ioerror_exception(self, mock_k1_get, mock_logger, mock_influx):
        e = IOError()
        mock_k1_get.side_effect = e

        result = service.get_ad_group_sources_stats(self.ad_group)
        self.assertEqual([], result)

        mock_logger.exception.assert_not_called()
        mock_influx.incr.assert_called_once_with('dash.realtimestats.error', 1, type='ioerror')
