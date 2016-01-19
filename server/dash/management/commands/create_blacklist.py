import argparse
import unicodecsv

from sets import Set

from django.core.management.base import CommandError
from django.db import transaction

from utils.command_helpers import ExceptionCommand

from actionlog import zwei_actions

from dash import api
from dash.constants import PublisherStatus
from dash.constants import PublisherBlacklistLevel
from dash.constants import SourceType
from dash.models import AdGroup
from dash.models import AdGroupSource


UNSUPPORTED_SOURCES = [SourceType.GRAVITY, SourceType.OUTBRAIN, SourceType.YAHOO]


class Command(ExceptionCommand):
    """ Blacklists domains for a given ad group.

    Takes an id of the ad group and a .csv file of the following format:

    Domains
    example.com
    ... """

    def add_arguments(self, parser):
        parser.add_argument('ad_group_id', nargs=1, type=int)
        parser.add_argument('csv_file', nargs=1, type=argparse.FileType('r'))

    def handle(self, *args, **options):
        ad_group_id = options['ad_group_id'][0]
        csv_file = options['csv_file'][0]

        ad_group = AdGroup.objects.get(id=ad_group_id)
        domains = self.parse_csv(csv_file)

        actionlogs = self.create_actionlogs_for_domains(ad_group, domains)

        zwei_actions.send(actionlogs)

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

    def create_actionlogs_for_domains(self, ad_group, domains):
        domains = self.clean_domains(domains)
        sources = self.get_sources(ad_group)
        blacklist = self.combine(ad_group, domains, sources)
        actionlogs = self.create_actionlogs_for_blacklist(ad_group, blacklist)

        return actionlogs

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
                print("Changing {} to {}, accept by pressing enter, or enter a correction:".format(domain,
                                                                                                   clean_domain))

                response = raw_input()

                if len(response) > 0:
                    clean_domain = response

            clean_domains.append(clean_domain)

        return clean_domains

    def get_sources(self, ad_group):
        ad_group_sources = AdGroupSource.objects.filter(ad_group=ad_group)
        sources = [ad_group_source.source
                   for ad_group_source in ad_group_sources
                   if ad_group_source.source.source_type.type not in UNSUPPORTED_SOURCES]

        return Set(sources)

    def combine(self, ad_group, domains, sources):
        combination = []

        for domain in domains:
            for source in sources:
                combination.append({'ad_group_id': ad_group.id, 'domain': domain, 'source': source})

        return combination

    def create_actionlogs_for_blacklist(self, ad_group, blacklist):
        actionlogs = []

        with transaction.atomic():
            actionlogs.extend(
                api.create_publisher_blacklist_actions(
                    ad_group,
                    PublisherStatus.BLACKLISTED,
                    PublisherBlacklistLevel.ADGROUP,
                    blacklist,
                    None,
                    send=False
                )
            )

        return actionlogs
