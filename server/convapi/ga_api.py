import json
import logging
import re
import httplib2
import googleapiclient.discovery
from oauth2client.client import SignedJwtAssertionCredentials
from django.conf import settings
from convapi.parse_v2 import ReportRow, GAReport
from utils.list_helper import list_chunker

logger = logging.getLogger(__name__)

GA_API_NAME = 'analytics'
GA_API_VERSION = 'v3'
GA_SCOPE = ['https://www.googleapis.com/auth/analytics.readonly']

MAX_METRICS_PER_GA_REQUEST = 10
NUM_METRICS_PER_GOAL = 2


def get_ga_service():
    logger.debug('Getting Google Analytics service.')
    credentials = SignedJwtAssertionCredentials(
            settings.GA_CLIENT_EMAIL,
            settings.GA_PRIVATE_KEY,
            GA_SCOPE
    )
    http = credentials.authorize(httplib2.Http())
    # Build the GA service object.
    service = googleapiclient.discovery.build(GA_API_NAME, GA_API_VERSION, http=http)
    return service


class GAApiReportRow(ReportRow):
    def __init__(self, report_date, content_ad_id, source_param):
        ReportRow.__init__(self)
        self.report_date = report_date.isoformat()
        self.content_ad_id = content_ad_id
        self.source_param = source_param

        self.visits = 0
        self.new_visits = 0
        self.bounce_rate = 0.0
        self.pageviews = 0
        self.total_time_on_site = 0
        self.bounced_visits = 0

        self.goals = {}

    def set_postclick_stats(self, ga_row_list):
        self.raw_row = json.dumps(ga_row_list or {})
        self.visits = int(ga_row_list[2])
        self.new_visits = int(ga_row_list[3])
        self.bounce_rate = float(ga_row_list[4]) / 100.0
        self.pageviews = int(ga_row_list[5])
        self.total_time_on_site = int(float(ga_row_list[6]))
        self.bounced_visits = int(self.bounce_rate * self.visits)

    def set_conversion_goal_stats_with(self, goals):
        self.goals = goals

    def key(self):
        return self.report_date, self.content_ad_id, self.source_param

    def merge_postclick_stats_with(self, ga_report_row):
        self.visits += ga_report_row.visits
        self.bounce_rate = (self.bounce_rate + ga_report_row.bounce_rate) / 2
        self.pageviews += ga_report_row.pageviews
        self.new_visits += ga_report_row.new_visits
        self.bounced_visits += ga_report_row.bounced_visits
        self.total_time_on_site += ga_report_row.total_time_on_site

    def merge_conversion_goal_stats_with(self, ga_report_row):
        for goal in ga_report_row.goals:
            self.goals.setdefault(goal, 0)
            self.goals[goal] += ga_report_row.goals[goal]

    def is_row_valid(self):
        if not self.is_valid():
            return False

        return self.content_ad_id is not None and self.source_param != '' and self.source_param is not None


class GAApiReport(GAReport):
    def __init__(self, ga_service, start_date):
        GAReport.__init__(self)
        self.ga_service = ga_service
        self.start_date = start_date

    def download(self, ga_account):
        profiles = self.ga_service.management().profiles().list(
                accountId=ga_account.ga_account_id, webPropertyId=ga_account.ga_web_property_id).execute()
        self._download_postclick_stats(profiles)
        self._download_goal_conversion_stats(profiles)

    def _download_postclick_stats(self, profiles):
        has_more = True
        start_index = 1
        while has_more:
            data = self.ga_service.data().ga().get(
                    ids='ga:' + profiles['items'][0]['id'],
                    start_date=self.start_date.strftime('%Y-%m-%d'),
                    end_date=self.start_date.strftime('%Y-%m-%d'),
                    metrics='ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite',
                    dimensions='ga:landingPagePath,ga:deviceCategory',
                    filters='ga:landingPagePath=@_z1_',
                    start_index=start_index
            ).execute()
            if data['totalResults'] == 0:
                logger.debug('No postclick data was found.')
                break
            rows = data.get('rows')
            for row in rows:
                logger.debug('Processing GA postclick data row: %s', row)
                content_ad_id, media_source_tracking_slug = self._parse_keyword_or_url(row[0])
                report_entry = GAApiReportRow(self.start_date, content_ad_id, media_source_tracking_slug)
                report_entry.set_postclick_stats(row)
                existing_entry = self.entries.get(report_entry.key())
                if existing_entry is None:
                    self.entries[report_entry.key()] = report_entry
                else:
                    existing_entry.merge_postclick_stats_with(report_entry)

            has_more = ((start_index + data['itemsPerPage']) < data['totalResults'])
            start_index += data['itemsPerPage']

    def _parse_keyword_or_url(self, data):
        content_ad_id, source_param = self._parse_z11z_keyword(data)
        if content_ad_id is None:
            content_ad_id, source_param = self._parse_landing_page(data)
        return content_ad_id, source_param

    def _download_goal_conversion_stats(self, profiles):
        profile = profiles['items'][0]
        goals_raw = self.ga_service.management().goals().list(accountId=profile['accountId'],
                                                          webPropertyId=profile['webPropertyId'],
                                                          profileId=profile['id']).execute()
        goals_dict = {}
        for sub_goals_raw in list_chunker(goals_raw['items'], MAX_METRICS_PER_GA_REQUEST / NUM_METRICS_PER_GOAL):
            ga_metrics = self._generate_ga_metrics(sub_goals_raw)
            has_more = True
            start_index = 1
            while has_more:
                data = self.ga_service.data().ga().get(
                        ids='ga:' + profile['id'],
                        start_date=self.start_date.strftime('%Y-%m-%d'),
                        end_date=self.start_date.strftime('%Y-%m-%d'),
                        metrics=ga_metrics,
                        dimensions='ga:landingPagePath,ga:deviceCategory',
                        filters='ga:landingPagePath=@_z1_',
                        start_index=start_index
                ).execute()
                if data['totalResults'] == 0:
                    logger.debug('No goal conversion data was found.')
                    return
                rows = data.get('rows')
                for row in rows:
                    logger.debug('Processing GA conversion goal data row: %s', row)
                    content_ad_id, media_source_tracking_slug = self._parse_keyword_or_url(row[0])
                    sub_goals = {}
                    for i, sub_goal in enumerate(sub_goals_raw):
                        goal_name = sub_goal['name']
                        sub_goals[goal_name] = int(row[3 + i * NUM_METRICS_PER_GOAL])
                    key = (self.start_date, content_ad_id, media_source_tracking_slug)
                    existing_goal = goals_dict.get(key)
                    if existing_goal is None:
                        goals_dict[key] = sub_goals
                    else:
                        goals_dict[key].update(sub_goals)
                    has_more = ((start_index + data['itemsPerPage']) < data['totalResults'])
                    start_index += data['itemsPerPage']
        for key, goals in goals_dict.iteritems():
            report_entry = GAApiReportRow(key[0], key[1], key[2])
            report_entry.set_conversion_goal_stats_with(goals)
            existing_entry = self.entries.get(report_entry.key())
            if existing_entry is None:
                self.entries[report_entry.key()] = report_entry
            else:
                existing_entry.merge_conversion_goal_stats_with(report_entry)

    def _generate_ga_metrics(self, goals):
        # we have to split the Google Analytics' metrics into chunks, because Google Analytics
        # supports at most 10 metrics per request.
        goal_ids = [goal['id'] for goal in goals]
        ga_metrics = ['ga:goal{0}ConversionRate,ga:goal{0}Completions'.format(goal_id) for goal_id in goal_ids]
        return ','.join(ga_metrics)
