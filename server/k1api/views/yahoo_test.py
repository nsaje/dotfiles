import json
import logging

from django.core.urlresolvers import reverse

import core.entity
import core.features.yahoo_accounts

from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)


class YahooTest(K1APIBaseTest):

    def test_get_all(self):
        yahoo_account = magic_mixer.blend(
            core.features.yahoo_accounts.YahooAccount,
        )
        yahoo_account_2 = magic_mixer.blend(
            core.features.yahoo_accounts.YahooAccount,
        )
        account = magic_mixer.blend(
            core.entity.Account,
            yahoo_account=yahoo_account,
        )
        account_2 = magic_mixer.blend(
            core.entity.Account,
            yahoo_account=yahoo_account_2,
        )
        account_3 = magic_mixer.blend(
            core.entity.Account,
            yahoo_account=yahoo_account_2,
        )
        response = self.client.get(
            reverse('k1api.yahoo_accounts'),
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        expected = [{
            'account_id': account.id,
            'advertiser_id': yahoo_account.advertiser_id
        }, {
            'account_id': account_2.id,
            'advertiser_id': yahoo_account_2.advertiser_id
        }, {
            'account_id': account_3.id,
            'advertiser_id': yahoo_account_2.advertiser_id
        }]
        self.assertCountEqual(expected, data['response'])

    def test_get_filtered_ad_group(self):
        yahoo_account = magic_mixer.blend(
            core.features.yahoo_accounts.YahooAccount,
        )
        account = magic_mixer.blend(core.entity.Account, yahoo_account=yahoo_account)
        # second, filtered out
        yahoo_account_2 = magic_mixer.blend(
            core.features.yahoo_accounts.YahooAccount,
        )
        magic_mixer.blend(core.entity.Account, yahoo_account=yahoo_account_2)
        response = self.client.get(
            reverse('k1api.yahoo_accounts'),
            {'account_ids': account.id}
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        expected = [{
            'account_id': account.id,
            'advertiser_id': yahoo_account.advertiser_id
        }]
        self.assertEqual(expected, data['response'])
