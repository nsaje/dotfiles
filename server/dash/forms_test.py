# -*- coding: utf-8 -*-
import unicodecsv
import datetime
from decimal import Decimal
import StringIO

from django.forms import ValidationError
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Permission
from mock import patch, Mock

from dash import constants
from dash import forms
from dash import models
from utils import test_helper
from zemauth.models import User
from utils.test_helper import ListMatcher
from utils.magic_mixer import magic_mixer

EXAMPLE_CSV_CONTENT = [
    forms.EXAMPLE_CSV_CONTENT['url'],
    forms.EXAMPLE_CSV_CONTENT['title'],
    forms.EXAMPLE_CSV_CONTENT['image_url'],
    'Tech Talk with Zemanta: How Content Ads Will Come to Dominant Publishers Advertising Efforts',
    'https://www.example.com/tracker',
]


class AccountSettingsFormTest(TestCase):
    fixtures = ['test_views.yaml']

    def setUp(self):
        self.account = models.Account.objects.get(pk=1)

    @classmethod
    def setUpClass(cls):
        super(AccountSettingsFormTest, cls).setUpClass()  # loads fixtures
        permission = Permission.objects.get(codename='campaign_settings_sales_rep')
        user = User.objects.get(pk=2)
        user.user_permissions.add(permission)
        user.save()

    def test_invalid_sales_rep(self):
        form = forms.AccountSettingsForm(self.account, {
            'id': 1,
            'name': 'Name',
            'default_account_manager': 2,
            'default_sales_representative': 3,
            'allowed_sources': {'1': {'name': 'Source name'}}
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('default_sales_representative'))

    def test_invalid_cs_rep(self):
        form = forms.AccountSettingsForm(self.account, {
            'id': 1,
            'name': 'Name',
            'default_account_manager': 2,
            'default_sales_representative': 2,
            'default_cs_representative': 3,
            'allowed_sources': {'1': {'name': 'Source name'}}
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('default_cs_representative'))

    def test_invalid_account_manager(self):
        account_manager_id = 123
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=account_manager_id)

        form = forms.AccountSettingsForm(self.account, {
            'id': 1,
            'name': 'Name',
            'default_account_manager': account_manager_id,
            'default_sales_representative': 2,
            'allowed_sources': {'1': {'name': 'Source name'}}
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('default_account_manager'))

    def test_invalid_account_type(self):
        form = forms.AccountSettingsForm(self.account, {
            'id': 1,
            'name': 'Name',
            'account_type': 'invalid'
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('account_type'))

    def test_allowed_sources(self):
        form = forms.AccountSettingsForm(self.account, {
            'id': 1,
            'name': 'Name',
            'default_account_manager': 3,
            'default_sales_representative': 2,
            'allowed_sources': {'1': {'name': 'Source name', 'allowed': False}}
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['allowed_sources'],
                         {1: {'name': 'Source name', 'allowed': False}}
                         )

    def test_publisher_groups(self):
        form = forms.AccountSettingsForm(self.account, {
            'id': 1,
            'name': 'Name',
            'default_account_manager': 3,
            'default_sales_representative': 2,
            'whitelist_publisher_groups': [1],
            'blacklist_publisher_groups': [1],
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['whitelist_publisher_groups'], [1])
        self.assertEqual(form.cleaned_data['blacklist_publisher_groups'], [1])

    def _gen_allowed_sources_form(self, allowed_sources_dict):
        return forms.AccountSettingsForm(self.account, {
            'id': 1,
            'name': 'Name',
            'default_account_manager': 3,
            'default_sales_representative': 2,
            'allowed_sources': allowed_sources_dict
        })

    def test_invalid_allowed_sources_list(self):
        form = self._gen_allowed_sources_form([])
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('allowed_sources'))

    def test_invalid_allowed_sources_int_as_key(self):
        form = self._gen_allowed_sources_form({1: {}})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('allowed_sources'))

    def test_invalid_allowed_sources_list_as_payload(self):
        form = self._gen_allowed_sources_form({'1': []})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('allowed_sources'))

    def test_invalid_allowed_sources_non_int_string(self):
        form = self._gen_allowed_sources_form({'string': {}})
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('allowed_sources'))


class AdGroupAdminFormTest(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        self.request = Mock()
        user = User()
        user.save()
        self.request.user = user

    def test_instance_without_settings(self):
        ad_group = models.AdGroup(
            name='Test',
            campaign_id=1,
        )
        ad_group.save(self.request)
        form = forms.AdGroupAdminForm(
            instance=ad_group
        )
        self.assertEqual('', form.initial['notes'])
        self.assertEqual([], form.initial['bluekai_targeting'])
        self.assertEqual([], form.initial['interest_targeting'])
        self.assertEqual([], form.initial['exclusion_interest_targeting'])
        self.assertEqual([], form.initial['redirect_pixel_urls'])
        self.assertEqual('', form.initial['redirect_javascript'])

    def test_instance_with_settings(self):
        ad_group = models.AdGroup(
            name='Test',
            campaign_id=1,
        )
        ad_group.save(self.request)
        settings = ad_group.get_current_settings().copy_settings()
        settings.notes = 'a'
        settings.bluekai_targeting = ['a']
        settings.interest_targeting = ['a']
        settings.exclusion_interest_targeting = ['a']
        settings.redirect_pixel_urls = ['a']
        settings.redirect_javascript = 'alert("a");'
        settings.save(None)

        form = forms.AdGroupAdminForm(
            instance=ad_group
        )
        self.assertEqual('a', form.initial['notes'])
        self.assertEqual(['a'], form.initial['bluekai_targeting'])
        self.assertEqual(['a'], form.initial['interest_targeting'])
        self.assertEqual(['a'], form.initial['exclusion_interest_targeting'])
        self.assertEqual(['a'], form.initial['redirect_pixel_urls'])
        self.assertEqual('alert("a");', form.initial['redirect_javascript'])


class CampaignSettingsFormTest(TestCase):
    fixtures = ['test_models.yaml', 'test_geolocations']

    def setUp(self):
        self.campaign = models.Campaign.objects.get(pk=1)

        self.user = User.objects.get(pk=1)
        self.data = {
            'id': '1',
            'name': 'Test campaign',
            'campaign_manager': self.user.pk,
            'iab_category': 'IAB1',
            'campaign_goal': 2,
            'goal_quantity': 10,
            'target_devices': ['DESKTOP', 'MOBILE'],
            'target_os': [{'name': 'IOS'}],
            'target_placements': ['SITE'],
            'target_regions': {'countries': ['US']},
            'exclusion_target_regions': {'postal_codes': ['US:12345']},
            'enable_ga_tracking': True,
            'ga_tracking_type': 2,
            'ga_property_id': 'UA-123456789-1',
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
        }

    @patch('utils.dates_helper.local_today')
    def test_form(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        form = forms.CampaignSettingsForm(self.campaign, self.data)

        self.assertTrue(form.is_valid())

        self.maxDiff = None
        self.assertEqual(form.cleaned_data, {
            'id': 1,
            'name': 'Test campaign',
            'campaign_manager': self.user,
            'iab_category': constants.IABCategory.IAB1,
            'campaign_goal': 2,
            'goal_quantity': Decimal('10'),
            'target_devices': ['desktop', 'mobile'],
            'target_os': [{'name': 'ios'}],
            'target_placements': ['site'],
            'target_regions': ['US'],
            'exclusion_target_regions': ['US:12345'],
            'enable_ga_tracking': True,
            'ga_tracking_type': 2,
            'ga_property_id': 'UA-123456789-1',
            'enable_adobe_tracking': False,
            'adobe_tracking_param': '',
            'whitelist_publisher_groups': [],
            'blacklist_publisher_groups': [],
        })

    @patch('utils.dates_helper.local_today')
    def test_default_value_enable_ga_tracking(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_ga_tracking', form.cleaned_data)
        self.assertTrue(form.cleaned_data['enable_ga_tracking'])

        del self.data['enable_ga_tracking']

        # should be True if not set
        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_ga_tracking', form.cleaned_data)
        self.assertTrue(form.cleaned_data['enable_ga_tracking'])

        self.data['enable_ga_tracking'] = False

        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_ga_tracking', form.cleaned_data)
        self.assertFalse(form.cleaned_data['enable_ga_tracking'])

    @patch('utils.dates_helper.local_today')
    def test_default_value_enable_adobe_tracking(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        # should be False if not set
        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_adobe_tracking', form.cleaned_data)

        # We need to use assertEqual here, because assertFalse passes
        # even if the value is falsy (None), which is not ok here
        self.assertEqual(form.cleaned_data['enable_adobe_tracking'], False)

        self.data['enable_adobe_tracking'] = False
        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_adobe_tracking', form.cleaned_data)
        self.assertEqual(form.cleaned_data['enable_adobe_tracking'], False)

        self.data['enable_adobe_tracking'] = True
        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_adobe_tracking', form.cleaned_data)
        self.assertEqual(form.cleaned_data['enable_adobe_tracking'], True)

    @patch('utils.dates_helper.local_today')
    def test_ga_tracking_type_email(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['ga_tracking_type'] = 1
        self.data['ga_property_id'] = 'abcd'

        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('ga_property_id', form.cleaned_data)
        self.assertIsNone(form.cleaned_data['ga_property_id'])

    @patch('utils.dates_helper.local_today')
    def test_ga_tracking_disabled(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['enable_ga_tracking'] = False
        self.data['ga_tracking_type'] = 2
        self.data['ga_property_id'] = 'abcd'

        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('ga_property_id', form.cleaned_data)
        self.assertIsNone(form.cleaned_data['ga_property_id'])

    @patch('utils.dates_helper.local_today')
    def test_ga_property_id_missing(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['ga_tracking_type'] = 2
        self.data['ga_property_id'] = ''

        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('ga_property_id', form.errors)
        self.assertEqual(form.errors['ga_property_id'], ['Web property ID is required.'])

    @patch('utils.dates_helper.local_today')
    def test_ga_property_id_invalid(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['ga_tracking_type'] = 2
        self.data['ga_property_id'] = 'ABC'

        form = forms.CampaignSettingsForm(self.campaign, self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('ga_property_id', form.errors)
        self.assertEqual(form.errors['ga_property_id'], ['Web property ID is not valid.'])


class AdGroupSettingsFormTest(TestCase):
    fixtures = ['test_models.yaml', 'test_geolocations.yaml']

    def setUp(self):
        self.ad_group = models.AdGroup.objects.get(pk=1)

        self.user = User.objects.get(pk=1)
        self.data = {
            'state': constants.AdGroupRunningStatus.INACTIVE,
            'cpc_cc': '1.00',
            'max_cpm': '1.50',
            'daily_budget_cc': '10.00',
            'end_date': '2014-12-31',
            'id': '248',
            'name': 'Test ad group',
            'start_date': '2014-12-11',
            'target_devices': ['DESKTOP', 'MOBILE'],
            'target_os': [{'name': 'IOS', 'version': {'min': 'IOS_8_0'}}],
            'target_placements': ['APP'],
            'target_regions': {'countries': ['US']},
            'exclusion_target_regions': {'postal_codes': ['US:12345']},
            'tracking_code': 'code=test',
            'retargeting_ad_groups': [3],
            'exclusion_retargeting_ad_groups': [5],
            'audience_targeting': [1, 2],
            'interest_targeting': ['fun', 'games'],
            'exclusion_interest_targeting': ['science', 'religion'],
            'exclusion_audience_targeting': [3, 4],
            'bluekai_targeting': ['and', 'bluekai:123', ['or', 'lotame:123', 'outbrain:321']],
            'autopilot_state': 2,
            'autopilot_daily_budget': '100.00',
            'dayparting': {"monday": [0, 1, 2, 3], "tuesday": [10, 11, 23], "timezone": "America/New_York"},
            'b1_sources_group_enabled': False,
            'b1_sources_group_daily_budget': '5.00',
            'b1_sources_group_state': 2,
            'b1_sources_group_cpc_cc': Decimal('0.1'),
            'whitelist_publisher_groups': [1],
            'blacklist_publisher_groups': [1],
            'delivery_type': '1',
            'click_capping_daily_ad_group_max_clicks': 10,
        }

    @patch('utils.dates_helper.local_today')
    def test_form(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)

        self.assertTrue(form.is_valid())

        self.maxDiff = None
        self.assertEqual(form.cleaned_data, {
            'state': constants.AdGroupRunningStatus.INACTIVE,
            'cpc_cc': Decimal('1.00'),
            'max_cpm': Decimal('1.50'),
            'daily_budget_cc': Decimal('10.00'),
            'end_date': datetime.date(2014, 12, 31),
            'name': 'Test ad group',
            'start_date': datetime.date(2014, 12, 11),
            'target_devices': ['desktop', 'mobile'],
            'target_os': [{'name': 'ios', 'version': {'min': 'ios_8_0'}}],
            'target_placements': ['app'],
            'target_regions': ['US'],
            'exclusion_target_regions': ['US:12345'],
            'tracking_code': 'code=test',
            'retargeting_ad_groups': [3],
            'exclusion_retargeting_ad_groups': [5],
            'interest_targeting': ['fun', 'games'],
            'exclusion_interest_targeting': ['science', 'religion'],
            'audience_targeting': ListMatcher([1, 2]),
            'exclusion_audience_targeting': ListMatcher([3, 4]),
            'bluekai_targeting': ['and', 'bluekai:123', ['or', 'lotame:123', 'outbrain:321']],
            'autopilot_state': 2,
            'autopilot_daily_budget': Decimal('100.00'),
            'dayparting': {"monday": [0, 1, 2, 3], "tuesday": [10, 11, 23], "timezone": "America/New_York"},
            'b1_sources_group_enabled': False,
            'b1_sources_group_daily_budget': Decimal('5.00'),
            'b1_sources_group_state': 2,
            'b1_sources_group_cpc_cc': Decimal('0.1'),
            'whitelist_publisher_groups': [1],
            'blacklist_publisher_groups': [1],
            'delivery_type': 1,
            'click_capping_daily_ad_group_max_clicks': 10,
        })

    @patch('utils.dates_helper.local_today')
    def test_no_non_propagated_fields(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['cpc_cc'] = None
        self.data['daily_budget_cc'] = None
        self.data['autopilot_state'] = None
        self.data['autopilot_daily_budget'] = None

        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)

        self.assertTrue(form.is_valid())

        self.assertEqual(form.cleaned_data.get('daily_budget_cc'), None)
        self.assertEqual(form.cleaned_data.get('cpc_cc'), None)
        self.assertEqual(form.cleaned_data.get('autopilot_state'), None)
        self.assertEqual(form.cleaned_data.get('autopilot_daily_budget'), None)

    @patch('utils.dates_helper.local_today')
    def test_errors_on_non_propagated_fields(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['cpc_cc'] = 0.01
        self.data['daily_budget_cc'] = 1
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {
            'cpc_cc': ['Maximum CPC can\'t be lower than $0.05.'],
            'daily_budget_cc': ['Please provide budget of at least $10.00.']})

    def test_max_cpc_setting_min_value(self):
        self.data['cpc_cc'] = 0.01
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

    @patch('utils.dates_helper.local_today')
    def test_max_cpc_setting_lower_min_deprecated_source(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['cpc_cc'] = 0.1
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())

    @patch('utils.dates_helper.local_today')
    def test_max_cpc_setting_equal_min_source_value(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['cpc_cc'] = 0.12
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())

    @patch('utils.dates_helper.local_today')
    def test_max_cpc_setting_high_value(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['cpc_cc'] = 4
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())

    @patch('utils.dates_helper.local_today')
    def test_max_cpc_setting_value_too_high(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['cpc_cc'] = 10.01
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

    @patch('utils.dates_helper.local_today')
    def test_max_cpm(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['max_cpm'] = '1.5'
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())

        self.data['max_cpm'] = '0.04'
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

        self.data['max_cpm'] = '10.1'
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

    def test_retargeting_ad_groups_wrong_account(self):
        ad_group = models.AdGroup.objects.get(pk=2)
        form = forms.AdGroupSettingsForm(ad_group, self.user, self.data)

        self.assertFalse(form.is_valid())
        expected = {
            'retargeting_ad_groups': [
                'Invalid ad group selection.'
            ],
            'exclusion_retargeting_ad_groups': [
                'Invalid ad group selection.'
            ],
            'audience_targeting': [
                'Invalid audience selection.'
            ],
            'exclusion_audience_targeting': [
                'Invalid audience selection.'
            ],
            'whitelist_publisher_groups': [
                # adgroup 2 belongs to account 2, publisher group 1 to account 1
                'Invalid whitelist publisher group selection.'
            ],
            'blacklist_publisher_groups': [
                # adgroup 2 belongs to account 2, publisher group 1 to account 1
                'Invalid blacklist publisher group selection.'
            ],
        }
        self.assertEqual(form.errors, expected)

    @patch('utils.dates_helper.local_today')
    def test_retargeting_ad_groups_no_access(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        user = User.objects.create(email='testuser@test.com')
        form = forms.AdGroupSettingsForm(self.ad_group, user, self.data)

        self.assertFalse(form.is_valid())
        expected = {
            'retargeting_ad_groups': [
                'Invalid ad group selection.'
            ],
            'exclusion_retargeting_ad_groups': [
                'Invalid ad group selection.'
            ]
        }
        self.assertEqual(form.errors, expected)

    @patch('utils.dates_helper.local_today')
    def test_bluekai_targeting_validation(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['bluekai_targeting'] = {
            "and": [
                {"category": "bluekai:446103"},
                {
                    "not": [{
                        "or": [
                            {"category": "lotame:510120"},
                            {"category": "outbrain:510122"}
                        ]
                    }]
                }
            ]
        }
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)

        self.assertTrue(form.is_valid())
        self.data['bluekai_targeting'] = {"xor": [{"category": "bluekai:446103"}]}
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

        self.data['bluekai_targeting'] = {"or": [{"category": "nonexistent:446103"}]}
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

        self.data['bluekai_targeting'] = {"or": [{"category": "bluekai446103"}]}
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

        self.data['bluekai_targeting'] = {"or": [{"category": "bluekai:abcdef"}]}
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())


class ConversionGoalFormTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        account = models.Account.objects.get(pk=1)
        models.ConversionPixel.objects.create(
            id=1, account=account, slug='slug', name='Test pixel name')

    def test_type(self):
        data = {
            'goal_id': '1',
            'conversion_window': 168,
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'type': ['This field is required.']}, form.errors)

        data['type'] = 98765

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'type': ['Select a valid choice. 98765 is not one of the available choices.']}, form.errors)

        data['type'] = 1

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())

    def test_conversion_window(self):
        data = {
            'goal_id': '1',
            'type': '1',
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'conversion_window': ['This field is required.']}, form.errors)

        data['conversion_window'] = 98765

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            {'conversion_window': ['Select a valid choice. 98765 is not one of the available choices.']}, form.errors)

        data['conversion_window'] = 24

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())

    def test_goal_id(self):
        data = {
            'type': '1',
            'conversion_window': '168',
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'goal_id': ['This field is required.']}, form.errors)

        data['goal_id'] = 'a' * 101

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'goal_id': ['Conversion goal id is too long (101/100).']}, form.errors)

        data['goal_id'] = '__new__'

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'goal_id': ['The new pixel not successfuly created yet, please try again in a little while.']}, form.errors)

        data['goal_id'] = '1'

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())

    def test_unique_goal_id(self):
        models.ConversionGoal.objects.create_unsafe(campaign_id=1, type=2, goal_id='1', name='Conversion goal')
        data = {
            'type': 2,
            'goal_id': '1'
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'goal_id': ['This field has to be unique.']}, form.errors)

        form = forms.ConversionGoalForm(data, campaign_id=2)
        self.assertTrue(form.is_valid())

        data['type'] = 3

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())

    def test_name(self):
        data = {
            'type': 2,
            'goal_id': 'Test goal id'
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Test goal id')

        data = {
            'type': 1,
            'goal_id': '1',
            'conversion_window': 168,
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['name'], 'Test pixel name - 7 days')


class AdGroupAdsUploadFormTest(TestCase):

    def setUp(self):
        self.batch_name = 'Test batch name'
        self.url = 'http://example.com'
        self.title = 'Test Title'
        self.image_url = 'http://example.com/image'
        self.crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        self.display_url = 'example.com'
        self.description = 'testdescription'
        self.brand_name = 'testbrandname'
        self.call_to_action = 'testcalltoaction'
        self.primary_tracker_url = 'http://example1.com'
        self.file_contents = [
            ['URL', 'title', 'image URL', 'crop areas'],
            [
                'http://www.nextadvisor.com/blog/2014/12/11/best-credit-cards-2015/?kw=zem_dsk_bc15q15_33',
                'See The Best Credit Cards of 2015',
                'http://i.zemanta.com/319205478_350_350.jpg',
                self.crop_areas,
            ],
        ]

    def test_parse_unknown_file(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {})
        with open('./dash/test_files/test.gif') as f:
            with self.assertRaises(ValidationError):
                form._parse_file(f)
        with open('./dash/test_files/test.jpg') as f:
            with self.assertRaises(ValidationError):
                form._parse_file(f)

    def test_parse_csv_file(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {})
        with open('./dash/test_files/test.csv') as f:
            rows = form._parse_file(f)
            self.assertEqual(self.file_contents, rows)

    def test_parse_xls_file(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {})
        with open('./dash/test_files/test.xls') as f:
            rows = form._parse_file(f)
            self.assertEqual(self.file_contents, rows)

    def test_parse_xlsx_file(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {})
        with open('./dash/test_files/test.xlsx') as f:
            rows = form._parse_file(f)
            self.assertEqual(self.file_contents, rows)

    def test_missing_all_columns(self):
        csv_file = self._get_csv_file([], ['http://example.com', 'Example', 'img.jpg'])

        form = self._init_form(csv_file, {'display_url': 'test.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'candidates': [u'First column in header should be URL.']})

    def test_missing_title_and_image_url(self):
        csv_file = self._get_csv_file(['Url'], ['http://example.com', 'Example', 'img.jpg'])

        form = self._init_form(csv_file, {'display_url': 'test.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'candidates': [u'Second column in header should be Title.']})

    def test_missing_image_url(self):
        csv_file = self._get_csv_file(['Url', 'Title'], ['http://example.com', 'Example', 'img.jpg'])

        form = self._init_form(csv_file, {'display_url': 'test.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'candidates': [u'Third column in header should be Image URL.']})

    def test_no_csv_content(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Primary impression tracker url'], [])

        form = self._init_form(csv_file, {'display_url': 'test.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'candidates': [u'Uploaded file is empty.']})

    def test_csv_empty_lines(self):
        csv_file = self._get_csv_file([], [['Url', 'Title', 'Image Url', 'Primary impression tracker url'], [],
                                           [self.url, self.title, self.image_url, self.primary_tracker_url], []])
        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())

    def test_csv_max_ads(self):
        lines = [[self.url, self.title, self.image_url, self.primary_tracker_url]] * 101
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Primary impression tracker url'], lines)
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'candidates': ['Too many content ads (max. 100)']})

    def test_csv_max_ads_empty_lines(self):
        lines = [['Url', 'Title', 'Image Url', 'Primary impression tracker url']]
        lines += [[self.url, self.title, self.image_url, self.primary_tracker_url], []] * 100
        csv_file = self._get_csv_file([], lines)
        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())

    def test_csv_example_content_without_data(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Description', 'Primary impression tracker url'],
                                      [EXAMPLE_CSV_CONTENT])
        form = self._init_form(csv_file, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'candidates': [u'Uploaded file is empty.']})

    def test_csv_example_content_with_data(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Description', 'Primary impression tracker url'],
                                      [EXAMPLE_CSV_CONTENT,
                                       [self.url, self.title, self.image_url,
                                        self.description, self.primary_tracker_url],
                                       EXAMPLE_CSV_CONTENT])
        form = self._init_form(csv_file, {})
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data['candidates']), 1)

    def test_csv_impression_trackers_column(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Primary impression tracker url'],
            [[self.url, self.title, self.image_url, self.primary_tracker_url]])

        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['candidates'][0]['primary_tracker_url'], self.primary_tracker_url)

    def test_csv_ignore_errors_column(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Errors'],
            [[self.url, self.title, self.image_url, 'some errors']])

        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())
        self.assertTrue('errors' not in form.cleaned_data['candidates'][0])

    def test_form(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Primary impression tracker url'],
            [[self.url, self.title, self.image_url, self.primary_tracker_url]])

        form = self._init_form(csv_file, None)

        self.assertTrue(form.is_valid())
        self.maxDiff = None
        self.assertEqual(form.cleaned_data, {
            'ad_group_id': None,
            'account_id': None,
            'batch_name': self.batch_name,
            'candidates': [{
                u'image_url': self.image_url,
                u'title': self.title,
                u'url': self.url,
                u'primary_tracker_url': self.primary_tracker_url,
            }]
        })

    def test_form_optional_fields_duplicated(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Primary impression tracker url', 'Primary impression tracker url'],
            [[self.url, self.title, self.image_url, self.crop_areas, self.primary_tracker_url]])

        form = self._init_form(csv_file, None)
        self.assertEqual(form.errors, {'candidates': [
                         u'Column "Primary impression tracker url" appears multiple times (2) in the CSV file.']})

    def test_incorrect_csv_format(self):
        csv_file = StringIO.StringIO()
        csv_file.write('TEST\x00TEST')

        form = self._init_form(csv_file, {'batch_name': self.batch_name})

        self.assertFalse(form.is_valid())

    def test_batch_name_missing(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {'batch_name': None})

        self.assertFalse(form.is_valid())

    def test_header_no_url(self):
        csv_file = self._get_csv_file(['aaa', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['candidates'], ['First column in header should be URL.'])

    def test_header_no_title(self):
        csv_file = self._get_csv_file(['URL', 'aaa', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['candidates'], ['Second column in header should be Title.'])

    def test_header_no_image_url(self):
        csv_file = self._get_csv_file(['URL', 'Title', 'aaa', 'Crop Areas'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['candidates'], ['Third column in header should be Image URL.'])

    def test_header_unknown_forth_column(self):
        csv_file = self._get_csv_file(['URL', 'Title', 'Image URL', 'aaa'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['candidates'],
            ['Unrecognized column name "aaa".']
        )

    def test_header_unknown_fifth_column(self):
        csv_file = self._get_csv_file(['URL', 'Title', 'Image URL', 'Primary impression tracker url', 'aaa'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors['candidates'],
            ['Unrecognized column name "aaa".']
        )

    def test_windows_1252_encoding(self):
        csv_file = self._get_csv_file(
            ['URL', 'Title', 'Image URL', 'Primary impression tracker url'],
            [[self.url, u'\u00ae', self.image_url, self.crop_areas]],
            encoding='windows-1252'
        )
        form = self._init_form(csv_file, None)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['candidates'][0]['title'], u'\xae')

    def _init_form(self, csv_file, data_updates):
        data = {
            'batch_name': self.batch_name,
        }

        if data_updates is not None:
            data.update(data_updates)

        return forms.AdGroupAdsUploadForm(
            data,
            {'candidates': SimpleUploadedFile('test_file.csv', csv_file.getvalue())}
        )

    def _get_csv_file(self, header, rows, encoding='utf-8'):
        csv_file = StringIO.StringIO()

        writer = unicodecsv.writer(csv_file, encoding=encoding)
        writer.writerow(header)

        for row in rows:
            writer.writerow(row)

        return csv_file


class CampaignAdminFormTest(TestCase):
    fixtures = ['test_models.yaml']

    def test_empty_form(self):
        form = forms.CampaignAdminForm()
        self.assertTrue(form.initial['automatic_campaign_stop'])

    def test_instance_witout_settings(self):
        campaign = models.Campaign(
            name='Test',
            account_id=1,
        )
        campaign.save(None)
        form = forms.CampaignAdminForm(
            instance=campaign
        )
        self.assertTrue(form.initial['automatic_campaign_stop'])

    def test_instance_with_settings(self):
        campaign = models.Campaign(
            name='Test',
            account_id=1,
        )
        campaign.save(None)
        settings = campaign.get_current_settings().copy_settings()
        settings.automatic_campaign_stop = True
        settings.save(None)

        form = forms.CampaignAdminForm(
            instance=campaign
        )
        self.assertTrue(form.initial['automatic_campaign_stop'])

        settings = campaign.get_current_settings().copy_settings()
        settings.automatic_campaign_stop = False
        settings.save(None)

        form = forms.CampaignAdminForm(
            instance=campaign
        )
        self.assertFalse(form.initial['automatic_campaign_stop'])


class ContentAdCandidateFormTestCase(TestCase):

    def _get_valid_data(self):
        data = {
            'label': 'label',
            'url': 'http://zemanta.com',
            'title': 'Title',
            'image_url': 'http://zemanta.com/img.jpg',
            'image_crop': 'center',
            'display_url': 'zemanta.com',
            'brand_name': 'Zemanta',
            'description': 'Description',
            'call_to_action': 'Read more',
            'primary_tracker_url': 'https://zemanta.com/px1',
            'secondary_tracker_url': 'https://zemanta.com/px2',
            'video_asset_id': '12345678-abcd-1234-abcd-123abcd12345',
        }
        files = {
            'image': self.valid_image,
        }
        return data, files

    def setUp(self):
        magic_mixer.blend(models.VideoAsset, id='12345678-abcd-1234-abcd-123abcd12345')

        self.valid_image = SimpleUploadedFile(
            name='test.jpg',
            content=open('./dash/test_files/test.jpg').read(),
            content_type='image/jpg'
        )
        self.invalid_image = SimpleUploadedFile(
            name='test.jpg',
            content=open('./dash/test_files/test.csv').read(),
            content_type='text/csv'
        )

    def test_valid(self):
        f = forms.ContentAdCandidateForm(*self._get_valid_data())
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data, {
            'label': 'label',
            'url': 'http://zemanta.com',
            'title': 'Title',
            'image': self.valid_image,
            'image_url': 'http://zemanta.com/img.jpg',
            'image_crop': 'center',
            'video_asset_id': '12345678-abcd-1234-abcd-123abcd12345',
            'display_url': 'zemanta.com',
            'brand_name': 'Zemanta',
            'description': 'Description',
            'call_to_action': 'Read more',
            'primary_tracker_url': 'https://zemanta.com/px1',
            'secondary_tracker_url': 'https://zemanta.com/px2',
        })

    def test_invalid_image(self):
        data, files = self._get_valid_data()
        files['image'] = self.invalid_image
        f = forms.ContentAdCandidateForm(data, files)
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors['image'], ['Invalid image file'])

    def test_capitalized_image_crop(self):
        data, files = self._get_valid_data()
        data['image_crop'] = 'Center'
        f = forms.ContentAdCandidateForm(data, files)
        self.assertTrue(f.is_valid())

    def test_skipped_image_crop(self):
        data, files = self._get_valid_data()
        del data['image_crop']
        f = forms.ContentAdCandidateForm(data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['image_crop'], 'center')

    def test_empty_image_crop(self):
        data, files = self._get_valid_data()
        data['image_crop'] = ''
        f = forms.ContentAdCandidateForm(data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['image_crop'], 'center')

    def test_skipped_call_to_action(self):
        data, files = self._get_valid_data()
        del data['call_to_action']
        f = forms.ContentAdCandidateForm(data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['call_to_action'], 'Read more')


class ContentAdFormTestCase(TestCase):

    def _get_valid_data(self):
        return {
            'label': 'label',
            'url': 'http://zemanta.com',
            'title': 'Title',
            'image_url': 'http://zemanta.com/img.jpg',
            'image_crop': 'center',
            'display_url': 'zemanta.com',
            'brand_name': 'Zemanta',
            'description': 'Description',
            'call_to_action': 'Read more',
            'primary_tracker_url': 'https://zemanta.com/px1',
            'secondary_tracker_url': 'https://zemanta.com/px2',
            'image_id': 'id123',
            'image_hash': 'imagehash',
            'image_width': 500,
            'image_height': 500,
            'image_status': constants.AsyncUploadJobStatus.OK,
            'url_status': constants.AsyncUploadJobStatus.OK,
        }

    def test_form(self):
        f = forms.ContentAdForm(self._get_valid_data())
        self.assertTrue(f.is_valid())

    def test_image_status_pending_start(self):
        data = self._get_valid_data()
        data['image_status'] = constants.AsyncUploadJobStatus.PENDING_START
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            '__all__': ['Content ad still processing'],
        }, f.errors)

    def test_image_status_waiting_response(self):
        data = self._get_valid_data()
        data['image_status'] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            '__all__': ['Content ad still processing'],
        }, f.errors)

    def test_url_status_pending_start(self):
        data = self._get_valid_data()
        data['url_status'] = constants.AsyncUploadJobStatus.PENDING_START
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            '__all__': ['Content ad still processing'],
        }, f.errors)

    def test_url_status_waiting_response(self):
        data = self._get_valid_data()
        data['url_status'] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            '__all__': ['Content ad still processing'],
        }, f.errors)

    def test_invalid_image_status(self):
        data = self._get_valid_data()
        data['image_status'] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image could not be processed']
        }, f.errors)

    def test_no_image_url_and_invalid_status(self):
        data = self._get_valid_data()
        data['image_url'] = None
        data['image_status'] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Missing image']
        }, f.errors)

    def test_not_reachable_url(self):
        data = self._get_valid_data()
        data['url_status'] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'url': ['Content unreachable']
        }, f.errors)

    def test_no_url_and_invalid_status(self):
        data = self._get_valid_data()
        data['url'] = None
        data['url_status'] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'url': ['Missing URL']
        }, f.errors)

    def test_missing_image_id(self):
        data = self._get_valid_data()
        del data['image_id']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image could not be processed']
        }, f.errors)

    def test_missing_image_hash(self):
        data = self._get_valid_data()
        del data['image_hash']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image could not be processed']
        }, f.errors)

    def test_missing_image_width(self):
        data = self._get_valid_data()
        del data['image_width']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image could not be processed']
        }, f.errors)

    def test_missing_image_height(self):
        data = self._get_valid_data()
        del data['image_height']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image could not be processed']
        }, f.errors)

    def test_image_min_width(self):
        data = self._get_valid_data()
        data['image_width'] = 1
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image too small (minimum size is 300x300 px)']
        }, f.errors)

    def test_image_max_width(self):
        data = self._get_valid_data()
        data['image_width'] = 40001
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image too big (maximum size is 10000x10000 px)']
        }, f.errors)

    def test_image_min_height(self):
        data = self._get_valid_data()
        data['image_height'] = 1
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image too small (minimum size is 300x300 px)']
        }, f.errors)

    def test_image_max_height(self):
        data = self._get_valid_data()
        data['image_height'] = 40001
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Image too big (maximum size is 10000x10000 px)']
        }, f.errors)

    def test_invalid_url_status(self):
        data = self._get_valid_data()
        data['url_status'] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'url': ['Content unreachable']
        }, f.errors)

    def test_label_too_long(self):
        data = self._get_valid_data()
        data['label'] = 'a' * 101
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'label': ['Label too long (max 100 characters)']
        }, f.errors)

    def test_missing_url(self):
        data = self._get_valid_data()
        del data['url']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'url': ['Missing URL']
        }, f.errors)

    def test_url_too_long(self):
        data = self._get_valid_data()
        data['url'] = 'http://example.com/' + ('repeat' * 200)
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'url': ['URL too long (max 936 characters)']
        }, f.errors)

    def test_invalid_url(self):
        data = self._get_valid_data()
        data['url'] = 'ttp://example.com'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'url': ['Invalid URL']
        }, f.errors)

    def test_missing_title(self):
        data = self._get_valid_data()
        del data['title']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'title': ['Missing title']
        }, f.errors)

    def test_title_too_long(self):
        data = self._get_valid_data()
        data['title'] = 'repeat' * 19
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'title': ['Title too long (max 90 characters)']
        }, f.errors)

    def test_missing_image_url(self):
        data = self._get_valid_data()
        del data['image_url']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Missing image']
        }, f.errors)

    def test_invalid_image_url(self):
        data = self._get_valid_data()
        data['image_url'] = 'ttp://example.com'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_url': ['Invalid image URL']
        }, f.errors)

    def test_invalid_image_crop(self):
        data = self._get_valid_data()
        data['image_crop'] = 'landscape'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'image_crop': ['Choose a valid image crop']
        }, f.errors)

    def test_capitalized_image_crop(self):
        data = self._get_valid_data()
        data['image_crop'] = 'Center'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())

    def test_empty_image_crop(self):
        data = self._get_valid_data()
        data['image_crop'] = ''
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())

    def test_missing_display_url(self):
        data = self._get_valid_data()
        del data['display_url']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'display_url': ['Missing display URL']
        }, f.errors)

    def test_display_url_too_long(self):
        data = self._get_valid_data()
        data['display_url'] = 'repeat' * 4 + '.com'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'display_url': ['Display URL too long (max 25 characters)']
        }, f.errors)

    def test_display_url_invalid(self):
        data = self._get_valid_data()
        data['display_url'] = 'test'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'display_url': ['Enter a valid URL.']
        }, f.errors)

    def test_display_url_with_http(self):
        data = self._get_valid_data()
        data['display_url'] = 'http://' + 'repeat' * 3 + '.com/'
        f = forms.ContentAdForm(data)
        self.assertTrue(f.is_valid())

    def test_missing_brand_name(self):
        data = self._get_valid_data()
        del data['brand_name']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'brand_name': ['Missing brand name']
        }, f.errors)

    def test_brand_name_too_long(self):
        data = self._get_valid_data()
        data['brand_name'] = 'repeat' * 6
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'brand_name': ['Brand name too long (max 25 characters)']
        }, f.errors)

    def test_missing_description(self):
        data = self._get_valid_data()
        del data['description']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'description': ['Missing description']
        }, f.errors)

    def test_description_too_long(self):
        data = self._get_valid_data()
        data['description'] = 'repeat' * 29
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'description': ['Description too long (max 140 characters)']
        }, f.errors)

    def test_missing_call_to_action(self):
        data = self._get_valid_data()
        del data['call_to_action']
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'call_to_action': ['Missing call to action']
        }, f.errors)

    def test_call_to_action_too_long(self):
        data = self._get_valid_data()
        data['call_to_action'] = 'repeat' * 6
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'call_to_action': ['Call to action too long (max 25 characters)']
        }, f.errors)

    def test_http_primary_tracker(self):
        data = self._get_valid_data()
        data['primary_tracker_url'] = 'http://zemanta.com/'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'primary_tracker_url': ['Impression tracker URLs have to be HTTPS']
        }, f.errors)

    def test_http_secondary_tracker(self):
        data = self._get_valid_data()
        data['secondary_tracker_url'] = 'http://zemanta.com/'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'secondary_tracker_url': ['Impression tracker URLs have to be HTTPS']
        }, f.errors)

    def test_unicode_primary_tracker(self):
        data = self._get_valid_data()
        data['primary_tracker_url'] = 'https://zemanta.com/š'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'primary_tracker_url': ['Invalid impression tracker URL']
        }, f.errors)

    def test_unicode_secondary_tracker(self):
        data = self._get_valid_data()
        data['secondary_tracker_url'] = 'https://zemanta.com/š'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'secondary_tracker_url': ['Invalid impression tracker URL']
        }, f.errors)


class AudienceFormTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        self.account = models.Account.objects.get(pk=1)
        self.user = User.objects.get(pk=1)

    def _get_valid_data(self):
        return {
            'name': 'Test Audience',
            'pixel_id': 1,
            'ttl': 90,
            'rules': [{
                'type': constants.AudienceRuleType.CONTAINS,
                'value': 'test',
            }]
        }

    def _expect_error(self, field_name, error_message, data):
        f = forms.AudienceForm(self.account, self.user, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            field_name: [error_message]
        }, f.errors)

    def test_form(self):
        f = forms.AudienceForm(self.account, self.user, self._get_valid_data())
        self.assertTrue(f.is_valid())

    def test_invalid_name(self):
        data = self._get_valid_data()
        data['name'] = None
        self._expect_error('name', 'Please specify audience name.', data)

        data['name'] = ''
        self._expect_error('name', 'Please specify audience name.', data)

        del(data['name'])
        self._expect_error('name', 'Please specify audience name.', data)

        data['name'] = 'a' * 128
        self._expect_error('name', 'Name is too long (max 127 characters)', data)

    def test_invalid_pixel_id(self):
        data = self._get_valid_data()
        data['pixel_id'] = None
        self._expect_error('pixel_id', 'Please select pixel.', data)

        del(data['pixel_id'])
        self._expect_error('pixel_id', 'Please select pixel.', data)

    def test_pixel_id_no_permissions(self):
        data = self._get_valid_data()
        data['pixel_id'] = 3
        self._expect_error('pixel_id', 'Pixel does not exist.', data)

    def test_pixel_id_archived(self):
        data = self._get_valid_data()
        data['pixel_id'] = 2
        self._expect_error('pixel_id', 'Pixel is archived.', data)

    def test_invalid_ttl(self):
        data = self._get_valid_data()
        data['ttl'] = None
        self._expect_error('ttl', 'Please select days.', data)

        del(data['ttl'])
        self._expect_error('ttl', 'Please select days.', data)

        data['ttl'] = 366
        self._expect_error('ttl', 'Maximum number of days is 365.', data)

    def test_invalid_rules(self):
        data = self._get_valid_data()
        data['rules'] = None
        self._expect_error('rules', 'Please select a rule.', data)

        data['rules'] = []
        self._expect_error('rules', 'Please select a rule.', data)

        del(data['rules'])
        self._expect_error('rules', 'Please select a rule.', data)

        data['rules'] = [{'type': None, 'value': 'bla'}]
        self._expect_error('rules', 'Please select a type of the rule.', data)

        data['rules'] = [{'type': constants.AudienceRuleType.CONTAINS, 'value': None}]
        self._expect_error('rules', 'Please enter conditions for the audience.', data)

        data['rules'] = [{'type': constants.AudienceRuleType.STARTS_WITH, 'value': None}]
        self._expect_error('rules', 'Please enter conditions for the audience.', data)

        data['rules'] = [{'type': constants.AudienceRuleType.STARTS_WITH, 'value': ['foo.com']}]
        self._expect_error('rules', 'Please enter valid URLs.', data)

    def test_valid_visit_rule(self):
        data = self._get_valid_data()
        data['rules'] = [{'type': constants.AudienceRuleType.VISIT, 'value': None}]
        f = forms.AudienceForm(self.account, self.user, data)
        self.assertTrue(f.is_valid())


