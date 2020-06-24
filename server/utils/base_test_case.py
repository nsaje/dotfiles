from django.contrib.auth.models import ContentType
from django.contrib.auth.models import Permission
from django.test import TestCase

import core.models
from utils import test_helper
from utils.magic_mixer import magic_mixer


class BaseTestCase(TestCase):
    fixtures = []
    permissions = []

    def setUp(self):
        self.user = magic_mixer.blend_user(permissions=self.permissions)

    def mix_agency(self, user=None, permissions=[], **kwargs):
        agency = magic_mixer.blend(core.models.Agency, **kwargs)
        if user is not None:
            agency.users.add(user)
        return agency

    def mix_account(self, user=None, permissions=[], **kwargs):
        account = magic_mixer.blend(core.models.Account, **kwargs)
        if user is not None:
            account.users.add(user)
        return account


class FutureBaseTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.content_type = magic_mixer.blend(ContentType, app_label="zemauth")
        cls.permission = magic_mixer.blend(
            Permission, codename="fea_use_entity_permission", content_type=cls.content_type
        )

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        cls.permission.delete()
        cls.content_type.delete()

    def setUp(self):
        super().setUp()
        if not hasattr(self, "user"):
            return
        self.user.user_permissions.add(self.permission)

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
