from django.test import TestCase

import core.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account, name="account 1", id=1)
        self.agency = magic_mixer.blend(core.models.Agency, name="agency 1", id=1)
        self.source1 = magic_mixer.blend(core.models.Source, name="source1")
        self.source2 = magic_mixer.blend(core.models.Source, name="source2")
        self.request = magic_mixer.blend_request_user()

    def test_update_account_without_agency(self):
        self.account.update(
            self.request,
            name="New Name",
            auto_archiving_enabled=True,
            salesforce_url="http://url.com",
            uses_bcm_v2=True,
        )

        self.assertIsNotNone(
            core.models.Account.objects.filter(
                name="New Name", auto_archiving_enabled=True, salesforce_url="http://url.com", uses_bcm_v2=True
            )
        )

    def test_udpate_account_with_agency(self):
        self.account.agency = self.agency
        self.account.save(None)
        self.account.update(
            self.request,
            name="New Name",
            auto_archiving_enabled=True,
            salesforce_url="http://url.com",
            uses_bcm_v2=True,
        )

        self.assertIsNotNone(
            core.models.Account.objects.filter(
                name="New Name", auto_archiving_enabled=True, salesforce_url="http://url.com", uses_bcm_v2=True
            )
        )

    def test_update_externally_managed_field(self):
        self.agency.update(self.request, is_externally_managed=True)
        self.account.agency = self.agency
        self.account.save(None)

        with self.assertRaisesMessage(
            exceptions.EditingAccountNotAllowed,
            "Field(s) 'name, salesforce_url, custom_attributes, salesforce_id' can only be edited through Outbrain Salesforce API",
        ):
            self.account.update(
                self.request,
                name="New Name",
                salesforce_url="http://url.com",
                custom_attributes=["country"],
                salesforce_id=1234,
            )

    def test_update_is_disabled_valid(self):
        self.request.user.email = "outbrain-salesforce@service.zemanta.com"
        self.agency.update(self.request, is_externally_managed=True)
        self.account.agency = self.agency
        self.account.save(None)

        self.account.update(self.request, is_disabled=True)
        self.assertTrue(core.models.Account.objects.get(id=1).is_disabled)

    def test_update_many_to_many(self):
        self.account.update(self.request, allowed_sources=[self.source1], entity_tags=["tag1"])
        self.assertEqual(self.account.allowed_sources.count(), 1)
        self.assertEqual(self.account.entity_tags.count(), 1)

        self.account.update(self.request, allowed_sources=[self.source1, self.source2])
        self.assertEqual(self.account.allowed_sources.count(), 2)
        self.assertEqual(self.account.entity_tags.count(), 1)

        self.account.update(self.request, allowed_sources=[], entity_tags=[])
        self.assertEqual(self.account.allowed_sources.count(), 0)
        self.assertEqual(self.account.entity_tags.count(), 0)
