import datetime
import mock

from django.test import TestCase

import dash.constants
from integrations.bizwire.internal import actions
from utils.test_helper import ListMatcher


class CheckMidnightTestCase(TestCase):

    @mock.patch('utils.dates_helper.utc_now')
    @mock.patch('dash.api.update_content_ads_state')
    def test_check_midnight_and_stop_ads_pst_time(self, mock_update_content_ads_state, mock_utc_now):
        mock_utc_now.return_value = datetime.datetime(2016, 6, 1, 6)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 6, 1, 8)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 6, 1, 7)
        actions.check_midnight_and_stop_ads()
        self.assertEqual(
            mock.call(ListMatcher([]), dash.constants.ContentAdSourceState.INACTIVE, None),
            mock_update_content_ads_state.call_args)

    @mock.patch('utils.dates_helper.utc_now')
    @mock.patch('dash.api.update_content_ads_state')
    def test_check_midnight_and_stop_ads_pdt_time(self, mock_update_content_ads_state, mock_utc_now):
        mock_utc_now.return_value = datetime.datetime(2016, 12, 1, 7)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 12, 1, 9)
        actions.check_midnight_and_stop_ads()
        self.assertFalse(mock_update_content_ads_state.called)

        mock_utc_now.return_value = datetime.datetime(2016, 12, 1, 8)
        actions.check_midnight_and_stop_ads()
        self.assertEqual(
            mock.call(ListMatcher([]), dash.constants.ContentAdSourceState.INACTIVE, None),
            mock_update_content_ads_state.call_args)
