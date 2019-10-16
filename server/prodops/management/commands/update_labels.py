import argparse

import unicodecsv
from django.core.management.base import CommandError

import structlog
from dash.models import ContentAd
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)


class Command(Z1Command):
    help = """Replaces Labels for a given account.

    Takes an id of the account and a .csv file of the following format:

    content ad id,new label
    1234,label
    ...

    """

    def add_arguments(self, parser):
        parser.add_argument("account_id", nargs=1, type=int)
        parser.add_argument("csv_file", nargs=1, type=argparse.FileType("r"))

    def handle(self, *args, **options):
        account_id = options["account_id"][0]
        csv_file = options["csv_file"][0]

        mapping = self.parse_csv(csv_file)

        self.replace(account_id, mapping)

        self.stdout.write("Done.")

    def parse_csv(self, csv_file):
        lines = unicodecsv.reader(csv_file)
        try:
            header = next(lines)
        except StopIteration:
            raise CommandError("Chosen file is empty.")

        if header[0].strip().lower() != "content ad id" or header[1].strip().lower() != "new label":
            raise CommandError(
                "Unrecognized column headers in chosen file " '(should be "Content Ad ID" and "New Label")'
            )

        mapping = {}
        for line in lines:
            mapping[int(line[0])] = line[1]

        return mapping

    def replace(self, account_id, mapping):
        content_ads = ContentAd.objects.filter(ad_group__campaign__account_id=account_id, pk__in=set(mapping.keys()))

        for i, content_ad in enumerate(content_ads):
            self.stdout.write(
                'Processing content ad {} of {} (label "{}" to "{}")'.format(
                    i + 1, len(content_ads), content_ad.label, mapping[content_ad.pk]
                )
            )
            content_ad.label = mapping[content_ad.pk]
            content_ad.save()
