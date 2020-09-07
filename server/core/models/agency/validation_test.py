from django.test import TestCase

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
        self.source3 = magic_mixer.blend(core.models.Source, name="source3")
        self.source4 = magic_mixer.blend(core.models.Source, name="source4")
        self.request = magic_mixer.blend_request_user()
        self.cs = magic_mixer.blend(zemauth.models.User, email="cs@test.com")
        self.sales = magic_mixer.blend(zemauth.models.User, email="sales@test.com")
        self.ob_sales_representative = magic_mixer.blend(zemauth.models.User, email="ob_sales_representative@test.com")
        self.ob_account_manager = magic_mixer.blend(zemauth.models.User, email="ob_account_manager@test.com")

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

        self.agency.update(self.request, available_sources=[self.source1, self.source2])
        self.assertEqual(self.agency.available_sources.count(), 2)

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
            ob_sales_representative=self.ob_sales_representative,
            ob_account_manager=self.ob_account_manager,
            sales_representative=self.sales,
            default_account_type=dash.constants.AccountType.ACTIVATED,
        )

        self.assertIsNotNone(
            core.models.Agency.objects.filter(
                is_externally_managed=True,
                is_disabled=True,
                cs_representative=self.cs,
                ob_sales_representative=self.ob_sales_representative,
                ob_account_manager=self.ob_account_manager,
                sales_representative=self.sales,
                default_account_type=dash.constants.AccountType.ACTIVATED,
            )
        )
        self.assertIsNotNone(
            core.models.Account.objects.filter(
                is_disabled=True,
                settings__default_cs_representative=self.cs,
                settings__ob_sales_representative=self.ob_sales_representative,
                settings__ob_account_manager=self.ob_account_manager,
                settings__default_sales_representative=self.sales,
                settings__account_type=dash.constants.AccountType.ACTIVATED,
            )
        )

    def test_update_allowed_sources(self):
        # case set allowed source present in available
        self.agency.update(None, available_sources=[self.source1, self.source2], allowed_sources=[])
        self.agency.update(None, allowed_sources=[self.source1])
        self.assertEqual(set(self.agency.allowed_sources.all()), {self.source1})

        # case set an allowed source not present in available
        self.agency.update(None, available_sources=[self.source1, self.source2], allowed_sources=[])
        with self.assertRaises(exceptions.EditingSourcesNotAllowed):
            self.agency.update(None, allowed_sources=[self.source3])

        # case unset an allowed source
        self.agency.update(None, available_sources=[self.source1, self.source2], allowed_sources=[self.source1])
        self.agency.update(None, allowed_sources=[])
        self.assertEqual(set(self.agency.allowed_sources.all()), set())

        # case both have the same, then remove an available source and add it in allowed
        self.agency.update(
            None, available_sources=[self.source1, self.source2], allowed_sources=[self.source1, self.source2]
        )
        with self.assertRaises(exceptions.EditingSourcesNotAllowed):
            self.agency.update(None, available_sources=[self.source1], allowed_sources=[self.source2])
        # case we update both at the same time
        self.agency.update(
            None,
            available_sources=[self.source1, self.source2, self.source3],
            allowed_sources=[self.source1, self.source2, self.source3],
        )
        self.assertEqual(set(self.agency.allowed_sources.all()), {self.source1, self.source2, self.source3})
        self.assertEqual(set(self.agency.available_sources.all()), {self.source1, self.source2, self.source3})

    def test_update_available_sources(self):
        # Case set available sources and allowed sources at the same time
        self.agency.update(
            None, available_sources=[self.source1, self.source2], allowed_sources=[self.source1, self.source2]
        )
        self.assertEqual(set(self.agency.available_sources.all()), {self.source1, self.source2})
        self.assertEqual(set(self.agency.allowed_sources.all()), {self.source1, self.source2})

        # Case remove a source only from available
        self.agency.update(
            None, available_sources=[self.source1, self.source2], allowed_sources={self.source1, self.source2}
        )
        with self.assertRaises(exceptions.EditingSourcesNotAllowed):
            self.agency.update(None, available_sources=[self.source2])

        # Case remove source1 from available and allowed
        self.agency.update(
            None, available_sources=[self.source1, self.source2], allowed_sources={self.source1, self.source2}
        )
        self.agency.update(None, available_sources=[self.source2], allowed_sources=[self.source2])
        self.assertEqual(set(self.agency.available_sources.all()), {self.source2})
        self.assertEqual(set(self.agency.allowed_sources.all()), {self.source2})

        # Case add a new source to available and remove one from allowed
        self.agency.update(None, available_sources=[self.source2, self.source3], allowed_sources=[self.source2])
        self.assertEqual(set(self.agency.available_sources.all()), {self.source2, self.source3})
        self.assertEqual(set(self.agency.allowed_sources.all()), {self.source2})

        # Case remove an available source source3 and add a new source one, which is also added to allowed sources.
        self.agency.update(
            None,
            available_sources=[self.source1, self.source2, self.source3],
            allowed_sources=[self.source1, self.source2],
        )
        self.agency.update(
            None, available_sources=[self.source1, self.source2], allowed_sources=[self.source1, self.source2]
        )
        self.assertEqual(set(self.agency.available_sources.all()), {self.source1, self.source2})
        self.assertEqual(set(self.agency.allowed_sources.all()), {self.source1, self.source2})

        # case remove all available sources while there is still allowed sources
        self.agency.update(
            None, available_sources=[self.source1, self.source2], allowed_sources=[self.source1, self.source2]
        )
        with self.assertRaises(exceptions.EditingSourcesNotAllowed):
            self.agency.update(None, available_sources=[])
