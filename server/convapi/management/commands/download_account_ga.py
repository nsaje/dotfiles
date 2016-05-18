import sys
import logging
import os
import os.path
import json

from optparse import make_option

from django.core.management.base import BaseCommand

from dash.models import Account, GAAnalyticsAccount

from utils.command_helpers import ExceptionCommand

from convapi import ga_api

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '-a', '--accounts',
            help='comma separated list of accounts',
            dest='accounts_csv',
        ),
        make_option(
            '-d', '--date',
            help='date for which to download GA. format YYYY-MM-DD',
            dest='date',
        ),
        make_option(
            '-o', '--outdir',
            help='output directory',
            dest='outdir',
        ),
    )

    def handle(self, *args, **options):
        account_ids = []
        dt = None
        outdir = None

        try:
            accounts_csv = options['accounts_csv']
            account_ids = [int(a.strip()) for a in accounts_csv.split(',')]
            dt = options['date']
            outdir = options['outdir']
        except:
            logger.exception('failed parsing command line arguments')
            sys.exit(1)

        ga_accounts = GAAnalyticsAccount.objects.filter(account__in=account_ids)

        ga_service = ga_api.get_ga_service()

        for ga_account in ga_accounts:
            # get GA profiles
            profiles = ga_service.management().profiles().list(
                accountId=ga_account.ga_account_id,
                webPropertyId=ga_account.ga_web_property_id,
            ).execute()
            profile_id = profiles['items'][0]['id']

            rows = []
            start_index = 1
            has_more = True
            while has_more:
                ga_stats = ga_service.data().ga().get(
                    ids='ga:' + profile_id,
                    start_date=dt,
                    end_date=dt,
                    metrics='ga:sessions,ga:newUsers,ga:bounceRate,ga:pageviews,ga:timeonsite',
                    dimensions='ga:landingPagePath,ga:keyword',
                    filters='ga:landingPagePath=@_z1_,ga:keyword=~.*z1[0-9]+[a-zA-Z].+?1z.*',
                    start_index=start_index,
                ).execute()

                if ga_stats is None:
                    logger.debug('No postclick data was found')
                    break

                if ga_stats.get("containsSampledData"):
                    logger.warning(
                        "Google API returned sampled data. Date: %s, profile id: %s",
                        dt,
                        profile_id
                    )
                rows.extend(ga_stats.get('rows', []))
                start_index += ga_stats['itemsPerPage']
                has_more = (start_index < ga_stats['totalResults'])


            json.dump(
                rows, 
                open(os.path.join(outdir, '%s_%s.json' % (ga_account.account.id, ga_account.id)), 'w')
            )




