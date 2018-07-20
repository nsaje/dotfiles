from decimal import Decimal
import mock

from django.core.urlresolvers import reverse

import restapi.common.views_base_test
import dash.models
import dash.constants
import dash.features.campaignlauncher
from utils.magic_mixer import magic_mixer


class CampaignLauncherValidateTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(CampaignLauncherValidateTest, self).setUp()
        self.account = magic_mixer.blend(dash.models.Account, users=[self.user])

    def test_validate_empty(self):
        r = self.client.post(reverse("campaignlauncher_validate", kwargs=dict(account_id=self.account.id)))
        r = self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {"campaign_name": "Hi!"}
        r = self.client.post(
            reverse("campaignlauncher_validate", kwargs=dict(account_id=self.account.id)), data, format="json"
        )
        r = self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {"iabCategory": "123"}
        r = self.client.post(
            reverse("campaignlauncher_validate", kwargs=dict(account_id=self.account.id)), data, format="json"
        )
        r = self.assertResponseError(r, "ValidationError")
        self.assertIn("Invalid choice 123!", r["details"]["iabCategory"][0])


class CampaignLauncherLaunchTest(restapi.common.views_base_test.RESTAPITest):
    @mock.patch.object(dash.features.campaignlauncher, "launch", autospec=True)
    def test_launch(self, mock_launch):
        account = magic_mixer.blend(dash.models.Account, users=[self.user])
        campaign = magic_mixer.blend(dash.models.Campaign, name="xyz")
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        upload_batch = magic_mixer.blend(dash.models.UploadBatch, account=account)
        mock_launch.return_value = campaign

        data = {
            "campaign_name": "xyz",
            "iabCategory": "IAB1_1",
            "language": "ENGLISH",
            "budgetAmount": 123,
            "maxCpc": "0.6",
            "dailyBudget": "15.0",
            "uploadBatch": str(upload_batch.id),
            "campaignGoal": {
                "type": "CPA",
                "value": "30.0",
                "conversionGoal": {"type": "PIXEL", "goalId": pixel.id, "conversionWindow": "LEQ_1_DAY"},
            },
            "targetRegions": {
                "countries": ["CA"],
                "regions": ["US-NY"],
                "dma": ["693"],
                "cities": ["123456"],
                "postalCodes": ["US:10001"],
            },
            "exclusionTargetRegions": {
                "countries": ["CA"],
                "regions": ["US-NY"],
                "dma": ["693"],
                "cities": ["123456"],
                "postalCodes": ["US:10001"],
            },
            "targetDevices": ["DESKTOP"],
            "targetPlacements": ["APP"],
            "targetOs": [{"name": "ANDROID"}],
        }
        r = self.client.post(
            reverse("campaignlauncher_launch", kwargs=dict(account_id=account.id)), data, format="json"
        )
        r = self.assertResponseValid(r, data_type=dict)
        self.assertIn("campaignId", r["data"])
        mock_launch.assert_called_once_with(
            request=mock.ANY,
            account=account,
            name="xyz",
            iab_category="IAB1-1",
            language="en",
            budget_amount=123,
            max_cpc=Decimal("0.6"),
            daily_budget=Decimal("15.0"),
            upload_batch=upload_batch,
            goal_type=dash.constants.CampaignGoalKPI.CPA,
            goal_value=Decimal(30.0),
            target_regions=["CA", "US-NY", "693", "123456", "US:10001"],
            exclusion_target_regions=["CA", "US-NY", "693", "123456", "US:10001"],
            target_devices=["desktop"],
            target_placements=["app"],
            target_os=[{"name": "android"}],
            conversion_goal_type=dash.constants.ConversionGoalType.PIXEL,
            conversion_goal_goal_id=str(pixel.id),
            conversion_goal_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
