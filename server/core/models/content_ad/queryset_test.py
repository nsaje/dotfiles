from typing import Any

from django.test import TestCase

import core.models
import zemauth.features.entity_permission.shortcuts
import zemauth.models
from utils.magic_mixer import magic_mixer

from . import model


class ContentAdQuerySetTest(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetTestCaseMixin, TestCase
):
    def test_archived_parent_ad_group(self):
        adgroup_archived = magic_mixer.blend(core.models.AdGroup, archived=True)
        magic_mixer.blend(core.models.ContentAd, archived=False, ad_group=adgroup_archived)
        magic_mixer.blend(core.models.ContentAd, archived=True, ad_group=adgroup_archived)

        groups = model.ContentAd.objects.exclude_archived(show_archived=False)
        self.assertEqual(len(groups), 0)

        groups = model.ContentAd.objects.exclude_archived(show_archived=True)
        self.assertEqual(len(groups), 2)

    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        return None

    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        return magic_mixer.blend(model.ContentAd, archived=False, ad_group=ad_group)
