import core.features.deals
import core.models
from utils.base_test_case import BaseTestCase
from utils.exc import ValidationError
from utils.magic_mixer import get_request_mock
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class InstanceTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request = get_request_mock(self.user)

    def test_create(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"

        deal = core.features.deals.DirectDeal.objects.create(self.request, source, deal_id, deal_name, agency)

        self.assertEqual(deal.deal_id, deal_id)
        self.assertEqual(deal.agency_id, agency.id)
        self.assertEqual(deal.source_id, source.id)
        self.assertEqual(deal.name, deal_name)

    def test_create_with_account(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"

        deal = core.features.deals.DirectDeal.objects.create(self.request, source, deal_id, deal_name, account=account)

        self.assertEqual(deal.deal_id, deal_id)
        self.assertEqual(deal.account_id, account.id)

    def test_create_with_agency_and_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"
        with self.assertRaises(ValidationError):
            core.features.deals.DirectDeal.objects.create(
                self.request, source, deal_id, deal_name, agency=agency, account=account
            )

    def test_create_with_agency(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"

        deal = core.features.deals.DirectDeal.objects.create(self.request, source, deal_id, deal_name, agency=agency)

        self.assertEqual(deal.deal_id, deal_id)
        self.assertEqual(deal.agency_id, agency.id)

    def test_update(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        source = magic_mixer.blend(core.models.Source)

        deal_id = "DEAL_123"
        name = "DEAL_123"
        description = "DEAL 123 DESCRIPTION"

        deal = magic_mixer.blend(
            core.features.deals.DirectDeal,
            agency=agency,
            source=source,
            deal_id=deal_id,
            name=name,
            description=description,
        )

        self.assertEqual(deal.name, name)
        self.assertEqual(deal.description, description)

        updated_deal_id = "DEAL_123_UPDATED"
        updated_name = "DEAL 123 (UPDATED)"
        updated_description = "DEAL 123 DESCRIPTION (UPDATED)"

        deal.update(self.request, deal_id=updated_deal_id, name=updated_name, description=updated_description)

        self.assertEqual(deal.deal_id, updated_deal_id)
        self.assertEqual(deal.name, updated_name)
        self.assertEqual(deal.description, updated_description)

    def test_update_valid_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, adgroup=adgroup)

        self.assertEqual(deal.agency, agency)
        self.assertEqual(deal.account, None)

        deal.update(self.request, agency=None, account=account)

        self.assertEqual(deal.agency, None)
        self.assertEqual(deal.account, account)

    def test_update_invalid_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account1 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account2 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account2)

        self.assertEqual(deal.agency, agency)
        self.assertEqual(deal.account, None)

        with self.assertRaises(ValidationError):
            deal.update(self.request, agency=None, account=account1)

    def test_update_invalid_account_campaign(self):
        account1 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account2 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account1)
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account1, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

        self.assertEqual(deal.agency, None)
        self.assertEqual(deal.account, account1)

        with self.assertRaises(ValidationError):
            deal.update(self.request, account=account2)

    def test_update_invalid_account_adgroup(self):
        account1 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account2 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account1)
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account1, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, adgroup=adgroup)

        self.assertEqual(deal.agency, None)
        self.assertEqual(deal.account, account1)

        with self.assertRaises(ValidationError):
            deal.update(self.request, account=account2)

    def test_update_invalid_agency(self):
        agency1 = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        account1 = magic_mixer.blend(core.models.Account, agency=agency1)
        agency2 = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency1, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account1)

        self.assertEqual(deal.agency, agency1)
        self.assertEqual(deal.account, None)

        with self.assertRaises(ValidationError):
            deal.update(self.request, agency=agency2, account=None)
