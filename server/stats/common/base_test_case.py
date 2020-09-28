import zemauth.models
from utils.base_test_case import BaseTestCase


class StatsTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.users = zemauth.models.User.objects.all()
        for user in cls.users:
            user.refresh_entity_permissions()
