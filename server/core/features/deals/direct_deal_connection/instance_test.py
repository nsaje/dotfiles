from django.test import TestCase

import core.features.deals
import core.models
from utils.magic_mixer import magic_mixer


class InstanceTestCase(TestCase):
    def test_create(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        source = magic_mixer.blend(core.models.Source)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)

        deal_connection = core.features.deals.DirectDealConnection.objects.create(request, deal, account=account)

        self.assertEqual(deal_connection.deal.id, deal.id)
        self.assertEqual(deal_connection.account.id, account.id)
        self.assertIsNone(deal_connection.campaign)
        self.assertIsNone(deal_connection.adgroup)
