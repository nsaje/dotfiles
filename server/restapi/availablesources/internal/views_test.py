from django.urls import reverse

import core.features.deals
import core.models
import utils.test_helper
from restapi.common.views_base_test_case import FutureRESTAPITestCase
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer


class LegacySourceViewSetTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        utils.test_helper.remove_permissions(self.user, ["can_see_all_available_sources"])

    @staticmethod
    def source_repr(source):
        return {
            "slug": source.bidder_slug,
            "name": source.name,
            "released": source.released,
            "deprecated": source.deprecated,
        }

    def test_list(self):
        agency = magic_mixer.blend(core.models.Agency)
        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.update(None, available_sources=[sources[0], sources[1], sources[2]])

        r = self.client.get(reverse("restapi.source.internal:source_list", kwargs={"agency_id": agency.id}))
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(len(resp_json["data"]), 3)
        self.assertTrue(self.source_repr(sources[0]) in resp_json["data"])
        self.assertTrue(self.source_repr(sources[1]) in resp_json["data"])
        self.assertTrue(self.source_repr(sources[2]) in resp_json["data"])


class SourceViewSetTest(FutureRESTAPITestCase, LegacySourceViewSetTest):
    pass
