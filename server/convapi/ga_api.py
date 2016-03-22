import copy
import dash
import json
import logging
import httplib2
import googleapiclient.discovery
from googleapiclient.errors import HttpError
from oauth2client.client import SignedJwtAssertionCredentials
from django.conf import settings
from convapi.parse_v2 import ReportRow, GAReport
from utils.list_helper import list_chunker

logger = logging.getLogger(__name__)

GA_API_NAME = 'analytics'
GA_API_VERSION = 'v3'
GA_SCOPE = ['https://www.googleapis.com/auth/analytics.readonly']
GA_GOAL_METRICS_FORMAT = 'ga:goal{0}Completions'
GA_DIMENSIONS = 'ga:landingPagePath,ga:keyword'

MAX_METRICS_PER_GA_REQUEST = 10
NUM_METRICS_PER_GOAL = len(GA_GOAL_METRICS_FORMAT.split(','))
NUM_GA_DIMENSIONS = len(GA_DIMENSIONS.split(','))


def get_ga_service():
    logger.debug('Getting Google Analytics service.')
    credentials = SignedJwtAssertionCredentials(
            settings.GA_CLIENT_EMAIL,
            settings.GA_PRIVATE_KEY,
            GA_SCOPE
    )
    http = credentials.authorize(httplib2.Http())
    # Build the GA service object.
    service = googleapiclient.discovery.build(GA_API_NAME, GA_API_VERSION, http=http, cache_discovery=False)
    return service


class GAApiReportRow(ReportRow):
    def __init__(self, report_date, content_ad_id, source_param, publisher_param):
        ReportRow.__init__(self)
        self.report_date = report_date.isoformat()
        self.content_ad_id = content_ad_id
        self.source_param = source_param
        self.publisher_param = publisher_param

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
        return self.report_date, self.content_ad_id, self.source_param, self.publisher_param

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


