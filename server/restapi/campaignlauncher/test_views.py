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
        mock_launch.return_value = campaign

        data = {
            'campaign_name': 'xyz',
            'iabCategory': 'IAB1_1',
            'startDate': '2017-01-01',
            'endDate': '2017-01-01',
            'budgetAmount': 123
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
            user=self.user,
            account=account,
            name='xyz',
            iab_category='IAB1-1',
            start_date=datetime.date(2017, 1, 1),
            end_date=datetime.date(2017, 1, 1),
            budget_amount=123,
        )
