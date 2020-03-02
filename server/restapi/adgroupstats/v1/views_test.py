import mock
from django.urls import reverse

import core.models.ad_group
from restapi.common.views_base_test import RESTAPITest


class RealtimestatsViewsTest(RESTAPITest):
    @mock.patch("dash.features.realtimestats.get_ad_group_stats")
    def test_adgroups_realtimestats(self, mock_get):
        mock_get.return_value = {"clicks": 12321, "spend": 12.3}
        r = self.client.get(reverse("restapi.adgroupstats.v1:adgroups_realtimestats", kwargs={"ad_group_id": 2040}))

        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"], {"spend": "12.30", "clicks": 12321})

        mock_get.assert_called_with(core.models.ad_group.AdGroup.objects.get(pk=2040))