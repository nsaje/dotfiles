from mock import patch

from django.test import TestCase
from utils.magic_mixer import magic_mixer

import core.entity


class AccountQuerySetTest(TestCase):

    def test_all_use_bcm_v2(self):
        magic_mixer.cycle(5).blend(core.entity.Account, uses_bcm_v2=True)
        self.assertTrue(core.entity.Account.objects.all().all_use_bcm_v2())

        magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        self.assertFalse(core.entity.Account.objects.all().all_use_bcm_v2())


class MigrateToBcmV2Test(TestCase):

    @patch.object(core.entity.adgroup.AdGroup, 'migrate_to_bcm_v2')
    def test_migrate_to_bcm_v2(self, mock_ad_group_migrate):
        account = magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        campaign = magic_mixer.blend(core.entity.Campaign, account=account)
        ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=campaign)

        request = magic_mixer.blend_request_user()
        account.migrate_to_bcm_v2(request)
        account.refresh_from_db()

        self.assertTrue(account.uses_bcm_v2)
        self.assertTrue(ad_group.migrate_to_bcm_v2.called)
