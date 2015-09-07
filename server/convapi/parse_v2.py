import csv
import datetime
import exc
import re
import StringIO
import logging

from utils import url_helper

LANDING_PAGE_COL_NAME = 'Landing Page'
KEYWORD_COL_NAME = 'Keyword'
REQUIRED_FIELDS = [
    'Sessions',
    '% New Sessions',
    'New Users',
    'Bounce Rate',
    'Pages / Session',
    'Avg. Session Duration',
]


logger = logging.getLogger(__name__)

Z11Z_RE = re.compile('.*z1([0-9]+)([a-zA-Z].+?)1z.*')
LANDING_PAGE_CAID_RE = re.compile('^[0-9]+')
LANDING_PAGE_MSID_RE = re.compile('^[_a-zA-Z0-9]+')

HARRYS_FIELD_KEYWORDS = ["conversion rate", "transactions", "revenue"]
GOAL_FIELD_KEYWORDS = ["conversions", "completions", "value"] + HARRYS_FIELD_KEYWORDS

GOAL_CONVERSION_KEYWORDS = ['completions', 'transactions']
GOAL_VALUE_KEWORDS = ['value', 'revenue']
GOAL_RATE_KEYWORDS = ['conversion rate']


class GaReportRow(object):
    def __init__(self, ga_row_dict, report_date, content_ad_id, source_param, goals):
        self.ga_row_dicts = [ga_row_dict]

        self.visits = self._atoi(ga_row_dict.get('Sessions'))
        self.bounce_rate_raw = ga_row_dict.get('Bounce Rate')
        if ga_row_dict.get('Bounce Rate') is not None:
            self.bounce_rate = self._atof(ga_row_dict['Bounce Rate'].replace('%', '')) / 100
        else:
            self.bounce_rate = 0
        self.pageviews = int(round(self._atof(ga_row_dict.get('Pages / Session', '0')) * self.visits))
        self.new_visits = self._atoi(ga_row_dict.get('New Users', '0'))
        self.bounced_visits = int(self.bounce_rate * self.visits)
        self.total_time_on_site = self.visits * self._parse_duration(ga_row_dict.get('Avg. Session Duration', '00:00:00'))

        self.report_date = report_date.isoformat()
        self.content_ad_id = content_ad_id
        self.source_param = source_param
        self.goals = goals

    def key(self):
        return (self.report_date, self.content_ad_id, self.source_param)

    def merge_with(self, ga_report_row):
        self.ga_row_dicts.extend(ga_report_row.ga_row_dicts)
        self.visits += ga_report_row.visits
        self.bounce_rate = (self.bounce_rate + ga_report_row.bounce_rate) / 2
        self.pageviews += ga_report_row.pageviews
        self.new_visits += ga_report_row.new_visits
        self.bounced_visits += ga_report_row.bounced_visits
        self.total_time_on_site += ga_report_row.total_time_on_site

        # merge goal conversions only for now
        for ga_report_row_goal in ga_report_row.goals:
            if ga_report_row_goal in self.goals:
                self.goals[ga_report_row_goal]['conversions'] = self.goals[ga_report_row_goal].get('conversions', 0)
                self.goals[ga_report_row_goal]['conversions'] +=\
                    ga_report_row.goals.get(ga_report_row_goal, {'conversions': 0}).get('conversions', 0)
            else:
                self.goals[ga_report_row_goal] = ga_report_row.goals[ga_report_row_goal]

    def is_row_valid(self):
        return self.content_ad_id is not None and\
            self.source_param != '' and\
            self.source_param is not None

    def are_goals_useful(self):
        if len(self.goals) == 0:
            return False
        for key, goal_dict in self.goals.iteritems():
            if 'conversions' in goal_dict.keys():
                return True
        return False

    def get_ga_fields(self, column):
        return [ga_row_dict.get(column, None) for ga_row_dict in self.ga_row_dicts]

    def sessions(self):
        all_row_raw_sessions = [ga_row_dict['Sessions'].replace(',', '').strip() for ga_row_dict in self.ga_row_dicts]
        all_row_sessions = [int(raw_sessions) if raw_sessions not in ('', None) else 0 for raw_sessions in all_row_raw_sessions]
        return sum(all_row_sessions)

    def _atoi(self, raw_str):
        # TODO: Implement locale specific parsing
        return int(raw_str.replace(',', ''))

    def _atof(self, raw_str):
        # TODO: Implement locale specific parsing
        return float(raw_str.replace(',', ''))

    def _parse_duration(self, durstr):
        hours_str, minutes_str, seconds_str = durstr.replace('<', '').split(':')
        return int(seconds_str) + 60 * int(minutes_str) + 60 * 60 * int(hours_str)

    def __str__(self):
        return "{date}-{caid}-{source_param}".format(
            date=self.report_date,
            caid=self.content_ad_id,
            source_param=self.source_param,
        )


