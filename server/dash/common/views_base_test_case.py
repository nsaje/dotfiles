from django.test import override_settings

import zemauth.models
from utils.base_test_case import APITestCase
from utils.base_test_case import FutureAPITestCase


@override_settings(R1_DEMO_MODE=True)
class DASHAPITestCase(APITestCase):
    pass


@override_settings(R1_DEMO_MODE=True)
class FutureDASHAPITestCase(FutureAPITestCase, DASHAPITestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.users = zemauth.models.User.objects.all()
        for user in cls.users:
            user.user_permissions.add(cls.permission)
            user.refresh_entity_permissions()
