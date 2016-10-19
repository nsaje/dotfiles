import logging

from django.core.management.base import CommandError

from utils.command_helpers import ExceptionCommand
from dash.models import Account, AdGroupSource, Source, OutbrainAccount
from dash.constants import SourceType

from redshiftapi import db

logger = logging.getLogger(__name__)
OB = Source.objects.get(source_type__type=SourceType.OUTBRAIN)
QUERY = '''
SELECT account_id, SUM(cost_nano::decimal)/1000000000
FROM mv_master where account_id in ({})
GROUP BY account_id;
'''


class Command(ExceptionCommand):
    help = """Release OB accounts on account list"""

    def add_arguments(self, parser):
        parser.add_argument('accounts', nargs=1, help='Comma separated list of account ids.')

    def handle(self, *args, **options):
        account_ids = [
            int(acc.strip()) for acc in options['accounts'][0].split(',')
        ]

        with db.get_stats_cursor() as c:
            c.execute(QUERY.format(','.join([str(pk) for pk in account_ids])))
            data = c.fetchall()
        if data:
            raise CommandError('Some accounts have spend in RS: {}'.format(
                ', '.join([
                    'account {} spent ${}'.format(acc_id, spend) for acc_id, spend in data
                ])
            ))

        marketer_ids = []
        count_released = 0
        for account_id in account_ids:
            account = Account.objects.get(pk=account_id)
            ad_group_sources = AdGroupSource.objects.filter(source=OB,
                                                            ad_group__campaign__account=account)
            if not account.outbrain_marketer_id:
                continue
            for ags in ad_group_sources:
                ags.source_credentials = None
                ags.source_campaign_key = {}
                ags.save()
            marketer_ids.append(account.outbrain_marketer_id)
            ob_accounts = OutbrainAccount.objects.filter(marketer_id=account.outbrain_marketer_id)
            for ob_account in ob_accounts:
                ob_account.used = False
                ob_account.save()

            account.outbrain_marketer_id = None
            count_released += 1
            account.save()

        self.stdout.write('Done. Released {} OB accounts.'.format(count_released))
        self.stdout.write('Marketers: {}'.format(', '.join([
            str(mid) for mid in marketer_ids
        ])))
