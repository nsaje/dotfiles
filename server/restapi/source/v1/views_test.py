from django.urls import reverse

import core
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class SourceViewSetTest(RESTAPITest):
    def setUp(self):
        super(SourceViewSetTest, self).setUp()
        self.user.user_permissions.clear()
        self.agency = magic_mixer.blend(core.models.Agency, users=[self.user])
        self.sources = magic_mixer.cycle(5).blend(core.models.Source, released=True, deprecated=False)
        self.sources_not_released = magic_mixer.cycle(2).blend(core.models.Source, released=False, deprecated=False)
        self.sources_deprecated = magic_mixer.cycle(2).blend(core.models.Source, released=False, deprecated=True)

    def test_list_with_no_filter(self):
        r = self.client.get(reverse("restapi.source.v1:sources_list"))
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 5)

    def test_list_with_limit(self):
        self.user.user_permissions.clear()
        r = self.client.get(reverse("restapi.source.v1:sources_list"), {"limit": 2})

        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 2)

    def test_list_with_offset(self):
        self.user.user_permissions.clear()
        r = self.client.get(reverse("restapi.source.v1:sources_list"), {"offset": 2})

        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 3)

    def test_list_with_limit_and_offset(self):
        self.user.user_permissions.clear()
        r = self.client.get(reverse("restapi.source.v1:sources_list"), {"limit": 2}, {"offset": 2})

        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 2)

    def test_list_with_pagination(self):
        self.user.user_permissions.clear()
        r = self.client.get(reverse("restapi.source.v1:sources_list"))
        r_paginated = self.client.get(reverse("restapi.source.v1:sources_list"), {"limit": 2, "offset": 2})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(
            sorted(sorted(entry.items()) for entry in resp_json["data"][2:4]),
            sorted(sorted(entry.items()) for entry in resp_json_paginated["data"]),
        )
