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

    def test_list(self):
        agency = magic_mixer.blend(core.models.Agency)
        sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        agency.update(None, available_sources=[sources[0], sources[1], sources[2]])

        r = self.client.get(reverse("restapi.source.internal:source_list", kwargs={"agency_id": agency.id}))
        resp_json = self.assertResponseValid(r, data_type=list)

        self.assertEqual(
            resp_json["data"],
            [
                {
                    "slug": sources[0].bidder_slug,
                    "name": sources[0].name,
                    "released": sources[0].released,
                    "deprecated": sources[0].deprecated,
                },
                {
                    "slug": sources[1].bidder_slug,
                    "name": sources[1].name,
                    "released": sources[1].released,
                    "deprecated": sources[1].deprecated,
                },
                {
                    "slug": sources[2].bidder_slug,
                    "name": sources[2].name,
                    "released": sources[2].released,
                    "deprecated": sources[2].deprecated,
                },
            ],
        )


class SourceViewSetTest(FutureRESTAPITestCase, LegacySourceViewSetTest):
    pass
