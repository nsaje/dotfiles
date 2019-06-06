from django.test import TestCase

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import queryset


class AccountQuerysetTestCase(TestCase):
    def test_filter_by_business(self):
        acc_z1 = magic_mixer.blend(core.models.Account)
        acc_ligatus = magic_mixer.blend(core.models.Account)
        acc_oen = magic_mixer.blend(core.models.Account, id=305)
        acc_ligatus.entity_tags.add(queryset.LIGATUS_TAG)
        acc_ligatus.save(None)

        self.assertEqual(set(core.models.Account.objects.filter_by_business([])), set([acc_z1, acc_ligatus, acc_oen]))
        self.assertEqual(
            set(core.models.Account.objects.filter_by_business([dash.constants.Business.Z1])), set([acc_z1])
        )
        self.assertEqual(
            set(core.models.Account.objects.filter_by_business([dash.constants.Business.OEN])), set([acc_oen])
        )
        self.assertEqual(
            set(core.models.Account.objects.filter_by_business([dash.constants.Business.LIGATUS])), set([acc_ligatus])
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
                    [dash.constants.Business.LIGATUS, dash.constants.Business.OEN]
                )
            ),
            set([acc_ligatus, acc_oen]),
        )
        self.assertEqual(
            set(
                core.models.Account.objects.filter_by_business(
                    [dash.constants.Business.Z1, dash.constants.Business.LIGATUS]
                )
            ),
            set([acc_z1, acc_ligatus]),
        )
        self.assertEqual(
            set(
                core.models.Account.objects.filter_by_business(
                    [dash.constants.Business.Z1, dash.constants.Business.LIGATUS, dash.constants.Business.OEN]
                )
            ),
            set([acc_z1, acc_ligatus, acc_oen]),
        )
