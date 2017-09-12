# -*- coding: utf-8 -*-

import json
from mock import patch
import datetime
import decimal

from django.test import TestCase, Client, RequestFactory
from django.test.utils import override_settings
from django.http.request import HttpRequest
from django.core.urlresolvers import reverse
from django.contrib.auth.models import Permission

from zemauth.models import User

from dash import models
from dash import constants
from dash.views import views
from dash import history_helpers

from utils import exc
from utils import test_helper
from utils.magic_mixer import magic_mixer

import zemauth.models


class UserTest(TestCase):
    fixtures = ['test_views.yaml']

    class MockDatetime(datetime.datetime):

        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 3, 1)

    class MockDatetimeNonExistent(datetime.datetime):

        @classmethod
        def utcnow(cls):
            return datetime.datetime(2015, 3, 8, 2, 30)

    class MockDatetimeAmbiguous(datetime.datetime):

        @classmethod
        def utcnow(cls):
            return datetime.datetime(2002, 10, 27, 1, 30, 00)

    @patch('dash.views.views.datetime.datetime', MockDatetime)
    def test_get(self):
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertDictEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'agency': None,
                    'name': '',
                    'permissions': {},
                    'timezone_offset': -18000.0
                }
            },
            'success': True
        })

    @patch('dash.views.views.datetime.datetime', MockDatetimeNonExistent)
    def test_get_non_existent_time(self):
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'agency': None,
                    'name': '',
                    'permissions': {},
                    'timezone_offset': -14400.0
                }
            },
            'success': True
        })

    @patch('dash.views.views.datetime.datetime', MockDatetimeAmbiguous)
    def test_get_ambiguous_time(self):
        self.maxDiff = None
        username = User.objects.get(pk=2).email
        self.client.login(username=username, password='secret')

        response = self.client.get(reverse('user', kwargs={'user_id': 'current'}))

        self.assertDictEqual(json.loads(response.content), {
            'data': {
                'user': {
                    'id': '2',
                    'email': 'user@test.com',
                    'agency': None,
                    'name': '',
                    'permissions': {},
                    'timezone_offset': -14400.0
                }
            },
            'success': True
        })


class AccountsTest(TestCase):
    fixtures = ['test_views.yaml']

    def test_put(self):
        johnny = User.objects.get(pk=2)

        rf = RequestFactory().put('accounts')
        rf.user = johnny
        with self.assertRaises(exc.MissingDataError):
            views.Account().put(rf)

        permission = Permission.objects.get(codename='all_accounts_accounts_add_account')
        johnny.user_permissions.add(permission)
        johnny.save()

        johnny = User.objects.get(pk=2)
        rf.user = johnny
        response = views.Account().put(rf)
        response_blob = json.loads(response.content)
        self.assertTrue(response_blob['success'])
        self.assertDictEqual(
            {
                'name': 'New account',
                'id': 3,
            },
            response_blob['data']
        )

        account = models.Account.objects.get(pk=3)
        self.assertIsNone(account.agency)

        settings = account.get_current_settings()
        self.assertEqual(settings.default_account_manager_id, 2)

    def test_put_as_agency_manager(self):
        johnny = User.objects.get(pk=2)

        rf = RequestFactory().put('accounts')
        rf.user = johnny

        ag = models.Agency(
            name='6Pack'
        )
        ag.save(rf)
        ag.users.add(johnny)
        ag.save(rf)

        with self.assertRaises(exc.MissingDataError):
            views.Account().put(rf)

        permission1 = Permission.objects.get(codename='all_accounts_accounts_add_account')
        johnny.user_permissions.add(permission1)
        johnny.save()

        johnny = User.objects.get(pk=2)
        rf.user = johnny
        response = views.Account().put(rf)
        response_blob = json.loads(response.content)

        acc = models.Account.objects.all().order_by('-created_dt').first()

        self.assertTrue(response_blob['success'])
        self.assertDictEqual(
            {
                'name': 'New account',
                'id': acc.id,
            },
            response_blob['data']
        )
        self.assertIsNotNone(acc.agency)

    def test_put_agency_defaults(self):
        user = User.objects.get(pk=2)
        user.user_permissions.add(Permission.objects.get(codename='all_accounts_accounts_add_account'))

        request = RequestFactory().put('accounts')
        request.user = user

        agency = models.Agency(
            name='agency-name',
            sales_representative=user,
            default_account_type=constants.AccountType.TEST,
        )
        agency.save(request)
        agency.users.add(user)

        client = Client()
        client.login(username=user.email, password='secret')

        response = client.put(reverse('accounts_create'))

        self.assertEqual(200, response.status_code)

        account = models.Account.objects.all().order_by('-created_dt').first()
        settings = account.get_current_settings()

        self.assertEqual(user, settings.default_sales_representative)
        self.assertEqual(constants.AccountType.ACTIVATED, settings.account_type)

    def test_put_agency_defaults_internal_user(self):
        internal_user = User.objects.get(pk=1)
        agency_user = User.objects.get(pk=2)
        internal_user.user_permissions.add(Permission.objects.get(codename='all_accounts_accounts_add_account'))
        agency_user.user_permissions.add(Permission.objects.get(codename='all_accounts_accounts_add_account'))

        request = RequestFactory().put('accounts')
        request.user = internal_user

        agency = models.Agency(
            name='agency-name',
            sales_representative=agency_user,
            default_account_type=constants.AccountType.UNKNOWN,
        )
        agency.save(request)
        agency.users.add(agency_user)

        client = Client()
        client.login(username=internal_user.email, password='secret')

        response = client.put(reverse('accounts_create'))

        self.assertEqual(200, response.status_code)

        account = models.Account.objects.all().order_by('-created_dt').first()
        settings = account.get_current_settings()

        self.assertEqual(None, settings.default_sales_representative)
        self.assertEqual(constants.AccountType.UNKNOWN, settings.account_type)


