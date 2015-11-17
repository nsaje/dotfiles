import datetime
import json
import mock

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

import actionlog.models
import actionlog.zwei_actions
import dash.models

from utils import test_helper


class SendTestCase(TestCase):

    fixtures = ['test_api.yaml']

    def setUp(self):
        self.action_log = actionlog.models.ActionLog.objects.create(
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
        actionlog.zwei_actions.send(self.action_log)
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
        actionlog.zwei_actions.send([self.action_log])
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
        self.action_log = actionlog.models.ActionLog.objects.create(
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

    def test_resend_not_failed_actions(self):
        with self.assertRaises(AssertionError):
            actionlog.zwei_actions.resend(self.action_log)
        with self.assertRaises(AssertionError):
            actionlog.zwei_actions.resend([self.action_log])
