from decimal import Decimal
import string
import datetime
import json
import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from zemauth.models import User
from django.core.urlresolvers import reverse

import dash.models
import fields
import views as restapi_views
from dash import constants
import redshiftapi.api_quickstats
from automation import autopilot_plus

from dash.features import contentupload
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

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.get(pk=1)
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


class AccountCreditsTest(RESTAPITest):

    @classmethod
    def credit_repr(
        cls,
        id=123,
        createdOn=datetime.datetime.now(),
        startDate=datetime.date.today(),
        endDate=datetime.date.today(),
        total='500',
        allocated='200.0',
        available='300.0',
    ):
        return cls.normalize({
            'id': id,
            'createdOn': createdOn,
            'startDate': startDate,
            'endDate': endDate,
            'total': total,
            'allocated': allocated,
            'available': available,
        })

    def validate_credit(self, credit):
        credit_db = dash.models.CreditLineItem.objects.get(pk=credit['id'])
        expected = self.credit_repr(
            id=str(credit_db.id),
            createdOn=credit_db.created_dt.date(),
            startDate=credit_db.start_date,
            endDate=credit_db.end_date,
            total=credit_db.effective_amount(),
            allocated=credit_db.get_allocated_amount(),
            available=credit_db.effective_amount() - credit_db.get_allocated_amount(),
        )
        self.assertEqual(expected, credit)

    def test_account_credits_list(self):
        r = self.client.get(reverse('accounts_credits_list', kwargs={'account_id': 186}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_credit(item)


class CampaignsTest(RESTAPITest):

    @classmethod
    def campaign_repr(
        cls,
        id=123,
        account_id=321,
        archived=False,
        iab_category=constants.IABCategory.IAB1_1,
        name='My Campaign',
        enable_ga_tracking=True,
        ga_tracking_type=constants.GATrackingType.EMAIL,
        ga_property_id='',
        enable_adobe_tracking=False,
        adobe_tracking_param='cid',
        whitelist_publisher_groups=[153],
        blacklist_publisher_groups=[154],
        target_devices=[constants.AdTargetDevice.DESKTOP],
        target_placements=[constants.Placement.APP],
        target_os=[{'name': constants.OperatingSystem.ANDROID}, {'name': constants.OperatingSystem.LINUX}],
    ):
        representation = {
            'id': str(id),
            'accountId': str(account_id),
            'archived': archived,
            'iabCategory': constants.IABCategory.get_name(iab_category),
            'name': name,
            'tracking': {
                'ga': {
                    'enabled': enable_ga_tracking,
                    'type': constants.GATrackingType.get_name(ga_tracking_type),
                    'webPropertyId': ga_property_id,
                },
                'adobe': {
                    'enabled': enable_adobe_tracking,
                    'trackingParameter': adobe_tracking_param,
                }
            },
            'targeting': {
                'devices': restapi.serializers.targeting.DevicesSerializer(target_devices).data,
                'placements': restapi.serializers.targeting.PlacementsSerializer(target_placements).data,
                'os': restapi.serializers.targeting.OSsSerializer(target_os).data,
                'publisherGroups': {
                    'included': whitelist_publisher_groups,
                    'excluded': blacklist_publisher_groups,
                }
            },
        }
        return cls.normalize(representation)

    def validate_campaign(self, campaign):
        campaign_db = dash.models.Campaign.objects.get(pk=campaign['id'])
        settings_db = campaign_db.get_current_settings()
        expected = self.campaign_repr(
            id=campaign_db.id,
            account_id=campaign_db.account_id,
            archived=settings_db.archived,
            iab_category=settings_db.iab_category,
            name=campaign_db.name,
            enable_ga_tracking=settings_db.enable_ga_tracking,
            ga_tracking_type=settings_db.ga_tracking_type,
            ga_property_id=settings_db.ga_property_id,
            enable_adobe_tracking=settings_db.enable_adobe_tracking,
            adobe_tracking_param=settings_db.adobe_tracking_param,
            whitelist_publisher_groups=settings_db.whitelist_publisher_groups,
            blacklist_publisher_groups=settings_db.blacklist_publisher_groups,
            target_devices=settings_db.target_devices,
            target_placements=settings_db.target_placements,
            target_os=settings_db.target_os,
        )
        self.assertEqual(expected, campaign)

    def test_campaigns_list(self):
        r = self.client.get(reverse('campaigns_list'))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_campaign(item)

    def test_campaigns_post(self):
        r = self.client.post(reverse('campaigns_list'), {'accountId': 186, 'name': 'test campaign'}, format='json')
        resp_json = self.assertResponseValid(r, data_type=dict, status_code=201)
        self.validate_campaign(resp_json['data'])

    def test_campaigns_get(self):
        r = self.client.get(reverse('campaigns_details', kwargs={'entity_id': 608}))
        resp_json = self.assertResponseValid(r)
        self.validate_campaign(resp_json['data'])

    def test_campaigns_put(self):
        test_campaign = self.campaign_repr(id=608, account_id=186, name="My test campaign!")
        put_data = test_campaign.copy()
        del put_data['id']
        del put_data['accountId']
        r = self.client.put(reverse('campaigns_details', kwargs={'entity_id': 608}), test_campaign, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_campaign(resp_json['data'])
        self.assertEqual(resp_json['data'], test_campaign)

    def test_campaigns_put_empty(self):
        put_data = {}
        settings_count = dash.models.CampaignSettings.objects.filter(campaign_id=608).count()
        r = self.client.put(reverse('campaigns_details', kwargs={'entity_id': 608}), put_data, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_campaign(resp_json['data'])
        self.assertEqual(settings_count, dash.models.CampaignSettings.objects.filter(campaign_id=608).count())

    def test_campaigns_put_archive_restore(self):
        r = self.client.put(
            reverse('campaigns_details', kwargs={'entity_id': 308}),
            data={'archived': True}, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_campaign(resp_json['data'])
        self.assertEqual(resp_json['data']['archived'], True)

        r = self.client.put(
            reverse('campaigns_details', kwargs={'entity_id': 308}),
            data={'archived': False}, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_campaign(resp_json['data'])
        self.assertEqual(resp_json['data']['archived'], False)


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
        target_regions={'countries': ['US']},
        exclusion_target_regions={},
        target_devices=[constants.AdTargetDevice.DESKTOP],
        target_placements=[constants.Placement.APP],
        target_os=[{'name': constants.OperatingSystem.ANDROID}],
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
                target_regions['regions'].append(tr)
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
            click_capping_daily_ad_group_max_clicks=settings_db.click_capping_daily_ad_group_max_clicks,
        )
        self.assertEqual(expected, adgroup)

    def test_adgroups_list(self):
        r = self.client.get(reverse('adgroups_list'))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)

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

    @mock.patch.object(autopilot_plus, 'initialize_budget_autopilot_on_ad_group', autospec=True)
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


class AdGroupSourcesTest(RESTAPITest):

    @classmethod
    def adgroupsource_repr(
        cls,
        source='yahoo',
        cpc='0.600',
        daily_budget='50.00',
        state=constants.AdGroupSourceSettingsState.ACTIVE
    ):
        representation = {
            'source': source,
            'cpc': cpc,
            'dailyBudget': daily_budget,
            'state': constants.AdGroupSourceSettingsState.get_name(state),
        }
        return cls.normalize(representation)

    def validate_against_db(self, ad_group_id, adgroupsourcesettings):
        slug = adgroupsourcesettings['source']
        agss_db = dash.models.AdGroupSource.objects.get(ad_group_id=ad_group_id, source__bidder_slug=slug).get_current_settings()
        expected = self.adgroupsource_repr(
            source=slug,
            cpc=agss_db.cpc_cc,
            daily_budget=agss_db.daily_budget_cc,
            state=agss_db.state,
        )
        self.assertEqual(expected, adgroupsourcesettings)

    def test_adgroups_sources_list(self):
        r = self.client.get(reverse('adgroups_sources_list', kwargs={'ad_group_id': 2040}))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(2040, item)

    def test_adgroups_sources_put(self):
        test_ags = self.adgroupsource_repr(
            source='gumgum',
            daily_budget='12.38',
            cpc='0.612',
            state=constants.AdGroupSourceSettingsState.INACTIVE
        )
        r = self.client.put(reverse('adgroups_sources_list', kwargs={'ad_group_id': 2040}), [test_ags], format='json')
        resp_json = self.assertResponseValid(r, data_type=list)
        self.validate_against_db(2040, resp_json['data'][0])


class AdGroupSourcesRTBTest(RESTAPITest):

    @classmethod
    def adgroupsourcertb_repr(
        cls,
        group_enabled=True,
        daily_budget=constants.SourceAllRTB.DEFAULT_DAILY_BUDGET,
        state=constants.AdGroupSourceSettingsState.ACTIVE,
        cpc=constants.SourceAllRTB.DEFAULT_CPC_CC
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


class ContentAdsTest(RESTAPITest):

    @classmethod
    def contentad_repr(
        cls,
        id=1,
        ad_group_id=1,
        state=constants.ContentAdSourceState.ACTIVE,
        url='https://www.example.com',
        title='My title',
        image_url='https://www.example.com/img',
        display_url='https://www.example.com/landing',
        brand_name='My brand',
        description='My description',
        call_to_action='Read more...',
        label='My label',
        image_crop='center',
        tracker_urls=[]
    ):
        representation = {
            'id': str(id),
            'adGroupId': str(ad_group_id),
            'state': constants.ContentAdSourceState.get_name(state),
            'url': url,
            'title': title,
            'imageUrl': image_url,
            'displayUrl': display_url,
            'brandName': brand_name,
            'description': description,
            'callToAction': call_to_action,
            'label': label,
            'imageCrop': image_crop,
            'trackerUrls': tracker_urls,
        }
        return cls.normalize(representation)

    def validate_against_db(self, cad):
        cad_db = dash.models.ContentAd.objects.get(pk=cad['id'])
        expected = self.contentad_repr(
            id=cad_db.pk,
            ad_group_id=cad_db.ad_group_id,
            state=cad_db.state,
            url=cad_db.url,
            title=cad_db.title,
            image_url=cad_db.get_image_url(),
            display_url=cad_db.display_url,
            brand_name=cad_db.brand_name,
            description=cad_db.description,
            call_to_action=cad_db.call_to_action,
            label=cad_db.label,
            image_crop=cad_db.image_crop,
            tracker_urls=cad_db.tracker_urls,
        )
        self.assertEqual(expected, cad)

    def test_contentads_list(self):
        r = self.client.get(reverse('contentads_list') + '?adGroupId=2040')
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)

    def test_contentads_get(self):
        r = self.client.get(reverse('contentads_details', kwargs={'content_ad_id': 16805}))
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])

    def test_contentads_put(self):
        r = self.client.put(
            reverse('contentads_details', kwargs={'content_ad_id': 16805}),
            data={'state': 'INACTIVE'}, format='json')
        resp_json = self.assertResponseValid(r)
        self.validate_against_db(resp_json['data'])
        self.assertEqual(resp_json['data']['state'], 'INACTIVE')

    def test_contentads_put_without_state(self):
        r = self.client.put(
            reverse('contentads_details', kwargs={'content_ad_id': 16805}),
            data={'title': 'test'}, format='json')
        self.assertResponseError(r, 'ValidationError')


@override_settings(R1_DEMO_MODE=True)
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

    @mock.patch('dash.features.contentupload.upload._invoke_external_validation', mock.Mock())
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
        contentupload.upload._handle_auto_save(batch)

    @mock.patch('dash.features.contentupload.upload._invoke_external_validation', mock.Mock())
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
        contentupload.upload._handle_auto_save(batch)


class PublisherGroupTest(RESTAPITest):
    fixtures = ['test_publishers.yaml']

    def setUp(self):
        super(PublisherGroupTest, self).setUp()
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
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=2))
        r = self.client.put(reverse('publisher_group_details', kwargs={
            'account_id': 1,
            'publisher_group_id': 1,
        }), data={'name': 'test'}, format='json')
        self.assertEqual(r.status_code, 403)


