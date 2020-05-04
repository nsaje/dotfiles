from typing import Any

from django.test import TestCase

import core.models
import zemauth.features.entity_permission.shortcuts
import zemauth.models
from utils.magic_mixer import magic_mixer

from . import models


class BidModifierQuerySetTestCase(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetTestCaseMixin, TestCase
):
    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        return None

    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        return magic_mixer.blend(models.BidModifier, ad_group=ad_group)
