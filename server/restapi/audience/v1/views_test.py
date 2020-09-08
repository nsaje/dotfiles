from django.urls import reverse

import core.features.audiences
import core.models
import dash.constants
import utils.dates_helper
import utils.test_helper
from restapi.common.views_base_test_case import FutureRESTAPITestCase
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyAudiencesTest(RESTAPITestCase):
    def setUp(self):
        super().setUp()

    @classmethod
    def audience_repr(
        cls,
        id=1,
        pixel_id=1,
        name="test audience",
        archived=False,
        ttl=10,
        rules=[{"id": 1, "type": dash.constants.AudienceRuleType.CONTAINS, "value": "test"}],
        created_dt=utils.dates_helper.local_now(),
    ):
        representation = {
            "id": str(id),
            "pixelId": str(pixel_id),
            "name": name,
            "archived": archived,
            "ttl": ttl,
            "rules": rules,
            "createdDt": created_dt,
        }
        return cls.normalize(representation)

    def validate_against_db(self, audience):
        audience_db = core.features.audiences.Audience.objects.get(pk=audience["id"])
        expected = self.audience_repr(
            id=audience_db.pk,
            pixel_id=audience_db.pixel_id,
            name=audience_db.name,
            archived=audience_db.archived,
            ttl=audience_db.ttl,
            rules=[
                {"type": dash.constants.AudienceRuleType.get_name(r.type), "value": r.value}
                for r in audience_db.audiencerule_set.all()
            ],
            created_dt=audience_db.created_dt,
        )
        self.assertEqual(expected, audience)

    def test_audience_get(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )

        r = self.client.get(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            )
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])

    def test_no_account_access(self):
        request = magic_mixer.blend_request_user()
        account = magic_mixer.blend(core.models.Account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )

        r = self.client.get(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            )
        )
        self.assertResponseError(r, "MissingDataError")

    def test_audiences_list(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        core.features.audiences.Audience.objects.create(
            request, "test1", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule1"}]
        )
        core.features.audiences.Audience.objects.create(
            request, "test2", pixel, 30, 40, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule2"}]
        )

        r = self.client.get(reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
        self.assertEqual(2, len(resp_json["data"]))

    def test_audiences_list_exclude_archived(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        core.features.audiences.Audience.objects.create(
            request, "test1", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule1"}]
        )
        core.features.audiences.Audience.objects.create(
            request, "test2", pixel, 30, 40, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule2"}]
        )
        audience = core.features.audiences.Audience.objects.create(
            request, "test2", pixel, 30, 40, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule3"}]
        )
        audience.update(request, archived=True)

        r = self.client.get(reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
        self.assertEqual(2, len(resp_json["data"]))

    def test_audiences_list_include_archived(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        core.features.audiences.Audience.objects.create(
            request, "test1", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule1"}]
        )
        core.features.audiences.Audience.objects.create(
            request, "test2", pixel, 30, 40, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule2"}]
        )
        audience = core.features.audiences.Audience.objects.create(
            request, "test2", pixel, 30, 40, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule3"}]
        )
        audience.update(request, archived=True)

        r = self.client.get(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}), {"includeArchived": "T"}
        )
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json["data"]:
            self.validate_against_db(item)
        self.assertEqual(3, len(resp_json["data"]))

    def test_post(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": pixel.id,
                "name": "posty",
                "ttl": 10,
                "rules": [{"type": "CONTAINS", "value": "test_rule"}],
            },
            format="json",
        )
        resp_json = self.assertResponseValid(r, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(str(pixel.id), resp_json["data"]["pixelId"])
        self.assertEqual("posty", resp_json["data"]["name"])
        self.assertEqual(10, resp_json["data"]["ttl"])
        self.assertEqual("CONTAINS", resp_json["data"]["rules"][0]["type"])
        self.assertEqual("test_rule", resp_json["data"]["rules"][0]["value"])

    def test_post_blank(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}), data={}, format="json"
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Please select a pixel."], resp_json["details"]["pixelId"])
        self.assertEqual(["Please specify the audience name."], resp_json["details"]["name"])
        self.assertEqual(["Please specify the user retention in days."], resp_json["details"]["ttl"])
        self.assertEqual(["Please select a rule."], resp_json["details"]["rules"])

    def test_post_invalid(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": 1000,
                "name": "posty" * 42,
                "ttl": 404,
                "rules": [{"type": "BLAH", "value": "test_rule" * 42}],
            },
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Ensure this field has no more than 127 characters."], resp_json["details"]["name"])
        self.assertEqual(["Maximum number of days is 365."], resp_json["details"]["ttl"])
        self.assertEqual(
            ["Invalid choice BLAH! Valid choices: STARTS_WITH, CONTAINS, VISIT"],
            resp_json["details"]["rules"][0]["type"],
        )
        self.assertEqual(
            ["Ensure this field has no more than 255 characters."], resp_json["details"]["rules"][0]["value"]
        )

    def test_post_pixel_does_not_exist(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={"pixel_id": 1000, "name": "posty", "ttl": 10, "rules": [{"type": "CONTAINS", "value": "test_rule"}]},
            format="json",
        )
        self.assertResponseError(r, "MissingDataError")

    def test_post_pixel_archived_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account, archived=True)
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": pixel.id,
                "name": "posty",
                "ttl": 10,
                "rules": [{"type": "CONTAINS", "value": "test_rule"}],
            },
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Pixel is archived."], resp_json["details"]["pixelId"])

    def test_post_ttl_rules_error(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": pixel.id,
                "name": "posty",
                "ttl": 10,
                "rules": [{"type": "CONTAINS", "value": "test_rule"}],
            },
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            ["Audience {} with the same ttl and rule already exists.".format(audience.name)],
            resp_json["details"]["pixelId"],
        )

    def test_post_rule_multiple_values(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": pixel.id,
                "name": "posty",
                "ttl": 10,
                "rules": [{"type": "CONTAINS", "value": "this,is,a,test"}],
            },
            format="json",
        )
        resp_json = self.assertResponseValid(r, status_code=201)
        self.validate_against_db(resp_json["data"])

        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": pixel.id,
                "name": "posty",
                "ttl": 10,
                "rules": [
                    {
                        "type": "STARTS_WITH",
                        "value": "http://this.com,   https://is.com,http://a.com, https://test.com ",
                    }
                ],
            },
            format="json",
        )
        resp_json = self.assertResponseValid(r, status_code=201)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(
            "http://this.com,https://is.com,http://a.com,https://test.com", resp_json["data"]["rules"][0]["value"]
        )

        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": pixel.id,
                "name": "posty",
                "ttl": 10,
                "rules": [{"type": "STARTS_WITH", "value": "https://this.com,http://is.com,https://a,http://test.com"}],
            },
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

    def test_post_rule_visit(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={"pixel_id": pixel.id, "name": "posty", "ttl": 10, "rules": [{"type": "VISIT", "value": ""}]},
            format="json",
        )
        resp_json = self.assertResponseValid(r, status_code=201)
        self.validate_against_db(resp_json["data"])

        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={"pixel_id": pixel.id, "name": "posty", "ttl": 11, "rules": [{"type": "VISIT"}]},
            format="json",
        )
        resp_json = self.assertResponseValid(r, status_code=201)
        self.validate_against_db(resp_json["data"])

    def test_post_rule_type_missing_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={"pixel_id": pixel.id, "name": "posty", "ttl": 10, "rules": [{"value": "test"}]},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Please select the type of the rule."], resp_json["details"]["rules"][0]["type"])

    def test_post_rule_value_missing_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={"pixel_id": pixel.id, "name": "posty", "ttl": 10, "rules": [{"type": "CONTAINS", "value": ""}]},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Please enter conditions for the audience."], resp_json["details"]["rules"][0]["value"])

        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={"pixel_id": pixel.id, "name": "posty", "ttl": 10, "rules": [{"type": "STARTS_WITH", "value": None}]},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["This field may not be null."], resp_json["details"]["rules"][0]["value"])

        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={"pixel_id": pixel.id, "name": "posty", "ttl": 10, "rules": [{"type": "STARTS_WITH"}]},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Please enter conditions for the audience."], resp_json["details"]["rules"][0]["value"])

    def test_post_rule_url_invalid_error(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        r = self.client.post(
            reverse("restapi.audience.v1:audiences_list", kwargs={"account_id": account.id}),
            data={
                "pixel_id": pixel.id,
                "name": "posty",
                "ttl": 10,
                "rules": [{"type": "STARTS_WITH", "value": "invalid_url"}],
            },
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(["Please enter valid URLs."], resp_json["details"]["rules"][0]["value"])

    def test_put(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        pixel2 = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )
        old_id = audience.id
        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={
                "id": old_id + 10,
                "pixel_id": pixel2.id,
                "name": "putty",
                "ttl": 30,
                "rules": [{"type": "STARTS_WITH", "value": "better_test_rule"}],
            },
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json["data"])
        self.assertEqual(str(old_id), resp_json["data"]["id"])
        self.assertEqual(str(pixel.id), resp_json["data"]["pixelId"])
        self.assertEqual("putty", resp_json["data"]["name"])
        self.assertEqual(10, resp_json["data"]["ttl"])
        self.assertEqual("CONTAINS", resp_json["data"]["rules"][0]["type"])
        self.assertEqual("test_rule", resp_json["data"]["rules"][0]["value"])

    def test_put_archived(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )
        self.assertFalse(audience.archived)
        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertTrue(resp_json["data"]["archived"])
        audience.refresh_from_db()
        self.assertTrue(audience.archived)

        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={"archived": False},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertFalse(resp_json["data"]["archived"])
        audience.refresh_from_db()
        self.assertFalse(audience.archived)

    def test_put_can_not_archive_error(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        ad_group.settings.update(request, audience_targeting=[audience.id])
        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={"archived": True},
            format="json",
        )
        resp_json = self.assertResponseError(r, "ValidationError")
        self.assertEqual(
            ["Audience '{}' is currently targeted on ad groups {}.".format(audience.name, ad_group.name)],
            resp_json["details"]["archived"],
        )

    def test_put_audience_does_not_exist(self):
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        r = self.client.put(
            reverse("restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": 1000}),
            data={"name": "new name"},
            format="json",
        )
        self.assertResponseError(r, "MissingDataError")

    def test_unsetting_blank(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )
        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={"name": ""},
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={"rules": [{"type": "STARTS_WITH", "value": ""}]},
            format="json",
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual("CONTAINS", resp_json["data"]["rules"][0]["type"])
        self.assertEqual("test_rule", resp_json["data"]["rules"][0]["value"])

    def test_unsetting_null(self):
        request = magic_mixer.blend_request_user()
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        pixel = magic_mixer.blend(core.models.ConversionPixel, account=account)
        audience = core.features.audiences.Audience.objects.create(
            request, "test", pixel, 10, 20, [{"type": dash.constants.AudienceRuleType.CONTAINS, "value": "test_rule"}]
        )
        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={"name": None},
            format="json",
        )
        self.assertResponseError(r, "ValidationError")

        r = self.client.put(
            reverse(
                "restapi.audience.v1:audiences_details", kwargs={"account_id": account.id, "audience_id": audience.id}
            ),
            data={"rules": [{"type": "STARTS_WITH", "value": None}]},
            format="json",
        )
        self.assertResponseError(r, "ValidationError")


class AudiencesTest(FutureRESTAPITestCase, LegacyAudiencesTest):
    pass
