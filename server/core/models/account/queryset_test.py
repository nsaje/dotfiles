from typing import Any

from django.test import TestCase

import core.models
import dash.constants
import zemauth.features.entity_permission.shortcuts
import zemauth.models
from utils.magic_mixer import magic_mixer

from . import model
from . import queryset


class AccountQuerySetTestCase(
    zemauth.features.entity_permission.shortcuts.HasEntityPermissionQuerySetTestCaseMixin, TestCase
):
    def test_filter_by_business(self):
        ag_zms = magic_mixer.blend(core.models.Agency)
        ag_zms.entity_tags.add(queryset.ZMS_TAG)

        ag_internal = magic_mixer.blend(core.models.Agency)
        ag_internal.entity_tags.add(queryset.INTERNAL_TAG)

        acc_oen = magic_mixer.blend(model.Account, id=305)
        acc_z1 = magic_mixer.blend(model.Account)
        acc_zms = magic_mixer.blend(model.Account, agency=ag_zms)
        acc_internal = magic_mixer.blend(model.Account, agency=ag_internal)

        self.assertEqual(set(model.Account.objects.filter_by_business([])), {acc_z1, acc_zms, acc_oen, acc_internal})
        self.assertEqual(set(model.Account.objects.filter_by_business([dash.constants.Business.Z1])), {acc_z1})
        self.assertEqual(set(model.Account.objects.filter_by_business([dash.constants.Business.OEN])), {acc_oen})
        self.assertEqual(set(model.Account.objects.filter_by_business([dash.constants.Business.ZMS])), {acc_zms})
        self.assertEqual(
            set(model.Account.objects.filter_by_business([dash.constants.Business.INTERNAL])), {acc_internal}
        )
        self.assertEqual(
            set(model.Account.objects.filter_by_business([dash.constants.Business.Z1, dash.constants.Business.OEN])),
            {acc_z1, acc_oen},
        )
        self.assertEqual(
            set(model.Account.objects.filter_by_business([dash.constants.Business.ZMS, dash.constants.Business.OEN])),
            {acc_zms, acc_oen},
        )
        self.assertEqual(
            set(model.Account.objects.filter_by_business([dash.constants.Business.Z1, dash.constants.Business.ZMS])),
            {acc_z1, acc_zms},
        )
        self.assertEqual(
            set(
                model.Account.objects.filter_by_business(
                    [dash.constants.Business.Z1, dash.constants.Business.ZMS, dash.constants.Business.OEN]
                )
            ),
            {acc_z1, acc_zms, acc_oen},
        )
        self.assertEqual(
            set(
                model.Account.objects.filter_by_business(
                    [
                        dash.constants.Business.Z1,
                        dash.constants.Business.ZMS,
                        dash.constants.Business.OEN,
                        dash.constants.Business.INTERNAL,
                    ]
                )
            ),
            {acc_z1, acc_zms, acc_oen, acc_internal},
        )
        self.assertEqual(
            set(
                model.Account.objects.filter_by_business([dash.constants.Business.Z1, dash.constants.Business.INTERNAL])
            ),
            {acc_z1, acc_internal},
        )
        self.assertEqual(
            set(
                model.Account.objects.filter_by_business(
                    [dash.constants.Business.OEN, dash.constants.Business.INTERNAL]
                )
            ),
            {acc_oen, acc_internal},
        )
        self.assertEqual(
            set(
                model.Account.objects.filter_by_business(
                    [dash.constants.Business.ZMS, dash.constants.Business.INTERNAL]
                )
            ),
            {acc_zms, acc_internal},
        )

    def _get_model_with_agency_scope(self, agency: core.models.Agency) -> Any:
        return None

    def _get_model_with_account_scope(self, account: core.models.Account) -> Any:
        return account
