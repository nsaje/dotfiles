import argparse
import unicodecsv

from django.core.management.base import CommandError

from utils.command_helpers import ExceptionCommand

import dash.constants
import dash.models
import dash.blacklist


ACTION_TO_BLACKLIST_STATUS = {
    'blacklist': dash.constants.PublisherStatus.BLACKLISTED,
    'enable': dash.constants.PublisherStatus.ENABLED
}


class Command(ExceptionCommand):
    help = """ Blacklists domains for a given ad group.

    Takes an id of the ad group, blacklist or whitelist action and a .csv file of the
    following format:

    Domains
    example.com
    ... """

    def add_arguments(self, parser):
        parser.add_argument('ad_group_id', nargs=1, type=int)
        parser.add_argument('status', nargs=1, type=str, choices=ACTION_TO_BLACKLIST_STATUS.keys(),
                            default='blacklist')
        parser.add_argument('csv_file', nargs=1, type=argparse.FileType('r'))

    def handle(self, *args, **options):
        ad_group_id = options['ad_group_id'][0]
        csv_file = options['csv_file'][0]

        ad_group = dash.models.AdGroup.objects.get(id=ad_group_id)
        domains = self.parse_csv(csv_file)

        status = ACTION_TO_BLACKLIST_STATUS[options['status'][0]]

        dash.blacklist.update(ad_group, {'ad_group': ad_group}, status, domains, all_sources=True)

    def parse_csv(self, csv_file):
        lines = unicodecsv.reader(csv_file)

        try:
            header = next(lines)
        except StopIteration:
            raise CommandError('Chosen file is empty.')

        if len(header) != 1 or header[0].strip().lower() != 'domains':
            raise CommandError(
                'Invalid header, should be a single column containing "Domains"'
            )

        return [line[0] for line in lines]

    def clean_domains(self, domains):
        clean_domains = []

        for domain in domains:
            clean_domain = domain

            if clean_domain.startswith("http://"):
                clean_domain = clean_domain[7:]
            if clean_domain.startswith("https://"):
                clean_domain = clean_domain[8:]
            if clean_domain.startswith("www."):
                clean_domain = clean_domain[4:]
            if clean_domain.endswith("/"):
                clean_domain = clean_domain[:-1]

            if clean_domain != domain:
                self.stdout.write(
                    "Changing {} to {}, accept by pressing enter, or enter a correction:".format(
                        domain,
                        clean_domain
                    )
                )
                response = raw_input()
                if len(response) > 0:
                    clean_domain = response

            clean_domains.append(clean_domain)

        return clean_domains
