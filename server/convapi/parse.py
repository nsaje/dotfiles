import datetime
import operator
import exc
import re
import csv
import StringIO
import urlparse
import urllib

class CsvReport(object):
    
    REQUIRED_FIELDS = [
        'Landing Page',
        'Device Category',
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
        
        self._parse()
        
    def get_fieldnames(self):
        return self.fieldnames
        
    def get_entries(self):
        return self.entries
        
    def get_date(self):
        return self.date
        
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
        if not self.lines[1].startswith('# All Web Site Data'):
            raise exc.CsvParseException('Second line should start with "# All Website Data"')
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
            
            
class LandingPageUrl(object):
    
    def __init__(self, raw_url):
        self.raw_url = raw_url
        self.clean_url = None
        self.ad_group_id = None
        self.source_param = None
        
        self._parse()
        
        if self.clean_url is None or self.ad_group_id is None or self.source_param is None:
            raise exc.LandingPageUrlParseError('Failed to parse landing page url. _z1_adgid and _z1_msid should be specified')
        
    def _parse(self):
        split_url = list(urlparse.urlsplit(self.raw_url))
        
        query_params = dict(urlparse.parse_qsl(split_url[3], keep_blank_values=True))
        
        if '_z1_adgid' in query_params:
            self.ad_group_id = int(query_params['_z1_adgid'])
        if '_z1_msid' in query_params:
            self.source_param = query_params['_z1_msid']
            
        clean_query_params = {k:v for k,v in query_params.items() if not k.startswith('_z1_') and not k.startswith('utm_')}
        
        split_url[3] = urllib.urlencode(sorted(clean_query_params.items(), key=lambda x: x[0]))
        
        self.clean_url = urlparse.urlunsplit(split_url)
        