from django.core.exceptions import ValidationError
from django.test import TestCase

import core.features.deals
import core.models
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
