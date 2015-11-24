import datetime
import json
import mock

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

from actionlog import models
from actionlog import constants
from actionlog import zwei_actions
import dash.models

from utils import test_helper


class SendTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.action_log = models.ActionLog.objects.create(
            action='get_reports',
            state=1,
            action_type=1,
            ad_group_source=dash.models.AdGroupSource.objects.get(id=1),
            expiration_dt=datetime.datetime(2015, 7, 1, 12),
            payload={
                'action': 'get_reports',
                'source': 'outbrain',
                'expiration_dt': datetime.datetime(2015, 7, 1, 12),
                'args': {
                    'source_campaign_key': '1234567890',
                    'date': '2015-07-01',
                },
                'callback_url': 'http://localhost/'
            }
        )

        patcher_urlopen = mock.patch('utils.request_signer._secure_opener.open')
        self.addCleanup(patcher_urlopen.stop)

        self.mock_urlopen = patcher_urlopen.start()
        test_helper.prepare_mock_urlopen(self.mock_urlopen)

    @override_settings(CREDENTIALS_ENCRYPTION_KEY='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    def test_send(self):
        zwei_actions.send(self.action_log)
        self.assertEqual(1, self.mock_urlopen.call_count)
        self.assertEqual(settings.ZWEI_API_TASKS_URL, self.mock_urlopen.call_args[0][0].get_full_url())
        self.assertEqual(
            [
                {
                    "args": {
                        "date": "2015-07-01",
                        "source_campaign_key": "1234567890"
                    },
                    "source": "outbrain",
                    "action": "get_reports",
                    "credentials": self.action_log.ad_group_source.source_credentials.decrypt(),
                    "callback_url": "http://localhost/",
                    "expiration_dt": "2015-07-01T12:00:00"
                }
            ],
            json.loads(self.mock_urlopen.call_args[0][0].data)
        )

    @override_settings(CREDENTIALS_ENCRYPTION_KEY='aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
    def test_send_batch(self):
        zwei_actions.send([self.action_log])
        self.assertEqual(1, self.mock_urlopen.call_count)
        self.assertEqual(settings.ZWEI_API_TASKS_URL, self.mock_urlopen.call_args[0][0].get_full_url())
        self.assertEqual(
            [
                {
                    "args": {
                        "date": "2015-07-01",
                        "source_campaign_key": "1234567890"
                    },
                    "source": "outbrain",
                    "action": "get_reports",
                    "credentials": self.action_log.ad_group_source.source_credentials.decrypt(),
                    "callback_url": "http://localhost/",
                    "expiration_dt": "2015-07-01T12:00:00"
                }
            ],
            json.loads(self.mock_urlopen.call_args[0][0].data)
        )


class ResendTestCase(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.action_log = models.ActionLog.objects.create(
            action=constants.Action.FETCH_REPORTS,
            state=constants.ActionState.SUCCESS,
            action_type=constants.ActionType.AUTOMATIC,
            ad_group_source=dash.models.AdGroupSource.objects.get(id=1),
            expiration_dt=datetime.datetime(2015, 7, 1, 12),
            payload={
                'action': 'get_reports',
                'source': 'outbrain',
                'expiration_dt': datetime.datetime(2015, 7, 1, 12),
                'args': {
                    'source_campaign_key': '1234567890',
                    'date': '2015-07-01',
                },
                'callback_url': 'http://localhost/'
            }
        )

    def test_resend_not_failed_actions(self):
        self.assertNotEqual(self.action_log.state, constants.ActionState.FAILED)

        with self.assertRaisesMessage(AssertionError, 'Not all selected actions have failed!'):
            zwei_actions.resend(self.action_log)
        with self.assertRaisesMessage(AssertionError, 'Not all selected actions have failed!'):
            zwei_actions.resend([self.action_log])

    def test_insert_content_ad_resend(self):
        action = models.ActionLog.objects.create(
            action=constants.Action.INSERT_CONTENT_AD,
            state=constants.ActionState.FAILED,
            action_type=constants.ActionType.AUTOMATIC,
            payload={
                'action': 'insert_content_ad',
                'args': {
                    'content_ad': {
                        'ad_group_id': 912,
                        'brand_name': "Land",
                        'call_to_action': 'Read Mode',
                        'content_ad_id': 164835,
                        'description': 'Get These 15 Ice Cubes',
                        'display_url': 'www.example.com',
                        'image_hash': '34248853030713512388',
                        'image_height': 407,
                        'image_id': '20c47729-59fa-4664-1127-c821aef9b608',
                        'image_width': 610,
                        'redirect_id': 'u1ee1mzswsg0',
                        'source_content_ad_id': None,
                        'state': 1,
                        'submission_status': -1,
                        'title': "15 Ways to Make an Ice Cubes",
                        'tracker_urls': None,
                        'tracking_slug': 'b1_gumgum',
                        'url': 'http://example.com/15-ice-cubes'
                    },
                    'source_campaign_key': [912, 'gumgum', 9999999999]
                },
                'callback_url': 'https://one.zemanta.com/api/zwei_callback/130284406',
                'expiration_dt': '2015-11-20T19:37:55.200',
                'source': 'b1'
            }
        )

        zwei_actions.resend(action)

        action.refresh_from_db()
        self.assertTrue(action.payload['args']['content_ad']['check_already_inserted'])

    def test_update_content_ad_resend(self):
        action = models.ActionLog.objects.create(
            action=constants.Action.UPDATE_CONTENT_AD,
            state=constants.ActionState.FAILED,
            action_type=constants.ActionType.AUTOMATIC,
            payload={
                'action': 'update_content_ad',
                'args': {
                    'changes': {
                        'state': 2
                    },
                    'content_ad': {
                        'ad_group_id': 1238,
                        'brand_name': 'SomeBrand',
                        'call_to_action': 'Read More',
                        'content_ad_id': 134544,
                        'description': "When yo're shopping for description",
                        'display_url': 'example.com',
                        'image_hash': '252645375',
                        'image_height': 350,
                        'image_id': '31eebdef-asd2-491d-9854-44dc3ea7106c',
                        'image_width': 350,
                        'redirect_id': 'u1lajugissr4',
                        'source_content_ad_id': None,
                        'state': 2,
                        'submission_status': 2,
                        'title': 'This is a title',
                        'tracker_urls': None,
                        'tracking_slug': 'b1_mopub',
                        'url': 'https://somebrand.com/asd/?v=5&BDID=8830'
                    },
                    'source_campaign_key': [1238, 'mopub']
                },
                'callback_url': 'https://one.zemanta.com/api/zwei_callback/132033168',
                'expiration_dt': '2015-11-23T10:54:29.350',
                'source': 'b1'
            }
        )

        zwei_actions.resend(action)

        action.refresh_from_db()
        self.assertNotIn('check_already_inserted', action.payload['args']['content_ad'])

