from django.test import TestCase

import core.models
import dash.constants
import zemauth.models
from utils.magic_mixer import magic_mixer

from . import exceptions
from .model import Account


class AccountManagerTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(AccountManagerTestCase, cls).setUpClass()

        cls.request = magic_mixer.blend_request_user()
        cls.source_released = magic_mixer.blend(core.models.Source, released=True)
        cls.source_unreleased = magic_mixer.blend(core.models.Source, released=False)

    def test_create_name(self):
        account = Account.objects.create(self.request, name="Test", agency=None)
        self.assertEqual(account.name, "Test")
        self.assertEqual(account.settings.name, "Test")

    def test_create_add_allowed_sources(self):
        account = Account.objects.create(self.request, name="Test", agency=None)

        self.assertTrue(self.source_released in account.allowed_sources.all())
        self.assertFalse(self.source_unreleased in account.allowed_sources.all())

    def test_create_currency(self):
        account = Account.objects.create(self.request, name="Test", agency=None, currency=dash.constants.Currency.EUR)

        self.assertEqual(dash.constants.Currency.EUR, account.currency)

    def test_create_no_currency(self):
        account = Account.objects.create(self.request, name="Test", agency=None)

        self.assertEqual(None, account.currency)

    def test_set_user_defaults_from_agency(self):
        sales_representative = magic_mixer.blend(zemauth.models.User)
        ob_representative = magic_mixer.blend(zemauth.models.User)
        cs_representative = magic_mixer.blend(zemauth.models.User)
        agency = magic_mixer.blend(
            core.models.Agency,
            sales_representative=sales_representative,
            ob_representative=ob_representative,
            cs_representative=cs_representative,
        )

        account = Account.objects.create(self.request, name="Test", agency=agency)

        self.assertEqual(sales_representative, account.settings.default_sales_representative)
        self.assertEqual(cs_representative, account.settings.default_cs_representative)
        self.assertEqual(ob_representative, account.settings.ob_representative)

    def test_create_externally_managed_agency_invalid(self):
        agency = magic_mixer.blend(core.models.Agency, id=1, name="Agency1", is_externally_managed=True)

        with self.assertRaisesMessage(
            exceptions.CreatingAccountNotAllowed, "Creating accounts for an externally managed agency is prohibited."
        ):
            Account.objects.create(self.request, name="Account 1", agency=agency)

    def test_create_externally_managed_agency_valid(self):
        agency = magic_mixer.blend(core.models.Agency, id=1, name="Agency1", is_externally_managed=True)
        self.request.user.email = "outbrain-salesforce@service.zemanta.com"
        Account.objects.create(self.request, name="Account 1", agency=agency)
        self.assertIsNotNone(core.models.Account.objects.filter(name="Account 1").first())

    def test_create_account_sources(self):
        source1 = magic_mixer.blend(core.models.Source, id=1, name="source1", released=True)
        source2 = magic_mixer.blend(core.models.Source, id=2, name="source2", released=True)
        source3 = magic_mixer.blend(core.models.Source, id=3, name="source3", released=False)
        source4 = magic_mixer.blend(core.models.Source, id=4, name="source4", released=False)

        agency = magic_mixer.blend(core.models.Agency, id=1, name="Agency1", allowed_sources=[], available_sources=[])
        account = Account.objects.create(self.request, name="Account 1", agency=agency)
        self.assertIsNotNone(account.allowed_sources.all())

        agency = magic_mixer.blend(
            core.models.Agency,
            id=1,
            name="Agency2",
            allowed_sources=[source1, source2],
            available_sources=[source1, source2, source3, source4],
        )
        account = Account.objects.create(self.request, name="Account 2", agency=agency)
        self.assertEqual(list(account.allowed_sources.all()), [source1, source2])

        agency = magic_mixer.blend(
            core.models.Agency,
            id=1,
            name="Agency3",
            available_sources=[source1, source2, source3, source4],
            allowed_sources=[],
        )
        account = Account.objects.create(self.request, name="Account 3", agency=agency)
        self.assertEqual(list(account.allowed_sources.all()), [])
