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

HARRYS_FIELD_KEYWORDS = ["conversion rate", "transactions", "revenue"]
GOAL_FIELD_KEYWORDS = ["conversions", "completions", "value"] + HARRYS_FIELD_KEYWORDS

GOAL_CONVERSION_KEYWORDS = ['completions', 'transactions']
GOAL_VALUE_KEWORDS = ['value', 'revenue']
GOAL_RATE_KEYWORDS = ['conversion rate']


class GaReportRow(object):
    def __init__(self, ga_row_dict, report_date, content_ad_id, source_param, goals):
        self.ga_row_dict = ga_row_dict
        self.report_date = report_date.isoformat()
        self.content_ad_id = content_ad_id
        self.source_param = source_param
        self.goals = goals

    def is_row_valid(self):
        return self.content_ad_id is not None and\
            self.source_param != '' and\
            self.source_param is not None

    def are_goals_useful(self):
        if len(self.goals) == 0:
            return False
        first_key = self.goals.keys()[0]
        if len(self.goals[first_key]) >= 2:
            return True
        return False

    def get_ga_field(self, column):
        return self.ga_row_dict.get(column, None)

    def sessions(self):
        raw_sessions = self.ga_row_dict['Sessions'].replace(',', '').strip()
        if raw_sessions == '':
            return 0
        else:
            return int(raw_sessions)

    def __str__(self):
        return "{date}-{caid}-{source_param}".format(
            date=self.report_date,
            caid=self.content_ad_id,
            source_param=self.source_param,
        )


class CsvReport(object):

    def __init__(self, csv_report_text):
        self.csv_report_text = csv_report_text
        # mapping from each url in report to corresponding z1 code or utm term
        self.entries = []
        self.start_date = None
        # first column of csv in GA report - Keyword or Landing Page
        self.first_column = None

    def is_empty(self):
        return self.entries == []

    def get_date(self):
        return self.start_date

    def debug_parsing_overview(self):
        count_all = len(self.entries)
        count_valid_rows = 0
        for entry in self.entries:
            if not entry.is_row_valid():
                continue
            count_valid_rows += 1

        count_goal_useful = 0
        for entry in self.entries:
            if not entry.are_goals_useful():
                continue
            count_goal_useful += 1
        return "Overview report_dt: {dt} cads: {count_useful_ca}/{count_all} goals {useful_ga}/{count_all}".format(
            dt=self.start_date.date().isoformat() if self.start_date != None else '',
            count_useful_ca=count_valid_rows,
            count_all=count_all,
            useful_ga=count_goal_useful,
        )

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

        date = datetime.datetime.strptime(group_dict['start_date'], "%Y%m%d")

        first_column_name = None
        if self._contains_column(lines, LANDING_PAGE_COL_NAME):
            first_column_name = LANDING_PAGE_COL_NAME
        elif self._contains_column(lines, KEYWORD_COL_NAME):
            first_column_name = KEYWORD_COL_NAME

        if not first_column_name:
            raise exc.EmptyReportException(
                'Header Check: There should be a line containing a column "Landing Page" or "Keyword"')

        return date, first_column_name

    def _contains_column(self, lines, name):
        return any(line.startswith('{col},'.format(col=name)) or\
                   line.endswith(',{col}'.format(col=name)) or\
                   ',{col},'.format(col=name) in line\
                   for line in lines)

    def parse(self):
        self._parse(self.csv_report_text)

    def _parse(self, csv_report_text):
        report_date, first_column_name = self._parse_header(self._extract_header_lines(csv_report_text))
        self.first_column = first_column_name
        self.start_date = report_date

        f_body, f_footer = self._extract_body_and_footer(csv_report_text)
        reader = csv.DictReader(f_body)
        try:
            self.fieldnames = reader.fieldnames
            self.entries = []
            for entry in reader:
                keyword_or_url = entry[self.first_column]
                if keyword_or_url is None or keyword_or_url.strip() == '':
                    continue
                content_ad_id, source_param = self._parse_keyword_or_url(keyword_or_url)
                goals = self._parse_goals(self.fieldnames, entry)
                report_entry = GaReportRow(entry, self.start_date, content_ad_id, source_param, goals)
                self.entries.append(report_entry)
        except:
            raise exc.CsvParseException('Could not parse CSV')

        if self.fieldnames is None and not set(self.fieldnames or []) >= set(REQUIRED_FIELDS):
            missing_fieldnames = list(set(REQUIRED_FIELDS) - (set(self.fieldnames) & set(REQUIRED_FIELDS)))
            raise exc.CsvParseException('Not all required fields are present. Missing: {}'.format(','.join(missing_fieldnames)))

        self._check_session_counts(f_footer)

    def _parse_keyword_or_url(self, data):
        if self.first_column == LANDING_PAGE_COL_NAME:
            return self._parse_landing_page(data)
        else:
            return self._parse_z11z_keyword(data)

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

    def _parse_landing_page(self, raw_url):
        url, query_params = url_helper.clean_url(raw_url)
        # parse caid
        content_ad_id = None
        try:
            if '_z1_caid' in query_params:
                content_ad_id = int(query_params['_z1_caid'])
        except ValueError:
            return None, ''

        source_param = ''
        if '_z1_msid' in query_params:
            source_param = query_params['_z1_msid']

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
        # parse well formatted goals if there are any
        goal_fields = filter(lambda field: '(Goal' in field, fields)
        if goal_fields == []:
            idx_mid = -1
            for field in fields:
                if "Session Duration" in field:
                    idx_mid = fields.index(field) + 1
            if idx_mid != -1:
                goal_fields = fields[idx_mid:]

        # reparse in case we didn't find any goals
        if goal_fields == []:
            goal_fields = fields

        # filter out fields which do not contain any relevant goal field
        ret = []
        for goal_field in goal_fields:
            found = False
            for goal_keyword in GOAL_FIELD_KEYWORDS:
                if goal_keyword in goal_field.lower():
                    found = True
            if found:
                ret.append(goal_field)
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
        sessions_sum = sum(entry.sessions() for entry in self.entries)
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

    def is_media_source_specified(self):
        media_source_not_specified = []
        for entry in self.entries:
            if entry.source_param == '':
                media_source_not_specified.append(entry.source_param)
        return (len(media_source_not_specified) == 0, list(media_source_not_specified))

    def is_content_ad_specified(self):
        content_ad_not_specified = set()
        for entry in self.entries:
            if entry.content_ad_id is None:
                content_ad_not_specified.add(entry.get_ga_field(self.first_column))
        return (len(content_ad_not_specified) == 0, list(content_ad_not_specified))
