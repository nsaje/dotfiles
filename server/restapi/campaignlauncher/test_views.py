from decimal import Decimal
import mock
import datetime

from django.core.urlresolvers import reverse

import restapi.test_views
import dash.models
import dash.constants
import dash.features.campaignlauncher
from utils.magic_mixer import magic_mixer


class CampaignLauncherValidateTest(restapi.test_views.RESTAPITest):

    def test_validate_empty(self):
        r = self.client.post(reverse('campaignlauncher_validate', kwargs=dict(account_id=1)))
        r = self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {
            'campaign_name': 'Hi!'
        }
        r = self.client.post(
            reverse('campaignlauncher_validate',
                    kwargs=dict(account_id=1)),
            data,
            format='json'
        )
        r = self.assertResponseValid(r, data_type=type(None))

    def test_validate_error(self):
        data = {
            'iabCategory': '123'
        }
        r = self.client.post(
            reverse('campaignlauncher_validate',
                    kwargs=dict(account_id=1)),
            data,
            format='json'
        )
        r = self.assertResponseError(r, 'ValidationError')
        self.assertIn(
            'Invalid choice 123!',
            r['details']['iabCategory'][0],
        )


class CampaignLauncherLaunchTest(restapi.test_views.RESTAPITest):

    @mock.patch.object(dash.features.campaignlauncher, 'launch', autospec=True)
    def test_launch(self, mock_launch):
        account = magic_mixer.blend(dash.models.Account, users=[self.user])
        campaign = magic_mixer.blend(dash.models.Campaign, name='xyz')
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        mock_launch.return_value = campaign

        data = {
            'campaign_name': 'xyz',
            'iabCategory': 'IAB1_1',
            'startDate': '2017-01-01',
            'endDate': '2017-01-01',
            'budgetAmount': 123,
            'maxCpc': '0.6',
            'dailyBudget': '15.0',
            'goal': {
                'type': 'CPA',
                'value': '30.0',
                'conversionGoal': {
                    'type': 'PIXEL',
                    'goalId': pixel.id,
                    'conversionWindow': 'LEQ_1_DAY'
                },
            },
        }
        r = self.client.post(
            reverse('campaignlauncher_launch',
                    kwargs=dict(account_id=account.id)),
            data,
            format='json'
        )
        r = self.assertResponseValid(r, data_type=dict)
        self.assertIn('campaignId', r['data'])
        mock_launch.assert_called_once_with(
            request=mock.ANY,
            account=account,
            name='xyz',
            iab_category='IAB1-1',
            start_date=datetime.date(2017, 1, 1),
            end_date=datetime.date(2017, 1, 1),
            budget_amount=123,
            max_cpc=Decimal('0.6'),
            daily_budget=Decimal('15.0'),
            goal_type=dash.constants.CampaignGoalKPI.CPA,
            goal_value=Decimal(30.0),
            conversion_goal_type=dash.constants.ConversionGoalType.PIXEL,
            conversion_goal_goal_id=str(pixel.id),
            conversion_goal_window=dash.constants.ConversionWindows.LEQ_1_DAY,
        )
