import datetime

import mock
from django.test import TestCase

import core.features.delivery_status
import core.models
import dash.constants
from utils import dates_helper
from utils.magic_mixer import magic_mixer

from . import service


class AccountDetailedDeliveryStatusServiceTest(TestCase):
    def test_get_account_delivery_status(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group)

        start_date = dates_helper.local_today() - datetime.timedelta(days=100)
        end_date = start_date + datetime.timedelta(days=80)
        ad_group.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )
        self.assertEqual(
            {account.id: core.features.delivery_status.DetailedDeliveryStatus.INACTIVE},
            service.get_account_detailed_delivery_status_map([account]),
        )

        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )
        ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.assertEqual(
            {account.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE},
            service.get_account_detailed_delivery_status_map([account]),
        )

        for adg in dash.models.AdGroup.objects.filter(campaign__account=campaign.account):
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            {account.id: core.features.delivery_status.DetailedDeliveryStatus.STOPPED},
            service.get_account_detailed_delivery_status_map([account]),
        )

    def test_get_account_detailed_delivery_status_map_multiple(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account_1 = magic_mixer.blend(core.models.Account, agency=agency)
        account_2 = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group_1 = magic_mixer.blend(core.models.AdGroup, campaign__account=account_1)
        ad_group_2 = magic_mixer.blend(core.models.AdGroup, campaign__account=account_2)

        start_date = dates_helper.local_today() - datetime.timedelta(days=50)
        end_date = start_date + datetime.timedelta(days=10)
        ad_group_1.settings.update_unsafe(
            None, state=dash.constants.AdGroupSettingsState.ACTIVE, start_date=start_date, end_date=end_date
        )

        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group_2.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )
        self.assertEqual(
            {
                account_1.id: core.features.delivery_status.DetailedDeliveryStatus.INACTIVE,
                account_2.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE,
            },
            service.get_account_detailed_delivery_status_map([account_1, account_2]),
        )

    def test_get_account_detailed_delivery_status_map_multiple_queryset(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account_1 = magic_mixer.blend(core.models.Account, agency=agency)
        account_2 = magic_mixer.blend(core.models.Account, agency=agency)
        ad_group_1 = magic_mixer.blend(core.models.AdGroup, campaign__account=account_1)
        ad_group_2 = magic_mixer.blend(core.models.AdGroup, campaign__account=account_2)

        start_date = dates_helper.local_today() - datetime.timedelta(days=50)
        end_date = start_date + datetime.timedelta(days=10)
        ad_group_1.settings.update_unsafe(
            None, state=dash.constants.AdGroupSettingsState.ACTIVE, start_date=start_date, end_date=end_date
        )

        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group_2.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )
        self.assertEqual(
            {
                account_1.id: core.features.delivery_status.DetailedDeliveryStatus.INACTIVE,
                account_2.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE,
            },
            service.get_account_detailed_delivery_status_map(
                core.models.Account.objects.filter(id__in=[account_1.id, account_2.id])
            ),
        )


