from django.test import TestCase

import core.models
import dash.constants
import zemauth.models
from utils.magic_mixer import magic_mixer

from . import exceptions


class AgencyManagerTestCase(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user()
        self.cs = magic_mixer.blend(zemauth.models.User, email="cs@test.com")

    def test_create_agency(self):

        core.models.Agency.objects.create(
            self.request,
            name="Agency",
            default_account_type=dash.constants.AccountType.UNKNOWN,
            cs_representative=self.cs,
        )
        self.assertIsNotNone(
            core.models.Agency.objects.get(
                name="Agency", default_account_type=dash.constants.AccountType.UNKNOWN, cs_representative=self.cs
            )
        )

    def test_create_agency_disabled_not_externally_managed(self):

        with self.assertRaisesMessage(
            exceptions.DisablingAgencyNotAllowed, "Agency can be disabled only if it is externally managed."
        ):
            core.models.Agency.objects.create(
                self.request,
                name="Agency1 ",
                default_account_type=dash.constants.AccountType.UNKNOWN,
                cs_representative=self.cs,
                is_disabled=True,
            )
        self.assertIsNone(core.models.Agency.objects.filter(name="Agency1").first())

    def test_create_agency_disabled_externally_managed(self):

        with self.assertRaisesMessage(
            exceptions.EditingAgencyNotAllowed, "'is_disabled' can only be edited through Outbrain Salesforce API"
        ):
            core.models.Agency.objects.create(
                self.request,
                name="Agency1 ",
                default_account_type=dash.constants.AccountType.UNKNOWN,
                cs_representative=self.cs,
                is_disabled=True,
                is_externally_managed=True,
            )
        self.assertIsNone(core.models.Agency.objects.filter(name="Agency1").first())