class Report(object):

    def __init__(self):
        # mapping from each url in report to corresponding z1 code or utm term
        self.entries = {}
        self.start_date = None

    def is_empty(self):
        return self.entries == {}

    def get_date(self):
        return self.start_date

    def valid_entries(self):
        return [entry for entry in self.entries.values() if entry.is_row_valid()]

    def debug_parsing_overview(self):
        count_all = len(self.entries.values())
        count_valid_rows = 0
        for entry in self.entries.values():
            if not entry.is_row_valid():
                continue
            count_valid_rows += 1

        count_goal_useful = 0
        for entry in self.entries.values():
            if not entry.are_goals_useful():
                continue
            count_goal_useful += 1
        return "Overview report_dt: {dt} cads: {count_useful_ca}/{count_all} goals {useful_ga}/{count_all}".format(
            dt=self.start_date.isoformat() if self.start_date != None else '',
            count_useful_ca=count_valid_rows,
            count_all=count_all,
            useful_ga=count_goal_useful,
        )

    def _parse_z11z_keyword(self, keyword):
        result = Z11Z_RE.match(keyword)
        if not result:
            return None, ''
        else:
            content_ad_id, source_param = result.group(1), result.group(2)

        try:
            content_ad_id = int(content_ad_id)
        except (ValueError, TypeError):
            return None, ''

        if source_param == '':
            logger.warning(
                'Could not parse keyword %s. content_ad_id: %s, source_param: %s',
                keyword,
                self.content_ad_id,
                self.source_param
            )
            return None, ''

        return content_ad_id, source_param

    def is_media_source_specified(self):
        media_source_not_specified = []
        for entry in self.entries.values():
            if entry.source_param == '' is None or entry.source_param == '':
                media_source_not_specified.append(entry.source_param)
        return (len(media_source_not_specified) == 0, list(media_source_not_specified))

    def is_content_ad_specified(self):
        content_ad_not_specified = set()
        for entry in self.entries.values():
            if entry.content_ad_id is None or entry.content_ad_id == '':
                content_ad_not_specified.add(entry.content_ad_id)
        return (len(content_ad_not_specified) == 0, list(content_ad_not_specified))


