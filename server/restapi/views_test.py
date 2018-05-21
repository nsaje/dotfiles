from decimal import Decimal
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
from dash import constants
import redshiftapi.api_quickstats

from utils import json_helper
from utils import test_helper
from utils.magic_mixer import magic_mixer


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


class CampaignGoalsTest(RESTAPITest):

    @classmethod
    def campaigngoal_repr(
        cls,
        id=1,
        primary=True,
        type=constants.CampaignGoalKPI.TIME_ON_SITE,
        conversionGoal=None,
        value='30.00'
    ):
        representation = {
            'id': id,
            'primary': primary,
            'type': constants.CampaignGoalKPI.get_name(type),
            'conversionGoal': conversionGoal,
            'value': value,
        }
        return cls.normalize(representation)

    def validate_campaigngoal(self, campaigngoal):
        campaigngoal_db = dash.models.CampaignGoal.objects.get(pk=campaigngoal['id'])
        conversiongoal_db = campaigngoal_db.conversion_goal
        expected_conversiongoal = None
        if conversiongoal_db:
            pixel_url = conversiongoal_db.pixel.get_url() if conversiongoal_db.pixel else None
            expected_conversiongoal = dict(
                goalId=conversiongoal_db.goal_id or conversiongoal_db.pixel.id,
                name=conversiongoal_db.name,
                pixelUrl=pixel_url,
                conversionWindow=constants.ConversionWindows.get_name(conversiongoal_db.conversion_window),
                type=constants.ConversionGoalType.get_name(conversiongoal_db.type),
            )

        rounding_format = '1.000' if campaigngoal_db.type == constants.CampaignGoalKPI.CPC else '1.00'
        expected = self.campaigngoal_repr(
            id=campaigngoal_db.id,
            primary=campaigngoal_db.primary,
            type=campaigngoal_db.type,
            conversionGoal=expected_conversiongoal,
            value=campaigngoal_db.values.last().value.quantize(Decimal(rounding_format)),
        )
        self.assertEqual(expected, campaigngoal)

    def test_campaigngoals_list(self):
        r = self.client.get(reverse('campaigngoals_list', kwargs={'campaign_id': 608}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_campaigngoal(item)

    def test_campaigngoals_post(self):
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPC,
            value='0.33',
            primary=True,
            conversionGoal=None
        )
        post_data = test_campaigngoal.copy()
        del post_data['id']
        del post_data['conversionGoal']
        r = self.client.post(
            reverse('campaigngoals_list', kwargs={'campaign_id': 608}),
            data=post_data, format='json')
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_campaigngoal(resp_json['data'])

    def test_campaigngoals_get(self):
        r = self.client.get(reverse('campaigngoals_details', kwargs={'campaign_id': 608, 'goal_id': 1238}))
        resp_json = self.assertResponseValid(r)
        self.validate_campaigngoal(resp_json['data'])

    def test_campaigngoals_put(self):
        test_campaigngoal = self.campaigngoal_repr(
            id=1238,
            value='0.39',
            primary=True
        )
        r = self.client.put(reverse('campaigngoals_details', kwargs={'campaign_id': 608, 'goal_id': 1238}), test_campaigngoal, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_campaigngoal(resp_json['data'])
        self.assertEqual(resp_json['data']['value'], test_campaigngoal['value'])

    def test_campaigngoals_cpa_post(self):
        account = dash.models.Account.objects.get(pk=186)
        pixel = magic_mixer.blend(dash.models.ConversionPixel, account=account)
        test_campaigngoal = self.campaigngoal_repr(
            type=constants.CampaignGoalKPI.CPA,
            value='0.33',
            primary=True,
            conversionGoal=dict(
                type='PIXEL',
                conversionWindow='LEQ_7_DAYS',
                goalId=pixel.id
            )
        )
        post_data = test_campaigngoal.copy()
        del post_data['id']
        r = self.client.post(
            reverse('campaigngoals_list', kwargs={'campaign_id': 608}),
            data=post_data, format='json')
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_campaigngoal(resp_json['data'])


class BudgetsTest(RESTAPITest):

    @classmethod
    def budget_repr(
        cls,
        id=1,
        creditId=1,
        amount='500',
        startDate=datetime.date.today(),
        endDate=datetime.date.today(),
        state=constants.BudgetLineItemState.ACTIVE,
        spend='200.0000',
        available='300.0000',
    ):
        representation = {
            'id': str(id),
            'creditId': str(creditId),
            'amount': str(amount),
            'startDate': startDate,
            'endDate': endDate,
            'state': constants.BudgetLineItemState.get_name(state),
            'spend': spend,
            'available': available,
        }
        return cls.normalize(representation)

    def validate_budget(self, budget):
        budget_db = dash.models.BudgetLineItem.objects.get(pk=budget['id'])
        spend = budget_db.get_spend_data()['etf_total']
        allocated = budget_db.allocated_amount()
        expected = self.budget_repr(
            id=budget_db.id,
            creditId=budget_db.credit.id,
            amount=budget_db.amount,
            startDate=budget_db.start_date,
            endDate=budget_db.end_date,
            state=budget_db.state(),
            spend=spend,
            available=allocated,
        )
        self.assertEqual(expected, budget)

    @mock.patch('dash.forms.dates_helper.local_today', lambda: TODAY)
    def test_campaigns_budgets_list(self):
        r = self.client.get(reverse('campaigns_budget_list', kwargs={'campaign_id': 608}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_budget(item)

    def test_campaigns_budgets_post(self):
        test_budget = self.budget_repr(
            id=1,
            creditId=861,
            amount=500,
            startDate=datetime.date.today() + datetime.timedelta(days=1),
            endDate=datetime.date.today() + datetime.timedelta(days=7),
        )
        r = self.client.post(
            reverse('campaigns_budget_list', kwargs={'campaign_id': 608}),
            data=test_budget, format='json')
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_budget(resp_json['data'])
        self.assertEqual(resp_json['data']['amount'], test_budget['amount'])
        self.assertEqual(resp_json['data']['startDate'], test_budget['startDate'])
        self.assertEqual(resp_json['data']['endDate'], test_budget['endDate'])

    def test_campaigns_budgets_get(self):
        r = self.client.get(reverse('campaigns_budget_details', kwargs={'campaign_id': 608, 'budget_id': 1910}))
        resp_json = self.assertResponseValid(r)
        self.validate_budget(resp_json['data'])

    def test_campaigns_budgets_put(self):
        r = self.client.put(
            reverse('campaigns_budget_details', kwargs={'campaign_id': 608, 'budget_id': 1910}),
            data={'amount': '900'}, format='json'
        )
        resp_json = self.assertResponseValid(r)
        self.validate_budget(resp_json['data'])
        self.assertEqual(resp_json['data']['amount'], '900')


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
