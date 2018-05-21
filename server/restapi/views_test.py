import datetime
import json
import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from zemauth.models import User
from django.core.urlresolvers import reverse

import dash.models
from . import fields
from . import views as restapi_views
import redshiftapi.api_quickstats

from utils import json_helper
from utils import test_helper


TODAY = datetime.datetime(2016, 1, 15).date()


class SerializerTests(TestCase):

    def test_allow_not_provided(self):
        NOT_PROVIDED = fields.NOT_PROVIDED
        d = {'name': 'test', 'tracking': {'ga': {'enabled': True}}}
        new_d = restapi_views.SettingsSerializer._allow_not_provided(d)
        self.assertEqual(new_d['name'], 'test')
        self.assertEqual(new_d['tracking']['ga']['enabled'], True)
        self.assertEqual(new_d['tracking']['ga']['property_id'], NOT_PROVIDED)
        self.assertEqual(new_d['tracking']['adobe']['enabled'], NOT_PROVIDED)


@override_settings(R1_DEMO_MODE=True)
class RESTAPITest(TestCase):
    fixtures = ['test_acceptance.yaml', 'test_geolocations']
    user_id = 1

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(pk=self.user_id)
        self.client.force_authenticate(user=self.user)
        self.maxDiff = None

    def assertResponseValid(self, r, status_code=200, data_type=dict):
        resp_json = json.loads(r.content)
        self.assertNotIn('errorCode', resp_json)
        self.assertEqual(r.status_code, status_code)
        self.assertIsInstance(resp_json['data'], data_type)
        return resp_json

    def assertResponseError(self, r, error_code):
        resp_json = json.loads(r.content)
        self.assertIn('errorCode', resp_json)
        self.assertEqual(resp_json['errorCode'], error_code)
        return resp_json

    @staticmethod
    def normalize(d):
        return json.loads(json.dumps(d, cls=json_helper.JSONEncoder))


class CampaignStatsTest(RESTAPITest):

    @mock.patch.object(redshiftapi.api_quickstats, 'query_campaign', autospec=True)
    def test_get(self, mock_query_campaign):
        mock_query_campaign.return_value = {
            'total_cost': 123.456,
            'cpc': 0.123,
            'impressions': 1234567,
            'clicks': 1234,
            'unneeded': 1,
            'fields': 2
        }
        today = datetime.date.today()
        r = self.client.get(reverse('campaignstats', kwargs={'campaign_id': 608}),
                            {'from': today, 'to': today})
        resp_json = self.assertResponseValid(r)
        self.assertEqual(resp_json['data'], {
            'totalCost': '123.46',
            'cpc': '0.123',
            'impressions': 1234567,
            'clicks': 1234,
        })


