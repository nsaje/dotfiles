import json
from datetime import date

from django.test import TestCase

from googleapiclient.discovery import build
from googleapiclient.http import HttpMockSequence

from convapi import ga_api
from convapi.ga_api import GAApiReport
from dash.models import GAAnalyticsAccount


class TestGAApiReport(TestCase):
    def test_download(self):
        http = HttpMockSequence([
            ({'status': '200'}, self._profile_list_response_mock()),
            ({'status': '200'}, self._postclick_response_mock()),
            ({'status': '200'}, self._goals_response_mock()),
            ({'status': '200'}, self._conversion_goals_response_mock()),
        ])
        api_key = 'dummy_key'
        mocked_ga_service = build(ga_api.GA_API_NAME, ga_api.GA_API_VERSION, http=http, developerKey=api_key)
        start_date = date(2015, 12, 7)
        ga_reports = GAApiReport(mocked_ga_service, start_date)
        ga_account = GAAnalyticsAccount()
        ga_account.ga_account_id = '1234567'
        ga_account.ga_web_property_id = 'UA-1234567-12'
        ga_reports.download(ga_account)
        self.assertTrue(len(ga_reports.entries) == 1)

    def _profile_list_response_mock(self):
        return json.dumps(
                {'username': 'account-1@zemanta-api.iam.gserviceaccount.com', 'kind': 'analytics#profiles', 'items': [
                    {'kind': 'analytics#profile', 'name': 'plugin-magazine.com', 'created': '2015-03-27T10:28:40.379Z',
                     'botFilteringEnabled': True, 'updated': '2015-06-01T11:15:05.212Z',
                     'websiteUrl': 'http://plugin-magazine.com', 'currency': 'EUR', 'internalWebPropertyId': '95912016',
                     'childLink': {
                         'href': 'https://www.googleapis.com/analytics/v3/management/accounts/2175716/webproperties/UA-2175716-35/profiles/100021248/goals',
                         'type': 'analytics#goals'}, 'eCommerceTracking': False, 'webPropertyId': 'UA-2175716-35',
                     'timezone': 'Europe/Ljubljana', 'parentLink': {
                        'href': 'https://www.googleapis.com/analytics/v3/management/accounts/2175716/webproperties/UA-2175716-35',
                        'type': 'analytics#webproperty'}, 'permissions': {'effective': ['READ_AND_ANALYZE']},
                     'type': 'WEB',
                     'id': '100021248',
                     'selfLink': 'https://www.googleapis.com/analytics/v3/management/accounts/2175716/webproperties/UA-2175716-35/profiles/100021248',
                     'accountId': '2175716'}], 'itemsPerPage': 1000, 'startIndex': 1, 'totalResults': 1})

    def _postclick_response_mock(self):
        return json.dumps({'kind': 'analytics#gaData', 'rows': [
            ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42001&_z1_msid=b1_pubmatic&_z1_disga=zemgagood', 'mobile',
             '1', '0', '100.0', '1', '0.0']], 'containsSampledData': False,
                           'profileInfo': {'webPropertyId': 'UA-2175716-35', 'internalWebPropertyId': '95912016',
                                           'tableId': 'ga:100021248', 'profileId': '100021248',
                                           'profileName': 'plugin-magazine.com', 'accountId': '2175716'},
                           'itemsPerPage': 1000,
                           'totalsForAllResults': {'ga:timeonsite': '0.0', 'ga:pageviews': '1',
                                                   'ga:bounceRate': '100.0',
                                                   'ga:sessions': '1', 'ga:newUsers': '0'},
                           'columnHeaders': [
                               {'dataType': 'STRING', 'columnType': 'DIMENSION', 'name': 'ga:landingPagePath'},
                               {'dataType': 'STRING', 'columnType': 'DIMENSION', 'name': 'ga:deviceCategory'},
                               {'dataType': 'INTEGER', 'columnType': 'METRIC', 'name': 'ga:sessions'},
                               {'dataType': 'INTEGER', 'columnType': 'METRIC', 'name': 'ga:newUsers'},
                               {'dataType': 'PERCENT', 'columnType': 'METRIC', 'name': 'ga:bounceRate'},
                               {'dataType': 'INTEGER', 'columnType': 'METRIC', 'name': 'ga:pageviews'},
                               {'dataType': 'TIME', 'columnType': 'METRIC', 'name': 'ga:timeonsite'}],
                           'query': {'max-results': 1000, 'dimensions': 'ga:landingPagePath,ga:deviceCategory',
                                     'start-date': '2015-12-07', 'start-index': 1, 'ids': 'ga:100021248',
                                     'metrics': ['ga:sessions', 'ga:newUsers', 'ga:bounceRate', 'ga:pageviews',
                                                 'ga:timeonsite'], 'filters': 'ga:landingPagePath=@_z1_',
                                     'end-date': '2015-12-07'}, 'totalResults': 1,
                           'id': 'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:100021248&dimensions=ga:landingPagePath,ga:deviceCategory&metrics=ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite&filters=ga:landingPagePath%3D@_z1_&start-date=2015-12-07&end-date=2015-12-07&start-index=1',
                           'selfLink': 'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:100021248&dimensions=ga:landingPagePath,ga:deviceCategory&metrics=ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite&filters=ga:landingPagePath%3D@_z1_&start-date=2015-12-07&end-date=2015-12-07&start-index=1'})

    def _goals_response_mock(self):
        return json.dumps({'username': 'account-1@zemanta-api.iam.gserviceaccount.com', 'kind': 'analytics#goals',
                           'items': [{'kind': 'analytics#goal', 'name': 'E-zin subscription',
                                      'created': '2015-09-07T13:39:36.339Z', 'updated': '2015-09-07T13:39:36.339Z',
                                      'value': 0.0, 'internalWebPropertyId': '95912016', 'eventDetails': {
                                   'eventConditions': [
                                       {'expression': 'E-zin', 'matchType': 'EXACT', 'type': 'CATEGORY'},
                                       {'expression': 'prijava', 'matchType': 'EXACT', 'type': 'ACTION'}],
                                   'useEventValue': True}, 'webPropertyId': 'UA-2175716-35', 'active': True,
                                      'profileId': '100021248', 'parentLink': {
                                   'href': 'https://www.googleapis.com/analytics/v3/management/accounts/2175716/webproperties/UA-2175716-35/profiles/100021248',
                                   'type': 'analytics#profile'}, 'type': 'EVENT', 'id': '1',
                                      'selfLink': 'https://www.googleapis.com/analytics/v3/management/accounts/2175716/webproperties/UA-2175716-35/profiles/100021248/goals/1',
                                      'accountId': '2175716'}], 'itemsPerPage': 1000, 'startIndex': 1,
                           'totalResults': 1})

    def _conversion_goals_response_mock(self):
        return json.dumps({'kind': 'analytics#gaData', 'rows': [
            ['/driving/voltbolt/?_z1_adgid=830&_z1_caid=42001&_z1_msid=b1_pubmatic&_z1_disga=zemgagood', 'mobile',
             '0.0', '0']], 'containsSampledData': False,
                           'profileInfo': {'webPropertyId': 'UA-2175716-35', 'internalWebPropertyId': '95912016',
                                           'tableId': 'ga:100021248', 'profileId': '100021248',
                                           'profileName': 'plugin-magazine.com', 'accountId': '2175716'},
                           'itemsPerPage': 1000,
                           'totalsForAllResults': {'ga:goal1Completions': '0', 'ga:goal1ConversionRate': '0.0'},
                           'columnHeaders': [
                               {'dataType': 'STRING', 'columnType': 'DIMENSION', 'name': 'ga:landingPagePath'},
                               {'dataType': 'STRING', 'columnType': 'DIMENSION', 'name': 'ga:deviceCategory'},
                               {'dataType': 'PERCENT', 'columnType': 'METRIC', 'name': 'ga:goal1ConversionRate'},
                               {'dataType': 'INTEGER', 'columnType': 'METRIC', 'name': 'ga:goal1Completions'}],
                           'query': {'max-results': 1000, 'dimensions': 'ga:landingPagePath,ga:deviceCategory',
                                     'start-date': '2015-12-07', 'start-index': 1, 'ids': 'ga:100021248',
                                     'metrics': ['ga:goal1ConversionRate', 'ga:goal1Completions'],
                                     'filters': 'ga:landingPagePath=@_z1_', 'end-date': '2015-12-07'},
                           'totalResults': 1,
                           'id': 'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:100021248&dimensions=ga:landingPagePath,ga:deviceCategory&metrics=ga:goal1ConversionRate,ga:goal1Completions&filters=ga:landingPagePath%3D@_z1_&start-date=2015-12-07&end-date=2015-12-07&start-index=1',
                           'selfLink': 'https://www.googleapis.com/analytics/v3/data/ga?ids=ga:100021248&dimensions=ga:landingPagePath,ga:deviceCategory&metrics=ga:goal1ConversionRate,ga:goal1Completions&filters=ga:landingPagePath%3D@_z1_&start-date=2015-12-07&end-date=2015-12-07&start-index=1'})
