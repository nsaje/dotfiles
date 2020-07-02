import zemauth.models
from utils.base_test_case import BaseTestCase
from utils.base_test_case import FutureBaseTestCase


class CoreTestCase(BaseTestCase):
    pass


class FutureCoreTestCase(FutureBaseTestCase, CoreTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.users = zemauth.models.User.objects.all()
        for user in cls.users:
            user.user_permissions.add(cls.permission)
            user.refresh_entity_permissions()