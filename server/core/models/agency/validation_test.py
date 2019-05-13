from django.test import TestCase

import core.features.yahoo_accounts
import core.models
import dash.constants
import zemauth
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account, name="account 1", id=1)
        self.agency = magic_mixer.blend(core.models.Agency, name="agency 1", id=1)
        self.source1 = magic_mixer.blend(core.models.Source, name="source1")
        self.source2 = magic_mixer.blend(core.models.Source, name="source2")
        self.request = magic_mixer.blend_request_user()
        self.cs = magic_mixer.blend(zemauth.models.User, email="cs@test.com")
        self.sales = magic_mixer.blend(zemauth.models.User, email="sales@test.com")
        self.ob = magic_mixer.blend(zemauth.models.User, email="ob@test.com")
        self.yahoo_account = magic_mixer.blend(core.features.yahoo_accounts.YahooAccount, advertiser_id=1234)

    def test_update_externally_managed_field(self):
        with self.assertRaisesMessage(
            exceptions.EditingAgencyNotAllowed,
            "Field(s) 'name, custom_attributes' can only be edited through Outbrain Salesforce API",
        ):
            self.agency.update(
                self.request, name="New Name", is_externally_managed=True, custom_attributes={"something": "else"}
            )

    def test_update_is_disabled_valid(self):
        self.account.update(self.request, agency=self.agency)
        self.request.user.email = "outbrain-salesforce@service.zemanta.com"
        self.agency.update(self.request, is_externally_managed=True)

        self.agency.update(self.request, is_disabled=True)
        self.assertTrue(core.models.Agency.objects.get(id=1).is_disabled)
        self.assertTrue(core.models.Account.objects.get(id=1).is_disabled)

    def test_update_many_to_many(self):

        self.agency.update(self.request, allowed_sources=[self.source1], entity_tags=["tag1"])
        self.assertEqual(self.agency.allowed_sources.count(), 1)
        self.assertEqual(self.agency.entity_tags.count(), 1)

        self.agency.update(self.request, allowed_sources=[self.source1, self.source2])
        self.assertEqual(self.agency.allowed_sources.count(), 2)
        self.assertEqual(self.agency.entity_tags.count(), 1)

        self.agency.update(self.request, allowed_sources=[], entity_tags=[])
        self.assertEqual(self.agency.entity_tags.count(), 0)
        self.assertEqual(self.agency.allowed_sources.count(), 0)

    def test_sub_accounts_update(self):
        self.request.user.email = "outbrain-salesforce@service.zemanta.com"
        self.account.update(self.request, agency=self.agency)
        self.agency.update(
            self.request,
            is_externally_managed=True,
            is_disabled=True,
            cs_representative=self.cs,
            ob_representative=self.ob,
            sales_representative=self.sales,
            yahoo_account=self.yahoo_account,
            default_account_type=dash.constants.AccountType.ACTIVATED,
        )

        self.assertIsNotNone(
            core.models.Agency.objects.filter(
                is_externally_managed=True,
                is_disabled=True,
                cs_representative=self.cs,
                ob_representative=self.ob,
                sales_representative=self.sales,
                yahoo_account=self.yahoo_account,
                default_account_type=dash.constants.AccountType.ACTIVATED,
            )
        )
        self.assertIsNotNone(
            core.models.Account.objects.filter(
                is_disabled=True,
                settings__default_cs_representative=self.cs,
                settings__ob_representative=self.ob,
                settings__default_sales_representative=self.sales,
                yahoo_account=self.yahoo_account,
                settings__account_type=dash.constants.AccountType.ACTIVATED,
            )
        )