class AccountCampaignsTest(TestCase):
    fixtures = ['test_views.yaml']

    class MockSettingsWriter(object):

        def __init__(self, init):
            pass

        def set(self, resource, request):
            pass

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

    def test_put(self):
        campaign_name = 'New campaign'

        response = self.client.put(
            reverse('account_campaigns', kwargs={'account_id': '1'}),
        )

        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)['data']
        self.assertIn('id', data)
        self.assertIn('name', data)
        self.assertEqual(data['name'], campaign_name)

        campaign_id = data['id']
        campaign = models.Campaign.objects.get(pk=campaign_id)

        self.assertEqual(campaign.name, campaign_name)

        settings = models.CampaignSettings.objects.get(campaign_id=campaign_id)

        self.assertEqual(settings.target_devices, constants.AdTargetDevice.get_all())
        self.assertEqual(settings.target_regions, ['US'])
        self.assertEqual(settings.name, campaign_name)
        self.assertEqual(settings.campaign_manager.id, 1)

        hist = history_helpers.get_campaign_history(campaign).first()
        self.assertEqual(constants.HistoryActionType.CREATE, hist.action_type)


class AdGroupSourceSettingsTest(TestCase):
    fixtures = ['test_models.yaml', 'test_views.yaml', ]

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')
        self.ad_group = models.AdGroup.objects.get(pk=1)

    def _set_autopilot_state(self, autopilot_state):
        new_settings = self.ad_group.get_current_settings().copy_settings()
        new_settings.autopilot_state = autopilot_state
        new_settings.save(None)

    def _set_ad_group_end_date(self, days_delta=0):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.end_date = datetime.datetime.utcnow().date() + datetime.timedelta(days=days_delta)
        new_settings.save(None)

    def _set_campaign_landing_mode(self):
        new_campaign_settings = self.ad_group.campaign.get_current_settings().copy_settings()
        new_campaign_settings.landing_mode = True
        new_campaign_settings.save(None)

    def _set_campaign_automatic_campaign_stop(self, automatic_campaign_stop):
        current_settings = self.ad_group.campaign.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.automatic_campaign_stop = automatic_campaign_stop
        request = HttpRequest()
        request.user = User.objects.get(id=1)
        new_settings.save(request)

    @patch('utils.k1_helper.update_ad_group')
    def test_cpc_bigger_than_max(self, mock_k1_ping):
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.cpc_cc = decimal.Decimal('1.0')
        new_settings.save(None)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '2.0'})
        )
        self.assertEqual(response.status_code, 400)

    @patch('utils.k1_helper.update_ad_group')
    def test_cpc_smaller_than_constraint(self, mock_k1_ping):
        models.CpcConstraint.objects.create(
            ad_group_id=1,
            source_id=1,
            min_cpc=decimal.Decimal('0.65')
        )
        current_settings = self.ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.cpc_cc = decimal.Decimal('0.70')
        new_settings.save(None)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.5'})
        )
        response_content = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response_content['data']['errors']['cpc_cc'],
            ["Bid CPC is violating some constraints: "
             "CPC constraint on source AdBlade with min. CPC $0.65"])

    @patch('utils.k1_helper.update_ad_group')
    def test_set_state_landing_mode(self, mock_k1_ping):
        self._set_campaign_landing_mode()
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'state': 1})
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(mock_k1_ping.called)

    def test_set_daily_budget_landing_mode(self):
        self._set_campaign_landing_mode()
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '15.00'})
        )
        self.assertEqual(response.status_code, 400)

    @patch('utils.k1_helper.update_ad_group')
    def test_logs_user_action(self, mock_k1_ping):
        self._set_ad_group_end_date(days_delta=0)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '0.15'})
        )
        self.assertEqual(response.status_code, 200)
        mock_k1_ping.assert_called_with(1, 'AdGroupSource.update')

        hist = history_helpers.get_ad_group_history(models.AdGroup.objects.get(pk=1)).first()
        self.assertEqual(constants.HistoryActionType.MEDIA_SOURCE_SETTINGS_CHANGE, hist.action_type)

    @patch('automation.campaign_stop.get_max_settable_source_budget')
    def test_daily_budget_over_max_settable(self, mock_max_settable_budget):
        mock_max_settable_budget.return_value = decimal.Decimal('500')
        self._set_ad_group_end_date(days_delta=3)
        self._set_campaign_automatic_campaign_stop(False)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '600'})
        )
        self.assertEqual(response.status_code, 200)

        self._set_campaign_automatic_campaign_stop(True)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '600'})
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '500'})
        )
        self.assertEqual(response.status_code, 200)

        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'daily_budget_cc': '400'})
        )
        self.assertEqual(response.status_code, 200)

    def test_source_cpc_over_ad_group_maximum(self):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '1.10'})
        )
        self.assertEqual(response.status_code, 400)

    def test_source_cpc_equal_ad_group_maximum(self):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'cpc_cc': '1.00'})
        )
        self.assertEqual(response.status_code, 200)

    @patch('automation.campaign_stop.can_enable_media_source')
    @patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group')
    def test_adgroup_on_budget_autopilot_trigger_budget_autopilot_on_source_state_change(self, mock_budget_ap, mock_campaign_stop):
        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '4', 'source_id': '1'}),
            data=json.dumps({'state': '2'})
        )
        mock_budget_ap.assert_called_with(models.AdGroup.objects.get(id=4).get_current_settings(), send_mail=False)
        self.assertEqual(response.status_code, 200)

    @patch('automation.campaign_stop.can_enable_media_source')
    @patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group')
    def test_adgroup_not_on_budget_autopilot_not_trigger_budget_autopilot_on_source_state_change(self, mock_budget_ap, mock_campaign_stop):
        self._set_ad_group_end_date(days_delta=3)
        self._set_autopilot_state(constants.AdGroupSettingsAutopilotState.INACTIVE)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'state': '2'})
        )
        self.assertEqual(mock_budget_ap.called, False)
        self.assertEqual(response.status_code, 200)

    def test_adgroup_w_retargeting_and_source_without(self):
        for source in models.Source.objects.all():
            source.supports_retargeting = False
            source.save()

        self._set_ad_group_end_date(days_delta=3)
        response = self.client.put(
            reverse('ad_group_source_settings', kwargs={'ad_group_id': '1', 'source_id': '1'}),
            data=json.dumps({'state': '1'})
        )
        self.assertEqual(response.status_code, 400)


