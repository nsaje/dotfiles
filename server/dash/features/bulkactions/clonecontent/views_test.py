import json

import mock
from django.urls import reverse
from rest_framework.test import APIClient

import core.models
import dash.constants
import restapi.common.views_base_test
from utils.magic_mixer import magic_mixer

from . import service


class CloneContentViewTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        self.user = magic_mixer.blend_user(permissions=["can_clone_contentads"])
        self.account = magic_mixer.blend(core.models.Account, users=[self.user])
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.content_ads = magic_mixer.cycle().blend(
            core.models.ContentAd, ad_group=self.ad_group, type=dash.constants.AdType.CONTENT
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @classmethod
    def clone_repr(cls, source_ad_group, destination_ad_group, selected_content_ads):
        return cls.normalize(
            {
                "adGroupId": str(source_ad_group.pk),
                "destinationAdGroupId": str(destination_ad_group.pk),
                "destinationBatchName": "New batch name",
                "contentAdIds": [x.pk for x in selected_content_ads],
            }
        )

    def test_no_obj_access(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        content_ads = magic_mixer.cycle().blend(core.models.ContentAd, ad_group=ad_group)

        data = self.clone_repr(ad_group, ad_group, content_ads)

        r = self.client.post(reverse("content_ad_clone"), data=data, format="json")
        self.assertResponseError(r, "MissingDataError")

    @mock.patch.object(service, "clone", autospec=True)
    def test_post(self, mock_clone):
        batch_clone = magic_mixer.blend(core.models.UploadBatch)
        mock_clone.return_value = batch_clone

        data = self.clone_repr(self.ad_group, self.ad_group, self.content_ads)

        r = self.client.post(reverse("content_ad_clone"), data=data, format="json")
        r = self.assertResponseValid(r)
        self.assertDictContainsSubset({"id": str(batch_clone.pk)}, r["data"])

    def test_post_type_fail(self):
        campaign = magic_mixer.blend(
            core.models.Campaign, account=self.account, type=dash.constants.CampaignType.DISPLAY
        )
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        data = self.clone_repr(self.ad_group, ad_group, self.content_ads)

        r = self.client.post(reverse("content_ad_clone"), data=data, format="json")
        r = self.assertEqual(
            {"errorCode": "ValidationError", "details": {"type": ["Creative type does not match the campaign type."]}},
            json.loads(r.content),
        )

    @mock.patch.object(core.models.AdGroup, "is_archived", return_value=True)
    def test_post_ad_group_archived_fail(self, mock_archived):
        campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)

        data = self.clone_repr(self.ad_group, ad_group, self.content_ads)

        r = self.client.post(reverse("content_ad_clone"), data=data, format="json")
        r = self.assertEqual(
            {
                "errorCode": "ValidationError",
                "details": {"destinationAdGroupId": ["Can not create a content ad on an archived ad group."]},
            },
            json.loads(r.content),
        )
