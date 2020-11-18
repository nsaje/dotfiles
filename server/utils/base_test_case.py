from contextlib import contextmanager
from unittest import mock

from django.test import TestCase

import core.models
from utils import test_helper
from utils.exc import MultipleValidationError
from utils.magic_mixer import magic_mixer


class BaseTestCase(TestCase):
    fixtures = []
    permissions = []

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

    def setUp(self):
        self.user = magic_mixer.blend_user(permissions=self.permissions)

    def mix_agency(self, user=None, permissions=[], **kwargs):
        agency = magic_mixer.blend(core.models.Agency, **kwargs)
        if user is not None:
            test_helper.add_entity_permissions(user, permissions, agency)
        return agency

    def mix_account(self, user=None, permissions=[], **kwargs):
        account = magic_mixer.blend(core.models.Account, **kwargs)
        if user is not None:
            test_helper.add_entity_permissions(user, permissions, account)
        return account

    @contextmanager
    def assert_multiple_validation_error(self, exceptions):
        try:
            yield
        except MultipleValidationError as e:
            excs = exceptions.copy()
            for err in e.errors:
                self.assertIn(type(err), excs)
                excs.remove(type(err))
            if len(excs) > 0:
                raise AssertionError(f"{excs} not raised")
        else:
            raise AssertionError(f"{exceptions} not raised")

    def prepare_threadpoolexecutor_mock(self, threadpoolexecutor):
        # NOTE: Code ran in a separate thread would use a separate transaction which would make testing hard. In order
        # to avoid this we use sequential map instead of threads to produce results.
        def _eager_map(fun, iter_):
            return list(map(fun, iter_))

        patcher = mock.patch(threadpoolexecutor)
        mock_threadpoolexecutor = patcher.start()

        mock_threadpoolexecutor.return_value.__enter__.return_value.map = _eager_map
        self.addCleanup(patcher.stop)
