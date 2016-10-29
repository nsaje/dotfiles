import json
import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from zemauth.models import User
from django.core.urlresolvers import reverse

import dash.models
import views as restapi_views
from dash import constants
from dash import upload


class SerializerTets(TestCase):

    def test_allow_not_provided(self):
        NOT_PROVIDED = restapi_views.NOT_PROVIDED
        d = {'name': 'test', 'tracking': {'ga': {'enabled': True}}}
        new_d = restapi_views.SettingsSerializer._allow_not_provided(d)
        self.assertEqual(new_d['name'], 'test')
        self.assertEqual(new_d['tracking']['ga']['enabled'], True)
        self.assertEqual(new_d['tracking']['ga']['property_id'], NOT_PROVIDED)
        self.assertEqual(new_d['tracking']['adobe']['enabled'], NOT_PROVIDED)


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
            self.assertEqual(set(item.keys()), {'tracking', 'id', 'accountId', 'name'})

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
        expected_fields = {
            'startDate', 'endDate', 'name', 'maxCpc', 'state', 'trackingCode',
            'autopilot', 'targeting', 'id', 'campaignId', 'dailyBudget'}
        for item in resp_json['data']:
            self.assertEqual(set(item.keys()), expected_fields)

    @override_settings(R1_DEMO_MODE=True)
    def test_adgroups_post(self):
        r = self.client.post(
            reverse('adgroups_list'),
            data={'campaignId': 1, 'name': 'test adgroup'}, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['name'], 'test adgroup')

    @override_settings(R1_DEMO_MODE=True)
    def test_adgroups_put(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        ad_group.get_current_settings().save(None)
        data = {
            'name': 'renamed test ad group',
            'targeting': {
                'interest': {
                    'included': ['HOME', 'FAMILY'],
                    'excluded': ['FINANCE', 'SHOPPING']
                }
            }
        }
        r = self.client.put(
            reverse('adgroups_details', kwargs={'entity_id': 1}),
            data=data, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['name'], 'renamed test ad group')
        self.assertEqual(resp_json['data']['targeting']['interest']['included'], ['HOME', 'FAMILY'])
        self.assertEqual(resp_json['data']['targeting']['interest']['excluded'], ['FINANCE', 'SHOPPING'])

        new_settings = ad_group.get_current_settings()
        self.assertEqual(new_settings.ad_group_name, 'renamed test ad group')
        self.assertEqual(new_settings.interest_targeting, ['home', 'family'])
        self.assertEqual(new_settings.exclusion_interest_targeting, ['finance', 'shopping'])

    @override_settings(R1_DEMO_MODE=True)
    def test_adgroups_put_state(self):
        ad_group = dash.models.AdGroup.objects.get(pk=1)
        settings = ad_group.get_current_settings()
        settings.state = constants.AdGroupSettingsState.ACTIVE
        settings.save(None)
        r = self.client.put(
            reverse('adgroups_details', kwargs={'entity_id': 1}),
            data={'state': 'INACTIVE'}, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['state'], 'INACTIVE')
        self.assertEqual(ad_group.get_current_settings().state, constants.AdGroupSettingsState.INACTIVE)

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


class TestBatchUpload(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=1))

    @staticmethod
    def _mock_content_ad(title):
        return {
            "state": "ACTIVE",
            "url": "https://www.example.com/p/83895c0e-3bbe-4ad7-a0f6-c1917788ceb9",
            "title": title,
            "imageUrl": "http://example.com/p/srv/9018/e5d6adb68f1d404f82541e335c50bbd3.jpg?w=1024&h=768&fit=crop&crop=center&fm=jpg",
            "displayUrl": "kuhic.com",
            "brandName": "Kassulke-Hartmann",
            "description": "People really should avert their gaze from the modern survival thinking for just a bit and also look at how folks 150 years ago did it.",
            "callToAction": "Watch More",
            "label": "",
            "imageCrop": "center",
            "trackerUrls": ["https://www.example.com/a", "https://www.example.com/b"]
        }

    @override_settings(R1_DEMO_MODE=True)
    @mock.patch('dash.upload._invoke_external_validation', mock.Mock())
    def test_batch_upload_success(self):
        to_upload = [self._mock_content_ad('test1'), self._mock_content_ad('test2')]
        r = self.client.post(reverse('contentads_batch_list') + '?adGroupId=1', to_upload, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'IN_PROGRESS')
        self.assertIn('id', resp_json['data'])

        batch_id = int(resp_json['data']['id'])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse('contentads_batch_details', kwargs={'batch_id': batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'IN_PROGRESS')
        self.assertEqual(batch_id, int(resp_json['data']['id']))

        self._approve_candidates(batch)

        r = self.client.get(reverse('contentads_batch_details', kwargs={'batch_id': batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'DONE')
        self.assertEqual(batch_id, int(resp_json['data']['id']))

        saved_content_ads = batch.contentad_set.all().order_by('pk')
        self.assertEqual(len(to_upload), len(resp_json['data']['approvedContentAds']))
        self.assertEqual(len(to_upload), len(saved_content_ads))
        for i in range(len(to_upload)):
            for field in ('state', 'title', 'displayUrl', 'brandName', 'description', 'callToAction', 'label', 'trackerUrls'):
                self.assertEqual(to_upload[i][field], resp_json['data']['approvedContentAds'][i][field])
            self.assertEqual(saved_content_ads[i].id, int(resp_json['data']['approvedContentAds'][i]['id']))

    @staticmethod
    def _approve_candidates(batch):
        for candidate in batch.contentadcandidate_set.all():
            candidate.image_id = 'p/srv/8678/13f72b5e37a64860a73ac95ff51b2a3e'
            candidate.image_hash = '1234'
            candidate.image_height = 500
            candidate.image_width = 500
            candidate.image_status = constants.AsyncUploadJobStatus.OK
            candidate.url_status = constants.AsyncUploadJobStatus.OK
            candidate.save()
        upload._handle_auto_save(batch)

    @mock.patch('dash.upload._invoke_external_validation', mock.Mock())
    def test_batch_upload_failure(self):
        to_upload = [self._mock_content_ad('test1'), self._mock_content_ad('test2')]
        r = self.client.post(reverse('contentads_batch_list') + '?adGroupId=1', to_upload, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'IN_PROGRESS')
        self.assertIn('id', resp_json['data'])

        batch_id = int(resp_json['data']['id'])
        batch = dash.models.UploadBatch.objects.get(pk=batch_id)

        r = self.client.get(reverse('contentads_batch_details', kwargs={'batch_id': batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'IN_PROGRESS')
        self.assertEqual(batch_id, int(resp_json['data']['id']))

        self._reject_candidates(batch)

        r = self.client.get(reverse('contentads_batch_details', kwargs={'batch_id': batch_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'FAILED')
        self.assertEqual(resp_json['data']['approvedContentAds'], [])
        self.assertEqual(batch_id, int(resp_json['data']['id']))

    @staticmethod
    def _reject_candidates(batch):
        for candidate in batch.contentadcandidate_set.all():
            candidate.image_status = constants.AsyncUploadJobStatus.FAILED
            candidate.url_status = constants.AsyncUploadJobStatus.FAILED
            candidate.save()
        upload._handle_auto_save(batch)
