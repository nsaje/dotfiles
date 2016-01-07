import datetime
import mock
from django import test
from django.test import TestCase
from django.forms.models import model_to_dict

from convapi.ga_api import GAApiReport
from convapi.management.commands.update_content_ad_stats_from_ga_api import Command
from reports.models import ContentAdPostclickStats, ContentAdGoalConversionStats
from server import settings


class CommandUpdateContentAdStatsFromGAApiTest(TestCase):
    fixtures = ['test_ga_aggregation.yaml']

    @mock.patch('convapi.ga_api.get_ga_service')
    @mock.patch.object(GAApiReport, '_get_ga_profiles')
    @mock.patch.object(GAApiReport, '_get_ga_goals')
    @mock.patch.object(GAApiReport, '_download_stats_from_ga')
    @mock.patch('utils.sqs_helper.write_message_json')
    def test_handle(self, sqs_write_message_mock, _download_stats_from_ga_mock, _get_ga_goals_mock,
                    _get_ga_profiles_mock, ga_service_mock):
        _get_ga_profiles_mock.return_value = self._create_ga_profiles_mock()
        _get_ga_goals_mock.return_value = self._create_ga_goals_mock()
        _download_stats_from_ga_mock.side_effect = self._download_stats_from_ga_side_effect
        ga_service_mock.return_value = None
        command = Command()
        command.handle(ga_date='2015-12-07')
        postclick_stats = ContentAdPostclickStats.objects.all()
        self.assertTrue(postclick_stats.count() == 1)
        self.assertEqual(
                {'content_ad': 1, 'pageviews': 1, 'new_visits': 1, 'total_time_on_site': 10, 'bounced_visits': 2,
                 'visits': 2, 'source': 4, 'date': datetime.date(2015, 12, 7), u'id': 1},
                model_to_dict(postclick_stats.first()))
        goal_conversion_stats = ContentAdGoalConversionStats.objects.all()
        self.assertTrue(goal_conversion_stats.count() == 1)
        self.assertEqual({'conversions': 2, 'content_ad': 1, 'goal_type': u'ga', 'source': 4,
                          'date': datetime.datetime(2015, 12, 7, 0, 0), u'id': 1},
                         model_to_dict(goal_conversion_stats.first()))
        sqs_write_message_mock.assert_called_once_with(settings.CAMPAIGN_CHANGE_QUEUE,
                                                       {'date': '2015-12-07', 'campaign_id': 1})

    def _create_ga_profiles_mock(self):
        return {'items': [{'id': '100021248', 'accountId': '2175716', 'webPropertyId': 'UA-2175716-35'}],
                'itemsPerPage': 1000, 'startIndex': 1, 'totalResults': 1}

    def _create_ga_goals_mock(self):
        return {'items': [{'id': '1', 'name': 'E-zin subscription', 'accountId': '2175716', 'value': 0.0}],
                'itemsPerPage': 1000, 'startIndex': 1, 'totalResults': 1}

    def _download_stats_from_ga_side_effect(self, start_date, profile_id, metrics, start_index):
        if metrics == 'ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite':
            return {'rows': [
                ['/driving/voltbolt/?_z1_adgid=1&_z1_caid=1&_z1_msid=adblade&_z1_disga=zemgagood',
                 '(not set)', '2', '1', '100.0', '1', '10.0']], 'itemsPerPage': 1000, 'totalResults': 1}
        elif metrics == 'ga:goal1Completions':
            return {'rows': [
                ['/driving/voltbolt/?_z1_adgid=1&_z1_caid=1&_z1_msid=adblade&_z1_disga=zemgagood',
                 '(not set)', '2']], 'itemsPerPage': 1000, 'totalResults': 1}
        else:
            raise Exception('Undefined GA metrics: ' + metrics)
