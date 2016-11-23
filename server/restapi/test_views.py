from decimal import Decimal
import datetime
import json
import mock

from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from zemauth.models import User
from django.core.urlresolvers import reverse

import dash.models
import dash.threads
import views as restapi_views
from dash import constants
from dash import upload
import restapi.models
from utils import json_helper
import redshiftapi.quickstats


TODAY = datetime.datetime(2016, 1, 15).date()


def normalize(d):
    return json.loads(json.dumps(d, cls=json_helper.JSONEncoder))


class SerializerTests(TestCase):

    def test_allow_not_provided(self):
        NOT_PROVIDED = restapi_views.NOT_PROVIDED
        d = {'name': 'test', 'tracking': {'ga': {'enabled': True}}}
        new_d = restapi_views.SettingsSerializer._allow_not_provided(d)
        self.assertEqual(new_d['name'], 'test')
        self.assertEqual(new_d['tracking']['ga']['enabled'], True)
        self.assertEqual(new_d['tracking']['ga']['property_id'], NOT_PROVIDED)
        self.assertEqual(new_d['tracking']['adobe']['enabled'], NOT_PROVIDED)


@override_settings(R1_DEMO_MODE=True)
class RESTAPITest(TestCase):
    fixtures = ['test_acceptance.yaml']

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=1))
        self.maxDiff = None

    def assertResponseValid(self, r, status_code=200, data_type=dict):
        self.assertEqual(r.status_code, status_code)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], data_type)
        if data_type == list:
            self.assertGreater(len(resp_json['data']), 0)
        return resp_json


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
        return normalize({
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
        name='My Campaign',
        enable_ga_tracking=True,
        ga_tracking_type=constants.GATrackingType.EMAIL,
        ga_property_id='',
        enable_adobe_tracking=False,
        adobe_tracking_param='cid'
            ):
        representation = {
            'id': str(id),
            'accountId': str(account_id),
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
            }
        }
        return normalize(representation)

    def validate_campaign(self, campaign):
        campaign_db = dash.models.Campaign.objects.get(pk=campaign['id'])
        settings_db = campaign_db.get_current_settings()
        expected = self.campaign_repr(
            id=campaign_db.id,
            account_id=campaign_db.account_id,
            name=campaign_db.name,
            enable_ga_tracking=settings_db.enable_ga_tracking,
            ga_tracking_type=settings_db.ga_tracking_type,
            ga_property_id=settings_db.ga_property_id,
            enable_adobe_tracking=settings_db.enable_adobe_tracking,
            adobe_tracking_param=settings_db.adobe_tracking_param,
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


class CampaignStatsTest(RESTAPITest):

    @mock.patch.object(redshiftapi.quickstats, 'query_campaign', autospec=True)
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
        return normalize(representation)

    def validate_campaigngoal(self, campaigngoal):
        campaigngoal_db = dash.models.CampaignGoal.objects.get(pk=campaigngoal['id'])
        conversiongoal_db = campaigngoal_db.conversion_goal
        expected_conversiongoal = None
        if conversiongoal_db:
            pixel_url = conversiongoal_db.pixel.get_url() if conversiongoal_db.pixel else None
            expected_conversiongoal = dict(
                goalId=conversiongoal_db.goal_id,
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
        return normalize(representation)

    def validate_budget(self, budget):
        budget_db = dash.models.BudgetLineItem.objects.get(pk=budget['id'])
        spend = budget_db.get_spend_data(use_decimal=True)['total']
        allocated = budget_db.allocated_amount()
        expected = self.budget_repr(
            id=budget_db.id,
            amount=budget_db.amount,
            startDate=budget_db.start_date,
            endDate=budget_db.end_date,
            state=budget_db.state(),
            spend=spend,
            available=allocated,
        )
        del expected['creditId']
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

    @classmethod
    def adgroup_repr(
        cls,
        id=1,
        campaign_id=1,
        name='My test ad group',
        state=constants.AdGroupSettingsState.INACTIVE,
        start_date=datetime.date.today(),
        end_date=None,
        max_cpc='0.600',
        daily_budget='15.00',
        tracking_code='a=b',
        target_regions=['US'],
        target_devices=['desktop'],
        interest_targeting=['women', 'fashion'],
        exclusion_interest_targeting=['politics'],
        autopilot_state=constants.AdGroupSettingsAutopilotState.INACTIVE,
        autopilot_daily_budget='50.00',
        dayparting={},
            ):
        representation = {
            'id': str(id),
            'campaignId': str(campaign_id),
            'name': name,
            'state': constants.AdGroupSettingsState.get_name(state),
            'startDate': start_date,
            'endDate': end_date,
            'maxCpc': max_cpc,
            'dailyBudget': daily_budget,
            'trackingCode': tracking_code,
            'targeting': {
                'geo': {
                    'included': {
                        'countries': target_regions,
                        'regions': [],
                        'dma': [],
                    },
                },
                'devices': [constants.AdTargetDevice.get_name(i) for i in target_devices],
                'interest': {
                    'included': [constants.InterestCategory.get_name(i) for i in interest_targeting],
                    'excluded': [constants.InterestCategory.get_name(i) for i in exclusion_interest_targeting],
                }
            },
            'autopilot': {
                'state': constants.AdGroupSettingsAutopilotState.get_name(autopilot_state),
                'dailyBudget': autopilot_daily_budget,
            },
            'dayparting': dayparting,
        }
        return normalize(representation)

    def validate_against_db(self, adgroup):
        adgroup_db = dash.models.AdGroup.objects.get(pk=adgroup['id'])
        settings_db = adgroup_db.get_current_settings()
        expected = self.adgroup_repr(
            id=adgroup_db.id,
            campaign_id=adgroup_db.campaign_id,
            name=adgroup_db.name,
            state=settings_db.state,
            start_date=settings_db.start_date,
            end_date=settings_db.end_date,
            max_cpc=settings_db.cpc_cc.quantize(Decimal('1.000')) if settings_db.cpc_cc else '',
            daily_budget=settings_db.daily_budget_cc.quantize(Decimal('1.00')),
            tracking_code=settings_db.tracking_code,
            target_regions=settings_db.target_regions,
            target_devices=settings_db.target_devices,
            interest_targeting=settings_db.interest_targeting,
            exclusion_interest_targeting=settings_db.exclusion_interest_targeting,
            autopilot_state=settings_db.autopilot_state,
            autopilot_daily_budget=settings_db.autopilot_daily_budget.quantize(Decimal('1.00')),
            dayparting=settings_db.dayparting,
        )
        self.assertEqual(expected, adgroup)

    def test_adgroups_list(self):
        r = self.client.get(reverse('adgroups_list'))
        resp_json = self.assertResponseValid(r, data_type=list)
        for item in resp_json['data']:
            self.validate_against_db(item)

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
        return normalize(representation)

    def validate_against_db(self, ad_group_id, adgroupsourcesettings):
        slug = adgroupsourcesettings['source']
        agss_db = dash.models.AdGroupSource.objects.get(ad_group_id=ad_group_id, source__tracking_slug=slug).get_current_settings()
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
        daily_budget='50.00',
        state=constants.AdGroupSourceSettingsState.ACTIVE
            ):
        representation = {
            'groupEnabled': group_enabled,
            'dailyBudget': daily_budget,
            'state': constants.AdGroupSourceSettingsState.get_name(state),
        }
        return normalize(representation)

    def validate_against_db(self, ad_group_id, agsrtb):
        settings_db = dash.models.AdGroup.objects.get(pk=ad_group_id).get_current_settings()
        expected = self.adgroupsourcertb_repr(
            group_enabled=settings_db.b1_sources_group_enabled,
            daily_budget=settings_db.b1_sources_group_daily_budget.quantize(Decimal('1.00')),
            state=settings_db.b1_sources_group_state
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
            state=constants.AdGroupSettingsState.ACTIVE
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
        return normalize(representation)

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


class PublisherBlacklistTest(RESTAPITest):

    def test_adgroups_publishers_list(self):
        r = self.client.get(reverse('publishers_list', kwargs={'ad_group_id': 2040}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], list)
        self.assertGreater(len(resp_json['data']), 0)
        expected_fields = ['status', 'source', 'externalId', 'name', 'level']
        for item in resp_json['data']:
            self.assertEqual(item.keys(), expected_fields)

    def test_adgroups_publishers_put(self):
        pass


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


class ReportsTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=User.objects.get(pk=1))

    @mock.patch('dash.threads.AsyncFunction', dash.threads.MockAsyncFunction)
    @mock.patch('restapi.reports.ReportJobExecutor', restapi.reports.MockJobExecutor)
    def test_new_job(self):
        query = {
            'fields': [{'field': 'Content Ad Id'}],
            'filters': [{'field': 'Ad Group Id', 'operator': '=', 'value': '123'},
                        {'field': 'Date', 'operator': '=', 'value': '2016-10-10'}]
        }
        r = self.client.post(reverse('reports_list'), query, format='json')
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'IN_PROGRESS')
        self.assertIn('id', resp_json['data'])

        job_id = int(resp_json['data']['id'])
        job = restapi.models.ReportJob.objects.get(pk=job_id)
        job.status = constants.ReportJobStatus.DONE
        job.save()

        r = self.client.get(reverse('reports_details', kwargs={'job_id': job_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json['data'], dict)
        self.assertEqual(resp_json['data']['status'], 'DONE')
        self.assertEqual(job_id, int(resp_json['data']['id']))