class CampaignAdGroups(TestCase):
    fixtures = ['test_models.yaml', 'test_views.yaml']

    def setUp(self):
        self.client = Client()
        user = User.objects.get(pk=1)
        self.user = user
        self.client.login(username=user.email, password='secret')

    @patch('utils.redirector_helper.insert_adgroup', autospec=True)
    @patch('automation.autopilot_plus.initialize_budget_autopilot_on_ad_group', autospec=True)
    def test_put(self, mock_autopilot_init, mock_r1):
        campaign = models.Campaign.objects.get(pk=1)
        goal = magic_mixer.blend(models.CampaignGoal,
                                 type=constants.CampaignGoalKPI.TIME_ON_SITE,
                                 campaign=campaign, primary=True)
        magic_mixer.blend(models.CampaignGoalValue, campaign_goal=goal)
        response = self.client.put(
            reverse('campaign_ad_groups', kwargs={'campaign_id': campaign.id}),
        )
        self.assertEqual(response.status_code, 200)

        response_dict = json.loads(response.content)
        self.assertDictContainsSubset({'name': 'New ad group'}, response_dict['data'])

    def test_add_media_sources_with_retargeting(self):
        ad_group = models.AdGroup.objects.get(pk=2)

        # remove ability to retarget from all sources
        for source in models.Source.objects.all():
            source.supports_retargeting = False
            source.save()

        request = RequestFactory()
        request.user = self.user

        ad_group_settings = ad_group.get_current_settings()
        ad_group_settings = ad_group_settings.copy_settings()
        ad_group_settings.retargeting_ad_groups = [1]
        ad_group_settings.save(request)
        request = None

        ad_group_source_settings = models.AdGroupSourceSettings.objects.all().filter(
            ad_group_source__ad_group=ad_group
        ).group_current_settings()
        self.assertTrue(all(
            [adgss.state == constants.AdGroupSourceSettingsState.ACTIVE for adgss in ad_group_source_settings]
        ))


