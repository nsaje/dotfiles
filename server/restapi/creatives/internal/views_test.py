import mock
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from parameterized import param
from parameterized import parameterized

import core.features.creatives
import core.features.videoassets.models
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

    def test_get_on_account(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        batch = magic_mixer.blend(core.features.creatives.CreativeBatch, account=account)

        r = self.client.get(reverse("restapi.creatives.internal:creative_batch_details", kwargs={"batch_id": batch.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(batch.id))

    def test_get_on_agency(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        batch = magic_mixer.blend(core.features.creatives.CreativeBatch, agency=agency)

        r = self.client.get(reverse("restapi.creatives.internal:creative_batch_details", kwargs={"batch_id": batch.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(batch.id))

    def test_validate_empty(self):
        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_validate"))
        self.assertResponseValid(r, data_type=type(None))

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

    @mock.patch("restapi.creatives.internal.helpers.generate_batch_name")
    def test_post_without_name(self, mock_generate_batch_name):
        mock_generate_batch_name.return_value = "02/03/2021 10:25 AM"

        data = {"agencyId": self.agency.id}

        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_list"), data=data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual(resp_json["data"]["name"], "02/03/2021 10:25 AM")

    def test_post_mode(self):
        data = {
            "mode": dash.constants.CreativeBatchMode.get_name(dash.constants.CreativeBatchMode.EDIT),
            "agencyId": self.agency.id,
        }

        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_list"), data=data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual(
            resp_json["data"]["mode"], dash.constants.CreativeBatchMode.get_name(dash.constants.CreativeBatchMode.EDIT)
        )

    def test_post_type(self):
        data = {
            "type": dash.constants.CreativeBatchType.get_name(dash.constants.CreativeBatchType.VIDEO),
            "agencyId": self.agency.id,
        }

        r = self.client.post(reverse("restapi.creatives.internal:creative_batch_list"), data=data, format="json")
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertEqual(
            resp_json["data"]["type"], dash.constants.CreativeBatchType.get_name(dash.constants.CreativeBatchType.VIDEO)
        )

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


class CreativeCandidateViewSet(RESTAPITestCase):
    PUT_TYPE_VALIDATION_TEST_CASES = [
        param("put_blank", value=""),
        param("put_invalid", value="invalid"),
    ]

    PUT_VALIDATION_TEST_CASES = [
        param("put_brand_url_blank", field_name="url", field_value=""),
        param("put_brand_url_invalid", field_name="url", field_value="invalid_url"),
        param("put_title_blank", field_name="title", field_value=""),
        param("put_display_url_blank", field_name="displayUrl", field_value=""),
        param("put_display_url_invalid", field_name="displayUrl", field_value="invalid_url"),
    ]

    PUT_NATIVE_VALIDATION_TEST_CASES = PUT_VALIDATION_TEST_CASES + [
        param("put_brand_name_blank", field_name="brandName", field_value=""),
        param("put_description_blank", field_name="description", field_value=""),
        param("put_call_to_action_blank", field_name="callToAction", field_value=""),
        param("put_image_crop_blank", field_name="imageCrop", field_value=""),
        param(
            "put_image_invalid",
            field_name="image",
            field_value=SimpleUploadedFile(
                name="test.csv", content=open("./dash/test_files/test.csv", "rb").read(), content_type="text/csv"
            ),
        ),
        param(
            "put_icon_invalid",
            field_name="icon",
            field_value=SimpleUploadedFile(
                name="test.csv", content=open("./dash/test_files/test.csv", "rb").read(), content_type="text/csv"
            ),
        ),
    ]

    PUT_VIDEO_VALIDATION_TEST_CASES = PUT_NATIVE_VALIDATION_TEST_CASES + [
        param("put_video_asset_id_blank", field_name="videoAssetId", field_value=""),
    ]

    IMAGE_VALIDATION_TEST_CASES = PUT_VALIDATION_TEST_CASES + [
        param(
            "put_image_invalid",
            field_name="image",
            field_value=SimpleUploadedFile(
                name="test.csv", content=open("./dash/test_files/test.csv", "rb").read(), content_type="text/csv"
            ),
        ),
    ]

    AD_TAG_VALIDATION_TEST_CASES = PUT_VALIDATION_TEST_CASES + [
        param("put_ad_tag_blank", field_name="adTag", field_value=""),
        param("put_image_width_blank", field_name="imageWidth", field_value=""),
        param("put_image_width_invalid", field_name="imageWidth", field_value="invalid_width"),
        param("put_image_width_zero", field_name="imageWidth", field_value=0),
        param("put_image_height_blank", field_name="imageHeight", field_value=""),
        param("put_image_height_invalid", field_name="imageHeight", field_value="invalid_height"),
        param("put_image_height_zero", field_name="imageHeight", field_value=0),
    ]

    @classmethod
    def get_candidate_representation(
        cls,
        *,
        type=None,
        url=None,
        title=None,
        display_url=None,
        brand_name=None,
        description=None,
        call_to_action=None,
        image_crop=None,
        image_url=None,
        icon_url=None,
        video_asset_id=None,
        ad_tag=None,
        image_width=None,
        image_height=None,
    ):
        representation = {
            "type": dash.constants.AdType.get_name(type) if type is not None else None,
            "url": url,
            "title": title,
            "displayUrl": display_url,
            "brandName": brand_name,
            "description": description,
            "callToAction": call_to_action,
            "imageCrop": image_crop,
            "imageUrl": image_url,
            "iconUrl": icon_url,
            "videoAssetId": video_asset_id,
            "adTag": ad_tag,
            "imageWidth": image_width,
            "imageHeight": image_height,
        }

        # (multipart/form-data) doesn't support None values
        res = cls.normalize(representation)
        return {k: v for k, v in res.items() if v is not None}

    def setUp(self):
        super(CreativeCandidateViewSet, self).setUp()
        self.agency = self.mix_agency(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.batch = magic_mixer.blend(core.features.creatives.CreativeBatch, agency=self.agency)

    def test_list(self):
        magic_mixer.cycle(5).blend(core.features.creatives.CreativeCandidate, batch=self.batch)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_candidate_list", kwargs={"batch_id": self.batch.id})
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 5)

    def test_list_pagination(self):
        magic_mixer.cycle(20).blend(core.features.creatives.CreativeCandidate, batch=self.batch)

        r = self.client.get(
            reverse("restapi.creatives.internal:creative_candidate_list", kwargs={"batch_id": self.batch.id}),
            {"offset": 0, "limit": 20},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(resp_json["count"], 20)
        self.assertIsNone(resp_json["next"])

        r_paginated = self.client.get(
            reverse("restapi.creatives.internal:creative_candidate_list", kwargs={"batch_id": self.batch.id}),
            {"offset": 10, "limit": 10},
        )
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)

        self.assertEqual(resp_json_paginated["count"], 20)
        self.assertIsNotNone(resp_json_paginated["previous"])
        self.assertIsNone(resp_json_paginated["next"])

        self.assertEqual(resp_json["data"][10:20], resp_json_paginated["data"])

    def test_get(self):
        candidate = magic_mixer.blend(
            core.features.creatives.CreativeCandidate,
            batch=self.batch,
        )

        r = self.client.get(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": self.batch.id, "candidate_id": candidate.id},
            )
        )
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(candidate.id))

    def test_post(self):
        r = self.client.post(
            reverse("restapi.creatives.internal:creative_candidate_list", kwargs={"batch_id": self.batch.id}),
            data={},
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)

        self.assertIsNotNone(resp_json["data"]["id"])
        candidate = core.features.creatives.CreativeCandidate.objects.get(pk=resp_json["data"]["id"])
        self.assertEqual(candidate.batch_id, self.batch.id)

    def test_post_no_access(self):
        agency = magic_mixer.blend(core.models.Agency)
        batch = magic_mixer.blend(core.features.creatives.CreativeBatch, agency=agency)

        r = self.client.post(
            reverse("restapi.creatives.internal:creative_candidate_list", kwargs={"batch_id": batch.id}),
            data={},
            format="json",
        )
        self.assertResponseError(r, "MissingDataError")

    def test_post_no_permission(self):
        utils.test_helper.remove_permissions(self.user, ["can_see_creative_library"])

        batch = magic_mixer.blend(core.features.creatives.CreativeBatch, agency=self.agency)

        r = self.client.post(
            reverse("restapi.creatives.internal:creative_candidate_list", kwargs={"batch_id": batch.id}),
            data={},
            format="json",
        )

        self.assertEqual(r.status_code, 403)
        resp_json = self.assertResponseError(r, "PermissionDenied")
        self.assertEqual(
            resp_json,
            {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."},
        )

    def test_put_no_type(self):
        candidate = magic_mixer.blend(
            core.features.creatives.CreativeCandidate,
            batch=self.batch,
        )

        r = self.client.put(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": self.batch.id, "candidate_id": candidate.id},
            ),
            data={},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIsNotNone(resp_json["details"]["type"][0])

    @parameterized.expand(PUT_TYPE_VALIDATION_TEST_CASES)
    def test_put_type_with_validation(self, _, *, value):
        candidate = magic_mixer.blend(
            core.features.creatives.CreativeCandidate,
            batch=self.batch,
        )

        put_data = {"type": value}
        r = self.client.put(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": self.batch.id, "candidate_id": candidate.id},
            ),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIsNotNone(resp_json["details"]["type"][0])

    def test_put_tags(self):
        before_tags = ["tag_one", "tag_two"]
        candidate = magic_mixer.blend(
            core.features.creatives.CreativeCandidate,
            batch=self.batch,
        )
        candidate.set_creative_tags(None, before_tags)

        self.assertEqual([x.name for x in candidate.get_creative_tags()], before_tags)

        after_tags = ["tag_three"]
        data = {"type": dash.constants.AdType.get_name(dash.constants.AdType.CONTENT), "tags": after_tags}

        r = self.client.put(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": self.batch.id, "candidate_id": candidate.id},
            ),
            data=data,
            format="json",
        )
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=200)

        self.assertCountEqual(resp_json["data"]["tags"], after_tags)

        candidate.refresh_from_db()
        self.assertEqual([x.name for x in candidate.get_creative_tags()], after_tags)

    @parameterized.expand(PUT_NATIVE_VALIDATION_TEST_CASES)
    def test_put_native_with_validation(self, _, *, field_name, field_value):
        with mock.patch("dash.image_helper.upload_image_to_s3") as mock_upload_image_to_s3:
            mock_upload_image_to_s3.return_value = "http://example.com/path/to/image"

            batch = magic_mixer.blend(
                core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.NATIVE
            )
            candidate = magic_mixer.blend(
                core.features.creatives.CreativeCandidate,
                batch=batch,
                type=dash.constants.AdType.CONTENT,
            )

            put_data = self._get_native_representation()
            put_data["image"] = SimpleUploadedFile(
                name="test.jpg", content=open("./dash/test_files/test.jpg", "rb").read(), content_type="image/jpg"
            )
            put_data["icon"] = SimpleUploadedFile(
                name="test.jpg", content=open("./dash/test_files/test.jpg", "rb").read(), content_type="image/jpg"
            )

            r = self.client.put(
                reverse(
                    "restapi.creatives.internal:creative_candidate_details",
                    kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
                ),
                data=put_data,
            )
            self.assertResponseValid(r, data_type=dict, status_code=200)
            # TODO (msuber): add db validation

            put_data[field_name] = field_value

            r = self.client.put(
                reverse(
                    "restapi.creatives.internal:creative_candidate_details",
                    kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
                ),
                data=put_data,
            )
            resp_json = self.assertResponseError(r, "ValidationError")
            self.assertIsNotNone(resp_json["details"][field_name][0])

    @parameterized.expand(PUT_VIDEO_VALIDATION_TEST_CASES)
    def test_put_video_with_validation(self, _, *, field_name, field_value):
        with mock.patch("dash.image_helper.upload_image_to_s3") as mock_upload_image_to_s3:
            mock_upload_image_to_s3.return_value = "http://example.com/path/to/image"

            batch = magic_mixer.blend(
                core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.VIDEO
            )
            candidate = magic_mixer.blend(
                core.features.creatives.CreativeCandidate,
                batch=batch,
                type=dash.constants.AdType.VIDEO,
            )
            video_asset = magic_mixer.blend(core.features.videoassets.models.VideoAsset)

            put_data = self._get_video_representation(video_asset_id=video_asset.id)
            put_data["image"] = SimpleUploadedFile(
                name="test.jpg", content=open("./dash/test_files/test.jpg", "rb").read(), content_type="image/jpg"
            )
            put_data["icon"] = SimpleUploadedFile(
                name="test.jpg", content=open("./dash/test_files/test.jpg", "rb").read(), content_type="image/jpg"
            )

            r = self.client.put(
                reverse(
                    "restapi.creatives.internal:creative_candidate_details",
                    kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
                ),
                data=put_data,
            )
            self.assertResponseValid(r, data_type=dict, status_code=200)
            # TODO (msuber): add db validation

            put_data[field_name] = field_value

            r = self.client.put(
                reverse(
                    "restapi.creatives.internal:creative_candidate_details",
                    kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
                ),
                data=put_data,
            )
            resp_json = self.assertResponseError(r, "ValidationError")
            self.assertIsNotNone(resp_json["details"][field_name][0])

    @parameterized.expand(IMAGE_VALIDATION_TEST_CASES)
    def test_put_image_with_validation(self, _, *, field_name, field_value):
        with mock.patch("dash.image_helper.upload_image_to_s3") as mock_upload_image_to_s3:
            mock_upload_image_to_s3.return_value = "http://example.com/path/to/image"

            batch = magic_mixer.blend(
                core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.DISPLAY
            )
            candidate = magic_mixer.blend(
                core.features.creatives.CreativeCandidate,
                batch=batch,
                type=dash.constants.AdType.IMAGE,
            )

            put_data = self._get_image_representation()
            put_data["image"] = SimpleUploadedFile(
                name="test.jpg", content=open("./dash/test_files/test.jpg", "rb").read(), content_type="image/jpg"
            )

            r = self.client.put(
                reverse(
                    "restapi.creatives.internal:creative_candidate_details",
                    kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
                ),
                data=put_data,
            )
            self.assertResponseValid(r, data_type=dict, status_code=200)
            # TODO (msuber): add db validation

            put_data[field_name] = field_value

            r = self.client.put(
                reverse(
                    "restapi.creatives.internal:creative_candidate_details",
                    kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
                ),
                data=put_data,
            )
            resp_json = self.assertResponseError(r, "ValidationError")
            self.assertIsNotNone(resp_json["details"][field_name][0])

    @parameterized.expand(AD_TAG_VALIDATION_TEST_CASES)
    def test_put_ad_tag_with_validation(self, _, *, field_name, field_value):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.DISPLAY
        )
        candidate = magic_mixer.blend(
            core.features.creatives.CreativeCandidate,
            batch=batch,
            type=dash.constants.AdType.AD_TAG,
        )

        put_data = self._get_ad_tag_representation(
            ad_tag="My ad tag",
            image_width=dash.constants.DisplayAdSize.BANNER[0],
            image_height=dash.constants.DisplayAdSize.BANNER[1],
        )

        r = self.client.put(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
            ),
            data=put_data,
        )
        self.assertResponseValid(r, data_type=dict, status_code=200)
        # TODO (msuber): add db validation

        put_data[field_name] = field_value

        r = self.client.put(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
            ),
            data=put_data,
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIsNotNone(resp_json["details"][field_name][0])

    def test_put_ad_tag_with_invalid_ad_size(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.DISPLAY
        )
        candidate = magic_mixer.blend(
            core.features.creatives.CreativeCandidate,
            batch=batch,
            type=dash.constants.AdType.AD_TAG,
        )

        put_data = self._get_ad_tag_representation(
            ad_tag="My ad tag",
            image_width=dash.constants.DisplayAdSize.BANNER[0],
            image_height=dash.constants.DisplayAdSize.BANNER[1],
        )

        r = self.client.put(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
            ),
            data=put_data,
        )
        self.assertResponseValid(r, data_type=dict, status_code=200)

        put_data["imageWidth"] = dash.constants.DisplayAdSize.BANNER[0]
        put_data["imageHeight"] = dash.constants.DisplayAdSize.PORTRAIT[1]

        r = self.client.put(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
            ),
            data=put_data,
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertIsNotNone(resp_json["details"]["nonFieldErrors"][0])

    def test_delete(self):
        batch = magic_mixer.blend(
            core.features.creatives.CreativeBatch, agency=self.agency, type=dash.constants.CreativeBatchType.NATIVE
        )
        candidate = magic_mixer.blend(
            core.features.creatives.CreativeCandidate,
            batch=batch,
            type=dash.constants.AdType.CONTENT,
        )

        self.assertIsNotNone(core.features.creatives.CreativeCandidate.objects.filter(pk=candidate.id).first())

        r = self.client.delete(
            reverse(
                "restapi.creatives.internal:creative_candidate_details",
                kwargs={"batch_id": batch.id, "candidate_id": candidate.id},
            ),
        )
        self.assertEqual(r.status_code, 204)
        self.assertIsNone(core.features.creatives.CreativeCandidate.objects.filter(pk=candidate.id).first())

    def _get_native_representation(
        self,
        *,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        brand_name="My brand",
        description="My description",
        call_to_action="Read more...",
        image_crop="center",
        image_url=None,
        icon_url=None,
    ):
        return self.get_candidate_representation(
            type=dash.constants.AdType.CONTENT,
            url=url,
            title=title,
            display_url=display_url,
            brand_name=brand_name,
            description=description,
            call_to_action=call_to_action,
            image_crop=image_crop,
            image_url=image_url,
            icon_url=icon_url,
        )

    def _get_video_representation(
        self,
        *,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        brand_name="My brand",
        description="My description",
        call_to_action="Read more...",
        image_crop="center",
        image_url=None,
        icon_url=None,
        video_asset_id=None,
    ):
        return self.get_candidate_representation(
            type=dash.constants.AdType.VIDEO,
            url=url,
            title=title,
            display_url=display_url,
            brand_name=brand_name,
            description=description,
            call_to_action=call_to_action,
            image_crop=image_crop,
            image_url=image_url,
            icon_url=icon_url,
            video_asset_id=video_asset_id,
        )

    def _get_image_representation(
        self,
        *,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        image_url=None,
    ):
        return self.get_candidate_representation(
            type=dash.constants.AdType.IMAGE,
            url=url,
            title=title,
            display_url=display_url,
            image_url=image_url,
        )

    def _get_ad_tag_representation(
        self,
        *,
        url="http://example.com",
        title="My title",
        display_url="http://example.com",
        ad_tag=None,
        image_width=None,
        image_height=None,
    ):
        return self.get_candidate_representation(
            type=dash.constants.AdType.AD_TAG,
            url=url,
            title=title,
            display_url=display_url,
            ad_tag=ad_tag,
            image_width=image_width,
            image_height=image_height,
        )
