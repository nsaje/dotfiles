import structlog
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from dcron.cron import process_crontab_items

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Sync cron jobs from crontab file to DB DCronJobSettings model."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="crontab.txt", help="Crontab file to load jobs from.")

    def handle(self, *args, **options):
        file_name = options["file"]
        self.stdout.write("Reading crontab file %s" % file_name)

        try:
            process_crontab_items(file_name=file_name)

        except Exception as exc:
            logger.exception("Failed syncing distributed cron jobs.")
            raise CommandError("Failed syncing distributed cron jobs.") from exc

        self.stdout.write(self.style.SUCCESS("Successfully synced distributed cron jobs."))