class AdGroupArchiveRestoreTest(TestCase):
    fixtures = ['test_models.yaml', 'test_views.yaml', ]

    class MockSettingsWriter(object):

        def __init__(self, init):
            pass

        def set(self, resource, request):
            pass

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

    def _post_archive_ad_group(self, ad_group_id):
        return self.client.post(
            reverse(
                'ad_group_archive',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def _post_restore_ad_group(self, ad_group_id):
        return self.client.post(
            reverse(
                'ad_group_restore',
                kwargs={'ad_group_id': ad_group_id}),
            data=json.dumps({}),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
            follow=True
        )

    def test_basic_archive_restore(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertFalse(ad_group.is_archived())

        ad_group_settings = ad_group.get_current_settings()

        with test_helper.disable_auto_now_add(models.AdGroupSettings, 'created_dt'):
            new_ad_group_settings = ad_group_settings.copy_settings()
            new_ad_group_settings.state = constants.AdGroupRunningStatus.INACTIVE
            new_ad_group_settings.created_dt = datetime.date.today() - datetime.timedelta(
                days=models.NR_OF_DAYS_INACTIVE_FOR_ARCHIVAL + 1)
            new_ad_group_settings.save(None)

        self._post_archive_ad_group(1)

        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertTrue(ad_group.is_archived())

        self._post_restore_ad_group(1)

        ad_group = models.AdGroup.objects.get(pk=1)
        self.assertFalse(ad_group.is_archived())


class AdGroupSourcesTest(TestCase):
    fixtures = ['test_api', 'test_views']

    def setUp(self):
        self.client = Client()
        self.client.login(username=User.objects.get(pk=1).email, password='secret')

    def test_get_name(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'Account š name that is toooooooo long',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'Campaign š name that is toooooooo long',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'Ad group š name that is toooooooo long',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Account š name that is / Campaign š name that / Ad group š name that / 123 / Outbrain')

    def test_get_name_long_first_word(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'Accountšnamethatistoooooooolong',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'Campaignšnamethatistoooooooolong',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'Adgroupšnamethatistoooooooolong',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()
        self.assertEqual(
            name, u'ONE: Accountšnamethatistooo / Campaignšnamethatistoo / Adgroupšnamethatistooo / 123 / Outbrain')

    def test_get_name_empty_strings(self):
        request = HttpRequest()
        request.user = User(id=1)

        account = models.Account(
            name=u'',
        )
        account.save(request)

        campaign = models.Campaign(
            name=u'',
            account=account,
        )
        campaign.save(request)

        source = models.Source(
            name="Outbrain",
        )
        source.save()

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=models.AdGroup(
                id=123,
                name=u'',
                campaign=campaign,
            ),
        )

        name = ad_group_source.get_external_name()

        self.assertEqual(
            name, u'ONE:  /  /  / 123 / Outbrain')

    def test_get_dma_targeting_compatible(self):
        username = User.objects.get(pk=1).email
        self.client.login(username=username, password='secret')

        ad_group_source = models.AdGroupSource.objects.get(id=3)
        ad_group_source.source.source_type.available_actions = [
            constants.SourceAction.CAN_MODIFY_DMA_AND_SUBDIVISION_TARGETING_AUTOMATIC
        ]
        ad_group_source.source.source_type.save()

        response = self.client.get(
            reverse(
                'ad_group_sources',
                kwargs={'ad_group_id': 2}),
            follow=True
        )

        response_dict = json.loads(response.content)
        self.assertItemsEqual(response_dict['data']['sources'], [
            {'id': 2, 'name': 'Gravity', 'can_target_existing_regions': False,
                'can_retarget': True},  # should return False when DMAs used
            {'id': 3, 'name': 'Outbrain', 'can_target_existing_regions': True, 'can_retarget': True},
            {'id': 9, 'name': 'Sharethrough', 'can_target_existing_regions': False, 'can_retarget': True},
        ])

    def test_available_sources(self):
        response = self.client.get(
            reverse('ad_group_sources', kwargs={'ad_group_id': 1}),
            follow=True
        )
        # Expected sources - 9 (Sharethrough)
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict['data']['sources']), 1)
        self.assertEqual(response_dict['data']['sources'][0]['id'], 9)

    def test_available_sources_with_filter(self):
        response = self.client.get(
            reverse('ad_group_sources', kwargs={'ad_group_id': 1}),
            {'filtered_sources': '7,8,9'},
            follow=True
        )
        # Expected sources - 9 (Sharethrough)
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict['data']['sources']), 1)
        self.assertEqual(response_dict['data']['sources'][0]['id'], 9)

    def test_available_sources_with_filter_empty(self):
        response = self.client.get(
            reverse('ad_group_sources', kwargs={'ad_group_id': 1}),
            {'filtered_sources': '7,8'},
            follow=True
        )
        # Expected sources - none
        # Allowed sources 1-9, Sources 1-7 already added, 8 has no default setting
        response_dict = json.loads(response.content)
        self.assertEqual(len(response_dict['data']['sources']), 0)

    def test_put(self):
        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '9'})
        )
        self.assertEqual(response.status_code, 200)

        ad_group = models.AdGroup.objects.get(pk=1)
        source = models.Source.objects.get(pk=9)
        ad_group_sources = ad_group.sources.all()
        self.assertIn(source, ad_group_sources)

    def test_put_overwrite_cpc(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.cpc_cc = decimal.Decimal('0.01')
        new_settings.save(None)

        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '9'})
        )
        self.assertEqual(response.status_code, 200)

        source = models.Source.objects.get(pk=9)
        ad_group_sources = ad_group.sources.all()
        self.assertIn(source, ad_group_sources)

    @override_settings(K1_CONSISTENCY_SYNC=True)
    def test_put_add_content_ad_sources(self):
        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '9'})
        )
        self.assertEqual(response.status_code, 200)

        ad_group = models.AdGroup.objects.get(pk=1)
        source = models.Source.objects.get(pk=9)
        ad_group_sources = ad_group.sources.all()
        self.assertIn(source, ad_group_sources)

        content_ads = models.ContentAd.objects.filter(ad_group=ad_group)
        content_ad_sources = models.ContentAdSource.objects.filter(content_ad__ad_group=ad_group, source=source)
        self.assertTrue(content_ad_sources.exists())
        self.assertEqual(len(content_ads), len(content_ad_sources))

    def test_put_with_retargeting(self):
        ad_group = models.AdGroup.objects.get(pk=1)

        request = RequestFactory()
        request.user = User(id=1)

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()
        new_settings.retargeting_ad_groups = [2]
        new_settings.save(request)

        source = models.Source.objects.get(pk=9)
        source.supports_retargeting = False
        source.save()

        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '9'})
        )
        self.assertEqual(response.status_code, 400)

        ad_group_sources = ad_group.sources.all()
        self.assertNotIn(source, ad_group_sources)

    def test_put_existing_source(self):
        response = self.client.put(
            reverse('ad_group_sources', kwargs={'ad_group_id': '1'}),
            data=json.dumps({'source_id': '1'})
        )
        self.assertEqual(response.status_code, 400)


