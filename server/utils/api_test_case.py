import json

from django.contrib.auth.models import ContentType
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient

import core.models
from utils import json_helper
from utils import test_helper
from utils.magic_mixer import magic_mixer


class APITestCase(TestCase):
    """
    APITestCase will be replaced with FutureAPITestCase
    after User Roles will be released.
    """

    fixtures = []
    permissions = []

    def setUp(self):
        self.client = APIClient()
        self.user = magic_mixer.blend_user(permissions=self.permissions)
        self.client.force_authenticate(user=self.user)
        self.maxDiff = None

    def assertResponseValid(self, r, status_code=200, data_type=dict):
        resp_json = json.loads(r.content)
        self.assertNotIn("errorCode", resp_json)
        self.assertEqual(r.status_code, status_code)
        self.assertIsInstance(resp_json["data"], data_type)
        return resp_json

    def assertResponseError(self, r, error_code):
        resp_json = json.loads(r.content)
        self.assertIn("errorCode", resp_json)
        self.assertEqual(resp_json["errorCode"], error_code)
        return resp_json

    @staticmethod
    def normalize(d):
        return json.loads(json.dumps(d, cls=json_helper.JSONEncoder))

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


class FutureAPITestCase(APITestCase):
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
