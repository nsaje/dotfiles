import decimal
from unittest import mock

import django.test

import automation.campaignstop
import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import models
from . import service


class AccountStatusCacheTestCase(django.test.TestCase):
    @mock.patch.object(service, "_get_accounts_statuses")
    @mock.patch.object(service, "_get_local_daily_budgets")
    def test_refresh_accounts_statuses_cache(self, mock_get_local_daily_budgets, mock_get_statuses):
        mock_get_statuses.return_value = {
            1: dash.constants.AdGroupRunningStatus.ACTIVE,
            2: dash.constants.AdGroupRunningStatus.ACTIVE,
            # 3 is "archived" so not returned here
            4: dash.constants.AdGroupRunningStatus.INACTIVE,
            5: dash.constants.AdGroupRunningStatus.INACTIVE,
            6: dash.constants.AdGroupRunningStatus.ACTIVE,  # not cached yet
        }
        mock_get_local_daily_budgets.return_value = {
            1: decimal.Decimal(100),
            2: decimal.Decimal(200),
            6: decimal.Decimal(600),  # not cached yet
        }
        models.AccountStatusCache.objects.all().delete()
        magic_mixer.blend(
            models.AccountStatusCache,
            account_id=1,
            status=dash.constants.AdGroupRunningStatus.ACTIVE,
            local_daily_budget=decimal.Decimal(1000),
        )
        magic_mixer.blend(
            models.AccountStatusCache,
            account_id=2,
            status=dash.constants.AdGroupRunningStatus.INACTIVE,
            local_daily_budget=decimal.Decimal(0),
        )
        magic_mixer.blend(
            models.AccountStatusCache,
            account_id=3,
            status=dash.constants.AdGroupRunningStatus.ACTIVE,
            local_daily_budget=decimal.Decimal(1000),
        )
        magic_mixer.blend(
            models.AccountStatusCache,
            account_id=4,
            status=dash.constants.AdGroupRunningStatus.ACTIVE,
            local_daily_budget=decimal.Decimal(1000),
        )
        magic_mixer.blend(
            models.AccountStatusCache,
            account_id=5,
            status=dash.constants.AdGroupRunningStatus.INACTIVE,
            local_daily_budget=decimal.Decimal(0),
        )

        service.refresh_accounts_cache()

        self.assertEqual(
            list(
                models.AccountStatusCache.objects.all()
                .order_by("account_id")
                .values_list("account_id", "status", "local_daily_budget")
            ),
            [
                (1, dash.constants.AdGroupRunningStatus.ACTIVE, decimal.Decimal(100)),
                (2, dash.constants.AdGroupRunningStatus.ACTIVE, decimal.Decimal(200)),
                (3, dash.constants.AdGroupRunningStatus.INACTIVE, decimal.Decimal(0)),
                (4, dash.constants.AdGroupRunningStatus.INACTIVE, decimal.Decimal(0)),
                (5, dash.constants.AdGroupRunningStatus.INACTIVE, decimal.Decimal(0)),
                (6, dash.constants.AdGroupRunningStatus.ACTIVE, decimal.Decimal(600)),
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
            dict(service._get_accounts_statuses([1, 2, 3])), {1: dash.constants.AdGroupRunningStatus.ACTIVE}
        )

    def test_get_local_daily_budgets(self):
        local_today = dates_helper.local_today()
        local_yesterday = dates_helper.day_before(local_today)
        local_tomorrow = dates_helper.day_after(local_today)

        # account with active ad group
        acc1 = magic_mixer.blend(core.models.Account, id=1)
        c1 = magic_mixer.blend(core.models.Campaign, account=acc1, id=1)
        magic_mixer.blend(
            automation.campaignstop.CampaignStopState,
            campaign=c1,
            allowed_to_run=automation.campaignstop.constants.CampaignStopState,
        )
        ag1 = magic_mixer.blend(core.models.AdGroup, campaign=c1)
        ag1.settings.update_unsafe(
            None,
            local_daily_budget=decimal.Decimal(100),
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            start_date=local_yesterday,
            end_date=local_tomorrow,
        )
        ags1 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ag1)
        ags1.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

        # account with ad group before start date
        acc2 = magic_mixer.blend(core.models.Account, id=2)
        c2 = magic_mixer.blend(core.models.Campaign, account=acc2, id=2)
        magic_mixer.blend(
            automation.campaignstop.CampaignStopState,
            campaign=c2,
            allowed_to_run=automation.campaignstop.constants.CampaignStopState,
        )
        ag2 = magic_mixer.blend(core.models.AdGroup, campaign=c2)
        ag2.settings.update_unsafe(
            None,
            local_daily_budget=decimal.Decimal(200),
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            start_date=local_tomorrow,
            end_date=local_tomorrow,
        )
        ags2 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ag2)
        ags2.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

        # account with ad group after end date
        acc3 = magic_mixer.blend(core.models.Account, id=3)
        c3 = magic_mixer.blend(core.models.Campaign, account=acc3, id=3)
        magic_mixer.blend(
            automation.campaignstop.CampaignStopState,
            campaign=c3,
            allowed_to_run=automation.campaignstop.constants.CampaignStopState,
        )
        ag3 = magic_mixer.blend(core.models.AdGroup, campaign=c3)
        ag3.settings.update_unsafe(
            None,
            local_daily_budget=decimal.Decimal(300),
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            start_date=local_yesterday,
            end_date=local_yesterday,
        )
        ags3 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ag3)
        ags3.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

        # account with ad group with paused state
        acc4 = magic_mixer.blend(core.models.Account, id=4)
        c4 = magic_mixer.blend(core.models.Campaign, account=acc4, id=4)
        magic_mixer.blend(
            automation.campaignstop.CampaignStopState,
            campaign=c4,
            allowed_to_run=automation.campaignstop.constants.CampaignStopState,
        )
        ag4 = magic_mixer.blend(core.models.AdGroup, campaign=c4)
        ag4.settings.update_unsafe(
            None,
            local_daily_budget=decimal.Decimal(400),
            state=dash.constants.AdGroupSettingsState.INACTIVE,
            start_date=local_yesterday,
            end_date=local_tomorrow,
        )
        ags4 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ag4)
        ags4.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)

        # account with ad group with paused source
        acc5 = magic_mixer.blend(core.models.Account, id=5)
        c5 = magic_mixer.blend(core.models.Campaign, account=acc5, id=5)
        magic_mixer.blend(
            automation.campaignstop.CampaignStopState,
            campaign=c5,
            allowed_to_run=automation.campaignstop.constants.CampaignStopState,
        )
        ag5 = magic_mixer.blend(core.models.AdGroup, campaign=c5)
        ag5.settings.update_unsafe(
            None,
            local_daily_budget=decimal.Decimal(500),
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            start_date=local_yesterday,
            end_date=local_tomorrow,
        )
        ags5 = magic_mixer.blend(core.models.AdGroupSource, ad_group=ag5)
        ags5.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)

        self.assertEqual(
            {
                1: decimal.Decimal(100),
            },
            service._get_local_daily_budgets([acc1.id, acc2.id, acc3.id, acc4.id, acc5.id]),
        )
