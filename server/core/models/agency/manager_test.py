from django.test import TestCase

import core.models
import dash.constants
import zemauth.models
from utils.magic_mixer import magic_mixer


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
        agency = core.models.Agency.objects.get(
            name="Agency", default_account_type=dash.constants.AccountType.UNKNOWN, cs_representative=self.cs
        )
        self.assertIsNotNone(agency)
        self.assertFalse(agency.uses_realtime_autopilot)
