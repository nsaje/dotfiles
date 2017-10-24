import unicodecsv as csv
import datetime
import uuid

import redshiftapi.db
import utils.command_helpers
import dash.models
import prodops.helpers as hlp

PUBS_PER_CHUNK = 1000
QUERY = """SELECT DISTINCT publisher, source_id
FROM mv_master_pubs
WHERE date >= '{date}' AND publisher IN ({publist})"""


def chunks(l, n):
    n = max(1, n)
    return (l[i:i + n] for i in xrange(0, len(l), n))


class Command(utils.command_helpers.ExceptionCommand):
    help = "Match publishers with media sources"

    def add_arguments(self, parser):
        parser.add_argument('--days', '-d', dest='days', default=30,
                            help='Days in the past to look (default: 30)')
        parser.add_argument('--source-names', '-n', dest='use_source_names', default=False, action='store_true',
                            help='Use source names instead of slugs')
        parser.add_argument('publishers_csv', type=str)

    def _print(self, msg):
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        self.from_date = datetime.date.today() - datetime.timedelta(options['days'])
        self.use_source_names = options['use_source_names']
        self.sources = {s.pk: s for s in dash.models.Source.objects.all()}

        publishers = []
        pubs_source_match = set()
        with open(options['publishers_csv']) as fd:
            for row in csv.reader(fd):
                if row[0].lower() in ('domains', 'publishers', 'domain', 'publisher'):
                    continue
                pub = row[0]
                publishers.append(pub)
                source = row[1] if len(row) > 1 else None
                pubs_source_match.add((pub, source))

        data = []
        pubs_len = float(len(publishers))
        for i, pub_sublist in enumerate(chunks(publishers, PUBS_PER_CHUNK)):
            self._print('Processing batch {}/{}'.format(i + 1, int(pubs_len / PUBS_PER_CHUNK) + 1))
            data.extend(self._match_sources(pub_sublist))

        self._print('Report generated.')

        self._print('Publisher matches: {}%'.format(round(float(len(data)) / len(publishers) * 100, 2)))

        count_source_matches = 0
        for pub, sources in data:
            for source in sources.split(','):
                if (pub, source) in pubs_source_match:
                    count_source_matches += 1
        self._print('Publisher/Source matches: {}%'.format(round(float(count_source_matches) / len(publishers) * 100, 2)))

        self._print('Report URL: ' + hlp.generate_report(
            'publisher-sources-map-' + uuid.uuid4().hex,
            [('publisher', 'media source', )] + data)
        )

    def _match_sources(self, publishers):
        pub_source_map = {}
        with redshiftapi.db.get_stats_cursor() as c:
            c.execute(QUERY.format(date=self.from_date, publist=', '.join(
                ['\'{}\''.format(pub) for pub in publishers]
            )))
            for row in c.fetchall():
                source = self.sources.get(row[1])
                pub_source_map.setdefault(row[0], set()).add(
                    source.name if self.use_source_names else source.bidder_slug)

        return [
            (pub, ', '.join(sources)) for pub, sources in pub_source_map.iteritems()
        ]
