import core.models
from utils import test_helper
from utils.base_test_case import BaseTestCase
from utils.base_test_case import FutureBaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import nas


class LegacyNASTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.request_user_no_access = magic_mixer.blend_request_user()
        self.request_user_in_agency = magic_mixer.blend_request_user()
        self.request_user_with_permission = magic_mixer.blend_request_user()

        self.agency = self.mix_agency(self.request_user_in_agency.user, permissions=[Permission.READ])
        self.source = magic_mixer.blend(core.models.Source)

        test_helper.add_permissions(self.request_user_with_permission.user, ["can_see_all_nas_in_inventory_planning"])

    def test_should_show_source(self):
        nas.NAS_MAPPING[self.source.id] = [self.agency.id]

        self.assertFalse(nas.should_show_nas_source(self.source, self.request_user_no_access))
        self.assertTrue(nas.should_show_nas_source(self.source, self.request_user_in_agency))
        self.assertTrue(nas.should_show_nas_source(self.source, self.request_user_with_permission))


class NASTestCase(FutureBaseTestCase, LegacyNASTestCase):
    def setUp(self):
        super().setUp()
        self.request_user_no_access.user.user_permissions.add(self.permission)
        self.request_user_in_agency.user.user_permissions.add(self.permission)
        self.request_user_with_permission.user.user_permissions.add(self.permission)
