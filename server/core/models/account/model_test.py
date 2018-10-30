from django.test import TestCase
from mock import patch

import core.models
from utils.magic_mixer import magic_mixer


class AccountQuerySetTest(TestCase):
    def test_all_use_bcm_v2(self):
        magic_mixer.cycle(5).blend(core.models.Account, uses_bcm_v2=True)
        self.assertTrue(core.models.Account.objects.all().all_use_bcm_v2())

        magic_mixer.blend(core.models.Account, uses_bcm_v2=False)
        self.assertFalse(core.models.Account.objects.all().all_use_bcm_v2())


class MigrateToBcmV2Test(TestCase):
    @patch.object(core.models.campaign.Campaign, "migrate_to_bcm_v2")
    def test_migrate_to_bcm_v2(self, mock_campaign_migrate):
        account = magic_mixer.blend(core.models.Account, uses_bcm_v2=False)
        magic_mixer.blend(core.models.Campaign, account=account)

        request = magic_mixer.blend_request_user()
        account.migrate_to_bcm_v2(request)
        account.refresh_from_db()

        self.assertTrue(account.uses_bcm_v2)
        self.assertTrue(mock_campaign_migrate.called)

    def test_migrate_agency(self):
        agency = magic_mixer.blend(core.models.Agency, new_accounts_use_bcm_v2=False)
        account_1 = magic_mixer.blend(core.models.Account, uses_bcm_v2=False, agency=agency)
        account_2 = magic_mixer.blend(core.models.Account, uses_bcm_v2=False, agency=agency)

        request = magic_mixer.blend_request_user()
        account_1.migrate_to_bcm_v2(request)
        account_1.refresh_from_db()
        agency.refresh_from_db()

        self.assertTrue(account_1.uses_bcm_v2)
        self.assertFalse(agency.new_accounts_use_bcm_v2)

        account_2.migrate_to_bcm_v2(request)
        account_2.refresh_from_db()
        agency.refresh_from_db()

        self.assertTrue(account_1.uses_bcm_v2)
        self.assertTrue(agency.new_accounts_use_bcm_v2)
