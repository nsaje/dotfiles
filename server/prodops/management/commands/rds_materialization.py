import logging

import influx

from prodops.rds_materialization import rds_materialization
from utils.command_helpers import ExceptionCommand

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    ALL_ENTITIES = {i.TABLE: i for i in rds_materialization.RDS_MATERIALIAZED_VIEW}
    help = """
    Description:
        Run the RDS materialization process: Export data to S3 as CSV and load them in Stats DB.
    Options:
        --specific-table: run the command for a given entity.
    Available tables: {}
    """.format(
        ",".join(ALL_ENTITIES.keys())
    )

    def add_arguments(self, parser):
        parser.add_argument("--specific-table", type=str)

    @influx.timer("etl.rds_materialization")
    def handle(self, *args, **options):
        print(options)
        specific_table = options.get("specific_table", False)

        if specific_table:
            self._process_rds(self.ALL_ENTITIES.get(specific_table))
        else:
            for entity in self.ALL_ENTITIES.values():
                self._process_rds(entity)

    def _process_rds(self, entity):
        try:
            instance = entity()
            instance.extract_load_data()
            influx.incr("etl.rds_materialization", 1)
        except Exception:
            logger.exception("Error while processing %s RDS data: %s", instance.TABLE)
            pass
