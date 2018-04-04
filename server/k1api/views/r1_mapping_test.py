import json
import logging

from django.core.urlresolvers import reverse

from .base_test import K1APIBaseTest

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class R1MappingTest(K1APIBaseTest):

    def test_get_accounts_slugs_ad_groups(self):
        accounts = (1, 2)
        response = self.client.get(
            reverse('k1api.r1_mapping'),
            {'account': accounts},
        )

        data = json.loads(response.content)
        self.assert_response_ok(response, data)
        data = data['response']

        for account_id, account_data in list(data.items()):
            self.assertIn(int(account_id), accounts)

            self.assertIn('ad_groups', account_data)
            self.assertIn('slugs', account_data)

            self.assertGreater(len(account_data['ad_groups']), 0)
            for ad_group in list(account_data['ad_groups'].values()):
                self.assertIn('campaign_id', ad_group)

            self.assertGreater(len(account_data['slugs']), 0)
