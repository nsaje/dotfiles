from typing import Any

from django.test import TestCase

import core.models
import zemauth.features.entity_permission.shortcuts
import zemauth.models
from utils.magic_mixer import magic_mixer

from . import model


class CreativeTagQuerySetTestCase(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetTestCaseMixin, TestCase
):
    def test_filter_by_agency(self):
        agency_one = magic_mixer.blend(core.models.Agency)
        agency_two = magic_mixer.blend(core.models.Agency)
        agency_one_tag = magic_mixer.blend(model.CreativeTag, name="agency_one_tag", agency=agency_one)
        magic_mixer.blend(model.CreativeTag, name="agency_two_tag", agency=agency_two)

        tags = list(model.CreativeTag.objects.filter_by_agency(agency_one))
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].id, agency_one_tag.id)

    def test_filter_by_agency_and_related_accounts(self):
        agency_one = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency_one)
        agency_two = magic_mixer.blend(core.models.Agency)
        agency_one_tag = magic_mixer.blend(model.CreativeTag, name="agency_one_tag", agency=agency_one)
        account_tag = magic_mixer.blend(model.CreativeTag, name="account_tag", account=account)
        magic_mixer.blend(model.CreativeTag, name="agency_two_tag", agency=agency_two)

        tags = list(model.CreativeTag.objects.filter_by_agency_and_related_accounts(agency_one))
        self.assertEqual(len(tags), 2)
        self.assertEqual(sorted([tag.id for tag in tags]), sorted([agency_one_tag.id, account_tag.id]))

    def test_filter_by_account(self):
        account_one = magic_mixer.blend(core.models.Account)
        account_two = magic_mixer.blend(core.models.Account)
        account_one_tag = magic_mixer.blend(model.CreativeTag, name="account_one_tag", account=account_one)
        magic_mixer.blend(model.CreativeTag, name="account_two_tag", account=account_two)

        tags = list(model.CreativeTag.objects.filter_by_account(account_one))
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0].id, account_one_tag.id)

    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        return magic_mixer.blend(model.CreativeTag, agency=None, account=account)

    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        return magic_mixer.blend(model.CreativeTag, agency=agency, account=None)
