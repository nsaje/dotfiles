from unittest.mock import patch

import django.test

import dash.constants
from utils.magic_mixer import magic_mixer

from . import models
from . import service


class AccountStatusCacheTestCase(django.test.TestCase):
    @patch.object(service, "get_accounts_statuses")
    def test_refresh_accounts_statuses_cache(self, mock_get_statuses):
        mock_get_statuses.return_value = {
            1: dash.constants.AdGroupRunningStatus.ACTIVE,
            2: dash.constants.AdGroupRunningStatus.ACTIVE,
            # 3 is "archived" so not returned here
            4: dash.constants.AdGroupRunningStatus.INACTIVE,
            5: dash.constants.AdGroupRunningStatus.INACTIVE,
            6: dash.constants.AdGroupRunningStatus.ACTIVE,  # not cached yet
        }
        models.AccountStatusCache.objects.all().delete()
        magic_mixer.blend(models.AccountStatusCache, account_id=1, status=dash.constants.AdGroupRunningStatus.ACTIVE)
        magic_mixer.blend(models.AccountStatusCache, account_id=2, status=dash.constants.AdGroupRunningStatus.INACTIVE)
        magic_mixer.blend(models.AccountStatusCache, account_id=3, status=dash.constants.AdGroupRunningStatus.ACTIVE)
        magic_mixer.blend(models.AccountStatusCache, account_id=4, status=dash.constants.AdGroupRunningStatus.ACTIVE)
        magic_mixer.blend(models.AccountStatusCache, account_id=5, status=dash.constants.AdGroupRunningStatus.INACTIVE)

        service.refresh_accounts_statuses_cache()

        self.assertEqual(
            list(models.AccountStatusCache.objects.all().order_by("account_id").values_list("account_id", "status")),
            [
                (1, dash.constants.AdGroupRunningStatus.ACTIVE),
                (2, dash.constants.AdGroupRunningStatus.ACTIVE),
                (3, dash.constants.AdGroupRunningStatus.INACTIVE),
                (4, dash.constants.AdGroupRunningStatus.INACTIVE),
                (5, dash.constants.AdGroupRunningStatus.INACTIVE),
                (6, dash.constants.AdGroupRunningStatus.ACTIVE),
            ],
        )
