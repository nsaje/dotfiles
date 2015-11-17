import logging
import unicodecsv
import argparse

from django.core.management.base import BaseCommand, CommandError

from dash.models import ContentAd

from utils.redirector_helper import update_redirect

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('ad_group_id', nargs=1, type=int)
        parser.add_argument('csv_file', nargs=1, type=argparse.FileType('r'))

    def handle(self, *args, **options):
        ad_group_id = options['ad_group_id'][0]
        csv_file = options['csv_file'][0]

        mapping = self.parse_csv(csv_file)

        self.replace(ad_group_id, mapping)

        self.stdout.write('Done.')

    def parse_csv(self, csv_file):
        lines = unicodecsv.reader(csv_file)
        try:
            header = next(lines)
        except StopIteration:
            raise CommandError('Chosen file is empty.')

        if header[0].strip().lower() != 'old url' or header[1].strip().lower() != 'new url':
            raise CommandError(
                'Unrecognized column headers in chosen file '
                '(should be "Old URL" and "New URL")'
            )

        mapping = {}
        for line in lines:
            mapping[line[0]] = line[1]

        return mapping

    def replace(self, ad_group_id, mapping):
        content_ads = ContentAd.objects.filter(ad_group_id=ad_group_id)

        for i, content_ad in enumerate(content_ads):
            if content_ad.url not in mapping:
                continue

            content_ad.url = mapping[content_ad.url]
            content_ad.save()

            update_redirect(content_ad.url, content_ad.redirect_id)

            self.stdout.write(
                'Processed {} of {} content_ads'.format(i + 1, len(content_ads)))
