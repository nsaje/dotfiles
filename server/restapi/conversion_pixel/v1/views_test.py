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

    @classmethod
    def pixel_repr(
        cls,
        id=None,
        account_id=None,
        name="test pixel",
        archived=False,
        audience_enabled=False,
        additional_pixel=False,
        url="https://www.example.com",
        redirect_url="https://www.example.com/1/1/",
        notes="test notes",
        last_triggered=None,
        impressions=0,
    ):
        representation = {
            "id": str(id) if id is not None else None,
            "accountId": str(account_id) if account_id is not None else None,
            "name": name,
            "archived": archived,
            "audienceEnabled": audience_enabled,
            "additionalPixel": additional_pixel,
            "url": url or "",
            "redirectUrl": redirect_url or "",
            "notes": notes,
            "lastTriggered": last_triggered,
            "impressions": impressions,
        }
        return cls.normalize(representation)

    def validate_against_db(self, pixel):
        pixel_db = core.models.ConversionPixel.objects.get(pk=pixel["id"])
        expected = self.pixel_repr(
            id=pixel_db.pk,
            account_id=pixel_db.account_id,
            name=pixel_db.name,
            archived=pixel_db.archived,
            audience_enabled=pixel_db.audience_enabled,
            additional_pixel=pixel_db.additional_pixel,
            url=pixel_db.get_url(),
            redirect_url=pixel_db.redirect_url,
            notes=pixel_db.notes,
            last_triggered=pixel_db.last_triggered,
            impressions=pixel_db.get_impressions(),
        )
        self.assertEqual(expected, pixel)

    def test_pixel_get(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel")
        r = self.client.get(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_no_account_access(self):
        account = magic_mixer.blend(core.models.Account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel")
        r = self.client.get(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_pixels_list(self):
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
        r = self.client.get(reverse("restapi.conversion_pixel.v1:pixels_list", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
        self.assertEqual(3, len(resp_json["data"]))

    def test_pixels_list_audience_enabled_only(self):
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
            reverse("restapi.conversion_pixel.v1:pixels_list", kwargs={"account_id": account.id}),
            {"audienceEnabledOnly": True},
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
        self.assertEqual(2, len(resp_json["data"]))

    def test_get_permissioned(self):
        utils.test_helper.remove_permissions(self.user, ["can_redirect_pixels"])
        account = self.mix_account(self.user, permissions=[Permission.READ])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel")
        r = self.client.get(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            )
        )
        resp_json = self.assertResponseValid(r)
        self.assertFalse("redirectUrl" in resp_json["data"])
        resp_json["data"]["redirectUrl"] = pixel.redirect_url or ""
        self.validate_against_db(resp_json["data"])

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
            data={"name": "posty", "additionalPixel": True, "redirectUrl": "https://test.com", "notes": "posty notes"},
            format="json",
        )
        resp_json = self.assertResponseValid(r, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual("posty", resp_json["data"]["name"])
        self.assertTrue(resp_json["data"]["additionalPixel"])
        self.assertEqual("https://test.com", resp_json["data"]["redirectUrl"])
        self.assertEqual("posty notes", resp_json["data"]["notes"])

    def test_put(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel", archived=False)
        self.assertFalse(pixel.archived)
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"audienceEnabled": True, "redirectUrl": "https://test.com", "notes": "putty notes"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertTrue(resp_json["data"]["audienceEnabled"])
        self.assertEqual("https://test.com", resp_json["data"]["redirectUrl"])
        self.assertEqual("putty notes", resp_json["data"]["notes"])

    def test_put_archived(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel", archived=False)
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertTrue(resp_json["data"]["archived"])

    def test_put_additional_pixel(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="audience pixel", audience_enabled=True)
        pixel = magic_mixer.blend(
            core.models.ConversionPixel, account=account, name="test pixel", additional_pixel=False
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"additional_pixel": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
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
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"additional_pixel": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertFalse("additionalPixel" in resp_json["data"])
        pixel.refresh_from_db()
        self.assertFalse(pixel.additional_pixel)
        resp_json["data"]["additionalPixel"] = False
        self.validate_against_db(resp_json["data"])

    def test_unsetting_blank(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(
            core.models.ConversionPixel,
            account=account,
            name="test pixel",
            redirect_url="http://test.com",
            notes="test notes",
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"redirect_url": "", "notes": ""},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual("", resp_json["data"]["redirectUrl"])
        self.assertEqual("", resp_json["data"]["notes"])

    def test_unsetting_null(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(
            core.models.ConversionPixel,
            account=account,
            name="test pixel",
            redirect_url="http://test.com",
            notes="test notes",
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"redirect_url": None, "notes": None},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["This field may not be null."], resp_json["details"]["notes"])
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"redirect_url": None},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual("", resp_json["data"]["redirectUrl"])

    def test_put_permissioned(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel")
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"redirectUrl": "https://test.com", "notes": "putty notes"},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual("https://test.com", resp_json["data"]["redirectUrl"])
        self.assertEqual("putty notes", resp_json["data"]["notes"])

    def test_name_too_long_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel")
        r = self.client.post(
            reverse("restapi.conversion_pixel.v1:pixels_list", kwargs={"account_id": account.id}),
            data={"name": "test pixel" * 10},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Ensure this field has no more than 50 characters."], resp_json["details"]["name"])

    def test_duplicate_name_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        magic_mixer.blend(core.models.ConversionPixel, account=account, name="test pixel")
        r = self.client.post(
            reverse("restapi.conversion_pixel.v1:pixels_list", kwargs={"account_id": account.id}),
            data={"name": "test pixel"},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Conversion pixel with name test pixel already exists."], resp_json["details"]["name"])

    def test_archived_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        audience_pixel = magic_mixer.blend(
            core.models.ConversionPixel, account=account, name="audience pixel", audience_enabled=True
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details",
                kwargs={"account_id": account.id, "pixel_id": audience_pixel.id},
            ),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            ["Can not archive pixel used for building custom audiences."], resp_json["details"]["audienceEnabled"]
        )
        additional_pixel = magic_mixer.blend(
            core.models.ConversionPixel, account=account, name="additional pixel", additional_pixel=True
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details",
                kwargs={"account_id": account.id, "pixel_id": additional_pixel.id},
            ),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            ["Can not archive pixel used for building custom audiences."], resp_json["details"]["audienceEnabled"]
        )

    def test_additional_audience_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(
            core.models.ConversionPixel,
            account=account,
            name="test pixel",
            audience_enabled=False,
            additional_pixel=False,
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"audience_enabled": True, "additional_pixel": True},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            ["Custom audience and additional audience can not be enabled at the same time on the same pixel."],
            resp_json["details"]["additionalPixel"],
        )

    def test_audience_already_exists_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        audience_pixel = magic_mixer.blend(
            core.models.ConversionPixel, account=account, name="audience pixel", audience_enabled=True
        )
        pixel = magic_mixer.blend(
            core.models.ConversionPixel,
            account=account,
            name="test pixel",
            audience_enabled=False,
            additional_pixel=False,
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"audience_enabled": True},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            [
                "This pixel can not be used for building custom audiences because another pixel is already used: {}.".format(
                    audience_pixel.name
                )
            ],
            resp_json["details"]["audienceEnabled"],
        )

    def test_additional_no_audience_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(
            core.models.ConversionPixel, account=account, name="test pixel", additional_pixel=False
        )
        r = self.client.put(
            reverse(
                "restapi.conversion_pixel.v1:pixels_details", kwargs={"account_id": account.id, "pixel_id": pixel.id}
            ),
            data={"additional_pixel": True},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            [
                "The pixel's account has no audience pixel set. Set an audience pixel before setting an additional audience pixel."
            ],
            resp_json["details"]["additionalPixel"],
        )
