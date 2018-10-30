import datetime
import logging

from django.core.management.base import CommandError
from django.db.models import Count

from dash.constants import SourceType
from dash.models import Account
from dash.models import AdGroup
from dash.models import AdGroupSource
from dash.models import OutbrainAccount
from dash.models import Source
from redshiftapi import db
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)
OB = Source.objects.get(source_type__type=SourceType.OUTBRAIN)
QUERY = """
SELECT account_id, SUM(impressions)
FROM mv_master
WHERE account_id in ({}) AND source_id = {}
GROUP BY account_id;
"""
ARCHIVED_AT_LEAST_DAYS = 30
MAX_AD_GROUP_COUNT_LIMIT = 50


class Command(ExceptionCommand):
    help = """Release OB accounts on account list"""

    def add_arguments(self, parser):
        parser.add_argument("accounts", nargs="?", help="Comma separated list of account ids.")
        parser.add_argument("--dry-run", action="store_true", dest="is_dry_run", default=False, help="Dry run command")

    def _validate_account_ids(self, account_ids, filter_only=False):
        account_ids = list(account_ids)
        with db.get_stats_cursor() as c:
            c.execute(QUERY.format(",".join(map(str, account_ids)), OB.pk))
            data = dict(c.fetchall())
        adgroup_counts = {
            obj["campaign__account_id"]: obj["total"]
            for obj in AdGroup.objects.all()
            .values("campaign__account_id")
            .annotate(total=Count("id"))
            .order_by("-total")
        }
        invalid_account_ids = [
            acc_id for acc_id in account_ids if adgroup_counts.get(acc_id, 0) > MAX_AD_GROUP_COUNT_LIMIT
        ]
        if not filter_only and invalid_account_ids:
            raise CommandError(
                "Some accounts have too many ad groups: " + ", ".join(str(acc_id) for acc_id in invalid_account_ids)
            )
        account_ids = list(set(account_ids) - set(invalid_account_ids))
        if data:
            if filter_only:
                return [acc_id for acc_id in account_ids if acc_id not in data]
            raise CommandError(
                "Some accounts have impressions in RS: {}".format(
                    ", ".join(["account {} - {}".format(acc_id, spend) for acc_id, spend in data.items()])
                )
            )
        return account_ids

    def _get_unused_archived_accounts_ids(self):
        youngest_change_date = datetime.datetime.now() - datetime.timedelta(ARCHIVED_AT_LEAST_DAYS)
        candidates = set(
            acc.pk
            for acc in Account.objects.filter(outbrain_marketer_id__isnull=False).exclude(outbrain_marketer_id="")
            if acc.adgroupsettings_set.all().count() and acc.get_current_settings().created_dt < youngest_change_date
        )
        unarchived_accounts = set(acc.pk for acc in Account.objects.all().exclude_archived())
        accounts_with_spend = set(acc.pk for acc in Account.objects.all().filter_with_spend())

        return self._validate_account_ids(candidates - accounts_with_spend - unarchived_accounts, filter_only=True)

    def _release_accounts(self, account_ids):
        class Request:
            class User:
                pass

        marketer_ids = []
        count_released = 0
        for account_id in account_ids:
            account = Account.objects.get(pk=account_id)
            ad_group_sources = AdGroupSource.objects.filter(source=OB, ad_group__campaign__account=account)
            if not account.outbrain_marketer_id:
                self.stdout.write("Missing marketer id for account {} {}".format(account.pk, account.name))
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

            request = Request()
            request.user = Request.User()
            request.user.is_anonymous = True
            account.save(request)
        return count_released, marketer_ids

    def handle(self, *args, **options):
        is_dry_run = options.get("is_dry_run")
        account_ids = (
            self._validate_account_ids(int(acc.strip()) for acc in options["accounts"].split(","))
            if options.get("accounts")
            else self._get_unused_archived_accounts_ids()
        )
        self.stdout.write("Cleaning accounts: " + ", ".join(map(str, account_ids)))

        count_released, marketer_ids = 0, []
        if not is_dry_run:
            count_released, marketer_ids = self._release_accounts(account_ids)

        self.stdout.write("Done. Released {} OB accounts.".format(count_released))
        self.stdout.write("Marketers: {}".format(", ".join([str(mid) for mid in marketer_ids])))
