import csv

import utils.command_helpers
import redshiftapi.db

MANDATORY_COLUMNS = {"account_id", "campaign_id", "ad_group_id", "content_ad_id", "source_id", "publisher"}


class Command(utils.command_helpers.ExceptionCommand):
    help = "Apply diff for mv_master"

    def add_arguments(self, parser):
        parser.add_argument("csv", type=str)

    def handle(self, *args, **options):
        header, data = [], []
        with open(options["csv"]) as fd:
            reader = csv.reader(fd)
            for i, row in enumerate(reader):
                if i == 0:
                    header = row
                else:
                    data.append(row)
        missing = MANDATORY_COLUMNS - set(header)
        if missing:
            raise Exception("Missing columns: {}".format(", ".join(missing)))
        query = "INSERT INTO mv_master_diff ({columns}) VALUES {values};".format(
            columns=", ".join(header),
            values=", ".join(["({})".format(", ".join("'{}'".format(cell) for cell in row)) for row in data]),
        )
        with redshiftapi.db.get_write_stats_cursor() as cur:
            cur.execute(query)