class GAReport(Report):

    def __init__(self, csv_report_text):
        Report.__init__(self)

        self.csv_report_text = csv_report_text
        # first column of csv in GA report - Keyword or Landing Page
        self.first_column = None

    def _parse_header(self, lines):
        '''
        Parse header and return tuple (report date, first col. name)
        '''
        if len(lines) < 5:
            raise exc.CsvParseException('Too few lines.')

        start_end_lines = [0, 4]
        for line_index in start_end_lines:
            if not lines[line_index].startswith('# -----'):
                raise exc.CsvParseException('Line {idx} should start with "# -----"'.format(idx=line_index))

        comment_lines = [2, 3]
        for line_index in comment_lines:
            if not lines[line_index].startswith('#'):
                raise exc.CsvParseException('Line {idx} should start with "#"'.format(idx=line_index))

        dateline = lines[3]
        m = re.search(r'(?P<start_date>[0-9]{8})-(?P<end_date>[0-9]{8})', dateline)
        if m is None:
            raise exc.CsvParseException('Date of the report could not be parsed')

        group_dict = m.groupdict()
        if 'start_date' not in group_dict or 'end_date' not in group_dict:
            raise exc.CsvParseException('Both, start date and end date, should be specified')

        if group_dict['start_date'] != group_dict['end_date']:
            raise exc.CsvParseException('start date and end date should be identical')

        date = datetime.datetime.strptime(group_dict['start_date'], "%Y%m%d").date()

        non_comment_lines = [line for line in lines if not (
            line.startswith('#') and line.replace(',', '').strip() != '')]

        first_column_name = None
        if self._contains_column(non_comment_lines, LANDING_PAGE_COL_NAME):
            first_column_name = LANDING_PAGE_COL_NAME
        elif self._contains_column(non_comment_lines, KEYWORD_COL_NAME):
            first_column_name = KEYWORD_COL_NAME

        if not first_column_name:
            raise exc.EmptyReportException(
                'Header Check: There should be a line containing a column "Landing Page" or "Keyword"')

        return date, first_column_name

    def _contains_column(self, lines, name):
        return any(name in line for line in lines)

    def parse(self):
        report_date, first_column_name = self._parse_header(self._extract_header_lines(self.csv_report_text))
        self.first_column = first_column_name
        self.start_date = report_date

        f_body, f_footer = self._extract_body_and_footer(self.csv_report_text)
        reader = csv.DictReader(f_body)
        try:
            self.fieldnames = reader.fieldnames
            self.entries = {}
            for entry in reader:
                keyword_or_url = entry[self.first_column]
                if keyword_or_url is None or keyword_or_url.strip() == '':
                    continue
                content_ad_id, source_param = self._parse_keyword_or_url(keyword_or_url)
                goals = self._parse_goals(self.fieldnames, entry)
                report_entry = GaReportRow(entry, self.start_date, content_ad_id, source_param, goals)

                existing_entry = self.entries.get(report_entry.key())
                if existing_entry is None:
                    self.entries[report_entry.key()] = report_entry
                else:
                    existing_entry.merge_with(report_entry)
        except:
            raise exc.CsvParseException('Could not parse CSV')

        if self.fieldnames is None and not set(self.fieldnames or []) >= set(REQUIRED_FIELDS):
            missing_fieldnames = list(set(REQUIRED_FIELDS) - (set(self.fieldnames or []) & set(REQUIRED_FIELDS)))
            raise exc.CsvParseException('Not all required fields are present. Missing: {}'.format(','.join(missing_fieldnames)))

        self._check_session_counts(f_footer)

    def _parse_keyword_or_url(self, data):
        if self.first_column == LANDING_PAGE_COL_NAME:
            return self._parse_landing_page(data)
        else:
            return self._parse_z11z_keyword(data)

    def _parse_landing_page(self, raw_url):
        url, query_params = url_helper.clean_url(raw_url)
        # parse caid
        content_ad_id = None
        try:
            if '_z1_caid' in query_params:
                content_ad_id_raw = query_params['_z1_caid']
                results = LANDING_PAGE_CAID_RE.search(content_ad_id_raw)
                if results is not None:
                    content_ad_id_raw = results.group(0)

                content_ad_id = int(content_ad_id_raw)
        except ValueError:
            return None, ''

        source_param = ''
        if '_z1_msid' in query_params:
            source_param = query_params['_z1_msid'] or ''
            results = LANDING_PAGE_MSID_RE.search(source_param)
            if results is not None:
                source_param = results.group(0)


        if content_ad_id is None or source_param == '':
            logger.warning(
                'Could not parse landing page url %s. content_ad_id: %s, source_param: %s',
                raw_url,
                content_ad_id,
                source_param
            )
            return None, ''
        return content_ad_id, source_param

    def _get_goal_name(self, goal_field):
        try:
            ix_goal = goal_field.index('(Goal')
        except:
            ix_goal = -1
        if ix_goal != -1:
            return goal_field[:ix_goal].strip()
        else:
            return 'Goal 1'

    def _get_goal_value_type(self, goal_field):
        try:
            ix_goal = goal_field.index('(Goal')
        except:
            ix_goal = -1
        if ix_goal != -1:
            return goal_field[ix_goal:].strip()
        else:
            return goal_field

    def _get_goal_fields(self, fields):
        # filter out fields which do not contain any relevant goal field
        ret = []
        for field in fields:
            found = False
            for goal_keyword in GOAL_FIELD_KEYWORDS:
                if goal_keyword in field.lower():
                    found = True
            if found:
                ret.append(field)
        return ret

    def _parse_goals(self, fieldnames, row_dict):
        goal_fields = self._get_goal_fields(fieldnames)
        result = {}
        for goal_field in goal_fields:
            goal_name = self._get_goal_name(goal_field)
            goal_value_type = self._get_goal_value_type(goal_field).lower()

            if row_dict[goal_field] == '':
                continue

            metric_fields = result.get(goal_name, {})
            if self._subset_match(goal_value_type, GOAL_CONVERSION_KEYWORDS):
                metric_fields['conversions'] = int(row_dict[goal_field])
            elif self._subset_match(goal_value_type, GOAL_VALUE_KEWORDS):
                metric_fields['value'] = row_dict[goal_field]
            elif self._subset_match(goal_value_type, GOAL_RATE_KEYWORDS):
                metric_fields['conversion_rate'] = row_dict[goal_field]
            result[goal_name] = metric_fields
        return result

    def _subset_match(self, value, lst):
        # if any string in lst matches a subset of value return true
        for el in lst:
            if el in value:
                return True
        return False

    def _check_session_counts(self, footer):
        sessions_total = self._get_sessions_total(footer)
        sessions_sum = sum(entry.sessions() for entry in self.entries.values())
        if sessions_total != sessions_sum:
            raise exc.IncompleteReportException(
                'Number of total sessions ({}) is not equal to sum of session counts ({})'.format(
                    sessions_total, sessions_sum)
            )

    def _get_sessions_total(self, footer):
        reader = csv.DictReader(footer)
        try:
            line = reader.next()
            return int(line['Sessions'].strip().replace(',', ''))
        except:
            raise exc.CsvParseException('Could not parse total sessions')

    def _extract_header_lines(self, raw_report_string):
        # assuming headers are less than 10 lines
        return raw_report_string.split('\n')[:10]

    def _extract_body_and_footer(self, raw_report_string):
        mainlines = []
        inside = False
        split_raw_report_string = raw_report_string.split('\n')
        for line in split_raw_report_string:
            if not inside and line.startswith(self.first_column):
                inside = True
            if inside:
                # There are instances of CSV files, that have 'Pages/Session' instead of 'Pages / Session'
                if 'Pages/Session' in line:
                    line = line.replace('Pages/Session', 'Pages / Session')
                mainlines.append(line)
            if inside and line.strip() == "" or line.strip().startswith('Day Index'):
                break

        inside = False
        day_index_lines = []
        for line in split_raw_report_string:
            if not inside and line.startswith('Day Index'):
                inside = True
            if inside and line.strip() != "":
                day_index_lines.append(line)

        return StringIO.StringIO('\n'.join(mainlines)), StringIO.StringIO('\n'.join(day_index_lines))

class OmnitureReport(Report):

    def __init__(self, csv_report_text):
        Report.__init__(self)

        self.csv_report_blob = csv_report_blob
        # first column of csv in GA report - Keyword or Landing Page
        self.first_column = None

    def _parse_header(self, lines):
        pass

    def parse(self):
        pass