class PublisherGroupTest(RESTAPITest):
    fixtures = ['test_publishers.yaml']
    user_id = 2

    def setUp(self):
        super(PublisherGroupTest, self).setUp()
        permissions = [
            'can_edit_publisher_groups',
            'can_use_restapi',
            'can_access_additional_outbrain_publisher_settings',
        ]
        test_helper.add_permissions(self.user, permissions)

        restapi_views.PublisherGroupViewSet.throttle_classes = tuple([])

    def publishergroup_repr(self, pg):
        return {
            'id': str(pg.pk),
            'name': pg.name,
            'accountId': str(pg.account_id) if pg.account_id else None,
        }

    def validate_against_db(self, data):
        m = dash.models.PublisherGroup.objects.get(pk=data['id'])
        self.assertDictEqual(data, self.publishergroup_repr(m))

    def test_get_list(self):
        r = self.client.get(reverse('publisher_group_list', kwargs={'account_id': 1}))
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        self.validate_against_db(response['data'][0])
        self.assertEqual(response['data'][0]['id'], '1')

    def test_get_list_now_allowed(self):
        r = self.client.get(reverse('publisher_group_list', kwargs={'account_id': 2}))
        self.assertEqual(r.status_code, 404)

    def test_create_new(self):
        r = self.client.post(reverse('publisher_group_list', kwargs={'account_id': 1}),
                             data={'name': 'test'},
                             format='json')
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(response['data'])

    def test_create_new_not_allowed(self):
        r = self.client.post(reverse('publisher_group_list', kwargs={'account_id': 2}),
                             data={'name': 'test'},
                             format='json')
        self.assertEqual(r.status_code, 404)

    def test_get(self):
        r = self.client.get(reverse('publisher_group_details', kwargs={
            'account_id': 1,
            'publisher_group_id': 1,
        }))
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'])
        self.assertEqual(response['data']['id'], '1')

    def test_get_now_allowed(self):
        r = self.client.get(reverse('publisher_group_details', kwargs={
            'account_id': 2,
            'publisher_group_id': 2,
        }))
        self.assertEqual(r.status_code, 404)

    def test_update(self):
        r = self.client.put(reverse('publisher_group_details', kwargs={
            'account_id': 1,
            'publisher_group_id': 1,
        }), data={'name': 'test'}, format='json')
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'])
        self.assertEqual(response['data'], {
            'id': '1',
            'accountId': '1',
            'name': 'test',
        })

    def test_update_now_allowed(self):
        r = self.client.put(reverse('publisher_group_details', kwargs={
            'account_id': 2,
            'publisher_group_id': 2,
        }), data={'name': 'test'}, format='json')
        self.assertEqual(r.status_code, 404)

    def test_delete(self):
        r = self.client.delete(reverse('publisher_group_details', kwargs={
            'account_id': 1,
            'publisher_group_id': 1,
        }))
        self.assertEqual(r.status_code, 204)

        # check if really deleted
        r = self.client.get(reverse('publisher_group_details', kwargs={
            'account_id': 1,
            'publisher_group_id': 1,
        }))
        self.assertEqual(r.status_code, 404)

    def test_delete_now_allowed(self):
        r = self.client.delete(reverse('publisher_group_details', kwargs={
            'account_id': 2,
            'publisher_group_id': 2,
        }))
        self.assertEqual(r.status_code, 404)

    def test_check_permission(self):
        test_helper.remove_permissions(
            self.user, ['can_edit_publisher_groups'])
        r = self.client.put(reverse('publisher_group_details', kwargs={
            'account_id': 1,
            'publisher_group_id': 1,
        }), data={'name': 'test'}, format='json')
        self.assertEqual(r.status_code, 403)


