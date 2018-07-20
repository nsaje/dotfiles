from django.test import TestCase

import core.source
import dash.constants
from .model import Account

from utils.magic_mixer import magic_mixer
import zemauth.models


class AccountManagerTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super(AccountManagerTestCase, cls).setUpClass()

        cls.request = magic_mixer.blend_request_user()
        cls.source_released = magic_mixer.blend(core.source.Source, released=True)
        cls.source_unreleased = magic_mixer.blend(core.source.Source, released=False)

    def test_create_add_allowed_sources(self):
        account = Account.objects.create(self.request, name="Test", agency=None)

        self.assertTrue(self.source_released in account.allowed_sources.all())
        self.assertFalse(self.source_unreleased in account.allowed_sources.all())

    def test_create_currency(self):
        account = Account.objects.create(self.request, name="Test", agency=None, currency=dash.constants.Currency.USD)

        self.assertEqual(dash.constants.Currency.USD, account.currency)

    def test_create_no_currency(self):
        account = Account.objects.create(self.request, name="Test", agency=None)

        self.assertEqual(None, account.currency)

    def test_set_user_defaults_from_agency(self):
        sales_representative = magic_mixer.blend(zemauth.models.User)
        ob_representative = magic_mixer.blend(zemauth.models.User)
        cs_representative = magic_mixer.blend(zemauth.models.User)
        agency = magic_mixer.blend(
            core.entity.Agency,
            sales_representative=sales_representative,
            ob_representative=ob_representative,
            cs_representative=cs_representative,
        )

        account = Account.objects.create(self.request, name="Test", agency=agency)

        self.assertEqual(sales_representative, account.settings.default_sales_representative)
        self.assertEqual(cs_representative, account.settings.default_cs_representative)
        self.assertEqual(ob_representative, account.settings.ob_representative)
