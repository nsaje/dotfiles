from typing import Any

from django.test import TestCase

import core.models
import zemauth.features.entity_permission.shortcuts
from utils.magic_mixer import magic_mixer

from . import model


class EntityPermissionMixinTestCase(
    zemauth.features.entity_permission.shortcuts.EntityPermissionTestCaseMixin, TestCase
):
    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        return None

    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        return magic_mixer.blend(model.AdGroup, campaign=campaign)