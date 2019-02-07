import mock
from django.urls import reverse

import core.models
from restapi.common.views_base_test import RESTAPITest
from utils.magic_mixer import magic_mixer


class AdGroupViewSetTest(RESTAPITest):
    def test_validate_empty(self):
        r = self.client.post(reverse("internal:adgroups_validate"))
        self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {"name": "My ad group 1", "campaignId": "123"}
        r = self.client.post(reverse("internal:adgroups_validate"), data=data, format="json")
        self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {"name": None, "campaignId": None}
        r = self.client.post(reverse("internal:adgroups_validate"), data=data, format="json")
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("This field may not be null.", r["details"]["name"][0])
        self.assertIn("This field may not be null.", r["details"]["campaignId"][0])

    @mock.patch("restapi.adgroup.internal.helpers.get_extra_data")
    def test_get_default(self, mock_get_extra_data):
        mock_get_extra_data.return_value = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
            "retargetable_adgroups": [],
            "audiences": [],
            "warnings": {"retargeting": {"sources": []}},
            "hacks": [],
        }

        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        r = self.client.get(reverse("internal:adgroups_defaults"), {"campaignId": campaign.id})
        resp_json = self.assertResponseValid(r)

        self.assertEqual(resp_json["data"]["name"], "New ad group")
        self.assertEqual(
            resp_json["extra"],
            {
                "actionIsWaiting": False,
                "canArchive": False,
                "canRestore": False,
                "retargetableAdgroups": [],
                "audiences": [],
                "warnings": {"retargeting": {"sources": []}},
                "hacks": [],
            },
        )

    @mock.patch("restapi.adgroup.internal.helpers.get_extra_data")
    def test_get(self, mock_get_extra_data):
        mock_get_extra_data.return_value = {
            "action_is_waiting": False,
            "can_archive": False,
            "can_restore": False,
            "retargetable_adgroups": [],
            "audiences": [],
            "warnings": {"retargeting": {"sources": []}},
            "hacks": [],
        }

        agency = magic_mixer.blend(core.models.Agency)
        account = magic_mixer.blend(core.models.Account, agency=agency, users=[self.user])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        r = self.client.get(reverse("internal:adgroups_details", kwargs={"ad_group_id": ad_group.id}))
        resp_json = self.assertResponseValid(r)

        self.assertEqual(
            resp_json["extra"],
            {
                "actionIsWaiting": False,
                "canArchive": False,
                "canRestore": False,
                "retargetableAdgroups": [],
                "audiences": [],
                "warnings": {"retargeting": {"sources": []}},
                "hacks": [],
            },
        )