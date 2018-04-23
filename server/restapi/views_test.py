from decimal import Decimal
import string
import datetime
import json
import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from zemauth.models import User
from django.core.urlresolvers import reverse

from core import source
import dash.models
from . import fields
from . import views as restapi_views
from dash import constants
import redshiftapi.api_quickstats
from automation import autopilot

from utils import json_helper
from utils import test_helper
from utils.magic_mixer import magic_mixer

import restapi.serializers.targeting


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


class AdGroupsTest(RESTAPITest):

    def adgroup_repr(
        cls,
        id=1,
        campaign_id=1,
        name='My test ad group',
        state=constants.AdGroupSettingsState.INACTIVE,
        archived=False,
        start_date=datetime.date.today(),
        end_date=None,
        max_cpc='0.600',
        max_cpm='1.700',
        daily_budget='15.00',
        tracking_code='a=b',
        target_regions={'countries': ['US'], 'postalCodes': ['CA:12345']},
        exclusion_target_regions={},
        target_devices=[constants.AdTargetDevice.DESKTOP],
        target_placements=[constants.Placement.APP],
        target_os=[{'name': constants.OperatingSystem.ANDROID}],
        target_browsers=[{'family': constants.BrowserFamily.CHROME}],
        interest_targeting=['women', 'fashion'],
        exclusion_interest_targeting=['politics'],
        demographic_targeting=['and', 'bluekai:671901', ['or', 'lotame:123', 'outbrain:123']],
        autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        autopilot_daily_budget='50.00',
        dayparting={},
        whitelist_publisher_groups=[153],
        blacklist_publisher_groups=[154],
        audience_targeting=[123],
        exclusion_audience_targeting=[124],
        retargeting_ad_groups=[2050],
        exclusion_retargeting_ad_groups=[2051],
        delivery_type=constants.AdGroupDeliveryType.STANDARD,
        click_capping_daily_ad_group_max_clicks=120,
        click_capping_daily_click_budget='12.0000',
    ):
        final_target_regions = {
            'countries': [],
            'regions': [],
            'dma': [],
            'cities': [],
            'postalCodes': []
        }
        final_target_regions.update(target_regions)
        final_exclusion_target_regions = {
            'countries': [],
            'regions': [],
            'dma': [],
            'cities': [],
            'postalCodes': []
        }
        final_exclusion_target_regions.update(exclusion_target_regions)

        representation = {
            'id': str(id),
            'campaignId': str(campaign_id),
            'name': name,
            'state': constants.AdGroupSettingsState.get_name(state),
            'archived': archived,
            'startDate': start_date,
            'endDate': end_date,
            'maxCpc': max_cpc,
            'maxCpm': max_cpm,
            'dailyBudget': daily_budget,
            'trackingCode': tracking_code,
            'targeting': {
                'geo': {
                    'included': final_target_regions,
                    'excluded': final_exclusion_target_regions,
                },
                'devices': restapi.serializers.targeting.DevicesSerializer(target_devices).data,
                'placements': restapi.serializers.targeting.PlacementsSerializer(target_placements).data,
                'os': restapi.serializers.targeting.OSsSerializer(target_os).data,
                'browsers': restapi.serializers.targeting.BrowsersSerializer(target_browsers).data,
                'interest': {
                    'included': [constants.InterestCategory.get_name(i) for i in interest_targeting],
                    'excluded': [constants.InterestCategory.get_name(i) for i in exclusion_interest_targeting],
                },
                'audience': restapi.serializers.targeting.AudienceSerializer(demographic_targeting).data,
                'demographic': demographic_targeting,
                'publisherGroups': {
                    'included': whitelist_publisher_groups,
                    'excluded': blacklist_publisher_groups,
                },
                'customAudiences': {
                    'included': audience_targeting,
                    'excluded': exclusion_audience_targeting,
                },
                'retargetingAdGroups': {
                    'included': retargeting_ad_groups,
                    'excluded': exclusion_retargeting_ad_groups,
                }
            },
            'autopilot': {
                'state': constants.AdGroupSettingsAutopilotState.get_name(autopilot_state),
                'dailyBudget': autopilot_daily_budget,
            },
            'dayparting': dayparting,
            'deliveryType': constants.AdGroupDeliveryType.get_name(delivery_type),
            'clickCappingDailyAdGroupMaxClicks': click_capping_daily_ad_group_max_clicks,
            'clickCappingDailyClickBudget': click_capping_daily_click_budget,
        }

        return cls.normalize(representation)

    @staticmethod
    def _partition_regions(target_regions):
        """ non-exact heuristics in order to not reimplement functionality in tests """
        geo = {
            'countries': [],
            'regions': [],
            'dma': [],
            'cities': [],
            'postalCodes': []
        }
        for tr in target_regions:
            if len(tr) == 2 and all(char in string.ascii_uppercase for char in tr):
                geo['countries'].append(tr)
            elif 5 <= len(tr) <= 6 and '-' in tr:
                geo['regions'].append(tr)
            elif ':' in tr:
                geo['postalCodes'].append(tr)
            elif len(tr) == 3:
                geo['dma'].append(tr)
            else:
                geo['cities'].append(int(tr))
        return geo

    def validate_against_db(self, adgroup):
        adgroup_db = dash.models.AdGroup.objects.get(pk=adgroup['id'])
        settings_db = adgroup_db.get_current_settings()
        expected = self.adgroup_repr(
            id=adgroup_db.id,
            campaign_id=adgroup_db.campaign_id,
            name=settings_db.ad_group_name,
            state=settings_db.state,
            archived=settings_db.archived,
            start_date=settings_db.start_date,
            end_date=settings_db.end_date,
            max_cpc=settings_db.cpc_cc.quantize(Decimal('1.000')) if settings_db.cpc_cc else '',
            max_cpm=settings_db.max_cpm.quantize(Decimal('1.000')) if settings_db.max_cpm else '',
            daily_budget=settings_db.daily_budget_cc.quantize(Decimal('1.00')),
            tracking_code=settings_db.tracking_code,
            target_regions=self._partition_regions(settings_db.target_regions),
            interest_targeting=settings_db.interest_targeting,
            exclusion_interest_targeting=settings_db.exclusion_interest_targeting,
            demographic_targeting=settings_db.bluekai_targeting,
            autopilot_state=settings_db.autopilot_state,
            autopilot_daily_budget=settings_db.autopilot_daily_budget.quantize(Decimal('1.00')),
            dayparting=settings_db.dayparting,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
            audience_targeting=settings_db.audience_targeting,
            exclusion_audience_targeting=settings_db.exclusion_audience_targeting,
            retargeting_ad_groups=settings_db.retargeting_ad_groups,
            exclusion_retargeting_ad_groups=settings_db.exclusion_retargeting_ad_groups,
            target_devices=settings_db.target_devices,
            target_placements=settings_db.target_placements,
            target_os=settings_db.target_os,
            target_browsers=settings_db.target_browsers,
            click_capping_daily_ad_group_max_clicks=settings_db.click_capping_daily_ad_group_max_clicks,
            click_capping_daily_click_budget=settings_db.click_capping_daily_click_budget,
        )
        self.assertEqual(expected, adgroup)

    def test_adgroups_list(self):
        r = self.client.get(reverse('adgroups_list'))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)

    def test_adgroups_list_pagination(self):
        campaign = magic_mixer.blend(dash.models.Campaign, account__users=[self.user])
        magic_mixer.cycle(10).blend(dash.models.AdGroup, campaign=campaign)
        r = self.client.get(reverse('adgroups_list'), {'campaignId': campaign.id})
        r_paginated = self.client.get(reverse('adgroups_list'), {'campaignId': campaign.id, 'limit': 2, 'offset': 5})
        resp_json = self.assertResponseValid(r, data_type=list)
        resp_json_paginated = self.assertResponseValid(r_paginated, data_type=list)
        self.assertEqual(resp_json['data'][5:7], resp_json_paginated['data'])

    def test_adgroups_list_campaign_filter(self):
        # TODO(nsaje): create a prettier test, this one is urgent and hackish
        account1 = magic_mixer.blend(dash.models.Account, users=[self.user])
        adgroup1_account1 = magic_mixer.blend(dash.models.AdGroup, campaign__account=account1)
        adgroup1_account1.get_current_settings().copy_settings().save(None)
        adgroup2_account1 = magic_mixer.blend(dash.models.AdGroup, campaign__account=account1)
        adgroup2_account1.get_current_settings().copy_settings().save(None)
        account2 = magic_mixer.blend(dash.models.Account)
        adgroup1_account2 = magic_mixer.blend(dash.models.AdGroup, campaign__account=account2)
        adgroup1_account2.get_current_settings().copy_settings().save(None)

        r = self.client.get(reverse('adgroups_list'), {'campaignId': adgroup1_account1.campaign_id})
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)
        self.assertEqual(len(resp_json['data']), 1)
        self.assertEqual(resp_json['data'][0]['id'], str(adgroup1_account1.id))

    def test_adgroups_post(self):
        r = self.client.post(
            reverse('adgroups_list'),
            data={'campaignId': 608, 'name': 'test adgroup'}, format='json')
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data']['name'], 'test adgroup')

    def test_adgroups_get(self):
        r = self.client.get(reverse('adgroups_details', kwargs={'entity_id': 2040}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])

    def test_adgroups_put(self):
        test_adgroup = self.adgroup_repr(id=2040, campaign_id=608)
        r = self.client.put(
            reverse('adgroups_details', kwargs={'entity_id': 2040}),
            data=test_adgroup, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data'], test_adgroup)

    def test_adgroups_put_state(self):
        r = self.client.put(
            reverse('adgroups_details', kwargs={'entity_id': 2040}),
            data={'state': 'INACTIVE'}, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data']['state'], 'INACTIVE')

    def test_adgroups_put_archive_restore(self):
        r = self.client.put(
            reverse('adgroups_details', kwargs={'entity_id': 2040}),
            data={'archived': True}, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data']['archived'], True)

        r = self.client.put(
            reverse('adgroups_details', kwargs={'entity_id': 2040}),
            data={'archived': False}, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data']['archived'], False)

    @mock.patch.object(autopilot, 'recalculate_budgets_ad_group', autospec=True)
    def test_adgroups_put_autopilot_budget(self, mock_autopilot):
        ag = dash.models.AdGroup.objects.get(pk=2040)
        new_settings = ag.get_current_settings().copy_settings()
        new_settings.b1_sources_group_enabled = True
        new_settings.save(None)
        test_adgroup = self.adgroup_repr(
            id=2040, campaign_id=608,
            autopilot_state=constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET,
            autopilot_daily_budget='20.00')
        r = self.client.put(
            reverse('adgroups_details', kwargs={'entity_id': 2040}),
            data=test_adgroup, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data'], test_adgroup)


class AdGroupSourcesRTBTest(RESTAPITest):

    @classmethod
    def adgroupsourcertb_repr(
        cls,
        group_enabled=True,
        daily_budget=source.AllRTBSource.default_daily_budget_cc,
        state=constants.AdGroupSourceSettingsState.ACTIVE,
        cpc=source.AllRTBSource.default_cpc_cc,
    ):
        representation = {
            'groupEnabled': group_enabled,
            'dailyBudget': daily_budget,
            'state': constants.AdGroupSourceSettingsState.get_name(state),
            'cpc': cpc
        }
        return cls.normalize(representation)

    def validate_against_db(self, ad_group_id, agsrtb):
        settings_db = dash.models.AdGroup.objects.get(pk=ad_group_id).get_current_settings()
        expected = self.adgroupsourcertb_repr(
            group_enabled=settings_db.b1_sources_group_enabled,
            daily_budget=settings_db.b1_sources_group_daily_budget.quantize(Decimal('1.00')),
            state=settings_db.b1_sources_group_state,
            cpc=settings_db.b1_sources_group_cpc_cc,
        )
        self.assertEqual(expected, agsrtb)

    def test_adgroups_sources_rtb_get(self):
        r = self.client.get(reverse('adgroups_sources_rtb_details', kwargs={'ad_group_id': 2040}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json['data'])

    def test_adgroups_sources_rtb_put(self):
        test_rtbs = self.adgroupsourcertb_repr(
            group_enabled=True,
            daily_budget='12.38',
            state=constants.AdGroupSettingsState.ACTIVE,
            cpc='0.1230'
        )
        r = self.client.put(
            reverse('adgroups_sources_rtb_details', kwargs={'ad_group_id': 2040}),
            data=test_rtbs, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json['data'])
        self.assertEqual(test_rtbs, resp_json['data'])

    def test_adgroups_sources_rtb_put_default_values(self):
        test_rtbs = self.adgroupsourcertb_repr(
            group_enabled=True,
            state=constants.AdGroupSettingsState.ACTIVE,
        )
        r = self.client.put(
            reverse('adgroups_sources_rtb_details', kwargs={'ad_group_id': 2040}),
            data=test_rtbs, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(2040, resp_json['data'])
        self.assertEqual(test_rtbs, resp_json['data'])


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
