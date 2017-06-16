from django.core.urlresolvers import reverse

import restapi.test_views
from dash import models
from dash import constants
from utils.magic_mixer import magic_mixer


class CampaignLauncherValidateTest(restapi.test_views.RESTAPITest):

    def test_validate_empty(self):
        r = self.client.post(reverse('campaignlauncher_validate', kwargs=dict(account_id=1)))
        r = self.assertResponseValid(r, data_type=type(None))

    def test_validate(self):
        data = {
            'name': 'Hi!'
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

    def test_launch(self):
        account = magic_mixer.blend(models.Account, users=[self.user])
        data = {
            'name': 'xyz',
            'iabCategory': 'IAB1_1',
        }
        r = self.client.post(
            reverse('campaignlauncher_launch',
                    kwargs=dict(account_id=account.id)),
            data,
            format='json'
        )
        r = self.assertResponseValid(r, data_type=dict)

        self.assertIn('campaignId', r['data'])
        campaign = models.Campaign.objects.get(pk=r['data']['campaignId'])
        campaign_settings = campaign.get_current_settings()
        self.assertEqual(campaign_settings.name, 'xyz')
        self.assertEqual(campaign_settings.iab_category, constants.IABCategory.IAB1_1)
