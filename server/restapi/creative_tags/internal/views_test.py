from django.urls import reverse

import core.models
import core.models.tags.creative
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CreativeTagViewSetTestCase(RESTAPITestCase):
    def test_list(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.blend(core.models.tags.creative.CreativeTag, agency=agency, name="tag_one")
        magic_mixer.blend(core.models.tags.creative.CreativeTag, agency=agency, name="tag_two")
        magic_mixer.blend(core.models.tags.creative.CreativeTag, agency=agency, name="tag_three")

        r = self.client.get(
            reverse("restapi.creative_tags.internal:creative_tag_list"),
            {"agencyId": agency.id, "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 3)
        self.assertCountEqual(resp_json["data"], ["tag_one", "tag_two", "tag_three"])

    def test_list_pagination(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(20).blend(core.models.tags.creative.CreativeTag, agency=agency)

        r = self.client.get(
            reverse("restapi.creative_tags.internal:creative_tag_list"),
            {"agencyId": agency.id, "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["next"])

        r_paginated = self.client.get(
            reverse("restapi.creative_tags.internal:creative_tag_list"),
            {"agencyId": agency.id, "offset": 10, "limit": 10},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)

        self.assertEqual(resp_json_paginated["count"], 20)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNone(resp_json_paginated["next"])

        self.assertEqual(resp_json["data"][10:20], resp_json_paginated["data"])

    def test_list_with_agency(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account1 = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = self.mix_account(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(3).blend(core.models.tags.creative.CreativeTag, agency=agency)
        magic_mixer.cycle(4).blend(core.models.tags.creative.CreativeTag, account=account1)
        magic_mixer.cycle(5).blend(core.models.tags.creative.CreativeTag, account=account2)

        r = self.client.get(
            reverse("restapi.creative_tags.internal:creative_tag_list"),
            {"agencyId": agency.id, "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 7)

    def test_list_with_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account1 = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = magic_mixer.blend(core.models.Account, agency=agency)
        magic_mixer.cycle(3).blend(core.models.tags.creative.CreativeTag, agency=agency)
        magic_mixer.cycle(4).blend(core.models.tags.creative.CreativeTag, account=account1)
        magic_mixer.cycle(5).blend(core.models.tags.creative.CreativeTag, account=account2)

        r = self.client.get(
            reverse("restapi.creative_tags.internal:creative_tag_list"),
            {"accountId": account1.id, "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 7)

    def test_filter_by_keyword(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.blend(core.models.tags.creative.CreativeTag, agency=agency, name="tag_one")
        magic_mixer.blend(core.models.tags.creative.CreativeTag, agency=agency, name="tag_two")
        magic_mixer.blend(core.models.tags.creative.CreativeTag, agency=agency, name="tag_three")
        magic_mixer.blend(core.models.tags.creative.CreativeTag, agency=agency, name="test")

        r = self.client.get(
            reverse("restapi.creative_tags.internal:creative_tag_list"),
            {"agencyId": agency.id, "keyword": "tag", "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 3)
        self.assertCountEqual(resp_json["data"], ["tag_one", "tag_two", "tag_three"])
