import unicodecsv as csv
import datetime
import re

import utils.command_helpers
import prodops.audience_report
import prodops.helpers


class Command(utils.command_helpers.ExceptionCommand):
    help = "Create inventory report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--where", dest="where", default=None, help="Additional WHERE clause"
        )
        parser.add_argument(
            "--daily", dest="monthly", action="store_true", help="Average daily"
        )
        parser.add_argument(
            "--blacklisted",
            dest="blacklisted",
            action="store_true",
            help="Blacklisted impressions",
        )
        parser.add_argument(
            "--days",
            dest="days",
            default=30,
            type=int,
            help="Days in past to check (default last 30)",
        )
        parser.add_argument("--breakdown", dest="breakdown", type=str, default="")
        parser.add_argument("name", type=str)
        parser.add_argument("publishers_csv", type=str)

    def handle(self, *args, **options):
        publishers = set()
        with open(options["publishers_csv"]) as fd:
            reg = re.compile(r"https?://")
            for row in csv.reader(fd):
                if row[0].lower() in ("domains", "publishers", "domain", "publisher"):
                    continue
                pub = reg.sub("", row[0]).strip("/")
                publishers.add(pub)
                if pub.startswith("www."):
                    publishers.add(pub[4:])

        end_date = datetime.date.today() - datetime.timedelta(1)
        start_date = datetime.date.today() - datetime.timedelta(options["days"])
        where = ""
        if options.get("where"):
            where = " AND " + options.get("where")

        query = (
            "SELECT exchange{breakdown}, SUM(bid_reqs){monthly} AS impressions FROM supply_stats "
            "WHERE date >= '{sdate}' AND date <= '{edate}' AND blacklisted = {bl}{pubs}{where} "
            "GROUP BY exchange{breakdown} ORDER BY impressions DESC"
        ).format(
            monthly="/{}".format(float(options["days"]))
            if options.get("monthly")
            else "",
            sdate=start_date,
            edate=end_date,
            bl=1 if options["blacklisted"] else 0,
            pubs=(
                " AND publisher IN ("
                + ", ".join("'{}'".format(pub) for pub in publishers)
                + ")"
            )
            if publishers
            else "",
            where=where,
            breakdown=(", " + options["breakdown"]) if options["breakdown"] else "",
        )
        self.stdout.write("Query: \n {}\n\n".format(query))
        self.stdout.write(
            "Report: {}\n".format(
                prodops.helpers.generate_report_from_query(options["name"], query)
            )
        )
