import datetime
import exc
import re
import csv
import StringIO
import logging

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


class CsvReport(object):

    def __init__(self, csv_report_text, report_log):
        self.csv_report_text = csv_report_text
        self.report_log = report_log
        # mapping from each url in report to corresponding z1 code or utm term
        self.report_z1_codes = {}
        self.report_utmterm_codes = {}
        self.entries = []
        self.start_date = None
        # first column of report - Keyword or Landing Page
        self.report_id = None
        self.z11z_pattern = re.compile('^z1([0-9]*)(.*)1z$')

    def is_empty(self):
        return self.entries == []

    def get_date(self):
        return self.start_date

    def _parse_header(self, lines):
        '''
        Parse header and return tuple (report date,

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
               raise exc.CsvParseException('Line {idx{ should start with "#"'.format(idx=line_index))

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

        report_id = None
        if any(ln.startswith(LANDING_PAGE_COL_NAME) for ln in lines):
            report_id = LANDING_PAGE_COL_NAME
        elif any(ln.startswith(KEYWORD_COL_NAME) for ln in lines):
            report_id = KEYWORD_COL_NAME

        if not report_id:
            raise exc.EmptyReportException(
                'Header Check: There should be a line starting with "Landing Page" or "Keyword"')

        return date, report_id

    def parse(self):
        self._parse(self.csv_report_text)

    def _parse(self, csv_report_text):
        report_date, report_id = self._parse_header(self._extract_header_lines(csv_report_text))
        self.report_id = report_id
        self.start_date = report_date

        f_body, f_footer = self._extract_body_and_footer(csv_report_text)
        reader = csv.DictReader(f_body)
        try:
            self.fieldnames = reader.fieldnames
            self.entries = []
            for entry in reader:
                url = entry[self.report_id]
                self.report_z1_codes[url] = self._parse_z11z_keyword(url)
                self.entries.append(entry)
        except:
            raise exc.CsvParseException('Could not parse CSV')

        if not set(self.fieldnames) >= set(REQUIRED_FIELDS):
            missing_fieldnames = list(set(REQUIRED_FIELDS) - (set(self.fieldnames) & set(REQUIRED_FIELDS)))
            raise exc.CsvParseException('Not all required fields are present. Missing: %s' % ','.join(missing_fieldnames))

        self._check_incomplete(f_footer)
        # self.report_log.state = constants.GAReportState.PARSED

    def _parse_z11z_keyword(self, url):
        result = self.z11z_pattern.match(url)
        if not result:
            return None, ''
        else:
            content_ad_id, source_param = result.group(1), result.group(2)

        content_ad = None
        try:
            content_ad_id = int(content_ad_id)
            content_ad = dash.api.get_content_ad(content_ad_id)
        except (ValueError, TypeError):
            pass

        if content_ad is None:
            return None, ''

        url = content_ad.url
        ad_group_id = content_ad.ad_group_id
        if ad_group_id is None or source_param == '':
            logger.warning(
                'Could not parse keyword %s. ad_group_id: %s, source_param: %s',
                keyword,
                self.ad_group_id,
                self.source_param
            )
            return None, ''
        return content_ad, source_param

    def _check_incomplete(self, footer):
        sessions_total = self._get_sessions_total(footer)
        sessions_sum = sum(int(entry['Sessions'].strip().replace(',', '')) for entry in self.entries)
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
        return raw_report_string.split('\n')[:10]

    def _extract_body_and_footer(self, raw_report_string):
        mainlines = []
        inside = False
        split_raw_report_string = raw_report_string.split('\n')
        for line in split_raw_report_string:
            if not inside and line.startswith(self.report_id):
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
        return True, []
        """
        media_source_not_specified = []
        for entry in self.entries:
            identifier = self.get_identifier_object(entry)
            if identifier.source_param == '':
                media_source_not_specified.append(identifier.id)

        return (len(media_source_not_specified) == 0, list(media_source_not_specified))
        """

    def is_ad_group_specified(self):
        return True, []
        """
        ad_group_not_specified = set()

        for entry in self.get_entries():
            identifier = self.get_identifier_object(entry)
            if identifier.ad_group_id is None:
                ad_group_not_specified.add(identifier.id)

        return (len(ad_group_not_specified) == 0, list(ad_group_not_specified))
        """
