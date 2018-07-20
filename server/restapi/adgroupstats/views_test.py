from restapi.common.views_base_test import RESTAPITest
from django.core.urlresolvers import reverse

import core.entity.adgroup
import mock


class RealtimestatsViewsTest(RESTAPITest):
    @mock.patch("dash.features.realtimestats.get_ad_group_stats")
    @mock.patch("restapi.adgroupstats.views.REALTIME_STATS_AGENCIES", [1])
    def test_adgroups_realtimestats(self, mock_get):
        mock_get.return_value = {"clicks": 12321, "spend": 12.3}
        r = self.client.get(reverse("adgroups_realtimestats", kwargs={"ad_group_id": 2040}))

        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json["data"], {"spend": "12.30", "clicks": 12321})

        mock_get.assert_called_with(core.entity.adgroup.AdGroup.objects.get(pk=2040))

    def test_adgroups_realtimestats_unauthorized(self):
        r = self.client.get(reverse("adgroups_realtimestats", kwargs={"ad_group_id": 2040}))
        self.assertEqual(r.status_code, 404)
