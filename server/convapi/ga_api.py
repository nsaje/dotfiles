import json
import logging
import re

from convapi.parse_v2 import ReportRow, Report
from utils.statsd_helper import statsd_timer

from utils.list_helper import list_chunker

logger = logging.getLogger(__name__)


MAX_METRICS_PER_GA_REQUEST = 10
NUM_METRICS_PER_GOAL = 2


class GAApiRow(ReportRow):
    def __init__(self, ga_row_list, report_date, content_ad_id, source_param, goals):
        ReportRow.__init__(self)
        self.raw_row = json.dumps(ga_row_list or {})
        # self.ga_row_dicts = [ga_row_dict]

        self.report_date = report_date.isoformat()
        self.content_ad_id = content_ad_id
        self.source_param = source_param

        self.visits = int(ga_row_list[2])
        self.new_visits = int(ga_row_list[3])
        self.bounce_rate = float(ga_row_list[4]) / 100.0
        self.pageviews = int(ga_row_list[5])
        self.total_time_on_site = int(float(ga_row_list[6]))
        self.bounced_visits = int(self.bounce_rate * self.visits)

        self.goals = goals

    def key(self):
        return self.report_date, self.content_ad_id, self.source_param

    def merge_with(self, ga_report_row):
        # self.ga_row_dicts.extend(ga_report_row.ga_row_dicts)
        self.visits += ga_report_row.visits
        self.bounce_rate = (self.bounce_rate + ga_report_row.bounce_rate) / 2
        self.pageviews += ga_report_row.pageviews
        self.new_visits += ga_report_row.new_visits
        self.bounced_visits += ga_report_row.bounced_visits
        self.total_time_on_site += ga_report_row.total_time_on_site

        for goal in ga_report_row.goals:
            self.goals.setdefault(goal, 0)
            self.goals[goal] += ga_report_row.goals[goal]

    def is_row_valid(self):
        if not self.is_valid():
            return False

        return self.content_ad_id is not None and self.source_param != '' and self.source_param is not None


