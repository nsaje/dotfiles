import datetime

import structlog

import redshiftapi.db
import utils.slack
from core.models.account import Account
from etl import refresh
from utils.command_helpers import Z1Command

logger = structlog.get_logger(__name__)
NUM_OF_BATCHES = 4


class Command(Z1Command):

    help = "Rematerialize agency stats per batch"

    def add_arguments(self, parser):
        parser.add_argument("agency_id", type=int)
        parser.add_argument("batch", type=int, help="Batch number - out of {} batches".format(NUM_OF_BATCHES))
        parser.add_argument("min_date", type=str)
        parser.add_argument("batch_size", type=int)
        parser.add_argument(
            "--skip-accounts", type=str, default="", dest="skip_accounts", help="Comma separated account ids to skip"
        )

    def handle(self, *args, **options):
        skip_accounts = set(
            map(int, (acc_id.strip() for acc_id in options.get("skip_accounts", "").split(",") if acc_id.strip()))
        )
        since = datetime.datetime.strptime(options["min_date"], "%Y-%m-%d")
        batch = options["batch"]
        num_of_batches = options["batch_size"] or NUM_OF_BATCHES
        accounts = (
            set(Account.objects.filter(agency_id=options["agency_id"]).values_list("pk", flat=True)) - skip_accounts
        )
        query = """select account_id, min(date) from mv_account
        where date >= '{}' and cost_nano > 0 and account_id in ({})
        group by account_id;""".format(
            options["min_date"], ", ".join(map(str, accounts))
        )
        account_since = {}
        with redshiftapi.db.get_stats_cursor() as cur:
            cur.execute(query)
            account_since = {
                int(account_id): max(datetime.datetime.strptime(str(start_date), "%Y-%m-%d"), since)
                for account_id, start_date in cur.fetchall()
            }
        if not account_since:
            return
        n_accounts_processed, n_accounts_all = (
            0,
            len([acc_id for acc_id in account_since.keys() if (acc_id % num_of_batches) == batch]),
        )
        for acc_id, since in account_since.items():
            if (acc_id % num_of_batches) != batch:
                continue
            utils.slack.publish(
                "batch {}: {}/{}".format(batch, n_accounts_processed + 1, n_accounts_all),
                msg_type=utils.slack.MESSAGE_TYPE_INFO,
                username=utils.slack.USER_ETL_MATERIALIZE,
            )
            print("reprocessing", acc_id, "since", since)
            try:
                refresh.refresh(since, acc_id)
            except Exception as e:
                print("Exception:", e)
            finally:
                from django import db

                db.connections.close_all()
            n_accounts_processed += 1
