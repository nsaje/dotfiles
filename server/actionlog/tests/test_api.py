# coding: utf-8

import datetime
import mock
import urlparse
import urllib2

from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http.request import HttpRequest

from actionlog import api, constants, models, sync, exceptions
from dash import models as dashmodels
from dash import constants as dashconstants
from utils import test_helper, url_helper
from zemauth.models import User


class ActionLogApiTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        patcher_urlopen = mock.patch('utils.request_signer._secure_opener.open')
        self.addCleanup(patcher_urlopen.stop)

        mock_urlopen = patcher_urlopen.start()
        test_helper.prepare_mock_urlopen(mock_urlopen)

        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

        self.maxDiff = None

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_set_ad_group_source_settings_non_maintenance(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        changes = {
            'state': dashconstants.AdGroupSourceSettingsState.ACTIVE,
            'cpc_cc': 0.33,
            'daily_budget_cc': 100,
        }

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=False)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        source_settings.save(request)

        api.set_ad_group_source_settings(changes, source_settings.ad_group_source, request)

        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source
        )

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).strftime(
            '%Y-%m-%dT%H:%M:%S.%f')[:-3]

        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse(
                'api.zwei_callback',
                kwargs={'action_id': action.id})
        )

        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.SET_CAMPAIGN_STATE,
            'expiration_dt': expiration_dt,
            'args': {
                'source_campaign_key': ad_group_source.source_campaign_key,
                'conf': {
                    'cpc_cc': 3300,
                    'daily_budget_cc': 1000000,
                    'state': dashconstants.AdGroupSourceSettingsState.ACTIVE
                },
                'extra': {},
            },
            'callback_url': callback,
        }
        self.assertEqual(action.payload, payload)

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_set_ad_group_source_settings_maintenance(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        changes = {
            'state': dashconstants.AdGroupSourceSettingsState.ACTIVE,
            'cpc_cc': 0.33,
            'daily_budget_cc': 100,
        }

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=True)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        source_settings.save(request)

        api.set_ad_group_source_settings(changes, source_settings.ad_group_source, request)

        actions = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).order_by('created_dt')[:3]

        for action in actions:
            self.assertEqual(action.action, constants.Action.SET_PROPERTY)
            self.assertEqual(action.action_type, constants.ActionType.MANUAL)
            self.assertEqual(action.state, constants.ActionState.WAITING)
            self.assertTrue('property' in action.payload)
            self.assertTrue('value' in action.payload)

            for k, v in changes.iteritems():
                if k == action.payload['property']:
                    self.assertEqual(action.payload['value'], v)

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_init_enable_ad_group_non_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=False)[0]

        ad_group.campaign.account.allowed_sources.add(ad_group_source.source_id)
        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        source_settings.save(request)

        api.init_enable_ad_group(ad_group, request)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.ACTIVE})

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )
        source_settings.save(request)

        api.init_enable_ad_group(ad_group, request)

        # Nothing changed, since the source is inactive
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ad_group_source).latest('created_dt'),
                         action)




    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_init_enable_ad_group_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=True)[0]

        ad_group.campaign.account.allowed_sources.add(ad_group_source.source_id) 

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        source_settings.save(request)

        api.init_enable_ad_group(ad_group, request)

        # No manual action is created
        self.assertEqual(list(models.ActionLog.objects.filter(ad_group_source=ad_group_source)), [])

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )
        source_settings.save(request)

        api.init_enable_ad_group(ad_group, request)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_PROPERTY)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload, {'property': 'state', 'value': dashconstants.AdGroupSourceSettingsState.ACTIVE})

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_init_pause_ad_group_non_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=False)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        source_settings.save(request)

        api.init_pause_ad_group(ad_group, request)

        action1 = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action1.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action1.action_type, constants.ActionType.AUTOMATIC)
        # Action can be delayed since we are changing two settings in source settings
        self.assertTrue(action1.state in (constants.ActionState.DELAYED, constants.ActionState.WAITING))
        self.assertEqual(action1.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.INACTIVE})

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )
        source_settings.save(request)

        api.init_pause_ad_group(ad_group, request)

        action2 = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        # Check if action is sent even ad group source is already paused
        self.assertNotEqual(action1.pk, action2.pk)
        self.assertEqual(action2.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action2.action_type, constants.ActionType.AUTOMATIC)
        # Action can be delayed since we are changing two settings in source settings
        self.assertTrue(action1.state in (constants.ActionState.DELAYED, constants.ActionState.WAITING))
        self.assertEqual(action2.payload.get('args', {}).get('conf'),
                         {'state': dashconstants.AdGroupSourceSettingsState.INACTIVE})

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_init_pause_ad_group_maintenance_source(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=True)[0]

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.ACTIVE
        )

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        source_settings.save(request)

        api.init_pause_ad_group(ad_group, request)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_PROPERTY)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload, {'property': 'state', 'value': dashconstants.AdGroupSourceSettingsState.INACTIVE})

        source_settings = dashmodels.AdGroupSourceSettings(
            ad_group_source=ad_group_source,
            cpc_cc=0.20,
            daily_budget_cc=50,
            state=dashconstants.AdGroupSourceSettingsState.INACTIVE
        )
        source_settings.save(request)

        api.init_pause_ad_group(ad_group, request)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_PROPERTY)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload, {'property': 'state', 'value': dashconstants.AdGroupSourceSettingsState.INACTIVE})

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_delaying_set_ad_group_source_settings(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)
        ad_group = dashmodels.AdGroup.objects.get(id=1)

        # Source is IS in maintenance mode
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=True)[0]

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        # Only one change per ad_group_source
        changes = {'cpc_cc': 0.3}
        api.set_ad_group_source_settings(changes, ad_group_source, request)

        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_PROPERTY)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload, {'property': 'cpc_cc', 'value': 3000})

        # Two changes
        changes = {'cpc_cc': 0.3, 'daily_budget_cc': 100.0}
        api.set_ad_group_source_settings(changes, ad_group_source, request)

        actions = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).order_by('created_dt')[:3]

        for action in actions:
            self.assertEqual(action.action, constants.Action.SET_PROPERTY)
            self.assertEqual(action.action_type, constants.ActionType.MANUAL)
            self.assertEqual(action.state, constants.ActionState.WAITING)
            self.assertTrue('property' in action.payload)
            self.assertTrue('value' in action.payload)

            for k, v in changes.iteritems():
                if k == action.payload['property']:
                    self.assertEqual(action.payload['value'], v)

        # Source is NOT in maintenance mode
        ad_group_source = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group,
                                                                  source__maintenance=False)[0]

        # Only one change per ad_group_source
        changes = {'cpc_cc': 0.3}
        api.set_ad_group_source_settings(changes, ad_group_source, request)
        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.WAITING)
        self.assertEqual(action.payload.get('args', {}).get('conf'), changes)

        # Two changes
        changes = {'cpc_cc': 0.3, 'daily_budget_cc': 100.0}
        api.set_ad_group_source_settings(changes, ad_group_source, request)
        action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source
        ).latest('created_dt')

        self.assertEqual(action.action, constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
        self.assertEqual(action.state, constants.ActionState.DELAYED)
        self.assertEqual(action.payload.get('args', {}).get('conf'), changes)

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_fetch_ad_group_status(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_sources = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=False)
        sync.AdGroupSync(ad_group).trigger_status()

        for ad_group_source in ad_group_sources.all():

            action = models.ActionLog.objects.get(
                ad_group_source=ad_group_source,
            )

            self.assertEqual(
                action.action,
                constants.Action.FETCH_CAMPAIGN_STATUS
            )
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
            self.assertEqual(action.state, constants.ActionState.WAITING)

            expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
                strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'source': ad_group_source.source.source_type.type,
                'action': constants.Action.FETCH_CAMPAIGN_STATUS,
                'expiration_dt': expiration_dt,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                },
                'callback_url': callback,
            }

            self.assertEqual(action.payload, payload)

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_fetch_ad_group_reports(self):
        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group = dashmodels.AdGroup.objects.get(id=1)
        ad_group_sources = dashmodels.AdGroupSource.objects.filter(ad_group=ad_group, source__maintenance=False)
        date = datetime.date(2014, 6, 1)

        ad_group_sync = sync.AdGroupSync(ad_group)
        for ad_group_source_sync in ad_group_sync.get_components():
            ad_group_source_sync.trigger_reports_for_dates([date])

        for ad_group_source in ad_group_sources.all():
            action = models.ActionLog.objects.get(
                ad_group_source=ad_group_source,
            )

            self.assertEqual(action.action, constants.Action.FETCH_REPORTS)
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)
            self.assertEqual(action.state, constants.ActionState.WAITING)

            expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
                strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
            callback = urlparse.urljoin(
                settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
            )
            payload = {
                'source': ad_group_source.source.source_type.type,
                'action': constants.Action.FETCH_REPORTS,
                'expiration_dt': expiration_dt,
                'args': {
                    'source_campaign_key': ad_group_source.source_campaign_key,
                    'date': date.strftime('%Y-%m-%d'),
                },
                'callback_url': callback
            }
            self.assertEqual(action.payload, payload)

    def test_init_set_ad_group_manual_property(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(pk=1)

        prop = 'fake_property'
        value = 'fake_value'

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.init_set_ad_group_manual_property(ad_group_source, request, prop, value)

        action = models.ActionLog.objects.get(ad_group_source=ad_group_source)

        self.assertEqual(action.action, constants.Action.SET_PROPERTY)
        self.assertEqual(action.action_type, constants.ActionType.MANUAL)

        payload = {
            'property': prop,
            'value': value
        }
        self.assertEqual(action.payload, payload)

    def test_init_set_ad_group_manual_action_pending(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(pk=1)
        ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

        prop = 'fake_property'
        value = 'fake_value'

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.init_set_ad_group_manual_property(ad_group_source, request, prop, value)

        with self.assertRaises(models.ActionLog.DoesNotExist):
            models.ActionLog.objects.get(ad_group_source=ad_group_source)

    def test_actionlog_added(self):
        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')
        ad_group_source = dashmodels.AdGroupSource.objects.get(pk=1)
        now = datetime.datetime.now()
        api.init_set_ad_group_manual_property(ad_group_source, request, 'test_property', 'test_value')
        # check if a new action log object was added
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.MANUAL,
            ad_group_source=ad_group_source,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value')
        for alog in alogs:
            alog.delete()

    def test_abort_waiting_actionlog(self):
        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')
        ad_group_source = dashmodels.AdGroupSource.objects.get(pk=1)
        now = datetime.datetime.now()
        api.init_set_ad_group_manual_property(ad_group_source, request, 'test_property', 'test_value_1')
        # insert a new action
        # if the ad_group_source and property are the same
        # the old one should be set to aborted and the new one should be set to waiting
        api.init_set_ad_group_manual_property(ad_group_source, request, 'test_property', 'test_value_2')
        # old action is aborted
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.ABORTED,
            action_type=constants.ActionType.MANUAL,
            ad_group_source=ad_group_source,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value_1')
        for alog in alogs:
            alog.delete()
        # new action is waiting
        alogs = models.ActionLog.objects.filter(
            action=constants.Action.SET_PROPERTY,
            state=constants.ActionState.WAITING,
            action_type=constants.ActionType.MANUAL,
            ad_group_source=ad_group_source,
            created_dt__gt=now
        )
        self.assertEqual(len(alogs) == 1, True)
        self.assertEqual(alogs[0].payload['property'], 'test_property')
        self.assertEqual(alogs[0].payload['value'], 'test_value_2')
        for alog in alogs:
            alog.delete()

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_create_campaign(self):

        utcnow = datetime.datetime.utcnow()
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ad_group_source_failing = dashmodels.AdGroupSource.objects.get(id=1)

        name = 'Test'

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.create_campaign(ad_group_source_failing, name, request)
        self.assertFalse(models.ActionLog.objects.filter(
            ad_group_source=ad_group_source_failing,
            action=constants.Action.CREATE_CAMPAIGN
        ).exists())

        ad_group_source = dashmodels.AdGroupSource.objects.get(id=5)
        ad_group_settings = ad_group_source.ad_group.get_current_settings()

        api.create_campaign(ad_group_source, name, request)
        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source,
            action=constants.Action.CREATE_CAMPAIGN
        )

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
            strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
        )
        payload = {
            'source': ad_group_source.source.source_type.type,
            'action': constants.Action.CREATE_CAMPAIGN,
            'expiration_dt': expiration_dt,
            'args': {
                'name': name,
                'extra': {
                    'tracking_code': url_helper.combine_tracking_codes(
                        ad_group_settings.get_tracking_codes(),
                        ad_group_source.get_tracking_ids(),  # should have tracking ids
                    ),
                    'tracking_slug': 'yahoo',
                    'target_regions': ['UK', 'US', 'CA'],
                    'target_devices': ['desktop', 'mobile'],
                    'start_date': '2015-03-02',
                    'end_date': '2015-04-02',
                    'brand_name': 'Example',
                    'display_url': 'example.com',
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)

        ad_group_source_extra = dashmodels.AdGroupSource.objects.get(id=8)
        ad_group_settings = ad_group_source_extra.ad_group.get_current_settings()

        api.create_campaign(ad_group_source_extra, name, request)
        action = models.ActionLog.objects.get(
            ad_group_source=ad_group_source_extra,
            action=constants.Action.CREATE_CAMPAIGN
        )

        expiration_dt = (utcnow + datetime.timedelta(minutes=models.ACTION_TIMEOUT_MINUTES)).\
            strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3]
        callback = urlparse.urljoin(
            settings.EINS_HOST, reverse('api.zwei_callback', kwargs={'action_id': action.id})
        )
        payload = {
            'source': ad_group_source_extra.source.source_type.type,
            'action': constants.Action.CREATE_CAMPAIGN,
            'expiration_dt': expiration_dt,
            'args': {
                'name': name,
                'extra': {
                    'iab_category': 'IAB24',
                    'tracking_code':  url_helper.combine_tracking_codes(
                        ad_group_settings.get_tracking_codes()  # no tracking ids as ga tracking is disabled
                    ),
                    'tracking_slug': 'industrybrains',
                    'target_devices': [],
                    'target_regions': ['693'],
                    'start_date': None,
                    'end_date': None,
                    'brand_name': 'Example',
                    'display_url': 'example.com',
                    'ad_group_id': 2,
                    'exchange': 'adsnative'
                },
            },
            'callback_url': callback
        }
        self.assertEqual(action.payload, payload)


class GetAdGroupSourcesWaitingTest(TestCase):
    fixtures = ['test_api.yaml', 'test_actionlog_waiting.yaml']

    def test_get_ad_group_sources_waiting(self):
        ad_group_sources = api.get_ad_group_sources_waiting()

        ad_group_source_ids = set(ags.id for ags in ad_group_sources)
        expected_ids = set([19, 21])

        self.assertEqual(ad_group_source_ids, expected_ids)


class ActionLogApiCancelExpiredTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_actionlog.yaml']

    @mock.patch('actionlog.api.datetime', test_helper.MockDateTime)
    def test_cancel_expired_actionlogs(self):

        waiting_actionlogs_before = models.ActionLog.objects.filter(
            state=constants.ActionState.WAITING
        )
        self.assertEqual(len(waiting_actionlogs_before), 10)

        api.datetime.utcnow = classmethod(lambda cls: datetime.datetime(2014, 7, 3, 18, 15, 0))
        api.cancel_expired_actionlogs()
        waiting_actionlogs_after = models.ActionLog.objects.filter(
            state=constants.ActionState.WAITING
        )
        self.assertEqual(len(waiting_actionlogs_after), 10)
        self.assertEqual(
            {action.id for action in waiting_actionlogs_before},
            {action.id for action in waiting_actionlogs_after}
        )

        api.datetime.utcnow = classmethod(lambda cls: datetime.datetime(2014, 7, 3, 18, 45, 0))
        api.cancel_expired_actionlogs()
        failed_actionlogs = models.ActionLog.objects.filter(
            state=constants.ActionState.FAILED
        )
        self.assertEqual(len(failed_actionlogs), 10)
        self.assertEqual(
            {action.id for action in failed_actionlogs},
            {action.id for action in waiting_actionlogs_after}
        )

    def test_init_ad_group_source_settings_w_source_key(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(id=1)

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        self.assertNotEqual(ad_group_source.source_campaign_key, {})
        self.assertIsNone(api._init_set_ad_group_source_settings(ad_group_source, {}, request, order=None))

    def test_init_ad_group_source_settings_pending_source_key(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(id=1)
        ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api._init_set_ad_group_source_settings(ad_group_source, {}, request, order=None)

        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ad_group_source).count(), 22)

        manual_action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=constants.ActionType.MANUAL
        )

        self.assertFalse(manual_action.exists())

    def test_init_ad_group_source_settings_manual_daily_budget(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(id=1)

        ad_group_source.source.source_type.available_actions = [
            dashconstants.SourceAction.CAN_UPDATE_DAILY_BUDGET_MANUAL
        ]
        ad_group_source.source.source_type.save()

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        manual_action = models.ActionLog.objects.filter(
            ad_group_source=ad_group_source,
            action_type=constants.ActionType.MANUAL
        )

        self.assertFalse(manual_action.exists())

        api._init_set_ad_group_source_settings(
            ad_group_source, {'daily_budget_cc': 100000}, request, order=None)

        self.assertTrue(manual_action.exists())

    def test_init_ad_group_source_settings_deprecated(self):
        ad_group_source = dashmodels.AdGroupSource.objects.get(id=3)

        ad_group_source.source.deprecated = True
        ad_group_source.source.save()

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        action = models.ActionLog.objects.filter(ad_group_source=ad_group_source)

        api._init_set_ad_group_source_settings(
            ad_group_source, {'daily_budget_cc': 100000}, request, order=None)

        self.assertFalse(action.exists())


class SendDelayedActionsTestCase(TestCase):

    fixtures = ['test_api.yaml', 'test_actionlog_send_delayed.yaml']

    def setUp(self):
        patcher_urlopen = mock.patch('utils.request_signer._secure_opener.open')
        self.addCleanup(patcher_urlopen.stop)

        mock_urlopen = patcher_urlopen.start()
        test_helper.prepare_mock_urlopen(mock_urlopen)

        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

        self.maxDiff = None

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_ad_group_specified(self):
        utcnow = datetime.datetime(2015, 2, 25, 18, 45)
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ags1 = dashmodels.AdGroupSource.objects.get(id=1)
        ags2 = dashmodels.AdGroupSource.objects.get(id=2)

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 2)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.SET_CAMPAIGN_STATE).count(),
                         0)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 2)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.SET_CAMPAIGN_STATE).count(),
                         0)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        api.send_delayed_actionlogs([ags1])

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 1)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 2)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 0)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')

        api.send_delayed_actionlogs([ags1])

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 1)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 2)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 0)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')

        api.send_delayed_actionlogs([ags2])

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 1)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 1)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')

    @mock.patch('actionlog.models.datetime', test_helper.MockDateTime)
    def test_ad_group_not_specified(self):
        utcnow = datetime.datetime(2015, 2, 25, 18, 45)
        models.datetime.utcnow = classmethod(lambda cls: utcnow)

        ags1 = dashmodels.AdGroupSource.objects.get(id=1)
        ags2 = dashmodels.AdGroupSource.objects.get(id=2)

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 2)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 0)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 2)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 0)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        api.send_delayed_actionlogs()

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 1)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags1,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags1,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')

        delayed_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.DELAYED,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(delayed_actions.count(), 1)
        waiting_actions = models.ActionLog.objects.filter(ad_group_source=ags2,
                                                          state=constants.ActionState.WAITING,
                                                          action=constants.Action.SET_CAMPAIGN_STATE)
        self.assertEqual(waiting_actions.count(), 1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_REPORTS).count(),
                         1)
        self.assertEqual(models.ActionLog.objects.filter(ad_group_source=ags2,
                                                         state=constants.ActionState.WAITING,
                                                         action=constants.Action.FETCH_CAMPAIGN_STATUS).count(),
                         1)

        for action in delayed_actions:
            self.assertIsNone(action.expiration_dt)

        for action in waiting_actions:
            self.assertEquals(action.expiration_dt, datetime.datetime(2015, 2, 25, 19, 15))
            self.assertEquals(action.payload['expiration_dt'], '2015-02-25T19:15:00')


class SyncInProgressTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def test_ad_groups_sync_in_progress(self):
        ad_group = dashmodels.AdGroup.objects.get(pk=1)

        self.assertEqual(models.ActionLog.objects.filter(ad_group_source__ad_group=ad_group).count(), 0)

        self.assertEqual(api.is_sync_in_progress([ad_group]), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=1),
        )
        alog.save()

        self.assertEqual(api.is_sync_in_progress([ad_group]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress([ad_group]), False)

    def test_multiple_ad_groups_sync_in_progress(self):
        ad_group = dashmodels.AdGroup.objects.get(pk=1)
        ad_group2 = dashmodels.AdGroup.objects.get(pk=2)

        self.assertEqual(
            models.ActionLog.objects.filter(ad_group_source__ad_group__in=[ad_group, ad_group2]).count(),
            0
        )

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=1),
        )
        alog.save()

        alog2 = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=7),
        )
        alog2.save()

        self.assertEqual(api.is_sync_in_progress([ad_group, ad_group2]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()
        self.assertEqual(api.is_sync_in_progress([ad_group, ad_group2]), True)

        alog2.state = constants.ActionState.SUCCESS
        alog2.save()
        self.assertEqual(api.is_sync_in_progress([ad_group, ad_group2]), False)

    def test_accounts_sync_in_progress(self):
        account = dashmodels.Account.objects.get(pk=1)
        self.assertEqual(
            models.ActionLog.objects.filter(ad_group_source__ad_group__campaign__account=account).count(),
            0
        )

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.filter(ad_group__campaign__account=account)[0],
        )
        alog.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), False)

    def test_multiple_accounts_sync_in_progress(self):
        account = dashmodels.Account.objects.get(pk=1)
        account2 = dashmodels.Account.objects.get(pk=2)
        self.assertEqual(
            models.ActionLog.objects.filter(
                ad_group_source__ad_group__campaign__account__in=[account, account2]
            ).count(), 0)

        self.assertEqual(api.is_sync_in_progress(accounts=[account]), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.filter(ad_group__campaign__account=account)[0],
        )
        alog.save()

        alog2 = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.filter(ad_group__campaign__account=account2)[0],
        )
        alog2.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account, account2]), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account, account2]), True)

        alog2.state = constants.ActionState.SUCCESS
        alog2.save()

        self.assertEqual(api.is_sync_in_progress(accounts=[account, account2]), False)

    def test_global_sync_in_progress(self):
        self.assertEqual(models.ActionLog.objects.all().count(), 0)

        self.assertEqual(api.is_sync_in_progress(), False)

        alog = models.ActionLog(
            action=constants.Action.FETCH_REPORTS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=1),
        )
        alog.save()

        self.assertEqual(api.is_sync_in_progress(), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_sync_in_progress(), False)

    def test_publisher_blacklist_adg_sync_in_progress(self):

        ad_group = dashmodels.AdGroup.objects.get(pk=1)

        #  def is_publisher_blacklist_sync_in_progress(ad_group):
        self.assertEqual(models.ActionLog.objects.all().count(), 0)

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)

        alog = models.ActionLog(
            action=constants.Action.SET_PUBLISHER_BLACKLIST,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dashmodels.AdGroupSource.objects.get(pk=1),
        )
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)

    def test_publisher_blacklist_campaign_sync_in_progress(self):

        ad_group = dashmodels.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign

        #  def is_publisher_blacklist_sync_in_progress(ad_group):
        self.assertEqual(models.ActionLog.objects.all().count(), 0)

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)

        alog = models.ActionLog(
            action=constants.Action.SET_PUBLISHER_BLACKLIST,
            action_type=constants.ActionType.AUTOMATIC,
            payload={
                "args": {
                    "level": dashconstants.PublisherBlacklistLevel.CAMPAIGN,
                    "key": [campaign.id]
                }
            }
        )
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)

    def test_publisher_blacklist_account_sync_in_progress(self):

        ad_group = dashmodels.AdGroup.objects.get(pk=1)
        campaign = ad_group.campaign
        account = campaign.account

        #  def is_publisher_blacklist_sync_in_progress(ad_group):
        self.assertEqual(models.ActionLog.objects.all().count(), 0)

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)

        alog = models.ActionLog(
            action=constants.Action.SET_PUBLISHER_BLACKLIST,
            action_type=constants.ActionType.AUTOMATIC,
            payload={
                "args": {
                    "level": dashconstants.PublisherBlacklistLevel.ACCOUNT,
                    "key": [account.id]
                }
            }
        )
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)

    def test_publisher_blacklist_global_sync_in_progress(self):

        ad_group = dashmodels.AdGroup.objects.get(pk=1)

        #  def is_publisher_blacklist_sync_in_progress(ad_group):
        self.assertEqual(models.ActionLog.objects.all().count(), 0)

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)

        alog = models.ActionLog(
            action=constants.Action.SET_PUBLISHER_BLACKLIST,
            action_type=constants.ActionType.AUTOMATIC,
            payload={
                "args": {
                    "level": dashconstants.PublisherBlacklistLevel.GLOBAL,
                }
            }
        )
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), True)

        alog.state = constants.ActionState.SUCCESS
        alog.save()

        self.assertEqual(api.is_publisher_blacklist_sync_in_progress(ad_group), False)
