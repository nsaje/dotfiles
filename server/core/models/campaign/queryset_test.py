from typing import Any

import mock
from django.test import TestCase

import automation.campaignstop
import core.models
import zemauth.features.entity_permission.shortcuts
import zemauth.models
from utils.magic_mixer import magic_mixer

from . import model


class CampaignQuerySetTest(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetTestCaseMixin, TestCase
):
    @mock.patch.object(automation.campaignstop, "get_campaignstop_states")
    def test_filter_active(self, mock_get_campaign_states):
        campaigns = magic_mixer.cycle(3).blend(model.Campaign)
        mock_get_campaign_states.return_value = {
            campaigns[0].id: {"allowed_to_run": True},
            campaigns[1].id: {"allowed_to_run": True},
            campaigns[2].id: {"allowed_to_run": False},
        }
        self.assertEqual(set(model.Campaign.objects.filter_active()), set(campaigns[0:2]))

    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        return None

    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        return magic_mixer.blend(model.Campaign, account=account)
