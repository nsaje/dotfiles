import datetime
import exc
import re
import csv
import StringIO
import logging

from utils import url_helper

from convapi import constants
import dash.api

logger = logging.getLogger(__name__)

LANDING_PAGE_COL_NAME = 'Landing Page'
KEYWORD_COL_NAME = 'Keyword'


class IReport(object):

    def get_identifier_object(self, entry):
        if self.first_col == LANDING_PAGE_COL_NAME:
            return LandingPageUrl(entry[LANDING_PAGE_COL_NAME])

        elif self.first_col == KEYWORD_COL_NAME:
            return Keyword(entry[KEYWORD_COL_NAME])

        raise Exception('Invalid first column name')

    def get_entries(self):
        raise NotImplementedError

    def get_fieldnames(self):
        raise NotImplementedError

    def get_date(self):
        raise NotImplementedError


class CsvReport(IReport):

    REQUIRED_FIELDS = [
        'Sessions',
        '% New Sessions',
        'New Users',
        'Bounce Rate',
        'Pages / Session',
        'Avg. Session Duration',
    ]

    def __init__(self, raw, report_log):
        self.raw = raw
        self.lines = raw.split('\n')
        self.date = None
        self.fieldnames = None
        self.entries = None
        self.ad_group_set = None
        self.report_log = report_log
        self.first_col = None

        self._parse()

    def get_fieldnames(self):
        return self.fieldnames

    def get_entries(self):
        return self.entries

    def _get_entries_for_ad_group(self, ad_group_id):
        result = []
        for entry in self.get_entries():
            identifier = self.get_identifier_object(entry)
            if identifier.ad_group_id is not None and int(identifier.ad_group_id) == ad_group_id:
                result.append(entry)
        return result

    def get_date(self):
        return self.date

    def get_content_type(self):
        return 'text/csv'

    def _get_ad_group_set(self):
        if self.ad_group_set is None:
            self.ad_group_set = set([])
            for entry in self.get_entries():
                identifier = self.get_identifier_object(entry)
                if identifier.ad_group_id is not None:
                    self.ad_group_set.add(int(identifier.ad_group_id))

        return self.ad_group_set

    def is_media_source_specified(self):
        media_source_not_specified = []

        for entry in self.get_entries():
            identifier = self.get_identifier_object(entry)
            if identifier.source_param == '':
                media_source_not_specified.append(identifier.id)

        return (len(media_source_not_specified) == 0, list(media_source_not_specified))

    def is_ad_group_specified(self):
        ad_group_not_specified = set()

        for entry in self.get_entries():
            identifier = self.get_identifier_object(entry)
            if identifier.ad_group_id is None:
                ad_group_not_specified.add(identifier.id)

        return (len(ad_group_not_specified) == 0, list(ad_group_not_specified))

    def split_by_ad_group(self):
        ad_group_reports = []
        for ad_group_id in self._get_ad_group_set():
            ad_group_reports.append(AdGroupReport(
                ad_group_id=ad_group_id,
                date=self.get_date(),
                fieldnames=self.get_fieldnames(),
                entries=self._get_entries_for_ad_group(ad_group_id),
                first_col=self.first_col
            ))
        return ad_group_reports

    def _parse_date(self):
        dateline = self.lines[3]
        m = re.search(r'(?P<start_date>[0-9]{8})-(?P<end_date>[0-9]{8})', dateline)
        if m is None:
            raise exc.CsvParseException('Date of the report could not be parsed')
        group_dict = m.groupdict()
        if 'start_date' not in group_dict or 'end_date' not in group_dict:
            raise exc.CsvParseException('Both, start date and end date, should be specified')
        if group_dict['start_date'] != group_dict['end_date']:
            raise exc.CsvParseException('start date and end date should be identical')
        datestr = group_dict['start_date']
        self.date = datetime.date(int(datestr[:4]), int(datestr[4:6]), int(datestr[6:]))

    def _check_header(self):
        if len(self.lines) < 5:
            raise exc.CsvParseException('Too few lines.')
        if not self.lines[0].startswith('# -----'):
            raise exc.CsvParseException('First line should start with "# -----"')
        if not self.lines[2].startswith('#'):
            raise exc.CsvParseException('Third line should start with "#"')
        if not self.lines[3].startswith('#'):
            raise exc.CsvParseException('Fourth line should start with "#"')
        self._parse_date()
        self.report_log.for_date = self.get_date()
        if not self.lines[4].startswith('# -----'):
            raise exc.CsvParseException('Fifth line should start with "# -----"')

        if any(ln.startswith(LANDING_PAGE_COL_NAME) for ln in self.lines):
            self.first_col = LANDING_PAGE_COL_NAME
        elif any(ln.startswith(KEYWORD_COL_NAME) for ln in self.lines):
            self.first_col = KEYWORD_COL_NAME

        if not self.first_col:
            raise exc.EmptyReportException(
                'Header Check: There should be a line starting with "Landing Page" or "Keyword"')

        return True

    def _get_file_like_object(self):
        mainlines = []
        inside = False
        for line in self.lines:
            if not inside and line.startswith(self.first_col):
                inside = True
            if inside:
                # There are instances of CSV files, that have 'Pages/Session' instead of 'Pages / Session'
                if 'Pages/Session' in line:
                    line = line.replace('Pages/Session', 'Pages / Session')
                mainlines.append(line)
        return StringIO.StringIO('\n'.join(mainlines))

    def _parse(self):
        self._check_header()

        reader = csv.DictReader(self._get_file_like_object())

        try:
            self.fieldnames = reader.fieldnames
            self.entries = []
            for entry in reader:
                if not entry[self.first_col].strip() or entry[self.first_col] in ('Day Index', 'Hour Index'):
                    break
                self.entries.append(entry)
        except:
            raise exc.CsvParseException('Could not parse CSV')

        if not set(self.fieldnames) >= set(CsvReport.REQUIRED_FIELDS):
            missing_fieldnames = list(set(CsvReport.REQUIRED_FIELDS) - (set(self.fieldnames) & set(CsvReport.REQUIRED_FIELDS)))
            raise exc.CsvParseException('Not all required fields are present. Missing: %s' % ','.join(missing_fieldnames))

        self._check_incomplete()

        self.report_log.state = constants.ReportState.PARSED

    def _check_incomplete(self):
        sessions_total = self._get_sessions_total()
        sessions_sum = sum(int(entry['Sessions'].strip().replace(',', '')) for entry in self.entries)

        # compromise for Omniture reports which regularly contain a difference
        # between session totals and sums of session entries
        acceptable_deviation = False
        if sessions_sum >= sessions_total:
            deviation = abs(float(sessions_total) - float(sessions_sum)) / float(sessions_total)
            if deviation <= 0.03:
                acceptable_deviation = True

        if sessions_total != sessions_sum and not acceptable_deviation:
            raise exc.IncompleteReportException(
                'Number of total sessions ({}) is not equal to sum of session counts ({})'.format(
                    sessions_total, sessions_sum)
            )

    def _get_sessions_total(self):
        index_lines = []
        inside = False

        day_index = False
        hour_index = False

        for line in self.lines:
            if not inside and line.startswith('Day Index'):
                inside = True
                day_index = True
            if not inside and line.startswith('Hour Index'):
                inside = True
                hour_index = True
            if inside:
                index_lines.append(line)

        reader = csv.DictReader(StringIO.StringIO('\n'.join(index_lines)))
        try:
            if day_index:
                return int(reader.next()['Sessions'].strip().replace(',', ''))
            if hour_index:
                for row in reader:
                    if row and row['Hour Index'] == '':
                        sessions_raw = row['Sessions']
                        return int(sessions_raw.strip().replace(',', ''))
        except:
            raise exc.CsvParseException('Could not parse total sessions')

        raise exc.CsvParseException('Could not parse total sessions')


