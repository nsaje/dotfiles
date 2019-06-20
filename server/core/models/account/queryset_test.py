from django.test import TestCase

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import queryset


class AccountQuerysetTestCase(TestCase):
    def test_filter_by_business(self):
        ay_zms = magic_mixer.blend(core.models.Agency)
        ay_zms.entity_tags.add(queryset.ZMS_TAG)

        acc_z1 = magic_mixer.blend(core.models.Account)
        acc_zms = magic_mixer.blend(core.models.Account, agency=ay_zms)
        acc_oen = magic_mixer.blend(core.models.Account, id=305)

        self.assertEqual(set(core.models.Account.objects.filter_by_business([])), set([acc_z1, acc_zms, acc_oen]))
        self.assertEqual(
            set(core.models.Account.objects.filter_by_business([dash.constants.Business.Z1])), set([acc_z1])
        )
        self.assertEqual(
            set(core.models.Account.objects.filter_by_business([dash.constants.Business.OEN])), set([acc_oen])
        )
        self.assertEqual(
            set(core.models.Account.objects.filter_by_business([dash.constants.Business.ZMS])), set([acc_zms])
        )
        self.assertEqual(
            set(
                core.models.Account.objects.filter_by_business(
                    [dash.constants.Business.Z1, dash.constants.Business.OEN]
                )
            ),
            set([acc_z1, acc_oen]),
        )
        self.assertEqual(
            set(
                core.models.Account.objects.filter_by_business(
                    [dash.constants.Business.ZMS, dash.constants.Business.OEN]
                )
            ),
            set([acc_zms, acc_oen]),
        )
        self.assertEqual(
            set(
                core.models.Account.objects.filter_by_business(
                    [dash.constants.Business.Z1, dash.constants.Business.ZMS]
                )
            ),
            set([acc_z1, acc_zms]),
        )
        self.assertEqual(
            set(
                core.models.Account.objects.filter_by_business(
                    [dash.constants.Business.Z1, dash.constants.Business.ZMS, dash.constants.Business.OEN]
                )
            ),
            set([acc_z1, acc_zms, acc_oen]),
        )
