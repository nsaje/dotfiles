import datetime

import mock
from django.urls import reverse

import core.models
import redshiftapi.api_quickstats
from restapi.common.views_base_test import RESTAPITest
from restapi.common.views_base_test import RESTAPITestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission


class LegacyCampaignStatsTest(RESTAPITest):
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

        account = self.mix_account(self.user, permissions=[Permission.READ])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        today = datetime.date.today()
        r = self.client.get(
            reverse("restapi.campaignstats.v1:campaignstats", kwargs={"campaign_id": campaign.id}),
            {"from": today, "to": today},
        )
        resp_json = self.assertResponseValid(r)
        self.assertEqual(
            resp_json["data"], {"totalCost": "123.46", "cpc": "0.123", "impressions": 1234567, "clicks": 1234}
        )
        mock_query_campaign.assert_called_once_with(campaign.id, today, today)

    def test_get_invalid_params(self):
        account = self.mix_account(self.user, permissions=[Permission.READ])
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        r = self.client.get(
            reverse("restapi.campaignstats.v1:campaignstats", kwargs={"campaign_id": campaign.id}),
            {"from": 123, "to": 321},
        )
        self.assertResponseError(r, "ValidationError")

    def test_get_no_permission(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)

        today = datetime.date.today()
        r = self.client.get(
            reverse("restapi.campaignstats.v1:campaignstats", kwargs={"campaign_id": campaign.id}),
            {"from": today, "to": today},
        )
        self.assertResponseError(r, "MissingDataError")


class CampaignStatsTest(RESTAPITestCase, LegacyCampaignStatsTest):
    pass
