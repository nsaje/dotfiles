# -*- coding: utf-8 -*-
import unicodecsv
import datetime
from decimal import Decimal
import StringIO

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Permission
from mock import patch

from dash import constants
from dash import forms
from dash import models
from zemauth.models import User


class AccountSettingsFormTest(TestCase):
    fixtures = ['test_views.yaml']

    @classmethod
    def setUpClass(cls):
        super(AccountSettingsFormTest, cls).setUpClass()  # loads fixtures
        permission = Permission.objects.get(codename='campaign_settings_sales_rep')
        user = User.objects.get(pk=2)
        user.user_permissions.add(permission)
        user.save()

    def test_invalid_sales_rep(self):
        form = forms.AccountSettingsForm({
            'id': 1,
            'name': 'Name',
            'default_account_manager': 2,
            'default_sales_representative': 3,
            'allowed_sources': {'1': {'name': 'Source name'}}
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('default_sales_representative'))

    def test_invalid_account_manager(self):
        account_manager_id = 123
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=account_manager_id)

        form = forms.AccountSettingsForm({
            'id': 1,
            'name': 'Name',
            'default_account_manager': account_manager_id,
            'default_sales_representative': 2,
            'allowed_sources': {'1': {'name': 'Source name'}}
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('default_account_manager'))

    def test_invalid_account_type(self):
        form = forms.AccountSettingsForm({
            'id': 1,
            'name': 'Name',
            'account_type': 'invalid'
        })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('account_type'))

    def test_allowed_sources(self):
        form = forms.AccountSettingsForm({
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

    def _gen_allowed_sources_form(self, allowed_sources_dict):
        return forms.AccountSettingsForm({
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

    def test_duplicated_account_name(self):
        form = forms.AccountSettingsForm({
            'id': 1,
            'name': 'test account 1',
            'default_account_manager': 3,
            'default_sales_representative': 2,
            'allowed_sources': {'1': {'name': 'Source name', 'allowed': False}}
            })
        self.assertTrue(form.is_valid(), "Form should be valid as the account id is the same")

        form = forms.AccountSettingsForm({
            'id': 2,
            'name': 'test account 1',
            'default_account_manager': 3,
            'default_sales_representative': 2,
            'allowed_sources': {'1': {'name': 'Source name', 'allowed': False}}
            })
        self.assertFalse(form.is_valid())
        self.assertTrue(form.has_error('name'))


class AdGroupSettingsFormTest(TestCase):
    fixtures = ['test_models.yaml']

    def setUp(self):
        self.ad_group = models.AdGroup.objects.get(pk=1)

        self.user = User.objects.get(pk=1)
        self.data = {
            'cpc_cc': '1.00',
            'daily_budget_cc': '10.00',
            'end_date': '2014-12-31',
            'id': '248',
            'name': 'Test ad group',
            'start_date': '2014-12-11',
            'target_devices': ['desktop', 'mobile'],
            'target_regions': ['US'],
            'tracking_code': 'code=test',
            'retargeting_ad_groups': [3],
            'enable_ga_tracking': True,
            'ga_tracking_type': 2,
            'ga_property_id': 'UA-123456789-1',
            'autopilot_state': 2,
            'autopilot_daily_budget': '100.00'
        }

    @patch('utils.dates_helper.local_today')
    def test_form(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)

        self.assertTrue(form.is_valid())

        self.assertEqual(form.cleaned_data, {
            'cpc_cc': Decimal('1.00'),
            'daily_budget_cc': Decimal('10.00'),
            'end_date': datetime.date(2014, 12, 31),
            'id': 248,
            'name': 'Test ad group',
            'start_date': datetime.date(2014, 12, 11),
            'target_devices': ['desktop', 'mobile'],
            'target_regions': ['US'],
            'tracking_code': 'code=test',
            'enable_ga_tracking': True,
            'ga_tracking_type': 2,
            'ga_property_id': 'UA-123456789-1',
            'retargeting_ad_groups': [3],
            'enable_adobe_tracking': False,
            'adobe_tracking_param': '',
            'autopilot_state': 2,
            'autopilot_daily_budget': Decimal('100.00')
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
            'cpc_cc': ['Maximum CPC can\'t be lower than $0.03.'],
            'daily_budget_cc': ['Please provide budget of at least $10.00.']})

    def test_max_cpc_setting_min_value(self):
        self.data['cpc_cc'] = 0.01
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())

    def test_max_cpc_setting_lower_min_source_value(self):
        source = models.Source.objects.get(pk=1)
        source.maintenance = False
        source.deprecated = False
        source.save()

        self.data['cpc_cc'] = 0.1
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
    def test_default_value_enable_ga_tracking(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_ga_tracking', form.cleaned_data)
        self.assertTrue(form.cleaned_data['enable_ga_tracking'])

        del self.data['enable_ga_tracking']

        # should be True if not set
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_ga_tracking', form.cleaned_data)
        self.assertTrue(form.cleaned_data['enable_ga_tracking'])

        self.data['enable_ga_tracking'] = False

        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_ga_tracking', form.cleaned_data)
        self.assertFalse(form.cleaned_data['enable_ga_tracking'])

    @patch('utils.dates_helper.local_today')
    def test_default_value_enable_adobe_tracking(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        # should be False if not set
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_adobe_tracking', form.cleaned_data)

        # We need to use assertEqual here, because assertFalse passes
        # even if the value is falsy (None), which is not ok here
        self.assertEqual(form.cleaned_data['enable_adobe_tracking'], False)

        self.data['enable_adobe_tracking'] = False
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_adobe_tracking', form.cleaned_data)
        self.assertEqual(form.cleaned_data['enable_adobe_tracking'], False)

        self.data['enable_adobe_tracking'] = True
        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('enable_adobe_tracking', form.cleaned_data)
        self.assertEqual(form.cleaned_data['enable_adobe_tracking'], True)

    @patch('utils.dates_helper.local_today')
    def test_ga_tracking_type_email(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['ga_tracking_type'] = 1
        self.data['ga_property_id'] = 'abcd'

        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('ga_property_id', form.cleaned_data)
        self.assertIsNone(form.cleaned_data['ga_property_id'])

    @patch('utils.dates_helper.local_today')
    def test_ga_tracking_disabled(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['enable_ga_tracking'] = False
        self.data['ga_tracking_type'] = 2
        self.data['ga_property_id'] = 'abcd'

        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertIn('ga_property_id', form.cleaned_data)
        self.assertIsNone(form.cleaned_data['ga_property_id'])

    @patch('utils.dates_helper.local_today')
    def test_ga_property_id_missing(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['ga_tracking_type'] = 2
        self.data['ga_property_id'] = ''

        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('ga_property_id', form.errors)
        self.assertEqual(form.errors['ga_property_id'], ['Web property ID is required.'])

    @patch('utils.dates_helper.local_today')
    def test_ga_property_id_invalid(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        self.data['ga_tracking_type'] = 2
        self.data['ga_property_id'] = 'ABC'

        form = forms.AdGroupSettingsForm(self.ad_group, self.user, self.data)
        self.assertFalse(form.is_valid())
        self.assertIn('ga_property_id', form.errors)
        self.assertEqual(form.errors['ga_property_id'], ['Web property ID is not valid.'])

    def test_retargeting_ad_groups_wrong_account(self):
        ad_group = models.AdGroup.objects.get(pk=2)
        form = forms.AdGroupSettingsForm(ad_group, self.user, self.data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'retargeting_ad_groups': ['Invalid ad group selection.']})

    @patch('utils.dates_helper.local_today')
    def test_retargeting_ad_groups_no_access(self, mock_today):
        mock_today.return_value = datetime.date(2014, 12, 31)
        user = User.objects.create(email='testuser@test.com')
        form = forms.AdGroupSettingsForm(self.ad_group, user, self.data)

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'retargeting_ad_groups': ['Invalid ad group selection.']})


class ConversionGoalFormTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def test_name(self):
        data = {
            'type': '2',
            'goal_id': '1'
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'name': ['This field is required.']}, form.errors)

        data['name'] = 'a' * 101

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'name': ['Conversion goal name is too long (101/100).']}, form.errors)

        data['name'] = 'a'

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())

    def test_type(self):
        data = {
            'name': 'name',
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
            'name': 'name',
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
            'name': 'name',
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

        data['goal_id'] = 'a'

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertTrue(form.is_valid())

    def test_unique_name(self):
        models.ConversionGoal.objects.create(campaign_id=1, type=2, goal_id='1', name='Conversion goal')
        data = {
            'name': 'Conversion goal',
            'type': 3,
            'goal_id': '2'
        }

        form = forms.ConversionGoalForm(data, campaign_id=1)
        self.assertFalse(form.is_valid())
        self.assertEqual({'name': ['This field has to be unique.']}, form.errors)

        form = forms.ConversionGoalForm(data, campaign_id=2)
        self.assertTrue(form.is_valid())

    def test_unique_goal_id(self):
        models.ConversionGoal.objects.create(campaign_id=1, type=2, goal_id='1', name='Conversion goal')
        data = {
            'name': 'Conversion goal 2',
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

    def test_filetypes(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {})
        with open('./dash/tests/test.gif') as f:
            valid = form.is_valid_input_file(f.read())
            self.assertFalse(valid)
        with open('./dash/tests/test.jpg') as f:
            valid = form.is_valid_input_file(f.read())
            self.assertFalse(valid)
        with open('./dash/tests/test.xlsx') as f:
            valid = form.is_valid_input_file(f.read())
            self.assertFalse(valid)
        with open('./dash/tests/test.csv') as f:
            valid = form.is_valid_input_file(f.read())
            self.assertTrue(valid)

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
                                      [forms.EXAMPLE_CSV_CONTENT.split(',')])
        form = self._init_form(csv_file, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'candidates': [u'Uploaded file is empty.']})

    def test_csv_example_content_with_data(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Description', 'Primary impression tracker url'],
            [forms.EXAMPLE_CSV_CONTENT.split(','),
             [self.url, self.title, self.image_url, self.description, self.primary_tracker_url],
             forms.EXAMPLE_CSV_CONTENT.split(',')]
        )
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
        }

    def test_valid(self):
        f = forms.ContentAdCandidateForm(self._get_valid_data())
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data, {
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
        })

    def test_capitalized_image_crop(self):
        data = self._get_valid_data()
        data['image_crop'] = 'Center'
        f = forms.ContentAdCandidateForm(data)
        self.assertTrue(f.is_valid())

    def test_skipped_image_crop(self):
        data = self._get_valid_data()
        del data['image_crop']
        f = forms.ContentAdCandidateForm(data)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['image_crop'], 'center')

    def test_empty_image_crop(self):
        data = self._get_valid_data()
        data['image_crop'] = ''
        f = forms.ContentAdCandidateForm(data)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data['image_crop'], 'center')


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
            'tracker_urls': 'https://zemanta.com/px1 https://zemanta.com/px2',
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
            'image_url': ['Missing image URL']
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
            'image_url': ['Missing image URL']
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
            'primary_tracker_url': ['Invalid impression tracker URLs']
        }, f.errors)

    def test_unicode_secondary_tracker(self):
        data = self._get_valid_data()
        data['secondary_tracker_url'] = 'https://zemanta.com/š'
        f = forms.ContentAdForm(data)
        self.assertFalse(f.is_valid())
        self.assertEqual({
            'secondary_tracker_url': ['Invalid impression tracker URLs']
        }, f.errors)