class CampaignDetailedDeliveryStatusServiceTest(TestCase):
    def test_get_campaign_detailed_delivery_status_map(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group)

        start_date = dates_helper.local_today() - datetime.timedelta(days=50)
        end_date = start_date + datetime.timedelta(days=10)
        ad_group.settings.update_unsafe(
            None, state=dash.constants.AdGroupSettingsState.ACTIVE, start_date=start_date, end_date=end_date
        )
        self.assertEqual(
            {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.INACTIVE},
            service.get_campaign_detailed_delivery_status_map([campaign]),
        )

        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )

        ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.assertEqual(
            {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE},
            service.get_campaign_detailed_delivery_status_map([campaign]),
        )

        campaign.settings.update_unsafe(None, autopilot=True)
        self.assertEqual(
            {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION},
            service.get_campaign_detailed_delivery_status_map([campaign]),
        )

        campaign.settings.update_unsafe(None, autopilot=True)

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = campaign.real_time_campaign_stop
            campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                {
                    campaign.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION
                },
                service.get_campaign_detailed_delivery_status_map([campaign]),
            )

            campaign.set_real_time_campaign_stop(None, old_value)

        campaign.settings.update_unsafe(None, autopilot=False)

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = campaign.real_time_campaign_stop
            campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": False}
            self.assertEqual(
                {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_STOPPED},
                service.get_campaign_detailed_delivery_status_map([campaign]),
            )

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE},
                service.get_campaign_detailed_delivery_status_map([campaign]),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": False,
            }
            self.assertEqual(
                {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE},
                service.get_campaign_detailed_delivery_status_map([campaign]),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": True,
            }
            self.assertEqual(
                {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_LOW_BUDGET},
                service.get_campaign_detailed_delivery_status_map([campaign]),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": True,
                "almost_depleted": False,
            }
            self.assertEqual(
                {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE},
                service.get_campaign_detailed_delivery_status_map([campaign]),
            )

            campaign.set_real_time_campaign_stop(None, old_value)

        for adg in campaign.adgroup_set.all():
            adg_settings = adg.get_current_settings().copy_settings()
            adg_settings.state = dash.constants.AdGroupSettingsState.INACTIVE
            adg_settings.save(None)

        self.assertEqual(
            {campaign.id: core.features.delivery_status.DetailedDeliveryStatus.STOPPED},
            service.get_campaign_detailed_delivery_status_map([campaign]),
        )

    def test_get_campaign_detailed_delivery_status_map_multiple(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign_1 = magic_mixer.blend(core.models.Campaign, account=account)
        campaign_2 = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group_1 = magic_mixer.blend(core.models.AdGroup, campaign=campaign_1)
        ad_group_2 = magic_mixer.blend(core.models.AdGroup, campaign=campaign_2)

        start_date = dates_helper.local_today() - datetime.timedelta(days=50)
        end_date = start_date + datetime.timedelta(days=10)
        ad_group_1.settings.update_unsafe(
            None, state=dash.constants.AdGroupSettingsState.ACTIVE, start_date=start_date, end_date=end_date
        )

        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group_2.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )
        self.assertEqual(
            {
                campaign_1.id: core.features.delivery_status.DetailedDeliveryStatus.INACTIVE,
                campaign_2.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE,
            },
            service.get_campaign_detailed_delivery_status_map([campaign_1, campaign_2]),
        )

    def test_get_campaign_detailed_delivery_status_map_multiple_queryset(self):
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign_1 = magic_mixer.blend(core.models.Campaign, account=account)
        campaign_2 = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group_1 = magic_mixer.blend(core.models.AdGroup, campaign=campaign_1)
        ad_group_2 = magic_mixer.blend(core.models.AdGroup, campaign=campaign_2)

        start_date = dates_helper.local_today() - datetime.timedelta(days=50)
        end_date = start_date + datetime.timedelta(days=10)
        ad_group_1.settings.update_unsafe(
            None, state=dash.constants.AdGroupSettingsState.ACTIVE, start_date=start_date, end_date=end_date
        )

        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group_2.settings.update_unsafe(
            None, start_date=start_date, end_date=end_date, state=dash.constants.AdGroupSettingsState.ACTIVE
        )
        self.assertEqual(
            {
                campaign_1.id: core.features.delivery_status.DetailedDeliveryStatus.INACTIVE,
                campaign_2.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE,
            },
            service.get_campaign_detailed_delivery_status_map(
                core.models.Campaign.objects.filter(id__in=[campaign_1.id, campaign_2.id])
            ),
        )


