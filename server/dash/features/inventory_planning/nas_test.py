from django.test import TestCase

import core.models
from utils import test_helper
from utils.magic_mixer import magic_mixer

from . import nas


class NASTest(TestCase):
    def test_should_show_source(self):
        request_user_no_access = magic_mixer.blend_request_user()
        request_user_in_agency = magic_mixer.blend_request_user()
        request_user_with_permission = magic_mixer.blend_request_user()
        agency = magic_mixer.blend(core.models.Agency)
        source = magic_mixer.blend(core.models.Source)

        agency.users.add(request_user_in_agency.user)
        test_helper.add_permissions(request_user_with_permission.user, ["can_see_all_nas_in_inventory_planning"])

        nas.NAS_MAPPING[source.id] = [agency.id]

        self.assertFalse(nas.should_show_nas_source(source, request_user_no_access))
        self.assertTrue(nas.should_show_nas_source(source, request_user_in_agency))
        self.assertTrue(nas.should_show_nas_source(source, request_user_with_permission))