class AdGroupOverviewTest(TestCase):
    fixtures = ['test_api.yaml', 'users']

    def setUp(self):
        self.client = Client()
        self.user = zemauth.models.User.objects.get(email='chuck.norris@zemanta.com')

    def setUpPermissions(self):
        campaign = models.Campaign.objects.get(pk=1)
        campaign.users.add(self.user)

    def _get_ad_group_overview(self, ad_group_id, with_status=False):
        self.client.login(username=self.user.username, password='norris')
        reversed_url = reverse(
            'ad_group_overview',
            kwargs={'ad_group_id': ad_group_id})

        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        ret = [s for s in settings if name in s['name'].lower()]
        if ret != []:
            return ret[0]
        else:
            return None

    @patch('redshiftapi.api_breakdowns.query_all')
    def test_run_empty(self, mock_query_all):
        self.setUpPermissions()
        mock_query_all.return_value = [{
            'adgroup_id': 1,
            'source_id': 9,
            'e_yesterday_cost': decimal.Decimal('0.0'),
            'yesterday_et_cost': decimal.Decimal('0.0'),
            'yesterday_etfm_cost': decimal.Decimal('0.0'),
        }]

        ad_group = models.AdGroup.objects.get(pk=1)
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        credit = models.CreditLineItem.objects.create_unsafe(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        models.BudgetLineItem.objects.create_unsafe(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        new_settings = ad_group.get_current_settings().copy_settings()
        new_settings.state = constants.AdGroupSettingsState.ACTIVE
        new_settings.save(None)

        new_settings = ad_group.adgroupsource_set.filter(id=1)[0].get_current_settings().copy_settings()
        new_settings.state = constants.AdGroupSourceSettingsState.ACTIVE
        new_settings.save(None)

        response = self._get_ad_group_overview(1)

        self.assertTrue(response['success'])
        header = response['data']['header']
        self.assertEqual(header['title'], u'test adgroup 1 Čžš')
        self.assertEqual(constants.InfoboxStatus.INACTIVE, header['active'])

        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']
        flight_setting = self._get_setting(settings, 'flight')
        self.assertEqual('03/02 - 04/02', flight_setting['value'])

        budget_setting = self._get_setting(settings, 'campaign budget')
        self.assertIsNone(budget_setting, 'no permission')

        pacing_setting = self._get_setting(settings, 'pacing')
        self.assertIsNone(pacing_setting, 'no permission')

        goal_setting = [s for s in settings if 'goal' in s['name'].lower()]
        self.assertEqual([], goal_setting)

        response = self._get_ad_group_overview(1)
        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']

        yesterday_spend = self._get_setting(settings, 'yesterday')
        self.assertEqual('$0.00', yesterday_spend['value'])

    @patch('redshiftapi.api_breakdowns.query_all')
    def test_run_mid(self, mock_query_all):
        self.setUpPermissions()
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        # check values for adgroup that is in the middle of flight time
        # and is overperforming
        ad_group = models.AdGroup.objects.get(pk=1)
        ad_group_settings = ad_group.get_current_settings()
        new_ad_group_settings = ad_group_settings.copy_settings()
        new_ad_group_settings.start_date = start_date
        new_ad_group_settings.end_date = end_date
        new_ad_group_settings.state = constants.AdGroupSettingsState.ACTIVE
        new_ad_group_settings.save(None)

        new_settings = ad_group.adgroupsource_set.filter(id=1)[0].get_current_settings().copy_settings()
        new_settings.state = constants.AdGroupSourceSettingsState.ACTIVE
        new_settings.save(None)

        credit = models.CreditLineItem.objects.create_unsafe(
            account=ad_group.campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        budget = models.BudgetLineItem.objects.create_unsafe(
            campaign=ad_group.campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        models.BudgetDailyStatement.objects.create(
            budget=budget,
            date=datetime.datetime.today() - datetime.timedelta(days=1),
            media_spend_nano=60 * 10**9,
            data_spend_nano=0,
            license_fee_nano=0,
            margin_nano=0,
        )

        mock_query_all.return_value = [{
            'e_yesterday_cost': decimal.Decimal('60.0'),
            'yesterday_et_cost': decimal.Decimal('60.0'),
            'yesterday_etfm_cost': decimal.Decimal('60.0'),
        }]

        response = self._get_ad_group_overview(1)

        self.assertTrue(response['success'])
        header = response['data']['header']
        self.assertEqual(header['title'], u'test adgroup 1 Čžš')
        self.assertEqual(constants.InfoboxStatus.AUTOPILOT, header['active'])

        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']

        flight_setting = self._get_setting(settings, 'flight')
        self.assertEqual('{sm}/{sd} - {em}/{ed}'.format(
            sm="{:02d}".format(start_date.month),
            sd="{:02d}".format(start_date.day),
            em="{:02d}".format(end_date.month),
            ed="{:02d}".format(end_date.day),
        ), flight_setting['value'])

        response = self._get_ad_group_overview(1)
        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']

        yesterday_setting = self._get_setting(settings, 'yesterday')
        self.assertEqual('$60.00', yesterday_setting['value'])
        self.assertEqual('12.00% of $500.00 Daily Spend Cap', yesterday_setting['description'])


class CampaignOverviewTest(TestCase):
    fixtures = ['test_api', 'users']

    def setUp(self):
        self.client = Client()
        self.user = zemauth.models.User.objects.get(email='chuck.norris@zemanta.com')

    def setUpPermissions(self):
        campaign = models.Campaign.objects.get(pk=1)
        campaign.users.add(self.user)

    def _get_campaign_overview(self, campaign_id, user_id=2, with_status=False):
        self.client.login(username=self.user.username, password='norris')
        reversed_url = reverse(
            'campaign_overview',
            kwargs={'campaign_id': campaign_id})
        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        matching_settings = [s for s in settings if name in s['name'].lower()]
        if matching_settings:
            return matching_settings[0]
        return None

    @patch('redshiftapi.api_breakdowns.query_all')
    def test_run_empty(self, mock_query_all):
        mock_query_all.return_value = [{
            'campaign_id': 1,
            'source_id': 9,
            'e_yesterday_cost': decimal.Decimal('0.0'),
            'yesterday_et_cost': decimal.Decimal('0.0'),
            'yesterday_etfm_cost': decimal.Decimal('0.0'),
        }]
        req = RequestFactory().get('/')
        req.user = self.user

        adg_start_date = datetime.datetime.now() - datetime.timedelta(days=1)
        adg_end_date = datetime.datetime.now() + datetime.timedelta(days=1)

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = adg_start_date
            new_adgs.end_date = adg_end_date
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)

        self.setUpPermissions()

        campaign = models.Campaign.objects.get(pk=1)
        start_date = (datetime.datetime.utcnow() - datetime.timedelta(days=15)).date()
        end_date = (datetime.datetime.utcnow() + datetime.timedelta(days=15)).date()

        credit = models.CreditLineItem.objects.create_unsafe(
            account=campaign.account,
            start_date=start_date,
            end_date=end_date,
            amount=100,
            status=constants.CreditLineItemStatus.SIGNED,
            created_by=self.user,
        )

        models.BudgetLineItem.objects.create_unsafe(
            campaign=campaign,
            credit=credit,
            amount=100,
            start_date=start_date,
            end_date=end_date,
            created_by=self.user,
        )

        response = self._get_campaign_overview(1)
        self.assertTrue(response['success'])

        header = response['data']['header']
        self.assertEqual(u'test campaign 1 \u010c\u017e\u0161', header['title'])
        self.assertEqual(constants.InfoboxStatus.ACTIVE, header['active'])

        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']

        goal_setting = [s for s in settings if 'goal' in s['name'].lower()]
        self.assertEqual([], goal_setting)

        response = self._get_campaign_overview(1)
        settings = response['data']['basic_settings'] +\
            response['data']['performance_settings']

        budget_setting = self._get_setting(settings, 'campaign budget')
        self.assertEqual('$80.00', budget_setting['value'])
        self.assertEqual('$80.00 remaining', budget_setting['description'])

        pacing_setting = self._get_setting(settings, 'pacing')
        self.assertEqual('$0.00', pacing_setting['value'])
        self.assertEqual('0.00% on plan', pacing_setting['description'])


class AccountOverviewTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.client = Client()

        self.user = zemauth.models.User.objects.get(pk=2)

    def _get_account_overview(self, account_id, user_id=2, with_status=False):
        user = User.objects.get(pk=user_id)
        self.client.login(username=user.username, password='secret')
        reversed_url = reverse(
            'account_overview',
            kwargs={'account_id': account_id})
        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def _get_setting(self, settings, name):
        return [s for s in settings if name in s['name'].lower()][0]

    @patch('dash.models.Account.get_current_settings')
    def test_run_empty(self, mock_current_settings):
        req = RequestFactory().get('/')
        req.user = self.user

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            new_adgs.end_date = datetime.datetime.now() + datetime.timedelta(days=1)
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)

        settings = models.AccountSettings(
            default_account_manager=zemauth.models.User.objects.get(pk=1),
            default_sales_representative=zemauth.models.User.objects.get(pk=2),
        )

        mock_current_settings.return_value = settings

        # do some extra setup to the account
        response = self._get_account_overview(1)
        settings = response['data']['basic_settings']

    @patch('dash.models.Account.get_current_settings')
    def test_run_empty_non_archived(self, mock_current_settings):
        req = RequestFactory().get('/')
        req.user = self.user

        # make all adgroups active
        for adgs in models.AdGroupSettings.objects.all():
            new_adgs = adgs.copy_settings()
            new_adgs.start_date = datetime.datetime.now() - datetime.timedelta(days=1)
            new_adgs.end_date = datetime.datetime.now() + datetime.timedelta(days=1)
            new_adgs.state = constants.AdGroupSettingsState.ACTIVE
            new_adgs.save(req)

        # make all adgroup sources active
        for adgss in models.AdGroupSourceSettings.objects.all():
            new_adgss = adgss.copy_settings()
            new_adgss.state = constants.AdGroupSourceSettingsState.ACTIVE
            new_adgss.save(req)
        settings = models.AccountSettings(
            default_account_manager=zemauth.models.User.objects.get(pk=1),
            default_sales_representative=zemauth.models.User.objects.get(pk=2),
        )

        mock_current_settings.return_value = settings

        campaign_settings = models.Campaign.objects.get(pk=1).get_current_settings()
        new_campaign_settings = campaign_settings.copy_settings()
        new_campaign_settings.archived = True
        new_campaign_settings.save(req)

        adgroup_settings = models.AdGroup.objects.get(pk=1).get_current_settings()
        new_adgroup_settings = adgroup_settings.copy_settings()
        new_adgroup_settings.archived = True
        new_adgroup_settings.save(req)

        # do some extra setup to the account
        response = self._get_account_overview(1)
        settings = response['data']['basic_settings']


class AllAccountsOverviewTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.client = Client()

    def _get_all_accounts_overview(self, campaign_id, user_id=2, with_status=False):
        user = User.objects.get(pk=user_id)
        self.client.login(username=user.username, password='secret')
        reversed_url = reverse(
            'all_accounts_overview',
            kwargs={})
        response = self.client.get(
            reversed_url,
            follow=True
        )
        return json.loads(response.content)

    def test_run_empty(self):
        permission_2 = Permission.objects.get(codename='can_access_all_accounts_infobox')
        user = zemauth.models.User.objects.get(pk=2)
        user.user_permissions.add(permission_2)
        user.save()

        response = self._get_all_accounts_overview(1)
        self.assertTrue(response['success'])

    def test_agency_permission(self):
        response = self._get_all_accounts_overview(1)
        self.assertFalse(response['success'])

        permission_2 = Permission.objects.get(codename='can_access_agency_infobox')
        user = zemauth.models.User.objects.get(pk=2)
        user.user_permissions.add(permission_2)
        user.save()

        response = self._get_all_accounts_overview(1)
        self.assertTrue(response['success'])

        self.assertEqual(
            set(['Active accounts:']),
            set(s['name'] for s in response['data']['basic_settings'])
        )

        response = self._get_all_accounts_overview(1)
        self.assertTrue(response['success'])

        self.assertEqual(
            set(['Active accounts:']),
            set(s['name'] for s in response['data']['basic_settings'])
        )


class DemoTest(TestCase):
    fixtures = ['test_api.yaml']

    def _get_client(self, has_permission=True):
        user = User.objects.get(pk=2)
        if has_permission:
            permission = Permission.objects.get(codename='can_request_demo_v3')
            user.user_permissions.add(permission)
            user.save()

        client = Client()
        client.login(username=user.username, password='secret')
        return client

    @patch.object(views.Demo, '_start_instance')
    @patch('dash.views.views.send_mail')
    @patch('dash.views.views.email_helper')
    def test_get(self, email_helper_mock, send_mail_mock, start_instance_mock):
        start_instance_mock.return_value = {'url': 'test-url', 'password': 'test-password'}
        email_helper_mock.format_email.return_value = ('test-subject', 'test-body', [])
        email_helper_mock.format_template.return_value = 'html'

        reversed_url = reverse('demov3')
        response = self._get_client().get(reversed_url, follow=True)
        self.assertEqual(200, response.status_code)

        start_instance_mock.assert_called_once_with()
        email_helper_mock.format_email.assert_called_once_with(15, url='test-url', password='test-password')
        send_mail_mock.assert_called_once_with(
            'test-subject',
            'test-body',
            'Zemanta <help-test@zemanta.com>',
            ['mad.max@zemanta.com'],
            fail_silently=False,
            html_message='html',
        )

        data = json.loads(response.content)
        self.assertEqual({'data': {'url': 'test-url', 'password': 'test-password'}, 'success': True}, data)

    def test_get_permission(self):
        reversed_url = reverse('demov3')
        response = self._get_client(has_permission=False).get(reversed_url, follow=True)
        self.assertEqual(404, response.status_code)
        self.assertTemplateUsed(response, '404.html')

    @patch('dash.views.views.request_signer')
    def test_start_instance(self, request_signer_mock):
        data = {
            'status': 'success',
            'instance_url': 'test-url',
            'instance_password': 'test-password',
        }

        request_signer_mock.urllib2_secure_open.return_value.getcode.return_value = 200
        request_signer_mock.urllib2_secure_open.return_value.read.return_value = json.dumps(data)

        demo = views.Demo()
        instance = demo._start_instance()

        self.assertEqual(instance, {'url': 'test-url', 'password': 'test-password'})
