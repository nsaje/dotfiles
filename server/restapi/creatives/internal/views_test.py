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
        creative.tags.set([tag_one, tag_two])
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
        creative.tags.set([tag_one])
        creative.save(None)
        tag_two = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_two", agency=agency)
        creative2 = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        creative2.tags.set([tag_two])
        creative2.save(None)
        tag_three = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_three", agency=agency)
        creative3 = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        creative3.tags.set([tag_three])
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
        creative.tags.set([tag_one])
        creative.save(None)
        tag_two = magic_mixer.blend(core.models.tags.CreativeTag, name="tag_two", agency=agency)
        creative2 = magic_mixer.blend(core.features.creatives.Creative, agency=agency)
        creative2.tags.set([tag_two])
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


class CreativeBatchViewSetTestCase(RESTAPITestCase):
    def setUp(self):
        super(CreativeBatchViewSetTestCase, self).setUp()
        self.agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])

    def test_validate_empty(self):
        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_validate"))
        self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {"name": "test_batch", "agencyId": self.agency.id}
        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_validate"), data=data, format="json")
        self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {"name": None, "agencyId": self.agency.id}
        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_validate"), data=data, format="json")
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be null.", r["details"]["name"][0])

    def test_post_for_agency(self):
        data = {"name": "test_batch", "agencyId": self.agency.id}

        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_list"), data=data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertEqual(resp_json["data"]["agencyId"], str(self.agency.id))
        self.assertIsNone(resp_json["data"]["accountId"])

    def test_post_for_account(self):
        data = {"name": "test_batch", "accountId": self.account.id}

        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_list"), data=data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertIsNone(resp_json["data"]["agencyId"])
        self.assertEqual(resp_json["data"]["accountId"], str(self.account.id))

    def test_post_name(self):
        data = {"name": "test_batch", "agencyId": self.agency.id}

        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_list"), data=data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual(resp_json["data"]["name"], "test_batch")

    def test_post_tags(self):
        tags = ["tag_one", "tag_two", "tag_three"]
        data = {"name": "test_batch", "agencyId": self.agency.id, "tags": tags}

        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_list"), data=data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertIsNotNone(resp_json["data"]["id"])
        self.assertCountEqual(resp_json["data"]["tags"], tags)

    def test_put_name(self):
        batch = magic_mixer.blend(core.features.creatives.CreativeBatch, name="before", agency=self.agency)
        self.assertEqual(batch.name, "before")

        data = {"name": "after"}

        r = self.client.put(
            reverse("restapi.creatives.internal:creative_batch_details", kwargs={"batch_id": batch.id}),
            data=data,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=200)

        self.assertEqual(resp_json["data"]["name"], "after")

        batch.refresh_from_db()
        self.assertEqual(batch.name, "after")

    def test_put_tags(self):
        before_tags = ["tag_one", "tag_two"]
        batch = magic_mixer.blend(core.features.creatives.CreativeBatch, name="before", agency=self.agency)
        batch.set_creative_tags(None, before_tags)

        self.assertEqual([x.name for x in batch.get_creative_tags()], before_tags)

        after_tags = ["tag_three"]
        data = {"tags": after_tags}

        r = self.client.put(
            reverse("restapi.creatives.internal:creative_batch_details", kwargs={"batch_id": batch.id}),
            data=data,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=200)

        self.assertCountEqual(resp_json["data"]["tags"], after_tags)

        batch.refresh_from_db()
        self.assertEqual([x.name for x in batch.get_creative_tags()], after_tags)
