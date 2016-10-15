import json

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from zemauth.models import User
from django.core.urlresolvers import reverse

import dash.models


class RESTAPITest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=1))

    def test_campaigns_list(self):
        r = self.client.get(reverse('campaigns_list'))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], list)
        self.assertGreater(len(resp_json['data']), 0)
        for item in resp_json['data']:
            self.assertEqual(item.keys(), ['tracking', 'id', 'name'])

    def test_campaigns_post(self):
        r = self.client.post(reverse('campaigns_list'), {'accountId': 1, 'name': 'test campaign'}, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['name'], 'test campaign')

    def test_campaigngoals_list(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        goal = dash.models.CampaignGoal(campaign=campaign)
        goal.save()
        dash.models.CampaignGoalValue(campaign_goal=goal, value='10.0').save()
        r = self.client.get(reverse('campaigngoals_list', kwargs={'campaign_id': 1}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], list)
        self.assertGreater(len(resp_json['data']), 0)
        expected_fields = ['campaignId', 'conversionGoal', 'primary', 'value', 'type', 'id']
        for item in resp_json['data']:
            self.assertEqual(item.keys(), expected_fields)

    @override_settings(R1_DEMO_MODE=True)
    def test_campaigngoals_post(self):
        r = self.client.post(
            reverse('campaigngoals_list', kwargs={'campaign_id': 1}),
            data={'type': 'TIME_ON_SITE', 'value': '30.0', 'primary': True, 'conversionGoal': None}, format='json')
        print r
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['value'], '30.00')

    def test_adgroups_list(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        ad_group.get_current_settings().save(None)
        r = self.client.get(reverse('adgroups_list'))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], list)
        self.assertGreater(len(resp_json['data']), 0)
        expected_fields = [
            'startDate', 'endDate', 'name', 'maxCpc', 'state', 'trackingCode',
            'autopilot', 'targeting', 'id', 'dailyBudget']
        for item in resp_json['data']:
            self.assertEqual(item.keys(), expected_fields)

    @override_settings(R1_DEMO_MODE=True)
    def test_adgroups_post(self):
        r = self.client.post(
            reverse('adgroups_list'),
            data={'campaignId': 1, 'name': 'test adgroup'}, format='json')
        print r
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['name'], 'test adgroup')

    def test_adgroups_sources_list(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        source = dash.models.Source()
        source.save()
        ags = dash.models.AdGroupSource(ad_group=ad_group, source=source)
        ags.save()
        r = self.client.get(reverse('adgroups_sources_list', kwargs={'ad_group_id': 1}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], list)
        self.assertGreater(len(resp_json['data']), 0)
        expected_fields = ['source', 'state', 'cpc', 'dailyBudget']
        for item in resp_json['data']:
            self.assertEqual(item.keys(), expected_fields)

    def test_adgroups_publishers_list(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        dash.models.PublisherBlacklist(name='test', ad_group=ad_group).save()
        r = self.client.get(reverse('publishers_list', kwargs={'ad_group_id': 1}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], list)
        self.assertGreater(len(resp_json['data']), 0)
        expected_fields = ['status', 'source', 'externalId', 'name', 'level']
        for item in resp_json['data']:
            self.assertEqual(item.keys(), expected_fields)
