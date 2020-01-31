from django.urls import reverse

import core.models
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AgencyViewSetTest(RESTAPITest):
    def test_agency_list(self):
        agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        magic_mixer.cycle(5).blend(core.models.Agency)

        r = self.client.get(reverse("restapi.agency.internal:agencies_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertGreater(len(resp_json["data"]), 1)
        self.assertEqual(resp_json["data"][0]["name"], agency.name)
