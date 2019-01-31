import json

from django.urls import reverse

import core.features.deals
import core.models
from utils.magic_mixer import magic_mixer

from .base_test import K1APIBaseTest


class DirectDealsTest(K1APIBaseTest):
    @classmethod
    def setUpTestData(cls):
        source = magic_mixer.blend(core.models.Source, bidder_slug="test_exchange_1")
        deal1 = magic_mixer.blend(core.features.deals.DirectDeal, deal_id="test_1")
        deal2 = magic_mixer.blend(core.features.deals.DirectDeal, deal_id="test_2")
        adgroup = magic_mixer.blend(core.models.AdGroup, pk=1000)
        adgroup2 = magic_mixer.blend(core.models.AdGroup, pk=1001)
        agency = magic_mixer.blend(core.models.Agency, pk=2000)
        account = magic_mixer.blend(core.models.Account, pk=3000)
        campaign = magic_mixer.blend(core.models.Campaign, pk=4000)

        magic_mixer.blend(core.features.deals.DirectDealConnection, source=source, deals=[deal1])
        magic_mixer.blend(
            core.features.deals.DirectDealConnection, source=source, deals=[deal1], adgroup=adgroup, exclusive=False
        )
        magic_mixer.blend(
            core.features.deals.DirectDealConnection, source=source, deals=[deal2], agency=agency, exclusive=False
        )
        magic_mixer.blend(
            core.features.deals.DirectDealConnection,
            source=source,
            deals=[deal1, deal2],
            adgroup=adgroup2,
            exclusive=True,
        )
        magic_mixer.blend(
            core.features.deals.DirectDealConnection, source=source, deals=[deal2], account=account, exclusive=False
        )
        magic_mixer.blend(
            core.features.deals.DirectDealConnection,
            source=source,
            deals=[deal1, deal2],
            campaign=campaign,
            exclusive=True,
        )

    def test_get_direct_deals(self):
        response = self.client.get(reverse("k1api.directdeals"))

        data = json.loads(response.content)
        self.assert_response_ok(response, data)

        expected_response = [
            {
                "exchange": "test_exchange_1",
                "exclusive": False,
                "adgroup_id": None,
                "agency_id": None,
                "account_id": None,
                "campaign_id": None,
                "deals": ["test_1"],
            },
            {
                "exchange": "test_exchange_1",
                "exclusive": False,
                "adgroup_id": 1000,
                "agency_id": None,
                "account_id": None,
                "campaign_id": None,
                "deals": ["test_1"],
            },
            {
                "exchange": "test_exchange_1",
                "exclusive": False,
                "adgroup_id": None,
                "agency_id": 2000,
                "account_id": None,
                "campaign_id": None,
                "deals": ["test_2"],
            },
            {
                "exchange": "test_exchange_1",
                "exclusive": True,
                "adgroup_id": 1001,
                "agency_id": None,
                "account_id": None,
                "campaign_id": None,
                "deals": ["test_1", "test_2"],
            },
            {
                "exchange": "test_exchange_1",
                "exclusive": False,
                "adgroup_id": None,
                "agency_id": None,
                "account_id": 3000,
                "campaign_id": None,
                "deals": ["test_2"],
            },
            {
                "exchange": "test_exchange_1",
                "exclusive": True,
                "adgroup_id": None,
                "agency_id": None,
                "account_id": None,
                "campaign_id": 4000,
                "deals": ["test_1", "test_2"],
            },
        ]
        self.assertEqual(expected_response, data["response"])
