from django.test import TestCase

import core.features.deals
import core.models
from utils.exc import ValidationError
from utils.magic_mixer import magic_mixer


class InstanceTestCase(TestCase):
    def test_create(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"

        deal = core.features.deals.DirectDeal.objects.create(request, source, deal_id, deal_name, agency)

        self.assertEqual(deal.deal_id, deal_id)
        self.assertEqual(deal.agency_id, agency.id)
        self.assertEqual(deal.source_id, source.id)
        self.assertEqual(deal.name, deal_name)

    def test_create_with_account(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"

        deal = core.features.deals.DirectDeal.objects.create(request, source, deal_id, deal_name, account=account)

        self.assertEqual(deal.deal_id, deal_id)
        self.assertEqual(deal.account_id, account.id)

    def test_create_with_agency_and_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user], agency=agency)
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"
        with self.assertRaises(ValidationError):
            core.features.deals.DirectDeal.objects.create(
                request, source, deal_id, deal_name, agency=agency, account=account
            )

    def test_create_with_agency(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        source = magic_mixer.blend(core.models.Source)
        deal_id = "DEAL_123"
        deal_name = "DEAL_NAME"

        deal = core.features.deals.DirectDeal.objects.create(request, source, deal_id, deal_name, agency=agency)

        self.assertEqual(deal.deal_id, deal_id)
        self.assertEqual(deal.agency_id, agency.id)

    def test_update(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
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

        deal.update(request, deal_id=updated_deal_id, name=updated_name, description=updated_description)

        self.assertEqual(deal.deal_id, updated_deal_id)
        self.assertEqual(deal.name, updated_name)
        self.assertEqual(deal.description, updated_description)

    def test_update_valid_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account = magic_mixer.blend(core.models.Account, users=[request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account, users=[request.user])
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, adgroup=adgroup)

        self.assertEqual(deal.agency, agency)
        self.assertEqual(deal.account, None)

        deal.update(request, agency=None, account=account)

        self.assertEqual(deal.agency, None)
        self.assertEqual(deal.account, account)

    def test_update_invalid_account(self):
        request = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency, users=[request.user])
        account1 = magic_mixer.blend(core.models.Account, users=[request.user])
        account2 = magic_mixer.blend(core.models.Account, users=[request.user])
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account2)

        self.assertEqual(deal.agency, agency)
        self.assertEqual(deal.account, None)

        with self.assertRaises(ValidationError):
            deal.update(request, agency=None, account=account1)

    def test_update_invalid_account_campaign(self):
        request = magic_mixer.blend_request_user()
        account1 = magic_mixer.blend(core.models.Account, users=[request.user])
        account2 = magic_mixer.blend(core.models.Account, users=[request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account1, users=[request.user])
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account1, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, campaign=campaign)

        self.assertEqual(deal.agency, None)
        self.assertEqual(deal.account, account1)

        with self.assertRaises(ValidationError):
            deal.update(request, account=account2)

    def test_update_invalid_account_adgroup(self):
        request = magic_mixer.blend_request_user()
        account1 = magic_mixer.blend(core.models.Account, users=[request.user])
        account2 = magic_mixer.blend(core.models.Account, users=[request.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account1, users=[request.user])
        adgroup = magic_mixer.blend(core.models.AdGroup, campaign=campaign, users=[request.user])
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, account=account1, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, adgroup=adgroup)

        self.assertEqual(deal.agency, None)
        self.assertEqual(deal.account, account1)

        with self.assertRaises(ValidationError):
            deal.update(request, account=account2)

    def test_update_invalid_agency(self):
        request = magic_mixer.blend_request_user()
        agency1 = magic_mixer.blend(core.models.Agency, users=[request.user])
        account1 = magic_mixer.blend(core.models.Account, agency=agency1, users=[request.user])
        agency2 = magic_mixer.blend(core.models.Agency, users=[request.user])
        source = magic_mixer.blend(core.models.Source)

        deal = magic_mixer.blend(core.features.deals.DirectDeal, agency=agency1, source=source)
        magic_mixer.blend(core.features.deals.DirectDealConnection, deal=deal, account=account1)

        self.assertEqual(deal.agency, agency1)
        self.assertEqual(deal.account, None)

        with self.assertRaises(ValidationError):
            deal.update(request, agency=agency2, account=None)
