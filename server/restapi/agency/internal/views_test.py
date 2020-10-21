from django.urls import reverse

import core.models
from restapi.common.views_base_test_case import RESTAPITestCase
from utils import test_helper
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class AgencyViewSetTest(RESTAPITestCase):
    def test_agency_list(self):
        agency_read_access = self.mix_agency(self.user, permissions=[Permission.READ])

        agency_no_read_access = magic_mixer.blend(core.models.Agency)
        self.mix_account(self.user, permissions=[Permission.READ], agency=agency_no_read_access)
        self.mix_account(self.user, permissions=[Permission.READ], agency=agency_no_read_access)
        self.mix_account(self.user, permissions=[Permission.READ], agency=agency_no_read_access)

        magic_mixer.cycle(5).blend(core.models.Agency)

        r = self.client.get(reverse("restapi.agency.internal:agencies_list"))
        resp_json = self.assertResponseValid(r, data_type=list)

        resp_json_ids = [int(x.get("id")) for x in resp_json["data"]]

        self.assertEqual(len(resp_json_ids), 2)
        self.assertTrue(agency_read_access.id in resp_json_ids)
        self.assertTrue(agency_no_read_access.id in resp_json_ids)

    def test_agency_list_internal_user(self):
        internal_user = magic_mixer.blend_user()
        test_helper.add_entity_permissions(internal_user, permissions=[Permission.READ], entity=None)
        self.client.force_authenticate(user=internal_user)

        agencies = magic_mixer.cycle(5).blend(core.models.Agency)

        r = self.client.get(reverse("restapi.agency.internal:agencies_list"))
        resp_json = self.assertResponseValid(r, data_type=list)

        resp_json_ids = [int(x.get("id")) for x in resp_json["data"]]
        for agency in agencies:
            self.assertTrue(agency.id in resp_json_ids)