class PublisherGroupEntryTest(RESTAPITest):
    fixtures = ['test_publishers.yaml']
    user_id = 2

    def setUp(self):
        super(PublisherGroupEntryTest, self).setUp()
        permissions = [
            'can_edit_publisher_groups',
            'can_use_restapi',
            'can_access_additional_outbrain_publisher_settings',
        ]
        test_helper.add_permissions(self.user, permissions)

        restapi_views.PublisherGroupEntryViewSet.throttle_classes = tuple([])

    def publishergroupentry_repr(self, pg, check_outbrain_pub_id):
        d = {
            'id': str(pg.pk),
            'publisher': pg.publisher,
            'source': pg.source.bidder_slug if pg.source else None,
            'includeSubdomains': pg.include_subdomains,
            'publisherGroupId': str(pg.publisher_group_id),
        }

        if check_outbrain_pub_id:
            d['outbrainPublisherId'] = pg.outbrain_publisher_id
            d['outbrainSectionId'] = pg.outbrain_section_id
            d['outbrainAmplifyPublisherId'] = pg.outbrain_amplify_publisher_id
            d['outbrainEngagePublisherId'] = pg.outbrain_engage_publisher_id

        return d

    def validate_against_db(self, data, check_outbrain_pub_id=True):
        m = dash.models.PublisherGroupEntry.objects.get(pk=data['id'])
        self.assertDictEqual(data, self.publishergroupentry_repr(m, check_outbrain_pub_id))

    def test_get_list(self):
        r = self.client.get(reverse('publisher_group_entry_list', kwargs={'publisher_group_id': 1}),
                            data={'offset': 0, 'limit': 10})
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        for x in response['data']:
            self.validate_against_db(x)
        self.assertCountEqual([x['id'] for x in response['data']], ['1', '2'])

    def test_get_list_check_pagination(self):
        r = self.client.get(reverse('publisher_group_entry_list', kwargs={'publisher_group_id': 1}),
                            data={'offset': 1, 'limit': 10})
        self.assertEqual(r.status_code, 200)
        response = self.assertResponseValid(r, data_type=list, status_code=200)
        for x in response['data']:
            self.validate_against_db(x)
        self.assertEqual(len(response['data']), 1)
        self.assertDictEqual(response, {
            'count': 2,
            'next': None,
            'previous': 'http://testserver/rest/v1/publishergroups/1/entries/?limit=10',
            'data': mock.ANY
        })

    def test_get_list_not_allowed(self):
        r = self.client.get(reverse('publisher_group_entry_list', kwargs={'publisher_group_id': 2}), data={'page': 1})
        self.assertEqual(r.status_code, 404)

    def test_create_new(self):
        r = self.client.post(reverse('publisher_group_entry_list', kwargs={'publisher_group_id': 1}),
                             data={'publisher': 'test', 'source': 'adsnative', 'includeSubdomains': False},
                             format='json')
        response = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(response['data'])

    def test_create_new_now_allowed(self):
        r = self.client.post(reverse('publisher_group_entry_list', kwargs={'publisher_group_id': 2}),
                             data={'publisher': 'test', 'source': 'adsnative'},
                             format='json')
        self.assertEqual(r.status_code, 404)

    def test_bulk_create_new(self):
        r = self.client.post(reverse('publisher_group_entry_list', kwargs={'publisher_group_id': 1}),
                             data=[{'publisher': 'test'}, {'publisher': 'bla'}],
                             format='json')
        response = self.assertResponseValid(r, data_type=list, status_code=201)
        for x in response['data']:
            self.validate_against_db(x)
        self.assertEqual(len(response['data']), 2)

    def test_get(self):
        r = self.client.get(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 1, 'entry_id': 1}))
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'])

    def test_get_not_allowed(self):
        r = self.client.get(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 2, 'entry_id': 3}))
        self.assertEqual(r.status_code, 404)

    def test_update(self):
        r = self.client.put(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 1, 'entry_id': 1}),
                            data={'publisher': 'cnn', 'source': 'gravity', 'outbrainPublisherId': '123'},
                            format='json')
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'])

    def test_update_not_allowed(self):
        r = self.client.put(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 2, 'entry_id': 3}),
                            data={'publisher': 'cnn', 'source': 'gravity', 'outbrainPublisherId': '123'},
                            format='json')
        self.assertEqual(r.status_code, 404)

    def test_delete(self):
        r = self.client.delete(reverse('publisher_group_entry_details', kwargs={
            'publisher_group_id': '1',
            'entry_id': '1',
        }))
        self.assertEqual(r.status_code, 204)

        r = self.client.get(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 1, 'entry_id': 1}))
        self.assertEqual(r.status_code, 404)

    def test_delete_not_allowed(self):
        r = self.client.delete(reverse('publisher_group_entry_details', kwargs={
            'publisher_group_id': '2',
            'entry_id': '3',
        }))
        self.assertEqual(r.status_code, 404)

    def test_check_permission(self):
        test_helper.remove_permissions(
            self.user, ['can_edit_publisher_groups'])
        r = self.client.get(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 1, 'entry_id': 1}))
        self.assertEqual(r.status_code, 403)

    def test_no_outbrain_permission(self):
        test_helper.remove_permissions(
            self.user, ['can_access_additional_outbrain_publisher_settings'])

        r = self.client.get(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 1, 'entry_id': 1}))
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'], check_outbrain_pub_id=False)

        r = self.client.put(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 1, 'entry_id': 1}),
                            data={'publisher': 'cnn', 'source': 'gravity', 'outbrainPublisherId': '123'},
                            format='json')
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'], check_outbrain_pub_id=False)

        # validate outbrainPublisherId was not changed
        self.assertEqual(dash.models.PublisherGroupEntry.objects.get(pk=1).outbrain_publisher_id, '')
