import influx

from etl import maintenance
from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):
    def add_arguments(self, parser):
        parser.add_argument("--interactive", help="Output the values to stdout", action="store_true")

    def handle(self, *args, **options):

        interactive = bool(options.get("interactive", False))
        usage = maintenance.cluster_disk_usage()

        if interactive:
            print("Disk capacity: {} GB".format(usage.capacity_gbytes))
            print("Disk used: {} GB".format(usage.used_gbytes))
            print(
                "Disk free: {:d} GB ({:.2f}%)".format(
                    usage.free_gbytes, ((usage.free_gbytes * 100.0) / usage.capacity_gbytes)
                )
            )

            print_row("Database", "Table", "Used [MB]", "Used [% of total]", "Nr. rows", "Unsorted [MB]")
            print(100 * "-")

        else:
            influx.gauge("etl.cluster.disk_capacity", usage.capacity_gbytes)
            influx.gauge("etl.cluster.disk_used", usage.used_gbytes)
            influx.gauge("etl.cluster.disk_free", usage.free_gbytes)

        for t in maintenance.cluster_tables_disk_usage():
            if interactive:
                print_row(
                    t.database,
                    t.table,
                    str(t.mbytes),
                    "{:.2f}%".format(t.pct_of_total),
                    str(t.rows),
                    str(t.unsorted_mbytes),
                )
            else:
                influx.gauge("etl.cluster.table_disk_usage_mbytes", t.mbytes, table=t.table, database=t.database)
                influx.gauge("etl.cluster.table_disk_usage_pct", t.pct_of_total, table=t.table, database=t.database)
                influx.gauge("etl.cluster.table_unsorted_mbytes", t.unsorted_mbytes, table=t.table, database=t.database)
                influx.gauge("etl.cluster.table_rows", t.rows, table=t.table, database=t.database)


def print_row(*values):
    print("{: <16}".format(values[0]), end=" ")
    print("{: <30}".format(values[1]), end=" ")
    print("{: <12}".format(values[2]), end=" ")
    print("{: <16}".format(values[3]), end=" ")
    print("{: <10}".format(values[4]), end=" ")
    print("{: <10}".format(values[5]))
