from django.test import TestCase
from utils.magic_mixer import magic_mixer

import core.entity


class AccountQuerySetTest(TestCase):

    def test_all_use_bcm_v2(self):
        magic_mixer.cycle(5).blend(core.entity.Account, uses_bcm_v2=True)
        self.assertTrue(core.entity.Account.objects.all().all_use_bcm_v2())

        magic_mixer.blend(core.entity.Account, uses_bcm_v2=False)
        self.assertFalse(core.entity.Account.objects.all().all_use_bcm_v2())
