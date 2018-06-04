import datetime
import logging

from utils.command_helpers import ExceptionCommand

from etl import refresh_k1
import redshiftapi.db
from core.entity.account import Account

import utils.slack

logger = logging.getLogger(__name__)
NUM_OF_BATCHES = 4


class Command(ExceptionCommand):

    help = "Rematerialize agency stats per batch"

    def add_arguments(self, parser):
        parser.add_argument('agency_id', type=int)
        parser.add_argument('batch', type=int,
                            help='Batch number - out of {} batches'.format(NUM_OF_BATCHES))
        parser.add_argument('min_date', type=str)
        parser.add_argument('--skip-accounts', type=str, default='', dest='skip_accounts',
                            help='Comma separated account ids to skip')

    def handle(self, *args, **options):
        skip_accounts = set(map(int, (
            acc_id.strip() for acc_id in options.get('skip_accounts', '').split(',')
            if acc_id.strip()
        )))
        since = datetime.datetime.strptime(options['min_date'], '%Y-%m-%d')
        batch = options['batch']
        accounts = set(Account.objects.filter(
            agency_id=options['agency_id']
        ).values_list('pk', flat=True)) - skip_accounts
        query = '''select account_id, min(date) from mv_account
        where cost_nano > 0 and account_id in ({})
        group by account_id;'''.format(', '.join(map(str, accounts)))
        account_since = {}
        with redshiftapi.db.get_stats_cursor() as cur:
            cur.execute(query)
            account_since = {
                int(account_id): max(
                    datetime.datetime.strptime(str(start_date), "%Y-%m-%d"),
                    since
                )
                for account_id, start_date in cur.fetchall()
            }
        if not account_since:
            return
        n_accounts_processed, n_accounts_all = 0, len(accounts)
        for acc_id, since in account_since.items():
            if (acc_id % NUM_OF_BATCHES) != batch:
                continue
            utils.slack.publish(
                "batch {}: {}/{}".format(batch, n_accounts_processed+1, n_accounts_all),
                msg_type=utils.slack.MESSAGE_TYPE_INFO,
                username='Rematerialize'
            )
            print("reprocessing", acc_id, "since", since)
            try:
                refresh_k1.refresh_k1_reports(since, acc_id,
                                              skip_vacuum=True, skip_analyze=True)
            except Exception as e:
                print("Exception:", e)
            finally:
                from django import db
                db.connections.close_all()
            n_accounts_processed += 1
