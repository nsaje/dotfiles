import datetime
import logging

from utils.command_helpers import ExceptionCommand

from etl import refresh_k1
import redshiftapi.db
from core.entity.account import Account

logger = logging.getLogger(__name__)
NUM_OF_BATCHES = 4


class Command(ExceptionCommand):

    help = "Rematerialize agency stats per batch"

    def add_arguments(self, parser):
        parser.add_argument('agency_id', type=int)
        parser.add_argument('batch', type=int,
                            help='Batch number - out of {} batches'.format(NUM_OF_BATCHES))
        parser.add_argument('min_date', type=str)

    def handle(self, *args, **options):
        since = datetime.datetime.strptime(options['min_date'], '%Y-%m-%d')
        batch = options['batch']
        accounts = Account.objects.filter(
            agency_id=options['agency_id']
        ).values_list('pk', flat=True)
        query = '''select account_id, min(date) from mv_account
        where cost_nano > 0 and account_id in ({})
        group by account_id;'''.format(', '.join(map(str, accounts)))
        account_since = {}

        with redshiftapi.db.get_stats_cursor() as cur:
            cur.execute(query)
            account_since = {
                account_id: max(
                    datetime.datetime.strptime(str(start_date), "%Y-%m-%d"),
                    since
                )
                for account_id, start_date in cur.fetchall()
            }
        if not account_since:
            return
        for acc_id, since in account_since.items():
            if (acc_id % NUM_OF_BATCHES) != batch:
                continue
            print("reprocessing", acc_id, "since", since)
            try:
                refresh_k1.refresh_k1_reports(since, acc_id,
                                              skip_vacuum=True, skip_analyze=True)
            except Exception as e:
                print("Exception:", e)
            finally:
                from django import db
                db.connections.close_all()
