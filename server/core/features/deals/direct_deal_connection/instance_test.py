import core.features.deals
import core.models
from utils.base_test_case import BaseTestCase
from utils.base_test_case import FutureBaseTestCase
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyInstanceTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)

    def test_create(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        source = magic_mixer.blend(core.models.Source)
        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)

        deal_connection = core.features.deals.DirectDealConnection.objects.create(self.request, deal, account=account)

        self.assertEqual(deal_connection.deal.id, deal.id)
        self.assertEqual(deal_connection.account.id, account.id)
        self.assertIsNone(deal_connection.campaign)
        self.assertIsNone(deal_connection.adgroup)


class InstanceTestCase(FutureBaseTestCase, LegacyInstanceTestCase):
    pass
