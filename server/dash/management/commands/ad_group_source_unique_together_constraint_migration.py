from django.db import connections

from utils.command_helpers import Z1Command

TABLE_NAME = "dash_adgroupsource"
INDEX_NAME = "dash_adgroupsource_source_id_ad_group_id_0feb89f6_uniq"
CONSTRAINT_NAME = "dash_adgroupsource_source_id_ad_group_id_0feb89f6_uniq"


class Command(Z1Command):
    help = "Performs custom DB migration instead of 0410_ad_group_source_unique_together_constraint that does not lock DB table"

    def add_arguments(self, parser):
        parser.add_argument("--forward", dest="forward", action="store_true", help="Perform a forward migration")
        parser.add_argument("--backward", dest="backward", action="store_true", help="Perform a backward migration")

    def handle(self, *args, **options):
        forward = options.get("forward", None)
        backward = options.get("backward", None)

        if not any((forward, backward)) or all((forward, backward)):
            self.stdout.write(self.style.ERROR("You must provide either forward or backward parameter"))
            return

        if forward is True:
            self.forward_migration()
        elif backward is True:
            self.backward_migration()

    def forward_migration(self):
        with connections["default"].cursor() as cursor:
            cursor.execute(
                """CREATE UNIQUE INDEX CONCURRENTLY %s ON %s USING btree ("source_id", "ad_group_id");"""
                % (INDEX_NAME, TABLE_NAME)
            )
            cursor.execute(
                """BEGIN; ALTER TABLE %s ADD CONSTRAINT %s UNIQUE USING INDEX %s; COMMIT;"""
                % (TABLE_NAME, CONSTRAINT_NAME, INDEX_NAME)
            )

    def backward_migration(self):
        with connections["default"].cursor() as cursor:
            cursor.execute("""BEGIN; ALTER TABLE %s DROP CONSTRAINT %s; COMMIT;""" % (TABLE_NAME, CONSTRAINT_NAME))
