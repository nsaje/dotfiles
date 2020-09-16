import mock
from django.urls import reverse

import core.models
import dash.constants
import dash.features.clonecontentad
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class CloneContentAdsViewSetTestCase(RESTAPITestCase):
    def setUp(self):
        super().setUp()
        self.account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.content_ads = magic_mixer.cycle().blend(
            core.models.ContentAd, ad_group=self.ad_group, type=dash.constants.AdType.CONTENT
        )

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

    @mock.patch.object(dash.features.clonecontentad.service, "clone_edit", autospec=True)
    def test_post(self, mock_clone):
        batch_clone = magic_mixer.blend(core.models.UploadBatch)
        mock_clone.return_value = (batch_clone, [])

        data = self.clone_repr(self.ad_group, self.ad_group, self.content_ads)

        response = self.client.post(
            reverse("restapi.contentad.internal:content_ads_batch_clone"), data=data, format="json"
        )
        response = self.assertResponseValid(response)

        self.assertDictContainsSubset({"id": str(batch_clone.pk)}, response["data"]["destinationBatch"])
