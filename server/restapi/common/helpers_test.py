from django.test import TestCase

import core.features.deals
import core.models
from utils.magic_mixer import magic_mixer

from . import helpers


class RESTAPIHelpersTest(TestCase):
    def test_get_applied_deals_dict(self):
        source = magic_mixer.blend(core.models.Source)
        ad_group = magic_mixer.blend(core.models.AdGroup)

        deal_1 = magic_mixer.blend(core.features.deals.DirectDeal)

        deal_connection_1 = magic_mixer.blend(
            core.features.deals.DirectDealConnection, source=source, adgroup=ad_group, exclusive=True, deal=deal_1
        )
        deal_connection_2 = magic_mixer.blend(
            core.features.deals.DirectDealConnection, source=source, exclusive=False, deal=deal_1
        )

        applied_deals = helpers.get_applied_deals_dict([deal_connection_1, deal_connection_2])

        self.assertEqual(
            applied_deals,
            [
                {
                    "level": deal_connection_1.level,
                    "direct_deal_connection_id": deal_connection_1.id,
                    "deal_id": deal_1.deal_id,
                    "source": deal_connection_1.source.name,
                    "exclusive": deal_connection_1.exclusive,
                    "description": deal_1.description,
                    "is_applied": True,
                },
                {
                    "level": deal_connection_2.level,
                    "direct_deal_connection_id": deal_connection_2.id,
                    "deal_id": deal_1.deal_id,
                    "source": deal_connection_2.source.name,
                    "exclusive": deal_connection_2.exclusive,
                    "description": deal_1.description,
                    "is_applied": False,
                },
            ],
        )
