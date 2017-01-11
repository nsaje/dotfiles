import decimal
import datetime
import mock

from django.db import connection
from django.conf import settings
from django.test import TestCase, override_settings
from django.http.request import HttpRequest

import dash.models

from dash import models
from dash import api
from dash import constants

from zemauth.models import User

from utils import test_helper


class AddContentAdSources(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.request = HttpRequest()
        self.request.user = User.objects.create_user('test@example.com')

    def test_ad_content_ad_sources_supported(self):
        ad_group_source = models.AdGroupSource(
            source_id=5,
            ad_group_id=1,
        )
        ad_group_source.can_manage_content_ads = True
        ad_group_source.save(self.request)

        content_ad_sources = api.add_content_ad_sources(ad_group_source)

        expected = [
            models.ContentAdSource.objects.create(
                source_id=5,
                content_ad_id=1,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.ACTIVE
            ),
            models.ContentAdSource.objects.create(
                source_id=5,
                content_ad_id=2,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.INACTIVE
            ),
            models.ContentAdSource.objects.create(
                source_id=5,
                content_ad_id=3,
                submission_status=constants.ContentAdSubmissionStatus.NOT_SUBMITTED,
                state=constants.ContentAdSourceState.INACTIVE
            )
        ]

        self.assertEqual(len(content_ad_sources), 3)
        content_ad_sources.sort(key=lambda x: x.content_ad_id)

        for content_ad_source, expected_object in zip(content_ad_sources, expected):
            self.assertEqual(content_ad_source.source_id, expected_object.source_id)
            self.assertEqual(content_ad_source.content_ad_id, expected_object.content_ad_id)
            self.assertEqual(content_ad_source.submission_status, expected_object.submission_status)
            self.assertEqual(content_ad_source.state, expected_object.state)

    def test_ad_content_ad_sources_not_supported(self):
        ad_group_source = models.AdGroupSource(
            source_id=4,
            ad_group_id=1,
        )
        ad_group_source.save(self.request)

        content_ad_sources = api.add_content_ad_sources(ad_group_source)

        self.assertEqual(content_ad_sources, [])


class UpdateAdGroupSourceState(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)

    def test_should_update_if_changed(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

    def test_should_not_update_if_unchanged(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': latest_state.state,
            'cpc_cc': int(latest_state.cpc_cc * 10000),
            'daily_budget_cc': int(latest_state.daily_budget_cc * 10000)
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(new_latest_state.id, latest_state.id)

    def test_should_update_if_no_state_yet(self):
        self.assertTrue(
            models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        # use raw sql to bypass model restrictions
        q = 'DELETE FROM dash_adgroupsourcestate WHERE ad_group_source_id=%s'
        connection.cursor().execute(q, [self.ad_group_source.id])

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

        self.assertEqual(
            models.AdGroupSourceState.objects.filter(ad_group_source=self.ad_group_source).count(),
            1
        )

    def test_should_update_if_latest_settings(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': 500,
            'daily_budget_cc': 10000
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(float(new_latest_state.cpc_cc), 0.05)
        self.assertEqual(float(new_latest_state.daily_budget_cc), 1.0)

    def test_should_disregard_null_and_unspecified_fields(self):
        latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        conf = {
            'state': 2,
            'cpc_cc': None,
        }

        api.update_ad_group_source_state(self.ad_group_source, conf)

        new_latest_state = models.AdGroupSourceState.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_state.id, latest_state.id)
        self.assertEqual(new_latest_state.state, conf['state'])
        self.assertEqual(new_latest_state.cpc_cc, latest_state.cpc_cc)
        self.assertEqual(new_latest_state.daily_budget_cc, latest_state.daily_budget_cc)


class PublisherCallbackTest(TestCase):
    fixtures = ['test_api.yaml']

    def test_update_publisher_blacklist(self):

        ad_group_source = models.AdGroupSource.objects.get(id=1)

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [
                {
                    'domain': 'zemanta.com',
                    'exchange': 'adiant',
                    'source_id': 7
                },
                {
                    'domain': 'test1.com',
                    'exchange': 'sharethrough',
                    'source_id': 9
                }
            ]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(2, allblacklist.count())

        first_blacklist = allblacklist[0]
        self.assertEqual(ad_group_source.ad_group.id, first_blacklist.ad_group.id)
        self.assertEqual('zemanta.com', first_blacklist.name)
        self.assertEqual('b1_adiant', first_blacklist.source.tracking_slug)
        self.assertEqual(dash.constants.PublisherStatus.BLACKLISTED, first_blacklist.status)

        second_blacklist = allblacklist[1]
        self.assertEqual(ad_group_source.ad_group.id, second_blacklist.ad_group.id)
        self.assertEqual('b1_sharethrough', second_blacklist.source.tracking_slug)
        self.assertEqual(dash.constants.PublisherStatus.BLACKLISTED, second_blacklist.status)

    def test_update_outbrain_publisher_blacklist(self):
        # ad_group_source = models.AdGroupSource.objects.get(id=1)
        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ACCOUNT,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [
                {
                    'domain': 'Awesome publisher',
                    'exchange': 'adiant',
                    'external_id': '12345',
                    'source_id': 3
                },
                {
                    'domain': 'Happy little publisher',
                    'exchange': 'outbrain',
                    'external_id': '67890',
                    'source_id': 3
                }
            ]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(2, allblacklist.count())

        first_blacklist = allblacklist[0]
        self.assertEqual(u'Awesome publisher', first_blacklist.name)
        self.assertEqual('outbrain', first_blacklist.source.tracking_slug)
        self.assertEqual('12345', first_blacklist.external_id)
        self.assertEqual(dash.constants.PublisherStatus.BLACKLISTED, first_blacklist.status)

        second_blacklist = allblacklist[1]
        self.assertEqual(u'Happy little publisher', second_blacklist.name)
        self.assertEqual('outbrain', second_blacklist.source.tracking_slug)
        self.assertEqual('67890', second_blacklist.external_id)
        self.assertEqual(dash.constants.PublisherStatus.BLACKLISTED, second_blacklist.status)

    def test_hiearchy_publisher_blacklist(self):
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        sharethrough = models.Source.objects.get(tracking_slug='b1_sharethrough')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            ad_group=ad_group,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        models.PublisherBlacklist.objects.create(
            name='test1.com',
            ad_group=ad_group,
            source=sharethrough,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.ENABLED,
            'publishers': [
                {
                    'domain': 'zemanta.com',
                    'exchange': 'adiant',
                    'source_id': 7,
                },
                {
                    'domain': 'test1.com',
                    'exchange': 'sharethrough',
                    'source_id': 9,
                }
            ]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(0, allblacklist.count())

    def test_hiearchy_publisher_blacklist_wo_delete(self):
        # if we get a request to blacklist per adgroup source
        # and we already have a blacklist per campaign source,
        # account source or globally nothing happens
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        sharethrough = models.Source.objects.get(tracking_slug='b1_sharethrough')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            campaign=ad_group.campaign,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        models.PublisherBlacklist.objects.create(
            name='test1.com',
            campaign=ad_group.campaign,
            source=sharethrough,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.ENABLED,
            'publishers': [
                {
                    'domain': 'zemanta.com',
                    'exchange': 'adiant',
                    'source_id': 7,
                },
                {
                    'domain': 'test1.com',
                    'exchange': 'sharethrough',
                    'source_id': 9,
                }
            ]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(2, allblacklist.count())

        self.assertTrue(all([blacklist.campaign is not None
                             for blacklist in allblacklist]))

    def test_hiearchy_publisher_blacklist_plus_one(self):
        # blacklisting on higher level overrides lower level blacklist
        # adgroup < campaign < account < global
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            ad_group=ad_group,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        args = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ADGROUP,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            }]
        }

        api.update_publisher_blacklist_state(args)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNotNone(allblacklist[0].ad_group)

        args1 = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.CAMPAIGN,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            }]
        }

        api.update_publisher_blacklist_state(args1)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNone(allblacklist[0].ad_group)
        self.assertIsNotNone(allblacklist[0].campaign)

        args2 = {
            'key': [1],
            'level': dash.constants.PublisherBlacklistLevel.ACCOUNT,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com',
                'exchange': 'adiant',
                'source_id': 7
            }]
        }

        api.update_publisher_blacklist_state(args2)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNone(allblacklist[0].ad_group)
        self.assertIsNone(allblacklist[0].campaign)
        self.assertIsNotNone(allblacklist[0].account)

        args3 = {
            'key': None,
            'level': dash.constants.PublisherBlacklistLevel.GLOBAL,
            'state': dash.constants.PublisherStatus.BLACKLISTED,
            'publishers': [{
                'domain': 'zemanta.com'
            }]
        }

        api.update_publisher_blacklist_state(args3)
        allblacklist = dash.models.PublisherBlacklist.objects.all()
        self.assertEqual(1, allblacklist.count())
        self.assertIsNone(allblacklist[0].ad_group)
        self.assertIsNone(allblacklist[0].campaign)
        self.assertIsNone(allblacklist[0].account)
        self.assertTrue(allblacklist[0].everywhere)
        self.assertIsNone(allblacklist[0].source)

    def test_refresh_publisher_blacklist_rtb(self):
        # blacklisting on higher level overrides lower level blacklist
        # adgroup < campaign < account < global
        ad_group = models.AdGroup.objects.get(pk=1)
        adiant = models.Source.objects.get(tracking_slug='b1_adiant')
        models.PublisherBlacklist.objects.create(
            name='zemanta.com',
            campaign=ad_group.campaign,
            source=adiant,
            status=dash.constants.PublisherStatus.BLACKLISTED
        )

        adgs = dash.models.AdGroupSource.objects.filter(
            ad_group=ad_group,
            source=adiant
        ).first()
        api.refresh_publisher_blacklist(adgs, None)


class SetAdGroupSourceSettingsTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)
        self.ad_group_settings = \
            models.AdGroupSettings.objects \
                                  .filter(ad_group=self.ad_group_source.ad_group) \
                                  .latest('created_dt')
        assert self.ad_group_settings.state == 2

        patcher = mock.patch('dash.api.k1_helper')
        self.k1_helper_mock = patcher.start()
        self.addCleanup(patcher.stop)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_no_settings_yet(self, mock_send_mail):
        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )
        # delete all ad_group_source_settings - use raw sql to bypass model restrictions
        q = 'DELETE FROM dash_adgroupsourcesettings'
        connection.cursor().execute(q, [])

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'state': 1},
            request
        )

        self.assertTrue(
            models.AdGroupSourceSettings.objects.filter(ad_group_source=self.ad_group_source).count() > 0
        )

        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.state, 1)
        self.assertTrue(latest_settings.cpc_cc is None)
        self.assertTrue(latest_settings.daily_budget_cc is None)

        mock_send_mail.assert_called_with(
            self.ad_group_source.ad_group, request, 'AdsNative State set to Enabled')

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_changed(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'cpc_cc': decimal.Decimal(2)},
            request
        )

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)

        self.assertEqual(request.user, new_latest_settings.created_by)
        self.assertIsNone(new_latest_settings.system_user)

        mock_send_mail.assert_called_with(
            self.ad_group_source.ad_group, request, 'AdsNative Max CPC bid set from $0.120 to $2.000')

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_request_none(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = None

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'cpc_cc': decimal.Decimal(0.1)},
            request,
            system_user=constants.SystemUserType.AUTOPILOT
        )

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 0.1)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertIsNone(new_latest_settings.created_by)
        self.assertEqual(constants.SystemUserType.AUTOPILOT, new_latest_settings.system_user)

        self.assertFalse(mock_send_mail.called)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_write_if_changed_no_action(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()
        request.user = User.objects.create_user('test@example.com')

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'cpc_cc': decimal.Decimal(2)},
            request
        )

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)

        mock_send_mail.assert_called_with(self.ad_group_source.ad_group, request,
                                          'AdsNative Max CPC bid set from $0.120 to $2.000')

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_should_not_write_if_unchanged(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        request = HttpRequest()

        api.set_ad_group_source_settings(
            self.ad_group_source,
            {'daily_budget_cc': decimal.Decimal(50)},
            request)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertEqual(latest_settings.id, new_latest_settings.id)
        self.assertEqual(latest_settings.state, new_latest_settings.state)
        self.assertEqual(latest_settings.cpc_cc, new_latest_settings.cpc_cc)
        self.assertEqual(latest_settings.daily_budget_cc, new_latest_settings.daily_budget_cc)

        self.assertFalse(mock_send_mail.called)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_set_system_user_valid(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        api.set_ad_group_source_settings(
            self.ad_group_source, {'cpc_cc': decimal.Decimal(2)}, None, landing_mode=True)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertTrue(True, new_latest_settings.landing_mode)

    @mock.patch('utils.email_helper.send_ad_group_notification_email')
    def test_set_system_user_not_valid(self, mock_send_mail):
        latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        api.set_ad_group_source_settings(
            self.ad_group_source, {'cpc_cc': decimal.Decimal(2)}, None, 1028)

        new_latest_settings = models.AdGroupSourceSettings.objects \
            .filter(ad_group_source=self.ad_group_source) \
            .latest('created_dt')

        self.assertNotEqual(new_latest_settings.id, latest_settings.id)
        self.assertEqual(float(new_latest_settings.cpc_cc), 2)
        self.assertNotEqual(new_latest_settings.cpc_cc, latest_settings.cpc_cc)
        self.assertEqual(new_latest_settings.state, latest_settings.state)
        self.assertEqual(new_latest_settings.daily_budget_cc, latest_settings.daily_budget_cc)
        self.assertEqual(new_latest_settings.landing_mode, latest_settings.landing_mode)


class AdGroupSettingsOrderTest(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.ad_group_source = models.AdGroupSource.objects.get(id=1)

    def test_settings_changes(self):

        set1 = models.AdGroupSettings(
            created_dt=datetime.date.today(),

            state=1,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.1'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        set2 = models.AdGroupSettings(
            created_dt=datetime.date.today() - datetime.timedelta(days=1),

            state=2,
            start_date=datetime.date.today(),
            end_date=datetime.date.today(),
            cpc_cc=decimal.Decimal('0.2'),
            daily_budget_cc=decimal.Decimal('50.'),
        )

        self.assertEqual(set1.get_setting_changes(set1), {})

        self.assertEqual(
            set1.get_setting_changes(set2),
            {'state': 2, 'cpc_cc': decimal.Decimal('0.2')},
        )


class UpdateContentAdSubmissionStatus(TestCase):

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

    def test_ad_group_submission_type(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 7

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.APPROVED
        ad_group_source.source_content_ad_id = '987654321'
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source1 = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.PENDING,
            source_content_ad_id='1234567890',
        )

        content_ad_source2 = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.REJECTED,
            source_content_ad_id=None,
        )

        api.update_content_ads_submission_status(ad_group_source, request=None)

        content_ad_source1 = models.ContentAdSource.objects.get(id=content_ad_source1.id)
        self.assertEqual(content_ad_source1.submission_status, constants.ContentAdSubmissionStatus.APPROVED)
        self.assertEqual(content_ad_source1.source_content_ad_id, '987654321')

        content_ad_source2 = models.ContentAdSource.objects.get(id=content_ad_source2.id)
        self.assertEqual(content_ad_source2.submission_status, constants.ContentAdSubmissionStatus.REJECTED)
        self.assertEqual(content_ad_source2.source_content_ad_id, None)

    def test_default_submission_type(self):
        batch = models.UploadBatch.objects.create(name='test', status=constants.UploadBatchStatus.DONE)
        ad_group_id = 1
        source_id = 1

        ad_group_source = models.AdGroupSource.objects.get(
            ad_group_id=ad_group_id,
            source_id=source_id,
        )

        ad_group_source.submission_status = constants.ContentAdSubmissionStatus.REJECTED
        ad_group_source.source_content_ad_id = None
        ad_group_source.save(None)

        content_ad = models.ContentAd.objects.create(
            url='test.com',
            title='test',
            ad_group=ad_group_source.ad_group,
            batch=batch
        )

        content_ad_source = models.ContentAdSource.objects.create(
            content_ad=content_ad,
            source=ad_group_source.source,
            submission_status=constants.ContentAdSubmissionStatus.APPROVED,
            source_content_ad_id='1234567890',
        )

        api.update_content_ads_submission_status(ad_group_source, request=None)

        content_ad_source = models.ContentAdSource.objects.get(id=content_ad_source.id)
        self.assertEqual(content_ad_source.submission_status, constants.ContentAdSubmissionStatus.APPROVED)
        self.assertEqual(content_ad_source.source_content_ad_id, '1234567890')
