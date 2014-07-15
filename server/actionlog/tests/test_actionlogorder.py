import datetime
import httplib
import mock

from django import test
from django.conf import settings

from actionlog import api, constants, models, refresh_orders
from dash import models as dashmodels
from utils.test_helper import MockDateTime


class ActionLogOrderApiTestCase(test.TestCase):

    fixtures = ['test_api.yaml', 'test_actionlog.yaml']

    def setUp(self):
        self.credentials_encription_key = settings.CREDENTIALS_ENCRYPTION_KEY
        settings.CREDENTIALS_ENCRYPTION_KEY = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'

    def tearDown(self):
        settings.CREDENTIALS_ENCRYPTION_KEY = self.credentials_encription_key

    @mock.patch('utils.request_signer._secure_opener.open')
    def test_init_fetch_all_order(self, mock_urlopen):
        mock_request = mock.Mock()
        mock_request.status_code = httplib.OK
        mock_urlopen.return_value = mock_request

        dates = [datetime.date.today()]
        api.init_fetch_all_order(dates)

        order = models.ActionLogOrder.objects.order_by('-created_dt').first()
        self.assertEqual(
            len(order.actionlog_set.filter(action=constants.Action.FETCH_REPORTS)),
            len(dashmodels.AdGroupNetwork.objects.all())
        )
        self.assertEqual(
            len(order.actionlog_set.filter(action=constants.Action.FETCH_REPORTS)),
            len(dashmodels.AdGroupNetwork.objects.all())
        )

        for action in order.actionlog_set.all():
            self.assertEqual(action.state, constants.ActionState.WAITING)
            self.assertIn(
                action.action,
                (constants.Action.FETCH_REPORTS, constants.Action.FETCH_CAMPAIGN_STATUS)
            )
            self.assertEqual(action.action_type, constants.ActionType.AUTOMATIC)

    def test_is_fetch_all_order_successful(self):
        successful_order = models.ActionLogOrder.objects.get(id=1)
        waiting_order = models.ActionLogOrder.objects.get(id=2)

        self.assertTrue(api._is_fetch_all_order_successful(successful_order))
        self.assertFalse(api._is_fetch_all_order_successful(waiting_order))

        action = successful_order.actionlog_set.first()
        action.state = constants.ActionState.FAILED
        action.save()

        self.assertFalse(api._is_fetch_all_order_successful(successful_order))

    def test_get_last_successful_fetch_all_order(self):
        last_successful_order = models.ActionLogOrder.objects.get(id=1)
        self.assertEqual(api.get_last_successful_fetch_all_order(), last_successful_order)

        action = last_successful_order.actionlog_set.first()
        action.state = constants.ActionState.FAILED
        action.save()

        self.assertIsNone(api.get_last_successful_fetch_all_order())

    @mock.patch('actionlog.api.datetime', MockDateTime)
    def test_is_fetch_all_data_recent(self):

        last_successful_order = api.get_last_successful_fetch_all_order()

        including_timedelta = datetime.timedelta(hours=api.NUM_RECENT_HOURS-1)
        api.datetime.utcnow = classmethod(lambda cls: last_successful_order.created_dt + including_timedelta)
        self.assertTrue(api.is_fetch_all_data_recent())

        excluding_timedelta = datetime.timedelta(hours=api.NUM_RECENT_HOURS+1)
        api.datetime.utcnow = classmethod(lambda cls: last_successful_order.created_dt + excluding_timedelta)
        self.assertFalse(api.is_fetch_all_data_recent())


class RefreshOrdersTestCase(test.TestCase):

    fixtures = ['test_api.yaml', 'test_actionlog.yaml']

    @mock.patch('actionlog.refresh_orders.datetime', MockDateTime)
    @mock.patch('utils.statsd_helper.statsd.gauge')
    def test_refresh_fetch_all_order_statsd_ping(self, statsd_gauge_mock):
        def fake_statsd_gauge(name, value):
            self.mock_gauge_called = True
            self.mock_gauge_value = value

        statsd_gauge_mock.side_effect = fake_statsd_gauge

        last_successful_order = api.get_last_successful_fetch_all_order()

        # make sure it can handle both hours in last day and in more days
        for hours_since in (2, 74):
            td = datetime.timedelta(hours=hours_since)
            refresh_orders.datetime.utcnow = classmethod(lambda cls: last_successful_order.created_dt + td)
            refresh_orders.refresh_fetch_all_orders()

            self.assertTrue(self.mock_gauge_called)
            self.assertEqual(self.mock_gauge_value, hours_since)
