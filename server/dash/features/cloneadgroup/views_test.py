import mock

from django.core.urlresolvers import reverse
from rest_framework.test import APIClient
from utils.magic_mixer import magic_mixer

import core.entity
import restapi.views_test

from . import service


class CloneAdGroupViewTest(restapi.views_test.RESTAPITest):
    def setUp(self):
        self.user = magic_mixer.blend_user(permissions=['can_clone_adgroups'])
        self.account = magic_mixer.blend(core.entity.Account, users=[self.user])
        self.campaign = magic_mixer.blend(core.entity.Campaign, account=self.account)
        self.ad_group = magic_mixer.blend(core.entity.AdGroup, campaign=self.campaign)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @classmethod
    def clone_repr(cls, source_ad_group, destination_campaign):
        return cls.normalize({
            'adGroupId': str(source_ad_group.pk),
            'destinationCampaignId': str(destination_campaign.pk),
            'destinationAdGroupName': "New ad group clone",
            'cloneAds': False,
        })

    def test_no_obj_access(self):
        campaign = magic_mixer.blend(core.entity.Campaign)
        ad_group = magic_mixer.blend(core.entity.AdGroup)

        data = self.clone_repr(ad_group, campaign)

        r = self.client.post(reverse('ad_group_clone'), data=data, format='json')
        self.assertResponseError(r, 'MissingDataError')

    @mock.patch.object(service, 'clone', autospec=True)
    def test_post(self, mock_clone):
        cloned_ad_group = magic_mixer.blend(core.entity.AdGroup)
        mock_clone.return_value = cloned_ad_group

        data = self.clone_repr(self.ad_group, self.campaign)

        r = self.client.post(reverse('ad_group_clone'), data=data, format='json')
        r = self.assertResponseValid(r)
        self.assertDictContainsSubset({'id': str(cloned_ad_group.pk)}, r['data'])
