from django.urls import reverse

import core.features.creatives
import core.models
import dash.constants
import utils.test_helper
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CreativeViewSetTestCase(RESTAPITestCase):
    def test_get(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        creative = magic_mixer.blend(core.features.creatives.Creative, account=account)

        r = self.client.get(reverse("restapi.creatives.internal:creative_details", kwargs={"creative_id": creative.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(creative.id))

    def test_get_no_access(self):
        account = magic_mixer.blend(core.models.Account)
        creative = magic_mixer.blend(core.features.creatives.Creative, account=account)

        r = self.client.get(reverse("restapi.creatives.internal:creative_details", kwargs={"creative_id": creative.id}))
        self.assertResponseError(r, "MissingDataError")

    def test_get_no_permission(self):
        utils.test_helper.remove_permissions(self.user, ["can_see_creative_library"])

        account = self.mix_account(self.user, permissions=[Permission.READ])
        creative = magic_mixer.blend(core.features.creatives.Creative, account=account)

        r = self.client.get(reverse("restapi.creatives.internal:creative_details", kwargs={"creative_id": creative.id}))
        self.assertEqual(r.status_code, 403)
        resp_json = self.assertResponseError(r, "PermissionDenied")
        self.assertEqual(
            resp_json,
            {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."},
        )

    def test_get_with_tags(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        creative = magic_mixer.blend(core.features.creatives.Creative, account=account)
        tag_one = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_one", account=account)
        tag_two = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_two", account=account)
        creative.tags = [tag_one, tag_two]
        creative.save(None)

        r = self.client.get(reverse("restapi.creatives.internal:creative_details", kwargs={"creative_id": creative.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(creative.id))
        self.assertEqual(resp_json["data"]["tags"], ["tag_one", "tag_two"])

    def test_list_pagination(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.cycle(20).blend(core.features.creatives.Creative, agency=agency)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"), {"agencyId": agency.id, "offset": 0, "limit": 20}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["next"])

        r_paginated = self.client.get(
            reverse("restapi.creatives.internal:creative_list"), {"agencyId": agency.id, "offset": 10, "limit": 10}
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
        magic_mixer.cycle(3).blend(core.features.creatives.Creative, agency=agency)
        magic_mixer.cycle(4).blend(core.features.creatives.Creative, account=account1)
        magic_mixer.cycle(5).blend(core.features.creatives.Creative, account=account2)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"), {"agencyId": agency.id, "offset": 0, "limit": 20}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 7)

    def test_list_with_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account1 = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = magic_mixer.blend(core.models.Account, agency=agency)
        magic_mixer.cycle(3).blend(core.features.creatives.Creative, agency=agency)
        magic_mixer.cycle(4).blend(core.features.creatives.Creative, account=account1)
        magic_mixer.cycle(5).blend(core.features.creatives.Creative, account=account2)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"), {"accountId": account1.id, "offset": 0, "limit": 20}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 7)

    def test_filter_by_keyword(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.blend(core.features.creatives.Creative, agency=agency, url="http://zemanta.com/")
        magic_mixer.blend(core.features.creatives.Creative, agency=agency, title="Ad by zemanta")
        magic_mixer.blend(core.features.creatives.Creative, agency=agency, description="Ad by zemanta DSP")
        magic_mixer.blend(core.features.creatives.Creative, agency=agency)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"),
            {"agencyId": agency.id, "keyword": "zem", "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 3)

    def test_filter_by_creative_type(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        magic_mixer.blend(core.features.creatives.Creative, agency=agency, type=dash.constants.AdType.CONTENT)
        magic_mixer.blend(core.features.creatives.Creative, agency=agency, type=dash.constants.AdType.AD_TAG)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"),
            {
                "agencyId": agency.id,
                "creativeType": dash.constants.AdType.get_name(dash.constants.AdType.CONTENT),
                "offset": 0,
                "limit": 20,
            },
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 1)

    def test_filter_by_tags(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        creative = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        tag_one = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_one", agency=agency)
        creative.tags = [tag_one]
        creative.save(None)
        tag_two = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_two", agency=agency)
        creative2 = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        creative2.tags = [tag_two]
        creative2.save(None)
        tag_three = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_three", agency=agency)
        creative3 = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        creative3.tags = [tag_three]
        creative3.save(None)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"),
            {"agencyId": agency.id, "tags": "tag_one,tag_two", "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 2)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"),
            {"agencyId": agency.id, "tags": "tag_three", "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 1)

    def test_filter_by_invalid_tags(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        creative = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        tag_one = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_one", agency=agency)
        creative.tags = [tag_one]
        creative.save(None)
        tag_two = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_two", agency=agency)
        creative2 = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        creative2.tags = [tag_two]
        creative2.save(None)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"),
            {"agencyId": agency.id, "tags": "invalid", "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn("Invalid tags", resp_json["details"]["tags"])

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"),
            {"agencyId": agency.id, "tags": "<div class='test'></div>", "offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIn("HTML tags are not allowed", resp_json["details"]["tags"])

    def test_list_invalid_params(self):
        r = self.client.get(
            reverse("restapi.creatives.internal:creative_list"),
            {
                "agencyId": "NON-NUMERICAL",
                "accountId": "NON-NUMERICAL",
                "offset": "NON-NUMERICAL",
                "limit": "NON-NUMERICAL",
            },
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            {
                "agencyId": ["Invalid format"],
                "accountId": ["Invalid format"],
                "offset": ["Invalid format"],
                "limit": ["Invalid format"],
            },
            resp_json["details"],
        )
