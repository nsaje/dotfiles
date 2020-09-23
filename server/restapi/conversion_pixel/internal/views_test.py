from django.urls import reverse

import core.models
import utils.test_helper
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class ConversionPixelViewSetTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        utils.test_helper.add_permissions(self.user, ["can_promote_additional_pixel", "can_redirect_pixels"])

    def test_get(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel")

        r = self.client.get(
            reverse("restapi.conversion_pixel.internal:pixels_details", kwargs={"pixel_id": pixel.id}),
            {"accountId": account.id},
        )
        self.assertEqual(r.status_code, 200)
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["id"], str(pixel.id))
        self.assertEqual(resp_json["data"]["name"], pixel.name)

    def test_list_with_agency(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account1 = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = self.mix_account(self.user, permissions=[Permission.READ])

        pixels = magic_mixer.cycle(4).blend(core.models.ConversionPixel, account=account1)
        magic_mixer.cycle(5).blend(core.models.ConversionPixel, account=account2)

        r = self.client.get(reverse("restapi.conversion_pixel.internal:pixels_list"), {"agencyId": agency.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 4)

        pixel_ids = [str(pixel.id) for pixel in pixels].sort()
        response_pixel_ids = [pixel["id"] for pixel in resp_json["data"]].sort()
        self.assertEqual(pixel_ids, response_pixel_ids)

    def test_list_with_account(self):
        agency = self.mix_agency(self.user, permissions=[Permission.READ])
        account = magic_mixer.blend(core.models.Account, agency=agency)
        account2 = magic_mixer.blend(core.models.Account, agency=agency)

        pixels = magic_mixer.cycle(4).blend(core.models.ConversionPixel, account=account)
        magic_mixer.cycle(5).blend(core.models.ConversionPixel, account=account2)

        r = self.client.get(reverse("restapi.conversion_pixel.internal:pixels_list"), {"accountId": account.id})
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(len(resp_json["data"]), 4)

        pixel_ids = [str(pixel.id) for pixel in pixels].sort()
        response_pixel_ids = [pixel["id"] for pixel in resp_json["data"]].sort()
        self.assertEqual(pixel_ids, response_pixel_ids)

    def test_list_without_agency_account(self):
        r = self.client.get(reverse("restapi.conversion_pixel.internal:pixels_list"))
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual("Either agency id or account id must be provided.", resp_json["details"])

    def test_list_keyword(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        test_pixel_1 = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test")
        test_pixel_2 = magic_mixer.blend(core.models.ConversionPixel, account=account, name="also test")
        new_pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="new name")

        r = self.client.get(
            reverse("restapi.conversion_pixel.internal:pixels_list"), {"accountId": account.id, "keyword": "test"}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(2, len(resp_json["data"]))

        response_pixel_ids = [pixel["id"] for pixel in resp_json["data"]]
        self.assertIn(str(test_pixel_1.id), response_pixel_ids)
        self.assertIn(str(test_pixel_2.id), response_pixel_ids)
        self.assertNotIn(str(new_pixel.id), response_pixel_ids)

    def test_list_audience_enabled_only(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        magic_mixer.blend(
            core.models.ConversionPixel, account=account, slug="test1", audience_enabled=False, additional_pixel=False
        )
        magic_mixer.blend(
            core.models.ConversionPixel, account=account, slug="test2", audience_enabled=True, additional_pixel=False
        )
        magic_mixer.blend(
            core.models.ConversionPixel, account=account, slug="test3", audience_enabled=False, additional_pixel=True
        )

        r = self.client.get(
            reverse("restapi.conversion_pixel.internal:pixels_list"),
            {"accountId": account.id, "audienceEnabledOnly": "true"},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        self.assertEqual(2, len(resp_json["data"]))

    def test_list_invalid_query_params(self):
        r = self.client.get(
            reverse("restapi.conversion_pixel.internal:pixels_list"),
            {"agencyId": "NON-NUMERIC", "accountId": "NON-NUMERIC"},
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual({"agencyId": ["Invalid format"], "accountId": ["Invalid format"]}, resp_json["details"])

    def test_put(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, notes="Old notes")

        r = self.client.get(
            reverse("restapi.conversion_pixel.internal:pixels_details", kwargs={"pixel_id": pixel.id}),
            {"accountId": account.id},
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["accountId"], str(account.id))
        self.assertEqual(resp_json["data"]["notes"], pixel.notes)

        put_data = {"notes": "New notes"}
        r = self.client.put(
            reverse("restapi.conversion_pixel.internal:pixels_details", kwargs={"pixel_id": pixel.id}),
            data=put_data,
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["id"], str(pixel.id))
        self.assertEqual(resp_json["data"]["notes"], put_data["notes"])

    def test_put_archived(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel", archived=False)
        self.assertFalse(pixel.archived)

        r = self.client.put(
            reverse("restapi.conversion_pixel.internal:pixels_details", kwargs={"pixel_id": pixel.id}),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["id"], str(pixel.id))
        self.assertTrue(resp_json["data"]["archived"])

    def test_put_additional_pixel(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="audience pixel", audience_enabled=True)
        pixel = magic_mixer.blend(
            core.models.ConversionPixel, account=account, name="test pixel", additional_pixel=False
        )
        r = self.client.put(
            reverse("restapi.conversion_pixel.internal:pixels_details", kwargs={"pixel_id": pixel.id}),
            data={"additional_pixel": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"]["id"], str(pixel.id))
        self.assertTrue(resp_json["data"]["additionalPixel"])

    def test_put_additional_pixel_no_permission(self):
        utils.test_helper.remove_permissions(self.user, ["can_promote_additional_pixel"])
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="audience pixel", audience_enabled=True)
        pixel = magic_mixer.blend(
            core.models.ConversionPixel, account=account, name="test pixel", additional_pixel=False
        )
        self.assertFalse(pixel.additional_pixel)
        r = self.client.put(
            reverse("restapi.conversion_pixel.internal:pixels_details", kwargs={"pixel_id": pixel.id}),
            data={"additional_pixel": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertFalse("additionalPixel" in resp_json["data"])
        self.assertEqual(resp_json["data"]["id"], str(pixel.id))

    def test_post(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="audience pixel", audience_enabled=True)
        r = self.client.post(
            reverse("restapi.conversion_pixel.v1:pixels_list", kwargs={"account_id": account.id}),
            data={},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Please specify a name."], resp_json["details"]["name"])
        r = self.client.post(
            reverse("restapi.conversion_pixel.v1:pixels_list", kwargs={"account_id": account.id}),
            data={
                "name": "pixel name",
                "additionalPixel": True,
                "redirectUrl": "https://test.com",
                "notes": "pixel name notes",
            },
            format="json",
        )
        resp_json = self.assertResponseValid(r, status_code=201)
        self.assertEqual("pixel name", resp_json["data"]["name"])
        self.assertTrue(resp_json["data"]["additionalPixel"])
        self.assertEqual("https://test.com", resp_json["data"]["redirectUrl"])
        self.assertEqual("pixel name notes", resp_json["data"]["notes"])