class GAApiReport(GAReport):
    def __init__(self, ga_service, start_date):
        GAReport.__init__(self)
        self.ga_service = ga_service
        self.start_date = start_date

    def download(self, ga_account):
        profiles = self._get_ga_profiles(ga_account)
        self._download_postclick_stats(profiles)
        self._download_goal_conversion_stats(profiles)

    def get_content_ad_stats(self):
        result = {}

        for key, entry in self.entries.iteritems():
            if not entry.is_row_valid():
                continue

            result_key = (entry.report_date, entry.content_ad_id, entry.source_param)
            if result_key not in result:
                result[result_key] = copy.deepcopy(entry)
            else:
                result[result_key].merge_postclick_stats_with(entry)
                result[result_key].merge_conversion_goal_stats_with(entry)

        return result.values()

    def get_publisher_stats(self):
        result = {}

        content_ad_ids = set([entry.content_ad_id for entry in self.entries.values()])

        content_ads_ad_groups = dash.models.ContentAd.objects.filter(
                pk__in=content_ad_ids
        ).values_list('ad_group', 'pk')

        ad_group_mapping = dict((k, v) for v, k in content_ads_ad_groups)

        for key, entry in self.entries.iteritems():
            if not entry.is_publisher_row_valid():
                continue

            ad_group_id = ad_group_mapping[entry.content_ad_id]

            result_key = (
                entry.report_date,
                ad_group_id,
                entry.publisher_param,
                entry.source_param
            )
            if result_key not in result:
                entry_copy = copy.deepcopy(entry)
                entry_copy.ad_group_id = ad_group_id
                entry_copy.content_ad_id = None
                result[result_key] = entry_copy
            else:
                result[result_key].merge_postclick_stats_with(entry)
                result[result_key].merge_conversion_goal_stats_with(entry)

        return result.values()

    def _get_ga_profiles(self, ga_account):
        return self.ga_service.management().profiles().list(
                accountId=ga_account.ga_account_id, webPropertyId=ga_account.ga_web_property_id).execute()

    def _download_postclick_stats(self, profiles):
        for row in self._ga_stats_generator(self.start_date, profiles['items'][0]['id'],
                                            'ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite'):
            logger.debug('Processing GA postclick data row: %s', row)
            content_ad_id, media_source_tracking_slug, publisher = self._parse_keyword_or_url(row)
            report_entry = GAApiReportRow(self.start_date, content_ad_id, media_source_tracking_slug, publisher)
            report_entry.set_postclick_stats(row)
            self._update_report_entry_postclick_stats(report_entry)

    def _ga_stats_generator(self, start_date, profile_id, metrics):
        start_index = 1
        has_more = True
        while has_more:
            ga_stats = self._download_stats_from_ga(self.start_date, profile_id, metrics, start_index)
            if ga_stats is None:
                logger.debug('No postclick data was found.')
                break
            rows = ga_stats.get('rows')
            for row in rows:
                yield row
            start_index += ga_stats['itemsPerPage']
            has_more = (start_index < ga_stats['totalResults'])

    def _download_stats_from_ga(self, start_date, profile_id, metrics, start_index):
        try:
            ga_stats = self.ga_service.data().ga().get(
                    ids='ga:' + profile_id,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=start_date.strftime('%Y-%m-%d'),
                    metrics=metrics,
                    dimensions=GA_DIMENSIONS,
                    filters='ga:landingPagePath=@_z1_,ga:keyword=~.*z1[0-9]+[a-zA-Z].+?1z.*',
                    start_index=start_index
            ).execute()
            if start_index == 1 and ga_stats['totalResults'] == 0:
                ga_stats = None
            return ga_stats
        except HttpError:
            logger.exception('Google Analytics API call failed.')
            raise
        except Exception:
            logger.exception('General exception when calling Google Analytics API.')
            raise

    def _parse_keyword_or_url(self, row):
        content_ad_id, source_param, publisher_param = self._parse_z11z_keyword(row[1])
        if content_ad_id is None:
            content_ad_id, source_param, publisher_param = self._parse_landing_page(row[0])
        return content_ad_id, source_param, publisher_param

    def _update_report_entry_postclick_stats(self, report_entry):
        existing_entry = self.entries.get(report_entry.key())
        if existing_entry is None:
            self.entries[report_entry.key()] = report_entry
        else:
            existing_entry.merge_postclick_stats_with(report_entry)

    def _download_goal_conversion_stats(self, profiles):
        profile = profiles['items'][0]
        goal_metadata = self._get_ga_goals(profile)
        goals = {}
        for sub_goal_metadata in list_chunker(goal_metadata['items'],
                                              MAX_METRICS_PER_GA_REQUEST / NUM_METRICS_PER_GOAL):
            ga_metrics = self._generate_ga_metrics(sub_goal_metadata)
            for row in self._ga_stats_generator(self.start_date, profile['id'], ga_metrics):
                logger.debug('Processing GA conversion goal data row: %s', row)
                self._update_goals(goals, row, sub_goal_metadata)
        for key, value in goals.iteritems():
            report_entry = GAApiReportRow(key[0], key[1], key[2], key[3])
            report_entry.set_conversion_goal_stats_with(value)
            self._update_report_entry_goal_conversion_stats(report_entry)

    def _get_ga_goals(self, profile):
        return self.ga_service.management().goals().list(accountId=profile['accountId'],
                                                         webPropertyId=profile['webPropertyId'],
                                                         profileId=profile['id']).execute()

    def _generate_ga_metrics(self, goals):
        # we have to split the Google Analytics' metrics into chunks, because Google Analytics
        # supports at most 10 metrics per request.
        ga_metrics = [GA_GOAL_METRICS_FORMAT.format(goal['id']) for goal in goals]
        return ','.join(ga_metrics)

    def _update_report_entry_goal_conversion_stats(self, report_entry):
        existing_entry = self.entries.get(report_entry.key())
        if existing_entry is None:
            self.entries[report_entry.key()] = report_entry
        else:
            existing_entry.merge_conversion_goal_stats_with(report_entry)

    def _update_goals(self, goals, row, sub_goal_metadata):
        content_ad_id, media_source_tracking_slug, publisher_param = self._parse_keyword_or_url(row)
        sub_goals = {}
        for i, metadata in enumerate(sub_goal_metadata):
            sub_goal_name = metadata['name']
            sub_goals[sub_goal_name] = int(row[NUM_GA_DIMENSIONS + i * NUM_METRICS_PER_GOAL])
        key = (self.start_date, content_ad_id, media_source_tracking_slug, publisher_param)
        existing_goal = goals.get(key)
        if existing_goal is None:
            goals[key] = sub_goals
        else:
            for sub_goal, value in sub_goals.iteritems():
                if sub_goal in goals[key]:
                    goals[key][sub_goal] += value
                else:
                    goals[key].update(sub_goals)