class GAApiReport(Report):
    def __init__(self, ga_service, ga_account, start_date):
        Report.__init__(self)
        self.ga_service = ga_service
        self.profiles = ga_service.management().profiles().list(
                accountId=ga_account.ga_account_id, webPropertyId=ga_account.ga_web_property_id).execute()
        self.start_date = start_date

    @statsd_timer('convapi.ga_api', 'download')
    def download(self):
        self._download_postclick_stats()
        self._download_goal_conversion_stats()

        # f_body, f_footer = self._extract_body_and_footer(self.csv_report_text)
        # reader = csv.DictReader(f_body)
        # try:
        #     self.fieldnames = reader.fieldnames
        #     self.entries = {}
        #     for entry in reader:
        #         keyword_or_url = entry[self.first_column]
        #         if keyword_or_url is None or keyword_or_url.strip() == '':
        #             continue
        #
        #         if keyword_or_url.startswith('Day Index') or keyword_or_url.startswith('Hour Index'):
        #             break
        #
        #         content_ad_id, source_param = self._parse_keyword_or_url(keyword_or_url)
        #         goals = self._parse_goals(self.fieldnames, entry)
        #         report_entry = GaReportRow(entry, self.start_date, content_ad_id, source_param, goals)
        #         self.add_imported_visits(report_entry.visits or 0)
        #
        #         existing_entry = self.entries.get(report_entry.key())
        #         if existing_entry is None:
        #             self.entries[report_entry.key()] = report_entry
        #         else:
        #             existing_entry.merge_with(report_entry)
        # except:
        #     logger.exception("Failed parsing GA report")
        #     raise exc.CsvParseException('Could not parse CSV')
        #
        # if not set(self.fieldnames or []) >= set(REQUIRED_FIELDS):
        #     missing_fieldnames = list(set(REQUIRED_FIELDS) - (set(self.fieldnames or []) & set(REQUIRED_FIELDS)))
        #     raise exc.CsvParseException(
        #         'Not all required fields are present. Missing: {}'.format(','.join(missing_fieldnames)))
        #
        # self._check_session_counts(f_footer)

    def _download_postclick_stats(self):
        has_more = True
        start_index = 1
        while has_more:
            data = self.ga_service.data().ga().get(
                    ids='ga:' + self.profiles['items'][0]['id'],
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
                content_ad_id = re.search('.*_z1_caid=(\d+)[&]?.*', row[0]).group(1)
                media_source_tracking_slug = re.search('.*_z1_msid=([\w-]+)[&]?.*', row[0]).group(1)
                # self._update_postclick_item(ga_date, content_ad_id, media_source_tracking_slug, row)
            has_more = ((start_index + data['itemsPerPage']) < data['totalResults'])
            start_index += data['itemsPerPage']

    def _download_goal_conversion_stats(self):
        profile = self.profiles['items'][0]
        goals = self.ga_service.management().goals().list(accountId=profile['accountId'],
                                                          webPropertyId=profile['webPropertyId'],
                                                          profileId=profile['id']).execute()
        for sub_goals in list_chunker(goals['items'], MAX_METRICS_PER_GA_REQUEST / NUM_METRICS_PER_GOAL):
            ga_metrics = self._generate_ga_metrics(sub_goals)
            has_more = True
            start_index = 1
            while has_more:
                data = self.ga_service.data().ga().get(
                        ids='ga:' + profile['id'],
                        start_date=self.ga_date.strftime('%Y-%m-%d'),
                        end_date=self.ga_date.strftime('%Y-%m-%d'),
                        metrics=ga_metrics,
                        dimensions='ga:landingPagePath,ga:deviceCategory',
                        filters='ga:landingPagePath=@_z1_',
                        start_index=start_index
                ).execute()
                if data['totalResults'] == 0:
                    logger.debug('No goal conversion data was found.')
                    break
                rows = data.get('rows')
                for row in rows:
                    logger.debug('Processing GA conversion goal data row: %s', row)
                    for i, sub_goal in enumerate(sub_goals):
                        content_ad_id = re.search('.*_z1_caid=(\d+)[&]?.*', row[0]).group(1)
                        media_source_tracking_slug = re.search('.*_z1_msid=([\w-]+)[&]?.*', row[0]).group(1)
                        # self._update_goal_conversion_item(self.ga_date, content_ad_id,
                        #                                   media_source_tracking_slug,
                        #                                   sub_goal['name'],
                        #                                   row[3 + i * NUM_METRICS_PER_GOAL])
                    has_more = ((start_index + data['itemsPerPage']) < data['totalResults'])
                    start_index += data['itemsPerPage']

    def _generate_ga_metrics(self, goals):
        # we have to split the Google Analytics' metrics into chunks, because Google Analytics
        # supports at most 10 metrics per request.
        goal_ids = [goal['id'] for goal in goals]
        ga_metrics = ['ga:goal{0}ConversionRate,ga:goal{0}Completions'.format(goal_id) for goal_id in goal_ids]
        return ','.join(ga_metrics)

    # def _parse_keyword_or_url(self, data):
    #     if self.first_column == LANDING_PAGE_COL_NAME:
    #         return self._parse_landing_page(data)
    #     else:
    #         return self._parse_z11z_keyword(data)
    #
    # def _parse_landing_page(self, raw_url):
    #     url, query_params = url_helper.clean_url(raw_url)
    #     # parse caid
    #     content_ad_id = None
    #     try:
    #         if '_z1_caid' in query_params:
    #             content_ad_id_raw = query_params['_z1_caid']
    #             results = LANDING_PAGE_CAID_RE.search(content_ad_id_raw)
    #             if results is not None:
    #                 content_ad_id_raw = results.group(0)
    #
    #             content_ad_id = int(content_ad_id_raw)
    #     except ValueError:
    #         return None, ''
    #
    #     source_param = ''
    #     if '_z1_msid' in query_params:
    #         source_param = query_params['_z1_msid'] or ''
    #         results = LANDING_PAGE_MSID_RE.search(source_param)
    #         if results is not None:
    #             source_param = results.group(0)
    #
    #     if content_ad_id is None or source_param == '':
    #         logger.warning(
    #                 'Could not parse landing page url %s. content_ad_id: %s, source_param: %s',
    #                 raw_url,
    #                 content_ad_id,
    #                 source_param
    #         )
    #         return None, ''
    #     return content_ad_id, source_param
    #
    #
    #
    # def _check_session_counts(self, footer):
    #     sessions_total = self._get_sessions_total(footer)
    #     sessions_sum = sum(entry.sessions() for entry in self.entries.values())
    #     if sessions_total != sessions_sum:
    #         raise exc.IncompleteReportException(
    #                 'Number of total sessions ({}) is not equal to sum of session counts ({})'.format(
    #                         sessions_total, sessions_sum)
    #         )
    #
    # def _get_sessions_total(self, footer):
    #     reader = csv.DictReader(footer)
    #     first_row = reader.next()
    #     if 'Day Index' in first_row:
    #         return _report_atoi(first_row['Sessions'])
    #
    #     for row in reader:
    #         if 'Hour Index' in row and row['Hour Index'] == '':
    #             return _report_atoi(row['Sessions'])
    #
    #     raise exc.CsvParseException('Could not parse total sessions')
    #
    # def _extract_header_lines(self, raw_report_string):
    #     # assuming headers are less than 10 lines
    #     return raw_report_string.split('\n')[:10]
    #
    # def _extract_body_and_footer(self, raw_report_string):
    #     mainlines = []
    #     inside = False
    #     split_raw_report_string = raw_report_string.split('\n')
    #     for line in split_raw_report_string:
    #         if not inside and line.startswith(self.first_column):
    #             inside = True
    #         if inside:
    #             # There are instances of CSV files, that have 'Pages/Session' instead of 'Pages / Session'
    #             if 'Pages/Session' in line:
    #                 line = line.replace('Pages/Session', 'Pages / Session')
    #             mainlines.append(line)
    #         stripped_line = line.strip()
    #         if inside and stripped_line == "" or \
    #                 stripped_line.startswith('Day Index') or \
    #                 stripped_line.startswith('Hour Index'):
    #             break
    #
    #     inside = False
    #     index_lines = []
    #     for line in split_raw_report_string:
    #         if not inside and (line.startswith('Day Index') or line.startswith('Hour Index')):
    #             inside = True
    #         if inside and line.strip() != "":
    #             index_lines.append(line)
    #
    #     return StringIO.StringIO('\n'.join(mainlines)), StringIO.StringIO('\n'.join(index_lines))