class PublisherTargetingFormTestCase(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        self.account = models.Account.objects.get(pk=1)
        self.user = User.objects.get(pk=1)

    def test_form(self):
        f = forms.PublisherTargetingForm(self.user, {
            'entries': [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }, {
                'publisher': 'cnn2.com',
                'source': 1,
                'include_subdomains': True,
            }],
            'status': constants.PublisherTargetingStatus.BLACKLISTED,
            'ad_group': 1,
        })

        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data, {
            'entries': test_helper.ListMatcher([{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }, {
                'publisher': 'cnn2.com',
                'source': models.Source.objects.get(pk=1),
                'include_subdomains': True,
            }]),
            'status': constants.PublisherTargetingStatus.BLACKLISTED,
            'ad_group': models.AdGroup.objects.get(pk=1),
            'campaign': None,
            'account': None,
            'entries_not_selected': [],
            'select_all': False,
            'start_date': None,
            'end_date': None,
            'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.all()),
            'enforce_cpc': False,
            'level': '',
        })

    def test_form_select_all_invalid(self):
        f = forms.PublisherTargetingForm(self.user, {
            'entries': [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }, {
                'publisher': 'cnn2.com',
                'source': 1,
                'include_subdomains': True,
            }],
            'status': constants.PublisherTargetingStatus.BLACKLISTED,
            'ad_group': 1,
            'select_all': True,
        })

        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors['select_all'], ['Please specify start and end date when selecting all publishers'])

    def test_form_select_all(self):
        f = forms.PublisherTargetingForm(self.user, {
            'entries': [{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }, {
                'publisher': 'cnn2.com',
                'source': 1,
                'include_subdomains': True,
            }],
            'status': constants.PublisherTargetingStatus.BLACKLISTED,
            'ad_group': 1,
            'select_all': True,
            'start_date': '2017-01-05',
            'end_date': '2017-01-30',
            'entries_not_selected': [{
                'publisher': 'cnn33.com',
                'source': None,
                'include_subdomains': False,
            }],
            'enforce_cpc': True,
        })

        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data, {
            'entries': test_helper.ListMatcher([{
                'publisher': 'cnn.com',
                'source': None,
                'include_subdomains': False,
            }, {
                'publisher': 'cnn2.com',
                'source': models.Source.objects.get(pk=1),
                'include_subdomains': True,
            }]),
            'status': constants.PublisherTargetingStatus.BLACKLISTED,
            'ad_group': models.AdGroup.objects.get(pk=1),
            'campaign': None,
            'account': None,
            'entries_not_selected': [{
                'publisher': 'cnn33.com',
                'source': None,
                'include_subdomains': False,
            }],
            'select_all': True,
            'start_date': datetime.date(2017, 1, 5),
            'end_date': datetime.date(2017, 1, 30),
            'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.all()),
            'enforce_cpc': True,
            'level': '',
        })

    def test_form_level(self):
        f = forms.PublisherTargetingForm(self.user, {
            'entries': [],
            'status': constants.PublisherTargetingStatus.BLACKLISTED,
            'ad_group': 1,
            'start_date': '2017-01-05',
            'end_date': '2017-01-30',
            'level': constants.PublisherBlacklistLevel.CAMPAIGN,
        })

        self.assertTrue(f.is_valid())
        self.assertDictContainsSubset({
            'ad_group': None,
            'campaign': models.Campaign.objects.get(pk=1),
            'account': None,
            'level': constants.PublisherBlacklistLevel.CAMPAIGN,
            'start_date': datetime.date(2017, 1, 5),
            'end_date': datetime.date(2017, 1, 30),
            'enforce_cpc': False,
        }, f.cleaned_data)