class PublisherGroupEntryTest(RESTAPITest):
    fixtures = ['test_publishers.yaml']

    def setUp(self):
        super(PublisherGroupEntryTest, self).setUp()
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
        self.assertItemsEqual([x['id'] for x in response['data']], ['1', '2'])

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
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=2))
        r = self.client.get(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 2, 'entry_id': 3}))
        self.assertEqual(r.status_code, 403)

    def test_no_outbrain_permission(self):
        user = User.objects.get(pk=2)
        test_helper.add_permissions(user, ['can_use_restapi', 'can_edit_publisher_groups'])

        self.client = APIClient()
        self.client.force_authenticate(user=user)

        r = self.client.get(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 2, 'entry_id': 3}))
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'], check_outbrain_pub_id=False)

        r = self.client.put(reverse('publisher_group_entry_details', kwargs={'publisher_group_id': 2, 'entry_id': 3}),
                            data={'publisher': 'cnn', 'source': 'gravity', 'outbrainPublisherId': '123'},
                            format='json')
        response = self.assertResponseValid(r, data_type=dict, status_code=200)
        self.validate_against_db(response['data'], check_outbrain_pub_id=False)

        # validate outbrainPublisherId was not changed
        self.assertEqual(dash.models.PublisherGroupEntry.objects.get(pk=3).outbrain_publisher_id, '')
