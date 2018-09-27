import mock

from django.test import TestCase

from core import models
from utils.magic_mixer import magic_mixer

from . import entity_limits


class EntityLimitEnforceTest(TestCase):
    def setUp(self):
        # these accounts do not actually exist, id is only used for entity_limits config
        self.ACCOUNT = 14
        self.ACCOUNT_WITH_EXCEPTION = 13

        self.DEFAULT_LIMITS = {"AdGroup": 2}
        self.ACCOUNT_EXCEPTIONS = {"AdGroup": {self.ACCOUNT_WITH_EXCEPTION: 3}}

        self.default_limits_patcher = mock.patch("core.common.entity_limits.DEFAULT_LIMITS", self.DEFAULT_LIMITS)
        self.default_limits_patcher.start()
        self.addCleanup(self.default_limits_patcher.stop)

        self.account_exceptions_patcher = mock.patch(
            "core.common.entity_limits.ACCOUNT_EXCEPTIONS", self.ACCOUNT_EXCEPTIONS
        )
        self.account_exceptions_patcher.start()
        self.addCleanup(self.account_exceptions_patcher.stop)

    def test_under_default_limit(self):
        magic_mixer.cycle(1).blend(models.AdGroup)

        entity_limits.enforce(models.AdGroup.objects.all(), self.ACCOUNT)

    def test_under_exception_limit(self):
        magic_mixer.cycle(2).blend(models.AdGroup)

        entity_limits.enforce(models.AdGroup.objects.all(), self.ACCOUNT_WITH_EXCEPTION)

    def test_over_default_limit(self):
        magic_mixer.cycle(2).blend(models.AdGroup)

        with self.assertRaises(entity_limits.EntityLimitExceeded):
            entity_limits.enforce(models.AdGroup.objects.all(), self.ACCOUNT)

    def test_over_exception_limit(self):
        magic_mixer.cycle(3).blend(models.AdGroup)

        with self.assertRaises(entity_limits.EntityLimitExceeded):
            entity_limits.enforce(models.AdGroup.objects.all(), self.ACCOUNT_WITH_EXCEPTION)

    def test_over_default_limit_create_count(self):
        magic_mixer.cycle(1).blend(models.AdGroup)

        with self.assertRaises(entity_limits.EntityLimitExceeded):
            entity_limits.enforce(models.AdGroup.objects.all(), self.ACCOUNT, create_count=2)
