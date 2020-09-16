import mock
from django.urls import reverse

import core.models.ad_group
from restapi.common.views_base_test_case import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class RealtimestatsViewsTest(RESTAPITestCase):
    @mock.patch("dash.features.realtimestats.get_ad_group_stats")
    def test_adgroups_realtimestats(self, mock_get):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)

        mock_get.return_value = {"clicks": 12321, "spend": 12.3}
        r = self.client.get(
            reverse("restapi.adgroupstats.v1:adgroups_realtimestats", kwargs={"ad_group_id": ad_group.id})
        )

        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"], {"spend": "12.30", "clicks": 12321})

        mock_get.assert_called_with(ad_group)
