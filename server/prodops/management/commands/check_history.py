import datetime

import utils.command_helpers

import dash.models
import dash.constants


class Command(utils.command_helpers.ExceptionCommand):
    help = "Check history"

    def add_arguments(self, parser):
        parser.add_argument("--agency", dest="agency", default=None, help="Agency ID")
        parser.add_argument(
            "--account", dest="account", default=None, help="Account ID"
        )
        parser.add_argument(
            "--campaign", dest="campaign", default=None, help="Campaign ID"
        )
        parser.add_argument(
            "--ad-group", dest="ad_group", default=None, help="Ad group ID"
        )
        parser.add_argument(
            "--start-date",
            "-s",
            dest="start_date",
            default=None,
            help="Start date (default: start of current month)",
        )
        parser.add_argument(
            "--end-date",
            "-e",
            dest="end_date",
            default=None,
            help="End date (excluded, default: today)",
        )
        parser.add_argument(
            "--search", dest="search", default=None, help="Search string in history"
        )
        parser.add_argument(
            "--action-type",
            dest="action_type",
            default=None,
            help="Specific action type. Types: "
            + ", ".join(
                "{} - {}".format(k, v)
                for k, v in dash.constants.HistoryActionType._get_all_kv_pairs()
            ),
        )

    def _print(self, msg):
        self.stdout.write("{}\n".format(msg))

    def handle(self, *args, **options):
        today = datetime.date.today()
        start_date = (
            options["start_date"]
            and datetime.datetime.strptime(options["start_date"], "%Y-%m-%d").date()
            or datetime.date(today.year, today.month, 1)
        )
        end_date = (
            options["end_date"]
            and datetime.datetime.strptime(options["end_date"], "%Y-%m-%d").date()
            or today
        )

        history = dash.models.History.objects.filter(
            created_dt__range=(
                datetime.datetime.combine(start_date, datetime.time.min),
                datetime.datetime.combine(end_date, datetime.time.max),
            )
        )
        if options.get("agency"):
            history = history.filter(agency_id=int(options.get("agency")))
        if options.get("account"):
            history = history.filter(account_id=int(options.get("account")))
        if options.get("campaign"):
            history = history.filter(campaign_id=int(options.get("campaign")))
        if options.get("ad_group"):
            history = history.filter(ad_group_id=int(options.get("ad_group")))
        if options.get("search"):
            history = history.filter(changes_text__icontains=options.get("search"))
        if options.get("action_type"):
            history = history.filter(action_type=int(options.get("action_type")))
        history = history.order_by("created_dt")

        grouped = {}
        for entry in history:
            grouped.setdefault(entry.action_type, []).append(entry)

        self._print("Summary: ")
        for action_type, entires in grouped.items():
            self._print(
                " - {}: {}".format(
                    dash.constants.HistoryActionType.get_text(action_type), len(entires)
                )
            )

        self._print("History: ")
        prev_agency, prev_account, prev_campaign, prev_ad_group = None, None, None, None
        for entry in history:
            if (
                prev_agency != entry.agency
                or prev_account != entry.account
                or prev_campaign != entry.campaign
                or prev_ad_group != entry.ad_group
            ):
                self._print(
                    " - {}, {}, {}, {},".format(
                        entry.agency or "/",
                        entry.account,
                        entry.campaign,
                        entry.ad_group,
                    )
                )
            self._print(
                "    - {} {} - {} ({}): {}".format(
                    entry.created_dt,
                    entry.created_by,
                    dash.constants.HistoryActionType.get_text(entry.action_type),
                    dash.constants.HistoryLevel.get_text(entry.level),
                    entry.changes_text,
                )
            )
            prev_agency, prev_account, prev_campaign, prev_ad_group = (
                entry.agency,
                entry.account,
                entry.campaign,
                entry.ad_group,
            )
