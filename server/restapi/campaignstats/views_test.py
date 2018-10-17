import mock
import datetime

from restapi.common.views_base_test import RESTAPITest

from django.urls import reverse
import redshiftapi.api_quickstats


class CampaignStatsTest(RESTAPITest):
    @mock.patch.object(redshiftapi.api_quickstats, "query_campaign", autospec=True)
    def test_get(self, mock_query_campaign):
        mock_query_campaign.return_value = {
            "local_total_cost": 123.456,
            "local_cpc": 0.123,
            "impressions": 1234567,
            "clicks": 1234,
            "unneeded": 1,
            "fields": 2,
        }
        today = datetime.date.today()
        r = self.client.get(reverse("campaignstats", kwargs={"campaign_id": 608}), {"from": today, "to": today})
        resp_json = self.assertResponseValid(r)
        self.assertEqual(
            resp_json["data"], {"totalCost": "123.46", "cpc": "0.123", "impressions": 1234567, "clicks": 1234}
        )
