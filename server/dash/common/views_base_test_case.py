from django.test import override_settings

import zemauth.models
from utils.base_test_case import BaseTestCase
from utils.base_test_case import FutureBaseTestCase


@override_settings(R1_DEMO_MODE=True)
class DASHAPITestCase(BaseTestCase):
    pass


@override_settings(R1_DEMO_MODE=True)
class FutureDASHAPITestCase(FutureBaseTestCase, DASHAPITestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.users = zemauth.models.User.objects.all()
        for user in cls.users:
            user.user_permissions.add(cls.permission)
            user.refresh_entity_permissions()
