import mock
from django.test import TestCase, override_settings

from utils import statsd_helper


@statsd_helper.statsd_timer('test')
def test_function():
    return 100


@statsd_helper.statsd_timer('test', 'custom_name')
def test_function2():
    return 200


@override_settings(HOSTNAME='testhost')
class StatsdHelperTestCase(TestCase):
    fake_time_call_count = 1
    mock_called = False

    @mock.patch('utils.statsd_helper.statsd.timing')
    @mock.patch('utils.statsd_helper.time')
    def test_statsd_timer(self, time_mock, statsd_timing_mock):
        def fake_time():
            if self.fake_time_call_count == 1:
                self.fake_time_call_count += 1
                return 1402523052.417958
            elif self.fake_time_call_count == 2:
                return 1402523052.818079

        time_mock.time.side_effect = fake_time

        def statsd_timing(name, time_ms):
            self.assertEqual(name, 'one-testhost.test.test_function')
            self.assertEqual(time_ms, 400)
            self.mock_called = True

        statsd_timing_mock.side_effect = statsd_timing

        self.assertFalse(statsd_timing_mock.called)

        result = test_function()
        self.assertEqual(result, 100)
        self.assertTrue(self.mock_called)

    @mock.patch('utils.statsd_helper.statsd.timing')
    @mock.patch('utils.statsd_helper.time')
    def test_statsd_timer_custom_name(self, time_mock, statsd_timing_mock):
        def fake_time():
            if self.fake_time_call_count == 1:
                self.fake_time_call_count += 1
                return 1402523052.417958
            elif self.fake_time_call_count == 2:
                return 1402523052.818079

        time_mock.time.side_effect = fake_time

        def statsd_timing(name, time_ms):
            self.assertEqual(name, 'one-testhost.test.custom_name')
            self.assertEqual(time_ms, 400)
            self.mock_called = True

        statsd_timing_mock.side_effect = statsd_timing

        self.assertFalse(statsd_timing_mock.called)

        result = test_function2()
        self.assertEqual(result, 200)
        self.assertTrue(self.mock_called)

    @mock.patch('utils.statsd_helper.statsd.incr')
    def test_statsd_incr(self, statsd_incr_mock):
        def fake_statsd_incr(name, count=1):
            self.assertEqual(name, 'one-testhost.test.metric')
            self.mock_called = True

        statsd_incr_mock.side_effect = fake_statsd_incr

        statsd_helper.statsd_incr('test.metric')
        self.assertTrue(self.mock_called)

    @mock.patch('utils.statsd_helper.statsd.gauge')
    def test_statsd_gauge(self, statsd_gauge_mock):
        def fake_statsd_gauge(name, value):
            self.assertEqual(name, 'one-testhost.test.metric')
            self.mock_called = True
            self.mock_value = value

        statsd_gauge_mock.side_effect = fake_statsd_gauge

        mock_value = 5
        statsd_helper.statsd_gauge('test.metric', mock_value)
        self.assertTrue(self.mock_called)
        self.assertTrue(self.mock_value, mock_value)

    def test_get_source(self):
        self.assertEqual(statsd_helper.get_source(), 'one-testhost')

    @override_settings(HOSTNAME='tes.th.ost')
    def test_get_source_with_periods(self):
        self.assertEqual(statsd_helper.get_source(), 'one-testhost')
