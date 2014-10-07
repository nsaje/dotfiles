import datetime
import operator
import exc
import re
import csv
import StringIO
import logging

import utils.url

logger = logging.getLogger(__name__)


class IReport(object):

    def get_entries(self):
        raise NotImplementedError

    def get_fieldnames(self):
        raise NotImplementedError

    def get_date(self):
        raise NotImplementedError


class CsvReport(IReport):

    REQUIRED_FIELDS = [
        'Landing Page',
        'Sessions',
        '% New Sessions',
        'New Users',
        'Bounce Rate',
        'Pages / Session',
        'Avg. Session Duration',
    ]

    def __init__(self, raw):
        self.raw = raw
        self.lines = raw.split('\n')
        self.date = None
        self.fieldnames = None
        self.entries = None
        self.ad_group_set = None

        self._parse()

    def get_fieldnames(self):
        return self.fieldnames

    def get_entries(self):
        return self.entries

    def _get_entries_for_ad_group(self, ad_group_id):
        result = []
        for entry in self.get_entries():
            landing_page_url = LandingPageUrl(entry['Landing Page'])
            if landing_page_url.ad_group_id is not None and int(landing_page_url.ad_group_id) == ad_group_id:
                result.append(entry)
        return result

    def get_date(self):
        return self.date

    def get_content_type(self):
        return 'text/csv'

    def _get_ad_group_set(self):
        if self.ad_group_set is None:
            self.ad_group_set = set()
            for entry in self.get_entries():
                landing_page_url = LandingPageUrl(entry['Landing Page'])
                if landing_page_url.ad_group_id is not None:
                    self.ad_group_set.add(int(landing_page_url.ad_group_id))
        return self.ad_group_set

    def is_media_source_specified(self):
        for entry in self.get_entries():
            landing_page_url = LandingPageUrl(entry['Landing Page'])
            if landing_page_url.ad_group_id is None:
                return False
        return True

    def is_ad_group_specified(self):
        for entry in self.get_entries():
            landing_page_url = LandingPageUrl(entry['Landing Page'])
            if landing_page_url.source_param is None:
                return False
        return True

    def split_by_ad_group(self):
        ad_group_reports = []
        for ad_group_id in self._get_ad_group_set():
            ad_group_reports.append(AdGroupReport(
                ad_group_id=ad_group_id,
                date=self.get_date(),
                fieldnames=self.get_fieldnames(),
                entries=self._get_entries_for_ad_group(ad_group_id)
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
        if not self.lines[2].startswith('# Landing Pages'):
            raise exc.CsvParseException('Third line should start with "# Landing Pages"')
        if not self.lines[3].startswith('#'):
            raise exc.CsvParseException('Fourth line should start with "#"')
        if not self.lines[4].startswith('# -----'):
            raise exc.CsvParseException('Fifth line should start with "# -----"')
        if not reduce(operator.ior, [ln.startswith('Landing Page') for ln in self.lines], False):
            raise exc.CsvParseException('There should be a line starting with "Landing Page"')
        return True

    def _get_file_like_object(self):
        mainlines = []
        inside = False
        for line in self.lines:
            if not inside and line.startswith('Landing Page'):
                inside = True
            if inside:
                mainlines.append(line)
        return StringIO.StringIO('\n'.join(mainlines))

    def _parse(self):
        self._check_header()
        self._parse_date()

        reader = csv.DictReader(self._get_file_like_object())

        try:
            self.fieldnames = reader.fieldnames
            self.entries = []
            for entry in reader:
                if not entry['Landing Page'].strip():
                    break
                self.entries.append(entry)
        except:
            raise exc.CsvParseException('Could not parse CSV')

        if not set(self.fieldnames) >= set(CsvReport.REQUIRED_FIELDS):
            raise exc.CsvParseException('Not all required fields are present')


class AdGroupReport(IReport):

    def __init__(self, ad_group_id, date, fieldnames, entries):
        self._ad_group_id = ad_group_id
        self._date = date
        self._fieldnames = fieldnames
        self._entries = entries

    def get_ad_group_id(self):
        return self._ad_group_id

    def get_date(self):
        return self._date

    def get_fieldnames(self):
        return self._fieldnames

    def get_entries(self):
        return self._entries


class LandingPageUrl(object):

    def __init__(self, raw_url):
        self.raw_url = raw_url
        self.clean_url = None
        self.ad_group_id = None
        self.source_param = None

        self.z1_did = None
        self.z1_kid = None
        self.z1_tid = None

        self._parse()

        if self.ad_group_id is None or self.source_param is None:
            logger.error('Could not parse landing page url %s', raw_url)

    def _parse(self):
        self.clean_url, query_params = utils.url.clean_url(self.raw_url)

        if '_z1_adgid' in query_params:
            self.ad_group_id = int(query_params['_z1_adgid'])
        if '_z1_msid' in query_params:
            self.source_param = query_params['_z1_msid']
        if '_z1_did' in query_params:
            self.z1_did = query_params['_z1_did']
        if '_z1_kid' in query_params:
            self.z1_kid = query_params['_z1_kid']
        if '_z1_tid' in query_params:
            self.z1_tid = query_params['_z1_tid']
