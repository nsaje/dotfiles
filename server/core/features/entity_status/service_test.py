from unittest import mock

import django.test

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import models
from . import service


class AccountStatusCacheTestCase(django.test.TestCase):
    @mock.patch.object(service, "get_accounts_statuses")
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

    @mock.patch("automation.campaignstop.get_campaignstop_states")
    def test_get_statuses(self, mock_campaignstop):
        acc1 = magic_mixer.blend(core.models.Account, id=1)  # ag active and allowed to run
        acc2 = magic_mixer.blend(core.models.Account, id=2)  # ag inactive and allowed to run
        acc3 = magic_mixer.blend(core.models.Account, id=3)  # ag active and not allowed to run
        ag1 = magic_mixer.blend(core.models.AdGroup, campaign__account=acc1)
        ag1.settings.update_unsafe(None, state=dash.constants.AdGroupRunningStatus.ACTIVE)
        ag2 = magic_mixer.blend(core.models.AdGroup, campaign__account=acc1)
        ag2.settings.update_unsafe(None, state=dash.constants.AdGroupRunningStatus.INACTIVE)
        ag3 = magic_mixer.blend(core.models.AdGroup, campaign__account=acc2)
        ag3.settings.update_unsafe(None, state=dash.constants.AdGroupRunningStatus.INACTIVE)
        ag4 = magic_mixer.blend(core.models.AdGroup, campaign__account=acc3)
        ag4.settings.update_unsafe(None, state=dash.constants.AdGroupRunningStatus.ACTIVE)
        mock_campaignstop.return_value = {
            ag1.campaign_id: {"allowed_to_run": True},
            ag2.campaign_id: {"allowed_to_run": True},
            ag3.campaign_id: {"allowed_to_run": True},
            ag4.campaign_id: {"allowed_to_run": False},
        }
        self.assertEqual(
            dict(service.get_accounts_statuses([1, 2, 3])), {1: dash.constants.AdGroupRunningStatus.ACTIVE}
        )