class AdGroupReport(IReport):

    def __init__(self, ad_group_id, date, fieldnames, entries, first_col):
        self._ad_group_id = ad_group_id
        self._date = date
        self._fieldnames = fieldnames
        self._entries = entries
        self.first_col = first_col

    def get_ad_group_id(self):
        return self._ad_group_id

    def get_date(self):
        return self._date

    def get_fieldnames(self):
        return self._fieldnames

    def get_entries(self):
        return self._entries


class IdentifierBase():
    def __init__(self, id_string):
        self.id = id_string
        self.url = None
        self.ad_group_id = None
        self.source_param = ''

        self._parse(id_string)

    def _parse(self, id_string):
        raise NotImplementedError


class Keyword(IdentifierBase):
    def _parse(self, keyword):
        content_ad_id, self.source_param = self._parse_keyword(keyword)

        content_ad = None
        try:
            content_ad_id = int(content_ad_id)
            content_ad = dash.api.get_content_ad(content_ad_id)
        except (ValueError, TypeError):
            pass

        if content_ad is None:
            return

        self.url = content_ad.url
        self.ad_group_id = content_ad.ad_group_id

        if self.ad_group_id is None or self.source_param == '':
            logger.warning(
                'Could not parse keyword %s. ad_group_id: %s, source_param: %s',
                keyword,
                self.ad_group_id,
                self.source_param
            )

    def _parse_keyword(self, keyword):
        pattern = re.compile('.*z1([0-9]*)(.*)1z.*')
        result = pattern.match(keyword)

        if not result:
            return None, ''

        return result.group(1), result.group(2)


class LandingPageUrl(IdentifierBase):
    def _parse(self, raw_url):
        self.url, query_params = url_helper.clean_url(raw_url)

        # parse ad group id
        try:
            if '_z1_adgid' in query_params:
                self.ad_group_id = int(query_params['_z1_adgid'])
            elif '_z1_agid' in query_params:
                self.ad_group_id = int(query_params['_z1_agid'])
        except ValueError:
            pass

        if '_z1_msid' in query_params:
            self.source_param = query_params['_z1_msid']

        if self.ad_group_id is None or self.source_param == '':
            logger.warning(
                'Could not parse landing page url %s. ad_group_id: %s, source_param: %s',
                raw_url,
                self.ad_group_id,
                self.source_param
            )