class AdGroupDetailedDeliveryStatusServiceTest(TestCase):
    def test_get_ad_group_detailed_delivery_status(self):
        # adgroup is inactive and no active sources
        agency = magic_mixer.blend(core.models.Agency, uses_realtime_autopilot=True)
        account = magic_mixer.blend(core.models.Account, agency=agency)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group_source = magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group)

        start_date = dates_helper.local_today() + datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.INACTIVE,
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.INACTIVE,
            created_dt=dates_helper.local_now(),
        )
        self.assertEqual(
            {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.STOPPED},
            service.get_ad_group_detailed_delivery_status_map([ad_group]),
        )

        # adgroup is active and sources are active
        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=dates_helper.local_now(),
        )
        ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.assertEqual(
            {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE},
            service.get_ad_group_detailed_delivery_status_map([ad_group]),
        )

        with self.assertNumQueries(2):
            service.get_ad_group_detailed_delivery_status_map([ad_group])

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = campaign.real_time_campaign_stop
            campaign.set_real_time_campaign_stop(None, True)

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": False}
            self.assertEqual(
                {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_STOPPED},
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE},
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": False,
            }
            self.assertEqual(
                {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE},
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": False,
                "pending_budget_updates": True,
                "almost_depleted": False,
            }
            self.assertEqual(
                {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE},
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": True,
                "almost_depleted": False,
            }
            self.assertEqual(
                {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.ACTIVE},
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            mock_get_campaignstop_state.return_value = {
                "allowed_to_run": True,
                "pending_budget_updates": False,
                "almost_depleted": True,
            }
            self.assertEqual(
                {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_LOW_BUDGET},
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            ad_group.campaign.set_real_time_campaign_stop(None, old_value)

        # campaign is on autopilot
        campaign.settings.update_unsafe(None, autopilot=True)
        self.assertEqual(
            {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.BUDGET_OPTIMIZATION},
            service.get_ad_group_detailed_delivery_status_map([ad_group]),
        )
        campaign.settings.update_unsafe(None, autopilot=False)

        # adgroup is active, sources are active and adgroup is on CPC autopilot
        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=datetime.datetime.utcnow(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,
        )
        self.assertEqual(
            {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.OPTIMAL_BID},
            service.get_ad_group_detailed_delivery_status_map([ad_group]),
        )

        # adgroup is active, sources are active and adgroup is on CPC+Budget autopilot
        start_date = dates_helper.local_today() - datetime.timedelta(days=10)
        end_date = start_date + datetime.timedelta(days=99)
        ad_group.settings.update_unsafe(
            None,
            start_date=start_date,
            end_date=end_date,
            state=dash.constants.AdGroupSettingsState.ACTIVE,
            created_dt=dates_helper.local_now(),
            autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
        )
        self.assertEqual(
            {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.OPTIMAL_BID},
            service.get_ad_group_detailed_delivery_status_map([ad_group]),
        )

        with mock.patch("automation.campaignstop.get_campaignstop_state") as mock_get_campaignstop_state:
            old_value = ad_group.campaign.real_time_campaign_stop
            ad_group.campaign.set_real_time_campaign_stop(None, True)

            # adgroup is active and on CPC autopilot with pending budget updates
            start_date = dates_helper.local_today() - datetime.timedelta(days=10)
            end_date = start_date + datetime.timedelta(days=99)
            ad_group.settings.update_unsafe(
                None,
                start_date=start_date,
                end_date=end_date,
                state=dash.constants.AdGroupSettingsState.ACTIVE,
                created_dt=dates_helper.local_now(),
                autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC,  # price_discovery
            )
            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                {
                    ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID
                },
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            # adgroup is active and on CPC+Budget autopilot with pending budget updates
            start_date = dates_helper.local_today() - datetime.timedelta(days=10)
            end_date = start_date + datetime.timedelta(days=99)
            ad_group.settings.update_unsafe(
                None,
                start_date=start_date,
                end_date=end_date,
                state=dash.constants.AdGroupSettingsState.ACTIVE,
                created_dt=dates_helper.local_now(),
                autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,  # autopilot
            )
            mock_get_campaignstop_state.return_value = {"allowed_to_run": False, "pending_budget_updates": True}
            self.assertEqual(
                {
                    ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID
                },
                service.get_ad_group_detailed_delivery_status_map([ad_group]),
            )

            ad_group.campaign.set_real_time_campaign_stop(None, old_value)

        # adgroup is active but sources are inactive
        ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)
        self.assertEqual(
            {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.OPTIMAL_BID},
            service.get_ad_group_detailed_delivery_status_map([ad_group]),
        )

        # adgroup is inactive but sources are active
        ad_group.settings.update_unsafe(None, state=dash.constants.AdGroupSettingsState.INACTIVE)
        ad_group_source.settings.update_unsafe(None, state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
        self.assertEqual(
            {ad_group.id: core.features.delivery_status.DetailedDeliveryStatus.STOPPED},
            service.get_ad_group_detailed_delivery_status_map([ad_group]),
        )
